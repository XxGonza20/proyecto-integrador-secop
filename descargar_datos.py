"""
Descarga el dataset del proyecto desde la API pública de datos.gov.co (Socrata).

Dataset : SECOP II - Contratos Electrónicos (ID jbjy-vk9h), Colombia Compra Eficiente
Filtro  : departamento = 'Boyacá' y fecha_de_firma >= 2022-01-01
Salida  : data/secop_boyaca_2022_2026.csv  (~85 MB, ~124.000 contratos)

Uso:  python descargar_datos.py
"""
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

COLUMNAS = [
    "nombre_entidad", "nit_entidad", "departamento", "ciudad", "orden", "sector", "rama",
    "proceso_de_compra", "id_contrato", "estado_contrato", "codigo_de_categoria_principal",
    "descripcion_del_proceso", "tipo_de_contrato", "modalidad_de_contratacion",
    "justificacion_modalidad_de", "fecha_de_firma", "fecha_de_inicio_del_contrato",
    "fecha_de_fin_del_contrato", "tipodocproveedor", "documento_proveedor", "proveedor_adjudicado",
    "es_pyme", "origen_de_los_recursos", "destino_gasto", "valor_del_contrato", "valor_facturado",
    "valor_pagado", "dias_adicionados", "duraci_n_del_contrato",
]
PARAMS = {
    "$select": ",".join(COLUMNAS),
    "$where": "departamento='Boyacá' AND fecha_de_firma >= '2022-01-01T00:00:00'",
    "$limit": 200000,
}
URL = "https://www.datos.gov.co/resource/jbjy-vk9h.csv?" + urlencode(PARAMS)
DESTINO = Path(__file__).parent / "data" / "secop_boyaca_2022_2026.csv"

if __name__ == "__main__":
    DESTINO.parent.mkdir(exist_ok=True)
    print("Descargando desde datos.gov.co (puede tardar 1-3 minutos)...")
    with urlopen(URL, timeout=600) as r, open(DESTINO, "wb") as f:
        while bloque := r.read(1 << 20):
            f.write(bloque)
    print(f"Listo: {DESTINO} ({DESTINO.stat().st_size / 1e6:,.1f} MB)")
