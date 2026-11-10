# ¿Quién compite por los contratos públicos en Boyacá?

**Contratación directa vs. contratación competitiva en SECOP II (2022–2026)**
Proyecto Integrador · Big Data 2026-2 · Universidad Santo Tomás – Seccional Tunja

**Integrantes:** Sebastian Gonzalo Ayala Garcia · Santiago Andres Avila Suarez · Gabriel Felipe Bastidas Alvarado

---

## Problema

1. **Problema:** la regla general es que el Estado contrate por modalidades competitivas, pero en Boyacá no hay una forma sencilla de ver cuánto del gasto público se adjudica sin competencia.
2. **A quién afecta:** veedurías ciudadanas, concejos y asamblea, periodistas locales, entes de control y proveedores que quieren competir.
3. **Qué responde:** cuánto pesa la contratación directa, en qué entidades y tipos de contrato se concentra, cómo cambia en el tiempo y si la Ley de Garantías la reduce.

## Dataset

- **Fuente:** [SECOP II – Contratos Electrónicos](https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-II-Contratos-Electr-nicos/jbjy-vk9h), Colombia Compra Eficiente (datos.gov.co, ID `jbjy-vk9h`).
- **Filtro:** `departamento = 'Boyacá'` y `fecha_de_firma ≥ 2022-01-01`.
- **Tamaño:** 124.434 contratos, 29 columnas (descarga del 9 de noviembre de 2026).
- Se excluyeron columnas con datos personales (cuentas bancarias, cédulas de supervisores) y la cédula del proveedor se reemplaza por un identificador seudonimizado.

## Estructura del repositorio

```
├── proyecto_integrador_secop.ipynb   # Notebook ejecutado de principio a fin
├── app.py                            # Dashboard en Streamlit
├── descargar_datos.py                # Descarga el CSV desde la API de datos.gov.co
├── requirements.txt
├── README.md
└── data/
    ├── secop_boyaca_2022_2026.csv    # Dataset crudo (lo genera descargar_datos.py)
    └── contratos_limpio.parquet      # Dataset limpio (lo genera el notebook; lo usa el dashboard)
```

## Temáticas aplicadas

| Temática | Dónde | Qué se hace |
|---|---|---|
| **PySpark** | Notebook §5.1 | Lectura del CSV, filtros, `groupBy` con ventanas, Spark SQL y un *join* (entidades dentro y fuera de la Ley de Garantías), todo verificado con `count()`. |
| **MongoDB** | Notebook §5.2 | Carga de los contratos 2025–2026 como documentos, consultas con `$gte`, `$in`, `$and`, `$ne` y un *pipeline* de agregación sobre concentración de proveedores. |
| **Streaming** | Notebook §5.3 | Spark Structured Streaming lee un archivo por mes (`maxFilesPerTrigger=1`) y actualiza el % acumulado de contratación directa en cada micro-lote. |
| **Visualización** | Notebook §6 y dashboard | NumPy (estadísticas y Gini), Matplotlib, Seaborn y Plotly. |

## Cómo ejecutarlo en local

Requisitos: **Python 3.10+** y **Java 17 o 21** (para PySpark).

```bash
# 1. Crear el entorno e instalar dependencias
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# 2. Descargar el dataset (si no está en data/)
python descargar_datos.py

# 3. Ejecutar el notebook completo (genera data/contratos_limpio.parquet)
jupyter nbconvert --to notebook --execute --inplace proyecto_integrador_secop.ipynb
#    o abrirlo con: jupyter notebook proyecto_integrador_secop.ipynb  → "Run All"

# 4. Lanzar el dashboard
streamlit run app.py
```

**MongoDB:** el notebook se conecta a `mongodb://localhost:27017` o al valor de la variable de entorno `MONGO_URI` (por ejemplo, un clúster de MongoDB Atlas). Si no encuentra servidor, usa `mongomock` (emulación en memoria) para que el notebook se ejecute igual. Para la sustentación se recomienda tener MongoDB local o Atlas activo:

```bash
# Windows (PowerShell)
$env:MONGO_URI="mongodb+srv://usuario:clave@cluster.mongodb.net"
# Linux/Mac
export MONGO_URI="mongodb+srv://usuario:clave@cluster.mongodb.net"
```

## Dashboard

- **KPIs:** contratos, valor contratado, % de contratos por directa, % del valor por directa y proveedores distintos.
- **6 gráficos de Plotly:** participación por año, serie mensual con las ventanas de Ley de Garantías, 15 entidades de mayor gasto, *treemap* del gasto por directa, proveedores con mayor valor y distribución por modalidad.
- **Filtros:** rango de años, municipio, orden de la entidad (territorial/nacional), entidad y tipo de contrato.

**Enlace público:** _pendiente — publicar en [Streamlit Community Cloud](https://streamlit.io/cloud) apuntando a `app.py` de este repositorio._

## Principales hallazgos

- Entre el **69 % y el 77 %** de los contratos de cada año se firman por contratación directa, aunque solo representan entre el **29 % y el 43 %** del valor.
- La **Gobernación de Boyacá**, la entidad de mayor gasto, adjudica por directa el 96 % de sus contratos y el 69 % de su valor.
- La **Ley de Garantías** reduce la contratación directa casi a cero (de 415 a menos de 2 contratos por día en 2026), pero las entidades **la adelantan**: enero de 2026 concentró el 48 % de los contratos firmados en el año.
- El 88 % de los contratos directos son prestación de servicios con personas naturales; en valor, el 1 % de los proveedores recibe el 56 % (Gini = 0,79).

## Declaración del uso de IA

| Herramienta | Tarea | Qué se verificó o corrigió |
|---|---|---|
| Claude (Anthropic) | Búsqueda del dataset y armado de la consulta filtrada a la API; borrador del notebook (PySpark, MongoDB, Streaming, visualizaciones), del dashboard y de este README; redacción inicial de las conclusiones. | _Completar por el equipo antes de entregar._ |
