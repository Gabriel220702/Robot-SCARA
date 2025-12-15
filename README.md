# 🤖 SCARA RRP Robot & Digital Twin
**Proyecto Integrador de Ingeniería Mecatrónica**

Este repositorio contiene el código fuente, modelos 3D y documentación de un Robot SCARA (Selective Compliance Assembly Robot Arm) de configuración RRP, diseñado desde cero. El sistema integra un **Gemelo Digital (Digital Twin)** que opera en tiempo real sincronizado con el robot físico.

## 🚀 Características Principales
* **Arquitectura IoT:** Comunicación bidireccional UDP/WebSockets entre el robot físico (ESP32) y el servidor de control.
* **Gemelo Digital:** Visualización 3D en navegador web utilizando Three.js, mostrando la **Matriz de Transformación Homogénea** y trazado de trayectoria en vivo.
* **Control Cinemático:**
    * **Cinemática Directa (FK):** Cálculo de posición (X,Y,Z) basado en ángulos.
    * **Cinemática Inversa (IK):** Algoritmo geométrico para alcanzar coordenadas específicas.
    * **Planificación de Trayectoria:** Interpolación lineal y articular.
* **Hardware Custom:** Diseño mecánico optimizado para impresión 3D (PLA/PETG) con gestión térmica activa.

## 🛠️ Stack Tecnológico

### Software
* **Backend:** Python 3.x (Flask, NumPy para álgebra matricial).
* **Frontend:** HTML5, JavaScript, Socket.IO, Three.js (Motor 3D).
* **Firmware:** C++ (Arduino Framework) para ESP32-C3 Super Mini.

### Hardware
* **Actuadores:** Servomotor 70kg·cm (Base), MG996R (Codo), MG995 (Eje Z).
* **Controlador:** ESP32-C3.
* **Potencia:** Regulación dual (8V y 6V) con fuentes conmutadas XL4016.

## 📏 Especificaciones Técnicas
| Parámetro | Valor |
| :--- | :--- |
| **Eslabón L1** | 29.5 cm |
| **Eslabón L2** | 12.3 cm |
| **Eje Z (Carrera)** | 5.5 cm |
| **Grados de Libertad** | 3 (R-R-P) + Gripper |
| **Comunicación** | WiFi (UDP + WebSockets) |

## 📸 Galería
*(Aquí puedes subir tus fotos del robot y capturas del panel web)*

## 👨‍💻 Autor
**Gabriel Carrizales**
Ingeniería Mecatrónica
