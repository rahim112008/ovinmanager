import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="OvinManager Pro", layout="wide", page_icon="🐑")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_stdio=True)

# --- SIMULATION DE BASE DE DONNÉES ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame({
        'ID': ['OV-001', 'OV-002', 'OV-003'],
        'Race': ['Ouled Djellal', 'Rembi', 'Hamra'],
        'Poids_Estime': [65.2, 58.0, 72.5],
        'Date_Scan': [datetime.date(2026, 2, 10), datetime.date(2026, 2, 15), datetime.date(2026, 2, 18)]
    })

# --- BARRE LATÉRALE (NAVIGATION) ---
st.sidebar.title("🐑 OvinManager Pro")
menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Scanner IA (1m Std)", "Echo (Assistant)", "Paramètres"])

# --- 1. TABLEAU DE BORD (DASHBOARD) ---
if menu == "Tableau de Bord":
    st.title("📊 Tableau de Bord de l'Élevage")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ovins", len(st.session_state.inventory))
    col2.metric("Poids Moyen (kg)", round(st.session_state.inventory['Poids_Estime'].mean(), 2))
    col3.metric("Dernier Scan", str(st.session_state.inventory['Date_Scan'].max()))
    
    st.subheader("Inventaire Actuel")
    st.dataframe(st.session_state.inventory, use_container_width=True)
    
    st.subheader("Évolution du Cheptel")
    st.line_chart(st.session_state.inventory.set_index('Date_Scan')['Poids_Estime'])

# --- 2. SCANNER IA AVEC ÉTALON DE 1 MÈTRE ---
elif menu == "Scanner IA (1m Std)":
    st.title("📸 Scanner IA de Mesure")
    st.info("Placez une règle de 1 mètre (étalon) à côté de l'animal pour une mesure précise.")
    
    uploaded_file = st.file_uploader("Prendre une photo ou uploader", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        img_array = np.array(image)
        
        st.image(image, caption="Analyse en cours...", use_container_width=True)
        
        # Simulation du calcul de pixels par mètre
        # Dans une version avancée, nous utiliserions un modèle de détection d'objet ici
        st.success("Étalon de 1 mètre détecté ✅")
        
        # Simulation de mesure
        longueur_pixels = 450 
        etalon_pixels = 300 # 300px = 1 mètre
        mesure_reelle = (longueur_pixels / etalon_pixels)
        
        st.metric("Longueur mesurée", f"{round(mesure_reelle, 2)} mètres")
        
        if st.button("Enregistrer le scan"):
            new_data = {'ID': f"OV-00{len(st.session_state.inventory)+1}", 
                        'Race': 'Inconnue', 'Poids_Estime': 60.0, 
                        'Date_Scan': datetime.date.today()}
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([new_data])], ignore_index=True)
            st.toast("Données enregistrées !")

# --- 3. ECHO (L'ASSISTANT TYPE ECHO-DOT) ---
elif menu == "Echo (Assistant)":
    st.title("🗣️ Echo - Assistant Intelligent")
    st.write("Posez une question sur votre élevage (ex: 'Quel est l'ovin le plus lourd ?')")
    
    query = st.text_input("Commande vocale ou texte :", placeholder="Écrivez ici...")
    
    if query:
        query = query.lower()
        if "lourd" in query:
            max_ov = st.session_state.inventory.loc[st.session_state.inventory['Poids_Estime'].idxmax()]
            st.write(f"🤖 Echo : L'ovin le plus lourd est le {max_ov['ID']} avec {max_ov['Poids_Estime']} kg.")
        elif "total" in query or "combien" in query:
            total = len(st.session_state.inventory)
            st.write(f"🤖 Echo : Vous avez actuellement {total} ovins dans votre base.")
        else:
            st.write("🤖 Echo : Je ne suis pas sûr de comprendre, mais je peux vous aider à gérer votre inventaire.")

# --- 4. PARAMÈTRES ---
elif menu == "Paramètres":
    st.title("⚙️ Paramètres")
    st.toggle("Mode Sombre")
    st.selectbox("Unité de mesure", ["Mètres", "Centimètres"])
    st.button("Sauvegarder les préférences")

# --- PIED DE PAGE ---
st.sidebar.markdown("---")
st.sidebar.caption(f"Dernière mise à jour : {datetime.date.today()}")
