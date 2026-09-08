# 🤖 **SCARA RRP - Gemelo Digital IoT** 🏭

## 📌 **Autor:** Gabriel Carrizales  
📍 **Institución:** Instituto Tecnológico Superior de la Región de los Llanos (ITSRLL)  
🎓 **Carrera:** Ingeniería Mecatrónica  

---

## 📖 **Descripción del Proyecto** 
Este proyecto consiste en el diseño, construcción y control de un **Robot SCARA** (Selective Compliance Assembly Robot Arm) de configuración RRP. El sistema integra un **Gemelo Digital (Digital Twin)** que opera en tiempo real, permitiendo monitorear y controlar el robot físico desde una interfaz web.

Es una implementación completa de **Industria 4.0**, combinando diseño mecánico (CAD/CAM), cinemática avanzada, electrónica de potencia y arquitectura IoT Cliente-Servidor.

---

## 📂 **Características Principales** 🔹 
**Arquitectura IoT Full-Stack** 🌐  
- Comunicación bidireccional en tiempo real vía **UDP y WebSockets**.  
- Sincronización milimétrica entre el robot físico y su réplica virtual.  

🔹 **Gemelo Digital (Digital Twin)** 🖥️  
- Visualización 3D interactiva en navegador web utilizando **Three.js**.  
- Cálculo y visualización en vivo de la **Matriz de Transformación Homogénea (T)**.  
- Trazado de trayectorias y delimitación del espacio de trabajo.  

🔹 **Diseño Mecánico Personalizado** 🛠️  
- Estructura optimizada para manufactura aditiva (Impresión 3D en PLA/PETG).  
- Sistema de transmisión RRP (2 Grados de Libertad Rotacionales + 1 Lineal).  

🔹 **Control Cinemático Avanzado** 📐  
- **Cinemática Directa (FK):** Cálculo de coordenadas (X, Y, Z) en tiempo real.  
- **Cinemática Inversa (IK):** Algoritmos geométricos para posicionamiento preciso.  
- **Planificación de Trayectorias:** Interpolación lineal y articular.  

---

## 📊 **Especificaciones Técnicas** 
| Parámetro | Valor / Descripción |
| :--- | :--- |
| **Configuración** | SCARA RRP (3 GDL + Efector Final) |
| **Eslabón L1** | 29.5 cm (Eje Base a Codo) |
| **Eslabón L2** | 12.3 cm (Eje Codo a Muñeca) |
| **Eje Z (Carrera)** | 5.5 cm (Actuador Lineal) |
| **Capacidad de Carga** | ~250g (Payload) |
| **Actuador Base** | Servo Alto Torque (70 kg·cm) |

---

## 💻 **Tecnologías Utilizadas** 
✅ **Python (Flask)** – Backend y Servidor de Cálculo Cinemático  
✅ **ESP32 (C++)** – Firmware del Controlador y Gestión de Hardware  
✅ **Three.js / JavaScript** – Motor Gráfico para el Gemelo Digital  
✅ **Socket.IO** – Protocolo de comunicación en tiempo real  
✅ **SolidWorks** – Diseño CAD y validación mecánica  

---

## 👥 **Integrantes del Equipo** 
Proyecto desarrollado como integración de competencias de Ingeniería Mecatrónica, abarcando desde la manufactura hasta el desarrollo de software de control.

---

## 📩 **Contacto** 
Para dudas técnicas sobre la implementación del Gemelo Digital o el diseño mecánico:  

📌 **GitHub:** https://github.com/Gabriel220702  
📌 **LinkedIn:** https://www.linkedin.com/in/gabriel-carrizales/

---

🚀 **Ingeniería Mecatrónica aplicada a la Industria 4.0** 🦾⚡
