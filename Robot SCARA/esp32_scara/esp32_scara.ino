#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

// --- 1. CONFIGURACIÓN DE RED ---
const char* ssid = "Redmi Note 13";   // INFINITUM86C2
const char* password = "22072207";   // ELd4TfVbHW

WiFiUDP udp;
unsigned int localPort = 4210;       // Puerto donde escucha el ESP32
unsigned int serverPort = 5005;      // Puerto donde escucha Python
char packetBuffer[255];

IPAddress serverIP;                  // Se llena automáticamente al recibir datos
bool connectionEstablished = false;  // Bandera para saber si ya nos hablaron

// Timer para el Heartbeat
unsigned long lastHeartbeat = 0;
const long heartbeatInterval = 1000; // Enviar ping cada 1 segundo

// --- 2. DEFINICIÓN DE OBJETOS SERVO ---
Servo servoBase;    
Servo servoCodo;    
Servo servoZ;        
Servo servoGripper;  

// --- 3. PINES REALES ---
#define PIN_BASE 5
#define PIN_CODO 4
#define PIN_Z    3
#define PIN_GRIP 2

// --- 4. CALIBRACIÓN ---
int offset_base = 85; 
int offset_codo = 90; 

const int ANGULO_ABIERTO = 20; 
const int ANGULO_CERRADO = 74; 

void moverRobot(float q1, float q2, float z, int grip);

void setup() {
  Serial.begin(115200);

  // Configuración de Servos
  servoBase.setPeriodHertz(50); servoBase.attach(PIN_BASE, 500, 2500);
  servoCodo.setPeriodHertz(50); servoCodo.attach(PIN_CODO, 500, 2500);
  servoZ.setPeriodHertz(50);    servoZ.attach(PIN_Z, 500, 2500);
  servoGripper.setPeriodHertz(50); servoGripper.attach(PIN_GRIP, 500, 2500);

  // Posición Inicial Segura
  servoBase.write(offset_base);
  servoCodo.write(offset_codo);
  servoZ.write(0);       
  servoGripper.write(ANGULO_ABIERTO);

  // Conexión WiFi
  Serial.print("Conectando a WiFi: ");
  Serial.println(ssid);
  
  // Aseguramos modo estación (Cliente)
  WiFi.mode(WIFI_STA); 
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // --- ¡ESTO FALTABA! ---
  // Desactiva el ahorro de energía para que el WiFi nunca se duerma.
  // Crucial para movimiento fluido en tiempo real.
  WiFi.setSleep(false); 
  
  Serial.println("\n--- CONECTADO ---");
  Serial.print("IP del Robot: ");
  Serial.println(WiFi.localIP()); 
  
  udp.begin(localPort);
  Serial.println("Esperando primer comando para sincronizar IP del servidor...");
}

void loop() {
  // 1. RECEPCIÓN DE COMANDOS
  int packetSize = udp.parsePacket();
  
  if (packetSize) {
    // Autodescubrimiento del servidor
    if (!connectionEstablished) {
        serverIP = udp.remoteIP();
        connectionEstablished = true;
        Serial.print("✅ Servidor detectado en: ");
        Serial.println(serverIP);
    }
    // Actualizar si la IP cambia
    if (udp.remoteIP() != serverIP) {
        serverIP = udp.remoteIP();
    }

    int len = udp.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0;
    
    float q1, q2, z;
    int grip;
    int n = sscanf(packetBuffer, "%f,%f,%f,%d", &q1, &q2, &z, &grip);
    
    if (n == 4) {
        moverRobot(q1, q2, z, grip);
    }
  }

  // 2. HEARTBEAT (PING CONSTANTE)
  unsigned long currentMillis = millis();
  if (connectionEstablished && (currentMillis - lastHeartbeat >= heartbeatInterval)) {
    lastHeartbeat = currentMillis;
    
    udp.beginPacket(serverIP, serverPort);
    udp.write((const uint8_t*)"PING", 4);
    udp.endPacket();
  }
}

void moverRobot(float q1, float q2, float z, int grip) {
  int angulo_base_servo = constrain(offset_base + q1, 0, 180);
  int angulo_codo_servo = constrain(offset_codo + q2, 0, 180);
  int angulo_z_servo = map(z * 10, 0, 55, 0, 180); 
  angulo_z_servo = constrain(angulo_z_servo, 0, 180);

  servoBase.write(angulo_base_servo);
  servoCodo.write(angulo_codo_servo);
  servoZ.write(angulo_z_servo);
  
  if (grip == 1) servoGripper.write(ANGULO_CERRADO); 
  else servoGripper.write(ANGULO_ABIERTO); 
}