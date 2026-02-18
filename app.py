import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="OvinManager Pro", layout="wide", page_icon="🐑")

# --- STYLE CSS (CORRIGÉ) ---
st.markdown("<style>.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }</style>", unsafe_allow_html=True)

# --- BASE DE DONNÉES TEMPORAIRE ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame({
        'ID': ['OV-001', 'OV-002', 'OV-003'],
        'Race': ['Ouled Djellal', 'Rembi', 'Hamra'],
        'Poids_Estime': [65.2, 58.0, 72.5],
        'Date_Scan': [datetime.date(2026, 2, 10), datetime.date(2026, 2, 15), datetime.date(2026, 2, 18)]
    })

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Scanner IA (1m Std)", "Echo (Assistant)"])

# --- 1. TABLEAU DE BORD ---
if menu == "Tableau de Bord":
    st.title("📊 Tableau de Bord")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ovins", len(st.session_state.inventory))
    c2.metric("Poids Moyen", f"{round(st.session_state.inventory['Poids_Estime'].mean(), 1)} kg")
    c3.metric("Dernier Scan", str(st.session_state.inventory['Date_Scan'].max()))
    
    st.subheader("Liste des animaux")
    st.dataframe(st.session_state.inventory, use_container_width=True)

# --- 2. SCANNER IA ---
elif menu == "Scanner IA (1m Std)":
    st.title("📸 Scanner avec Étalon (1m)")
    img_file = st.file_uploader("Prendre une photo", type=['jpg', 'png'])
    
    if img_file:
        img = Image.open(img_file)
        st.image(img, caption="Analyse de l'étalon...", use_container_width=True)
        # Simulation calcul
        st.success("Mesure effectuée : 1.12 mètres")

# --- 3. ECHO ---
elif menu == "Echo (Assistant)":
    st.title("🗣️ Echo Assistant")
    cmd = st.text_input("Posez une question :")
    if cmd:
        st.write(f"🤖 Echo : Analyse de '{cmd}' en cours...")
        st.info("Réponse : Les données suggèrent une croissance stable du troupeau.")
