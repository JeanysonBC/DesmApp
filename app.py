import streamlit as st
import geopandas as gpd
import pandas as pd
from geobr import read_municipality, read_prodes
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide", page_title="Desmatamento Municipal (PRODES)")

@st.cache_data
def load_data(year):
    munis = read_municipality(year=2020)[["code_muni", "name_muni", "geometry"]]
    munis = munis.to_crs("EPSG:4326")
    prodes = read_prodes(year=year)[["code_muni", "geometry"]]
    prodes = prodes.to_crs("EPSG:4326")
    return munis, prodes

st.sidebar.title("Configurações")
year = st.sidebar.select_slider(
    "Ano do PRODES",
    options=list(range(2005, 2024)),
    value=2023
)
munis, prodes = load_data(year)

municipios = munis["name_muni"].sort_values().tolist()
selecionado = st.sidebar.selectbox("Escolha o município", municipios)

muni_sel = munis[munis["name_muni"] == selecionado]
code_sel = muni_sel["code_muni"].iloc[0]

desm_sel = gpd.overlay(prodes, muni_sel, how="intersection")
desm_sel["area_ha"] = desm_sel.geometry.area / 1e4

st.write(f"## Desmatamento em **{selecionado}** em {year}")
col1, col2 = st.columns([2,1])

with col1:
    centroid = muni_sel.geometry.centroid.iloc[0]
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=8, control_scale=True)
    folium.GeoJson(
        muni_sel,
        name="Município",
        style_function=lambda x: {"color": "#0000ff", "weight": 2, "fill": False}
    ).add_to(m)
    folium.GeoJson(
        desm_sel,
        name="Desmatamento",
        style_function=lambda x: {"color": "red", "weight": 1, "fillOpacity": 0.6}
    ).add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, width="100%", height=600)

with col2:
    total_ha = desm_sel["area_ha"].sum()
    st.metric(label="Total (ha)", value=f"{total_ha:,.2f}")
    st.write("#### Top 5 polígonos por área")
    top5 = desm_sel.nlargest(5, "area_ha")[["area_ha"]]
    st.table(top5.reset_index(drop=True))

if st.checkbox("Mostrar mapa nacional (todas as áreas de desmatamento)"):
    st.write("### Desmatamento no Brasil em " + str(year))
    m2 = folium.Map(location=[-10.0, -55.0], zoom_start=4, control_scale=True)
    folium.GeoJson(
        prodes,
        name="Desmatamento BR",
        style_function=lambda x: {"color": "darkgreen", "weight": 0.5, "fillOpacity": 0.4}
    ).add_to(m2)
    st_folium(m2, width="100%", height=500)
