# find_binaries
Este es un algoritmo que combina métodos estadísticos con modelos de Machine Learning que nos ayuda a encontrar estrellas binarias.

# Stars Binary Analysis

Este proyecto tiene como objetivo analizar si un conjunto de estrellas cumple con la característica de ser pares binarios. Para llevar a cabo este análisis, se utilizan varios archivos, incluyendo `funciones.py`, `main.py`, `modelo_reglog.joblib` y `knn_model.joblib`. A continuación, se describen brevemente cada uno de ellos:

- `funciones.py`: Este archivo contiene diversas funciones que se utilizan en el análisis de estrellas binarias. Estas funciones incluyen operaciones matemáticas, procesamiento de datos y cálculos necesarios para el análisis.

- `main.py`: El archivo `main.py` es el punto de entrada principal del proyecto. Aquí se realiza la carga de los modelos de regresión logística y KNN almacenados en los archivos `modelo_reglog.joblib` y `knn_model.joblib`, respectivamente. Además, se realiza la lectura de un archivo CSV que contiene los datos de las estrellas a analizar.

- `modelo_reglog.joblib`: Este archivo contiene un modelo entrenado de regresión logística utilizado en el análisis de estrellas binarias. El modelo es cargado y utilizado en el archivo `main.py` para realizar predicciones sobre los datos de entrada.

- `knn_model.joblib`: Este archivo contiene un modelo entrenado de K-Nearest Neighbors (KNN) utilizado en el análisis de estrellas binarias. Al igual que el modelo de regresión logística, este modelo es cargado y utilizado en el archivo `main.py` para realizar predicciones sobre los datos de entrada.

Además de los archivos mencionados, se requiere tener un archivo CSV que contenga los datos de las estrellas a analizar para determinar si son pares binarios. Asegúrate de tener todos estos archivos en el mismo directorio para que el análisis se realice correctamente. Este archivo CSV debe tener las siguientes columnas:

- `source_id`: Identificador único de la estrella.
- `ra`: Coordenada de ascensión recta de la estrella.
- `dec`: Coordenada de declinación de la estrella.
- `parallax`: Paralaje de la estrella.
- `parallax error`: Error asociado al valor de paralaje.
- `pmra`: Movimiento propio en ascensión recta de la estrella.
- `pmdec`: Movimiento propio en declinación de la estrella.
- `pmra error`: Error asociado al movimiento propio en ascensión recta.
- `pmdec error`: Error asociado al movimiento propio en declinación.
- `phot g mean mag`: Magnitud media del brillo en el filtro fotométrico g.

Estas columnas contienen información clave para el análisis de las estrellas y su clasificación como pares binarios. Asegúrate de que el archivo CSV que utilices tenga estas columnas correctamente definidas y que los datos estén formateados adecuadamente.

**Nota:** El archivo `knn_model.joblib` se encuentra en el directorio "assets" del repositorio y no está disponible para su visualización directa en GitHub. Sin embargo, puedes descargarlo y colocarlo en el mismo directorio que los demás archivos para su correcto funcionamiento.

Si tienes alguna pregunta o necesitas más información, no dudes en contactarme a luciano.godoi.caceres@gmail.com. ¡Buena suerte con tu análisis de estrellas binarias!


