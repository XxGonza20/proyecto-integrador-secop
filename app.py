"""
Dashboard — Contratación directa vs. competitiva en Boyacá (SECOP II, 2022–2026)
Proyecto Integrador · Big Data 2026-2 · Universidad Santo Tomás – Seccional Tunja

Ejecutar:  streamlit run app.py
Requiere:  data/contratos_limpio.parquet  (lo genera el notebook, sección 4)
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Contratación pública Boyacá", page_icon="📑", layout="wide")

RUTA = Path(__file__).parent / "data" / "contratos_limpio.parquet"
ORDEN = ["Directa", "Régimen especial", "Competitiva"]
COLORES = {"Directa": "#d1495b", "Régimen especial": "#edae49", "Competitiva": "#00798c"}
VENTANAS_LG = [("2022-01-29", "2022-06-19"), ("2026-01-31", "2026-06-21")]


@st.cache_data
def cargar() -> pd.DataFrame:
    cols = ["id_contrato", "nombre_entidad", "ciudad", "orden", "tipo_de_contrato", "modalidad_de_contratacion",
            "grupo_modalidad", "fecha_de_firma", "anio", "anio_mes", "valor_analisis", "valor_valido",
            "ley_garantias", "tipo_proveedor", "id_proveedor", "proveedor_adjudicado"]
    return pd.read_parquet(RUTA, columns=cols)


def es(texto: str) -> str:
    """Formato numérico colombiano: punto para miles y coma para decimales."""
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_cop(v: float) -> str:
    if v >= 1e12:
        return es(f"${v/1e12:,.2f} billones")
    if v >= 1e9:
        return es(f"${v/1e9:,.1f} mil M")
    return es(f"${v/1e6:,.1f} M")


if not RUTA.exists():
    st.error("No se encontró `data/contratos_limpio.parquet`. Ejecuta primero el notebook (sección 4).")
    st.stop()

df = cargar()

# ------------------------------------------------------------------ FILTROS
st.sidebar.header("Filtros")
anios = sorted(df["anio"].unique())
rango = st.sidebar.slider("Año de firma", int(min(anios)), int(max(anios)), (int(min(anios)), int(max(anios))))

ciudades = df["ciudad"].fillna("SIN DEFINIR").value_counts().index.tolist()
sel_ciudad = st.sidebar.multiselect("Municipio de la entidad", ciudades, placeholder="Todos los municipios")

orden_ent = st.sidebar.radio("Orden de la entidad", ["Todas", "Territorial", "Nacional"], horizontal=True)

base = df[df["anio"].between(*rango)]
if sel_ciudad:
    base = base[base["ciudad"].fillna("SIN DEFINIR").isin(sel_ciudad)]
if orden_ent != "Todas":
    base = base[base["orden"] == orden_ent]

entidades = base.groupby("nombre_entidad")["valor_analisis"].sum().sort_values(ascending=False).index.tolist()
sel_ent = st.sidebar.selectbox("Entidad", ["Todas las entidades"] + entidades)
if sel_ent != "Todas las entidades":
    base = base[base["nombre_entidad"] == sel_ent]

sel_tipo = st.sidebar.multiselect("Tipo de contrato", sorted(base["tipo_de_contrato"].dropna().unique()),
                                  placeholder="Todos los tipos")
if sel_tipo:
    base = base[base["tipo_de_contrato"].isin(sel_tipo)]

st.sidebar.caption("Los contratos con valor menor a $10.000 o mayor a $50.000 M (errores de registro) se cuentan, "
                   "pero se excluyen de las sumas de valor.")

# ------------------------------------------------------------------ ENCABEZADO
st.title("¿Quién compite por los contratos públicos en Boyacá?")
st.markdown("Contratación **directa** vs. **competitiva** en SECOP II · contratos firmados por entidades de Boyacá, "
            f"{rango[0]}–{rango[1]}. Fuente: datos.gov.co (`jbjy-vk9h`).")

if base.empty:
    st.warning("No hay contratos con esos filtros.")
    st.stop()

# ------------------------------------------------------------------ KPIs
valido = base[base["valor_valido"]]
es_dir = base["grupo_modalidad"] == "Directa"
valor_total = valido["valor_analisis"].sum()
valor_dir = valido.loc[valido["grupo_modalidad"] == "Directa", "valor_analisis"].sum()
pct_valor_dir = 100 * valor_dir / valor_total if valor_total else 0
pct_n_dir = 100 * es_dir.mean()
n_prov = base["id_proveedor"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Contratos", es(f"{len(base):,}"))
k2.metric("Valor contratado", fmt_cop(valor_total))
k3.metric("% contratos por directa", es(f"{pct_n_dir:.1f} %"))
k4.metric("% del valor por directa", es(f"{pct_valor_dir:.1f} %"))
k5.metric("Proveedores distintos", es(f"{n_prov:,}"))

st.divider()

# ------------------------------------------------------------------ GRÁFICOS
c1, c2 = st.columns(2)

with c1:
    anual = (base.groupby(["anio", "grupo_modalidad"]).size().rename("contratos").reset_index())
    anual["pct"] = 100 * anual["contratos"] / anual.groupby("anio")["contratos"].transform("sum")
    fig1 = px.bar(anual, x="anio", y="pct", color="grupo_modalidad", category_orders={"grupo_modalidad": ORDEN},
                  color_discrete_map=COLORES, text=anual["pct"].round(0).astype(int).astype(str) + "%",
                  labels={"anio": "Año", "pct": "% de contratos", "grupo_modalidad": "Grupo"},
                  title="Participación por grupo de modalidad y año")
    fig1.update_layout(legend=dict(orientation="h", y=-0.2), xaxis=dict(type="category"), height=420)
    st.plotly_chart(fig1, width="stretch")

with c2:
    mens = (base.groupby("anio_mes")
                .agg(contratos=("id_contrato", "count"),
                     pct_dir=("grupo_modalidad", lambda s: 100 * (s == "Directa").mean()))
                .reset_index())
    mens = mens[mens["anio_mes"] < df["anio_mes"].max()]
    fig2 = go.Figure()
    fig2.add_bar(x=mens["anio_mes"], y=mens["contratos"], name="Contratos", marker_color="#b8c4cc")
    fig2.add_scatter(x=mens["anio_mes"], y=mens["pct_dir"], name="% directa", yaxis="y2",
                     mode="lines+markers", line=dict(color=COLORES["Directa"], width=3))
    for ini, fin in VENTANAS_LG:
        fig2.add_vrect(x0=ini, x1=fin, fillcolor="#edae49", opacity=0.2, line_width=0,
                       annotation_text="Ley de Garantías", annotation_position="top left")
    fig2.update_layout(title="Contratos por mes y % de contratación directa", height=420,
                       yaxis=dict(title="Contratos"), legend=dict(orientation="h", y=-0.2),
                       yaxis2=dict(title="% directa", overlaying="y", side="right", range=[0, 100]))
    st.plotly_chart(fig2, width="stretch")

c3, c4 = st.columns(2)

with c3:
    ent = (valido.groupby("nombre_entidad")
                 .apply(lambda g: pd.Series({
                     "valor_mm": g["valor_analisis"].sum() / 1e9,
                     "pct_dir": 100 * g.loc[g["grupo_modalidad"] == "Directa", "valor_analisis"].sum()
                                / g["valor_analisis"].sum()}), include_groups=False)
                 .reset_index())
    ent = ent.nlargest(15, "valor_mm").sort_values("pct_dir")
    fig3 = px.bar(ent, x="pct_dir", y="nombre_entidad", orientation="h", color="valor_mm",
                  color_continuous_scale="Reds", range_x=[0, 100],
                  labels={"pct_dir": "% del valor por directa", "nombre_entidad": "", "valor_mm": "Valor (mil M)"},
                  title="15 entidades de mayor gasto: % del valor por directa")
    fig3.update_layout(height=480, margin=dict(l=5))
    st.plotly_chart(fig3, width="stretch")

with c4:
    dirs = valido[valido["grupo_modalidad"] == "Directa"]
    tree = (dirs.groupby(["tipo_de_contrato", "tipo_proveedor"])["valor_analisis"].sum() / 1e9).reset_index(name="valor_mm")
    if tree.empty:
        st.info("No hay contratación directa con valor válido en esta selección.")
    else:
        fig4 = px.treemap(tree, path=[px.Constant("Contratación directa"), "tipo_de_contrato", "tipo_proveedor"],
                          values="valor_mm", color="valor_mm", color_continuous_scale="Reds",
                          title="¿En qué se gasta la contratación directa? (valor, mil M)")
        fig4.update_layout(height=480, margin=dict(t=50, l=5, r=5, b=5))
        st.plotly_chart(fig4, width="stretch")

c5, c6 = st.columns([3, 2])

with c5:
    prov = (dirs.groupby(["id_proveedor", "proveedor_adjudicado", "tipo_proveedor"])
                .agg(contratos=("id_contrato", "count"), valor=("valor_analisis", "sum"))
                .reset_index().nlargest(12, "valor"))
    prov["valor_mm"] = prov["valor"] / 1e9
    fig5 = px.bar(prov.sort_values("valor_mm"), x="valor_mm", y="proveedor_adjudicado", orientation="h",
                  color="tipo_proveedor", hover_data=["contratos"],
                  labels={"valor_mm": "Valor por contratación directa (mil M)", "proveedor_adjudicado": "",
                          "tipo_proveedor": "Proveedor"},
                  title="Proveedores con mayor valor por contratación directa")
    fig5.update_layout(height=460, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig5, width="stretch")

with c6:
    mod = base["modalidad_de_contratacion"].value_counts().reset_index()
    mod.columns = ["modalidad", "contratos"]
    mod.loc[mod.index >= 7, "modalidad"] = "Otras"
    mod = mod.groupby("modalidad", as_index=False)["contratos"].sum()
    fig6 = px.pie(mod, names="modalidad", values="contratos", hole=0.5, title="Contratos por modalidad")
    fig6.update_layout(height=460, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig6, width="stretch")

with st.expander("Ver datos filtrados"):
    st.dataframe(base.drop(columns=["id_proveedor"]).sort_values("fecha_de_firma", ascending=False).head(500),
                 width="stretch")
    st.caption("Se muestran los 500 contratos más recientes de la selección.")
