import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import socket
import threading
import time
import sys
from scara_kinematics import ScaraRobot

app = Flask(__name__)
# Configuración para permitir conexiones desde cualquier origen (CORS) y modo asíncrono
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ==========================================
# --- CONFIGURACIÓN DE RED ---
# ==========================================
# IP inicial del ESP32 (se actualizará automáticamente si el ESP32 manda PING)
ESP32_IP = "10.85.197.201"      # 10.85.197.201
ESP32_PORT_SEND = 4210     # Puerto donde el ESP32 escucha comandos
SERVER_PORT_LISTEN = 5005  # Puerto donde este servidor escucha el PING del robot

sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ==========================================
# --- ESTADO GLOBAL ---
# ==========================================
robot = ScaraRobot() # Instancia de tu clase matemática
robot.grip = 0 

rutina_guardada = []
velocidad_actual = 50
emergency_active = False 

pendant_sid = None          # ID de sesión del celular (Teach Pendant)
robot_last_seen = 0         # Timestamp del último PING recibido
ROBOT_TIMEOUT = 4.0         # Segundos para considerar al robot desconectado

last_manual_command_time = 0 

# ==========================================
# 1. FUNCIONES AUXILIARES
# ==========================================
def get_local_ip():
    """Obtiene la IP real de la PC en la red WiFi para mostrar en el Pendant"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # No envía nada, solo determina la interfaz de salida
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def enviar_a_esp32(q1, q2, z, grip):
    """Empaqueta y envía comandos UDP al microcontrolador"""
    # Actualizamos el estado interno del objeto robot
    robot.q1 = q1
    robot.q2 = q2
    robot.z = z
    robot.grip = int(grip)
    
    # Formato CSV simple: "q1,q2,z,grip"
    mensaje = f"{q1:.2f},{q2:.2f},{z:.2f},{int(grip)}"
    try:
        sock_send.sendto(mensaje.encode(), (ESP32_IP, ESP32_PORT_SEND))
    except Exception:
        pass 

def enviar_keepalive():
    """Mantiene la conexión viva con el ESP32"""
    try:
        sock_send.sendto(b"KEEPALIVE", (ESP32_IP, ESP32_PORT_SEND))
    except Exception:
        pass

def get_system_status():
    """Resumen del estado del sistema para el frontend"""
    is_robot_alive = (time.time() - robot_last_seen) < ROBOT_TIMEOUT
    return {
        'speed': velocidad_actual,
        'estop': emergency_active,
        'rutina': bool(rutina_guardada) and not emergency_active,
        'pendant': pendant_sid is not None,                       
        'robot_connected': is_robot_alive                         
    }

def emit_gemelo_update(broadcast=False):
    """
    Envía el estado completo al navegador (Panel y Pendant).
    Calcula FK y Matriz Homogénea antes de enviar.
    """
    # Calculamos la posición cartesiana actual basada en los ángulos actuales
    coords_data = robot.forward_kinematics(robot.q1, robot.q2, robot.z)
    
    payload = {
        'angulos': {'q1': robot.q1, 'q2': robot.q2, 'z': robot.z, 'grip': robot.grip},
        'coords': coords_data,
        'status': get_system_status()
    }
    socketio.emit('actualizar_gemelo', payload)

# ==========================================
# 2. HILOS DE FONDO (Background Threads)
# ==========================================
def udp_receiver_loop():
    """Escucha PINGS del ESP32 para autodescubrimiento de IP"""
    global robot_last_seen, ESP32_IP
    port_ok = False
    try:
        sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_listen.bind(('0.0.0.0', SERVER_PORT_LISTEN))
        sock_listen.settimeout(0.5)
        print(f"👂 Escuchando PINGS en puerto {SERVER_PORT_LISTEN}...")
        port_ok = True
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: Puerto {SERVER_PORT_LISTEN} ocupado. {e}")
        return 

    if not port_ok: return

    while True:
        try:
            data, addr = sock_listen.recvfrom(1024)
            message = data.decode('utf-8', errors='ignore')
            if "PING" in message:
                robot_last_seen = time.time()
                # Si la IP cambió, la actualizamos dinámicamente
                if addr[0] != ESP32_IP:
                    ESP32_IP = addr[0]
                    print(f"🔄 Robot IP actualizada: {ESP32_IP}")
        except socket.timeout:
            pass
        except Exception:
            pass
        eventlet.sleep(0.1) 

def keep_alive_loop():
    """Hilo principal de 'latido' del servidor"""
    print("💓 Sistema Vital Iniciado...")
    while True:
        # Solo enviamos KeepAlive si no estamos moviendo manualmente (para no saturar red)
        if (time.time() - last_manual_command_time) > 0.5:
            enviar_keepalive() 
        
        # Actualizamos la interfaz web periódicamente (1Hz)
        emit_gemelo_update(broadcast=True)
        eventlet.sleep(1.0)

# ==========================================
# 3. RUTAS WEB
# ==========================================
@app.route('/')
def index(): return render_template('panel.html') # Por defecto abre el panel

@app.route('/panel')
def panel(): return render_template('panel.html')

@app.route('/pendant')
def pendant(): return render_template('pendant.html')

@app.route('/ajustador')
def ajustador(): return render_template('scara_ajustador.html')

@app.route('/carmen')
def carmen(): return render_template('carmen.html')

@app.route('/panelcarmen')
def panelcarmen(): return render_template('panelcarmen.html')

@app.route('/manguera')
def manguera(): return render_template('scara_manguera.html')

# ==========================================
# 4. EVENTOS SOCKET.IO (Lógica de Control)
# ==========================================
@socketio.on('connect')
def handle_connect(): 
    print(f"➕ Cliente conectado: {request.sid}")

@socketio.on('register_pendant')
def handle_pendant_reg():
    global pendant_sid
    pendant_sid = request.sid
    print(f"📱 TEACH PENDANT REGISTRADO")
    ip_address = get_local_ip()
    emit('server_status', {'ip': ip_address})
    emit_gemelo_update()

@socketio.on('disconnect')
def handle_disconnect():
    global pendant_sid
    if request.sid == pendant_sid:
        print("📱 TEACH PENDANT: Desconectado")
        pendant_sid = None
    emit_gemelo_update()

@socketio.on('cambiar_velocidad')
def handle_speed_change(data):
    global velocidad_actual
    velocidad_actual = int(data['velocidad'])
    emit_gemelo_update()

@socketio.on('comando_manual')
def handle_manual(data):
    """Mueve el robot por articulaciones (Joint Jogging)"""
    global last_manual_command_time
    if emergency_active: return
    
    last_manual_command_time = time.time()

    # Recibimos datos crudos
    q1 = float(data['q1'])
    q2 = float(data['q2'])
    z = float(data['z'])
    grip = int(data['grip'])

    # Enviamos al hardware
    enviar_a_esp32(q1, q2, z, grip)
    
    # Calculamos la cinemática directa para actualizar el 3D
    robot.forward_kinematics(q1, q2, z)
    
    # Actualizamos a todos los clientes (Panel y Pendant)
    emit_gemelo_update()

# ---------------------------------------------------------
#  MODIFICADO: EVENTO IK CON MOVIMIENTO SUAVE (INTERPOLACIÓN)
# ---------------------------------------------------------
@socketio.on('comando_ik')
def handle_ik_move(data):
    """Recibe X, Y, Z y calcula los ángulos para mover suavemente"""
    global last_manual_command_time
    
    if emergency_active:
        socketio.emit('notificacion', {'msg': '❌ ERROR: E-STOP ACTIVO', 'type': 'error'})
        return

    try:
        x_target = float(data['x'])
        y_target = float(data['y'])
        z_target = float(data['z'])
        
        # 1. Calcular el destino final (Ángulos Objetivo)
        resultado = robot.inverse_kinematics(x_target, y_target, z_target)
        
        if resultado is None:
            print(f"⚠️ Punto inalcanzable: {x_target}, {y_target}, {z_target}")
            socketio.emit('notificacion', {'msg': '⚠️ PUNTO FUERA DE ALCANCE', 'type': 'warning'})
        else:
            # Desempaquetamos los ángulos destino
            q1_target, q2_target, z_target_piston = resultado
            
            # 2. Capturar la posición actual (Ángulos Inicio)
            q1_start = robot.q1
            q2_start = robot.q2
            z_start  = robot.z
            
            # 3. Configuración de interpolación
            PASOS = 100  # Cantidad de pasos para suavidad (más pasos = más fluido)
            
            # Bloqueamos el keepalive manual mientras nos movemos
            last_manual_command_time = time.time() + 9999
            
            socketio.emit('notificacion', {'msg': 'MOVIMIENTO JOINT (ARCO)...', 'type': 'success'})

            # 4. Bucle de Movimiento (Interpolación Lineal)
            for i in range(1, PASOS + 1):
                if emergency_active: break
                
                # t es el porcentaje de avance (0.0 a 1.0)
                t = i / PASOS
                
                # Calcular posiciones intermedias
                current_q1 = q1_start + (q1_target - q1_start) * t
                current_q2 = q2_start + (q2_target - q2_start) * t
                current_z  = z_start  + (z_target_piston - z_start) * t
                
                # Enviar al hardware y al gemelo
                enviar_a_esp32(current_q1, current_q2, current_z, robot.grip)
                robot.forward_kinematics(current_q1, current_q2, current_z)
                emit_gemelo_update()
                
                # CÁLCULO DE VELOCIDAD
                # Ajustamos el 'sleep' según la velocidad_actual (0-100%)
                factor = max(velocidad_actual, 5) / 100.0
                delay = 0.02 / factor 
                eventlet.sleep(delay)
            
            last_manual_command_time = time.time() # Liberar KeepAlive
            
            socketio.emit('notificacion', {'msg': f'LLEGADA: X{x_target} Y{y_target}', 'type': 'success'})

    except ValueError:
        socketio.emit('notificacion', {'msg': '❌ Error en datos', 'type': 'error'})

# ---------------------------------------------------------
#  NUEVO: EVENTO PARA MOVIMIENTO LINEAL (LÍNEA RECTA)
# ---------------------------------------------------------
@socketio.on('comando_lineal')
def handle_linear_move(data):
    """Recibe X, Y, Z y mueve el efector en LÍNEA RECTA"""
    global last_manual_command_time
    
    if emergency_active:
        socketio.emit('notificacion', {'msg': '❌ ERROR: E-STOP ACTIVO', 'type': 'error'})
        return

    try:
        # 1. Datos del destino
        x_target = float(data['x'])
        y_target = float(data['y'])
        z_target = float(data['z'])
        
        # 2. Obtener coordenadas cartesianas ACTUALES (Punto de inicio)
        # Usamos Forward Kinematics para saber dónde estamos exactamente en X,Y
        current_coords = robot.forward_kinematics(robot.q1, robot.q2, robot.z)
        x_start = current_coords['final']['x']
        y_start = current_coords['final']['y']
        z_start = robot.D1_OFFSET - robot.z # <--- ASÍ ES CORRECTO ✅ (12.3 - extension)
        
        # 3. Configuración de interpolación
        PASOS = 100 # Más pasos para garantizar la rectitud de la línea
        last_manual_command_time = time.time() + 9999
        
        socketio.emit('notificacion', {'msg': 'TRAZANDO LINEA RECTA...', 'type': 'success'})
        
        valid_path = True

        # 4. Bucle de Interpolación Cartesiana
        for i in range(1, PASOS + 1):
            if emergency_active: break
            
            t = i / PASOS
            
            # --- LA MAGIA LINEAL ---
            # Calculamos el punto X, Y, Z intermedio geométrico
            next_x = x_start + (x_target - x_start) * t
            next_y = y_start + (y_target - y_start) * t
            next_z = z_start + (z_target - z_start) * t
            
            # Calculamos IK para este punto intermedio exacto
            # Esto obliga a los motores Q1 y Q2 a coordinarse para mantener la recta
            ik_result = robot.inverse_kinematics(next_x, next_y, next_z)
            
            if ik_result is None:
                socketio.emit('notificacion', {'msg': '⚠️ TRAYECTORIA IMPOSIBLE (SINGULARIDAD)', 'type': 'error'})
                valid_path = False
                break
            
            # Extraemos los ángulos resultantes para este milímetro de avance
            q1_next, q2_next, z_next_piston = ik_result
            
            # Enviamos
            enviar_a_esp32(q1_next, q2_next, z_next_piston, robot.grip)
            robot.forward_kinematics(q1_next, q2_next, z_next_piston)
            emit_gemelo_update()
            
            # Velocidad
            factor = max(velocidad_actual, 5) / 100.0
            delay = 0.02 / factor 
            eventlet.sleep(delay)
        
        last_manual_command_time = time.time()
        
        if valid_path:
            socketio.emit('notificacion', {'msg': 'MOVIMIENTO LINEAL FINALIZADO', 'type': 'success'})

    except ValueError:
        socketio.emit('notificacion', {'msg': '❌ Error en datos', 'type': 'error'})
# ---------------------------------------------------------

@socketio.on('request_status')
def send_status():
    emit_gemelo_update()
    ip_address = get_local_ip()
    emit('server_status', {'ip': ip_address})

@socketio.on('guardar_punto')
def guardar_punto(data):
    if emergency_active: return
    rutina_guardada.append(data)
    socketio.emit('notificacion', {'msg': f'Punto {len(rutina_guardada)} guardado', 'type': 'success'})
    emit_gemelo_update() 

@socketio.on('borrar_rutina')
def borrar_rutina():
    global rutina_guardada
    rutina_guardada = []
    emit_gemelo_update()

@socketio.on('ejecutar_rutina')
def ejecutar_rutina():
    """Ejecuta la lista de puntos interpolando el movimiento"""
    global emergency_active, last_manual_command_time
    if emergency_active or not rutina_guardada: return
    
    print("▶ Ejecutando Rutina...")
    emit_gemelo_update() 
    
    PASOS = 30 
    DELAY_BASE = 0.005 
    
    # Bloqueamos el KeepAlive manual mientras corre la rutina
    last_manual_command_time = time.time() + 99999 

    q1_act, q2_act, z_act = robot.q1, robot.q2, robot.z
    
    for punto in rutina_guardada:
        if emergency_active: break
        
        q1_tgt, q2_tgt = float(punto['q1']), float(punto['q2'])
        z_tgt, grip = float(punto['z']), int(punto['grip'])
        
        # Interpolación Lineal
        for paso in range(1, PASOS + 1):
            if emergency_active: break
            
            t = paso / PASOS
            q1 = q1_act + (q1_tgt - q1_act) * t
            q2 = q2_act + (q2_tgt - q2_act) * t
            z  = z_act  + (z_tgt - z_act) * t
            
            enviar_a_esp32(q1, q2, z, grip)
            robot.forward_kinematics(q1, q2, z)
            
            if paso % 5 == 0: emit_gemelo_update()
            
            factor = max(velocidad_actual, 1) / 100.0
            eventlet.sleep(DELAY_BASE / factor)
        
        q1_act, q2_act, z_act = q1_tgt, q2_tgt, z_tgt
        eventlet.sleep(0.5 / factor) # Pausa en cada punto
    
    last_manual_command_time = 0 # Liberar KeepAlive
    print("⏹ Rutina Finalizada")
    emit_gemelo_update() 

@socketio.on('emergency_stop')
def handle_emergency():
    global emergency_active
    emergency_active = not emergency_active
    print(f"🚨 ESTOP CAMBIO: {emergency_active}")
    emit_gemelo_update()

if __name__ == '__main__':
    # Lanzar hilos
    eventlet.spawn(udp_receiver_loop)
    eventlet.spawn(keep_alive_loop)
    
    print("🚀 SCARA SERVER V10 (LINEAR & JOINT MOTION) INICIADO")
    print(f"👉 Panel en: http://{get_local_ip()}:5000/panel")
    
    # Arrancar Servidor
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)