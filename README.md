
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
    *   Utiliza una segunda cámara (o una imagen estática) para monit- Detecta y lee la **patente del vehículo** mediante OCR (Reconocimiento Óptico de Caracterorear los espacios de estacionamiento.
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
- **Comunicación por Base de Datos:** Los dos módulos están desacoplados y se comunican de forma asíncrona a través deetección Dual:** Utiliza modelos YOLOv8 separados para la detección de vehículos/placas y para los espacios de estacionamiento una base de datos `SQLite`, lo que garantiza un sistema robusto y escalable.

## 🏛️ Arquitectura del.
- **OCR Integrado:** Emplea PaddleOCR para una lectura precisa de patentes.
- ** Sistema

El proyecto está diseñado de forma modular para separar responsabilidades y facilitar el mantenimiento.

1.  **Pestaña de Control de Acceso (`AccessControlTab`)**:
    - **Modelos Utilizados:** `YOLOv8`Asignación Automática:** Asigna inteligentemente el primer espacio libre a los vehículos autorizados.
- **Base de Datos Centralizada:** Usa SQLite para gestionar usuarios y el estado en tiempo real de cada espacio.
- **Interfaz para detección de vehículos y `YOLOv8` para detección de placas.
    - **OCR:** `PaddleOCR` para leer el texto de las patentes.
    - **Flujo de Trabajo:**
        1.  Un vehículo entra Gráfica Intuitiva:** Desarrollada con PyQt5, presenta la información de forma clara y organizada en pestañas.
 en la "zona de detección".
        2.  El sistema identifica el tipo de vehículo.
        3.  Se busca- **Comunicación entre Módulos:** La asignación en el módulo de acceso actualiza instantáneamente la vista del módulo de monitoreo gracias a un sistema de señales y slots de PyQt.
- **Optimización de Rendimiento:** La detección de patentes solo se activa cuando un vehículo entra en una zona específica, ahorrando recursos computacionales.

## y recorta la patente dentro del vehículo detectado.
        4.  Se aplica OCR para leer la patente.
         🛠️ Requisitos e Instalación

Para ejecutar este proyecto, necesitas tener Python 3.10 o superior.5.  Se verifica si el usuario está en la base de datos.
        6.  Si está autorizado, consulta la base Puedes instalar todas las dependencias necesarias usando el archivo `requirements.txt` proporcionado.

### 1. Cl de datos en busca de un espacio `Libre`.
        7.  Si encuentra un espacio, lo marca como `Reservado` en la base de datos y se lo notifica al conductor.

2.  **Pestaña de Estadoona el Repositorio

```bash
git clone https://github.com/tu_usuario/tu_repositorio. del Estacionamiento (`ParkingStatusTab`)**:
    - **Modelo Utilizado:** `YOLOv8` entrengit
cd tu_repositorio
```

### 2. (Recomendado) Crea un Entorno Virtualado para detectar espacios de estacionamiento y clasificarlos como `Libre` u `Ocupado`.
    - **Flujo de Trabajo:**
        1.  El usuario carga una imagen del estacionamiento.
        2.

Es una buena práctica trabajar en un entorno virtual para aislar las dependencias del proyecto.

```bash
# Windows
  El sistema analiza la imagen para determinar el estado físico de cada espacio.
        3.  Compara el estado físico detectado con el estado lógico en la base de datos.
        4.  Actualiza la base de datos depython -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instala las Librerías

Usa el gestor de paquetes `pip` para instalar todas las librerías desde el archivo `requirements.txt`. forma inteligente (ej: un vehículo que se va libera el espacio; un vehículo que llega confirma una ocupación).
        5.

```bash
pip install -r requirements.txt
```

El archivo `requirements.txt` contiene las siguientes librerías  Muestra una vista visual del estacionamiento con los estados actualizados, así como un resumen y una tabla detallada. principales:

- `PyQt5`: Para la interfaz gráfica.
- `opencv-python`: Para el procesamiento de imágenes

3.  **Base de Datos Central (`estacionamiento.db`)**:
    - Actúa como el y video.
- `ultralytics`: Para el modelo de detección de objetos YOLOv8.
- `paddleocr "cerebro" y la memoria del sistema.
    - Contiene dos tablas principales: `usuarios` y ``: Para el Reconocimiento Óptico de Caracteres.
- `paddlepaddle`: Dependencia principal deestacionamientos`.
    - Permite que ambas pestañas se comuniquen sin estar directamente acopladas.

 PaddleOCR.
- `numpy`: Para manipulación de arrays numéricos.

### 4. (Opcional)## ⚙️ Requisitos e Instalación

Para ejecutar este proyecto, necesitas tener Python 3.10 o superior y las siguientes librerías. Puedes instalarlas todas juntas creando un archivo `requirements.txt` y ejecutando `pip install -r Aceleración por GPU

Para un rendimiento significativamente mejor, especialmente con video en tiempo real, se recomienda usar una GPU NVIDIA requirements.txt`.

### Librerías Necesarias

Crea un archivo `requirements.txt` con el siguiente contenido. Esto requiere la instalación manual de versiones específicas de `torch` y `paddlepaddle`.

> **Nota:** Asegúrate de tener los drivers de NVIDIA y el CUDA Toolkit instalados.

```bash
# Desinstala primero las versiones de CPU
pip uninstall torch paddlepaddle

# Instala las versiones para GPU (ejemplo para CUDA 11.8):

```txt
# Framework de Visión por Computadora (Detección de Objetos)
ultralytics

# Framework de Visión por Computadora (Procesamiento de Imágenes)
opencv-python

# Reconocimiento Ópt
# Para YOLO:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whico de Caracteres (OCR)
paddleocr>=2.0.1

# Dependencia principal de PaddleOCR
paddlepaddle

# Framework para la Interfaz Gráfica de Usuario (GUI)
PyQt5
l/cu118
# Para PaddleOCR:
pip install paddlepaddle-gpu==2.6.```

### Pasos para la Instalación

1.  **Clona el repositorio o descarga los archivos del proyecto.**

1
```

## 🚀 Cómo Ejecutar

1.  **Modelos:** Asegúrate de que los archivos de los modelos YOLO (`.pt`) se encuentren en las rutas especificadas dentro del script de Python.
2.  **Ej2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv vecuta la Aplicación Principal:** Abre una terminal en la raíz del proyecto y ejecuta el siguiente comando:

    ```bash
    env
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3python tu_script_principal.py
    ```

3.  **Uso de la Interfaz:**
    .  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Opcional pero Recomendado) Aceleración por GPU:**
    Si tienes una tarjeta gráfica NVIDIA*   En la pestaña "Control de Acceso", haz clic en "Elegir archivo de video" para cargar un video de la cámara de entrada.
    *   En la pestaña "Estado del Estacionamiento", haz clic en compatible con CUDA, el rendimiento mejorará drásticamente. Para ello, instala las versiones de `torch` y `paddle "Analizar Imagen y Actualizar BD" para cargar una imagen del estacionamiento y sincronizar el estado.
    *   paddle` para GPU. Consulta sus guías oficiales para obtener los comandos de instalación específicos para tu versión de CUDA.

    *Ejemplo para CUDA 11.8:*
    ```bash
    # Primero, desinstala las versionesObserva cómo el sistema procesa los vehículos y actualiza el estado del estacionamiento en tiempo real.

## 🤝 de CPU
    pip uninstall torch paddlepaddle

    # Instala PyTorch para GPU (YOLO lo usará)
     Contribuciones

Las contribuciones son bienvenidas. Si tienes ideas para mejorar el sistema, por favor, abre un "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

    # Instala PaddlePaddle para GPU
    pip install paddlepaddle-gpu==2.6.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

## ▶️ Cómo Ejecutar

1.  **Coloca los modelos entrenados (`.pt`)** en las rutas especificadas en la sección de "Configuración Global" del script.
2.  **Ejecuta el script principal** desde tu terminal:
    ```bash
    python tu_script_principal.py
    ```
3.  La aplicación se abrirá en pantalla completa.
4.  En la pestaña "Control de Acceso", carga un video de la entrada de vehículos.
5.  En la pestaña "Estado del Estacionamiento", carga una imagen del estacionamiento para sincronizar el estado inicial.

## 🚀 Posibles Mejoras Futuras

-   Implementar el monitoreo del estacionamiento con video en tiempo real en lugar de imágenes estáticas.
-   Añadir una función para registrar la salida de vehículos y liberar automáticamente sus espacios.
-   Crear un sistema de reportes para analizar la ocupación a lo largo del tiempo.
-   Integrar un sistema de pagos o tarifasissue" para discutirlo o envía un "pull request".
