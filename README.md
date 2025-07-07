
# Sistema Integrado de Gestión de Estacionamiento con tiempo real.

<img src="Logo-ResiPark.png" alt="resipark" />

## 📜 Descripción

El sistema se compone de dos módulos Visión por Computadora

Este proyecto es una solución completa y profesional para la gestión automatizada de un estacionamiento, utilizando técnicas avanzadas de visión por computadora. El sistema está dividido en dos módulos principales que operan de forma coordinada a principales integrados en una sola interfaz con pestañas:

1.  **🛂 Módulo de Control de Acceso:**
 través de una base de datos central.

    *   Utiliza una cámara para vigilar la entrada de un estacionamiento.
    *   Detecta vehículos que ingresan a una "zona de detección" configurable.
    *   Identifica el tipo de vehículo

## 🌟 Características Principales

- **Interfaz Gráfica Intuitiva:** Una única ventana con dos pestañas para una gestión centralizada:
  - **Control de Acceso:** Monitorea en tiempo real la entrada de vehículos.
  - **Estado del Estacionamiento:** Pro Auto, Camioneta).
    *   Localiza y recorta la placa del vehículo.
    *   Aplica OCR para leer los caracteres de la patente.
    *   Verifica si la patente pertenece a un usuario autorizadoporciona una vista general del estado de todos los espacios.
- **Detección Dual en la Entrada:**
 (`Estudiante` o `Profesor`) en una base de datos.
    *   Si el usuario está autorizado y hay espacio, asigna automáticamente un lugar de estacionamiento libre.

2.  **📊 Módulo de Monitore  - Reconoce el **tipo de vehículo** (Auto, Camioneta, etc.) que se aproxima.
  o de Estacionamiento:**
    *   Utiliza una segunda cámara (o una imagen estática) para monitoreo de estacionamientos- Detecta y lee la **patente del vehículo** mediante OCR (Reconocimiento Óptico de Caracterorear los espacios de estacionamiento).
    *   Detecta si cada espacio está `Libre` u `Ocupadoes).
- **Verificación de Usuarios:** Compara la patente detectada con una base de datos de usuarios autorizados (`Est`.
    *   Actualiza el estado de cada espacio en una base de datos central.
    *   Visualudiante`, `Profesor`).
- **Monitoreo de Espacios:** Analiza una imagen o video del estacionamiento paraiza el estado de cada espacio con un sistema de colores intuitivo.
    *   Proporciona un resumen en determinar el estado de cada espacio (`Libre`, `Ocupado`, `Reservado`).
- **Asignación tiempo real de la ocupación total.

Ambos módulos se comunican a través de una base de datos SQLite compartida, lo que permite un sistema desacoplado y robusto.

## ✨ Características Principales

- **D Inteligente:** Asigna automáticamente un espacio libre a los vehículos autorizados al momento de su ingreso.
- **Comunicación por Base de Datos:** Los dos módulos están desacoplados y se comunican de forma asíncrona a través deetección Dual:** Utiliza modelos YOLOv11 separados para la detección de vehículos/placas y para los espacios de estacionamiento una base de datos `SQLite`, lo que garantiza un sistema robusto y escalable.

## 🏛️ Arquitectura del.
- **OCR Integrado:** Emplea PaddleOCR para una lectura precisa de patentes.
- ** Sistema

El proyecto está diseñado de forma modular para separar responsabilidades y facilitar el mantenimiento.

1.  **Pestaña de Control de Acceso (`AccessControlTab`)**:
    - **Modelos Utilizados:** `YOLOv11`Asignación Automática:** Asigna inteligentemente el primer espacio libre a los vehículos autorizados.
- **Base de Datos Centralizada:** Usa SQLite para gestionar usuarios y el estado en tiempo real de cada espacio.
- **Interfaz para detección de vehículos y `YOLOv11` para detección de placas.
    - **OCR:** `PaddleOCR` para leer el texto de las patentes.
    - **Flujo de Trabajo:**
        1.  Un vehículo entra Gráfica Intuitiva:** Desarrollada con PyQt5, presenta la información de forma clara y organizada en pestañas.
 en la "zona de detección".
        2.  El sistema identifica el tipo de vehículo.
        3.  Se busca- **Comunicación entre Módulos:** La asignación en el módulo de acceso actualiza instantáneamente la vista del módulo de monitoreo gracias a un sistema de señales y slots de PyQt.
- **Optimización de Rendimiento:** La detección de patentes solo se activa cuando un vehículo entra en una zona específica, ahorrando recursos computacionales.

## 🚀 Posibles Mejoras Futuras

-   Implementar el monitoreo del estacionamiento con video en tiempo real en lugar de imágenes estáticas.
-   Añadir una función para registrar la salida de vehículos y liberar automáticamente sus espacios.
-   Crear un sistema de reportes para analizar la ocupación a lo largo del tiempo.
-   Integrar un sistema de pagos o tarifasissue" para discutirlo o envía un "pull request".
