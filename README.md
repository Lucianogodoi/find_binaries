# find_binaries
Este es un algoritmo que combina métodos estadísticos con modelos de Machine Learning que nos ayuda a encontrar estrellas binarias.

# Stars Binary Analysis

Este proyecto tiene como objetivo analizar si un conjunto de estrellas cumple con la característica de ser pares binarios. Para llevar a cabo este análisis, se utilizan varios archivos, incluyendo `funciones.py`, `main.py`, `modelo_reglog.joblib` y `knn_model.joblib`. A continuación, se describen brevemente cada uno de ellos:

- `funciones.py`: Este archivo contiene diversas funciones que se utilizan en el análisis de estrellas binarias. Estas funciones incluyen operaciones matemáticas, procesamiento de datos y cálculos necesarios para el análisis.

- `main.py`: El archivo `main.py` es el punto de entrada principal del proyecto. Aquí se realiza la carga de los modelos de regresión logística y KNN almacenados en los archivos `modelo_reglog.joblib` y `knn_model.joblib`, respectivamente. Además, se realiza la lectura de un archivo CSV que contiene los datos de las estrellas a analizar.

- `modelo_reglog.joblib`: Este archivo contiene un modelo entrenado de regresión logística utilizado en el análisis de estrellas binarias. El modelo es cargado y utilizado en el archivo `main.py` para realizar predicciones sobre los datos de entrada.

- `knn_model.joblib`: Este archivo contiene un modelo entrenado de K-Nearest Neighbors (KNN) utilizado en el análisis de estrellas binarias. Al igual que el modelo de regresión logística, este modelo es cargado y utilizado en el archivo `main.py` para realizar predicciones sobre los datos de entrada.

Además de los archivos mencionados, se requiere tener un archivo CSV que contenga los datos de las estrellas a analizar para determinar si son pares binarios. Asegúrate de tener todos estos archivos en el mismo directorio para que el análisis se realice correctamente.

**Nota:** El archivo `knn_model.joblib` se encuentra en el directorio "assets" del repositorio y no está disponible para su visualización directa en GitHub. Sin embargo, puedes descargarlo y colocarlo en el mismo directorio que los demás archivos para su correcto funcionamiento.

Si tienes alguna pregunta o necesitas más información, no dudes en contactarme. ¡Buena suerte con tu análisis de estrellas binarias!
