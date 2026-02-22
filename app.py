import streamlit as st
import sqlite3
import json
import math
import hashlib
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from PIL import Image
import io
import base64
import time
import numpy as np
from scipy import stats
import statsmodels.api as sm
import zipfile

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
class Config:
    APP_NAME = "Ovin Manager Pro"
    LABORATOIRE = "GenApAgiE"
    VERSION = "4.0"
    
    VERT = "#2E7D32"
    ORANGE = "#FF6F00"
    BLEU = "#1565C0"
    ROUGE = "#C62828"
    VIOLET = "#6A1B9A"
    CYAN = "#00838F"
    
    NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    ETALONS = {
        "baton_1m": {"nom": "Bâton 1m", "largeur": 1000, "hauteur": None},
        "a4": {"nom": "Feuille A4", "largeur": 210, "hauteur": 297},
        "carte": {"nom": "Carte bancaire", "largeur": 85.6, "hauteur": 53.98},
        "piece_100da": {"nom": "Pièce 100 DA", "diametre": 29.5}
    }
    
    RACES = {
        "Hamra": {"origine": "Atlas saharien", "aptitude": "Mixte", "genes": ["BMP15", "GDF9"]},
        "Ouled Djellal": {"origine": "Steppes algériennes", "aptitude": "Viande", "genes": ["MSTN", "IGF2"]},
        "Sidahou": {"origine": "Aurès", "aptitude": "Lait", "genes": ["LALBA", "CSN3", "DGAT1"]},
        "Rembi": {"origine": "Tell", "aptitude": "Mixte", "genes": ["BMP15", "LALBA"]},
        "Autre": {"origine": "Inconnue", "aptitude": "Variable", "genes": []}
    }
    
    GENES_ECONOMIQUES = {
        "BMP15": {"nom": "Bone Morphogenetic Protein 15", "chr": "X", "effet": "Fécondité"},
        "GDF9": {"nom": "Growth Differentiation Factor 9", "chr": "5", "effet": "Fécondité"},
        "BMPR1B": {"nom": "BMP Receptor 1B", "chr": "6", "effet": "Prolificité (Booroola)"},
        "MSTN": {"nom": "Myostatin", "chr": "2", "effet": "Hypertrophie musculaire"},
        "IGF2": {"nom": "Insulin-like Growth Factor 2", "chr": "2", "effet": "Croissance"},
        "GH": {"nom": "Growth Hormone", "chr": "19", "effet": "Croissance"},
        "GHR": {"nom": "Growth Hormone Receptor", "chr": "16", "effet": "Efficacité alimentaire"},
        "LALBA": {"nom": "Alpha-Lactalbumin", "chr": "3", "effet": "Protéines lait"},
        "CSN3": {"nom": "Kappa-Casein", "chr": "6", "effet": "Qualité fromagère"},
        "DGAT1": {"nom": "Diacylglycerol Acyltransferase 1", "chr": "14", "effet": "Matière grasse lait"},
        "SCD": {"nom": "Stearoyl-CoA Desaturase", "chr": "22", "effet": "Acides gras insaturés"},
        "TLR4": {"nom": "Toll-like Receptor 4", "chr": "1", "effet": "Résistance infections"},
        "MHC": {"nom": "Major Histocompatibility Complex", "chr": "20", "effet": "Immunité"},
        "PRNP": {"nom": "Prion Protein", "chr": "13", "effet": "Résistance tremblante"},
        "CAST": {"nom": "Calpastatin", "chr": "7", "effet": "Tendreté viande"},
        "CAPN1": {"nom": "Calpain 1", "chr": "16", "effet": "Tendreté viande"},
        "FABP4": {"nom": "Fatty Acid Binding Protein 4", "chr": "8", "effet": "Marbling (gras intramusculaire)"}
    }
    
    ETATS_PHYSIO = [
        "Jeune", "Gestation début", "Gestation fin",
        "Lactation début", "Lactation milieu", "Lactation fin",
        "Tarie", "Engraissement"
    ]

# -----------------------------------------------------------------------------
# BASE DE DONNÉES (version enrichie)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_database():
    return Database()

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("ovin_streamlit.db", check_same_thread=False)
        self.init_database()
    
    def init_database(self):
        cursor = self.conn.cursor()
        
        # Tables existantes (inchangées)
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT,
                nom_laboratoire TEXT DEFAULT 'GenApAgiE', date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS eleveurs (
                id INTEGER PRIMARY KEY, user_id INTEGER, nom TEXT, region TEXT,
                telephone TEXT, email TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS elevages (
                id INTEGER PRIMARY KEY, eleveur_id INTEGER, nom TEXT,
                localisation TEXT, superficie REAL
            )""",
            """CREATE TABLE IF NOT EXISTS brebis (
                id INTEGER PRIMARY KEY, elevage_id INTEGER, numero_id TEXT UNIQUE,
                nom TEXT, race TEXT, date_naissance TEXT, etat_physio TEXT,
                photo_profil TEXT, photo_mamelle TEXT, sequence_fasta TEXT,
                variants_snps TEXT, profil_genetique TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mesures_morpho (
                id INTEGER PRIMARY KEY, brebis_id INTEGER, date_mesure TIMESTAMP,
                longueur_corps REAL, hauteur_garrot REAL, tour_poitrine REAL,
                circonference_canon REAL, largeur_bassin REAL, score_global REAL
            )""",
            """CREATE TABLE IF NOT EXISTS mesures_mamelles (
                id INTEGER PRIMARY KEY, brebis_id INTEGER, date_mesure TIMESTAMP,
                longueur_trayon REAL, diametre_trayon REAL, symetrie TEXT,
                attache TEXT, forme TEXT, score_total REAL
            )""",
            """CREATE TABLE IF NOT EXISTS composition_corporelle (
                id INTEGER PRIMARY KEY, brebis_id INTEGER, date_estimation TIMESTAMP,
                poids_vif REAL, poids_carcasse REAL, rendement_carcasse REAL,
                poids_viande REAL, pct_viande REAL, poids_graisse REAL,
                pct_graisse REAL, poids_os REAL, pct_os REAL,
                gigot_poids REAL, epaule_poids REAL, cotelette_poids REAL
            )""",
            """CREATE TABLE IF NOT EXISTS analyses_genomiques (
                id INTEGER PRIMARY KEY, brebis_id INTEGER, date_analyse TIMESTAMP,
                gene_cible TEXT, sequence_query TEXT, blast_hits TEXT,
                identite_pct REAL, e_value REAL
            )"""
        ]
        
        for table in tables:
            cursor.execute(table)
        
        # ========== NOUVELLES TABLES ==========
        # Production laitière et analyses biochimiques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productions (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                date DATE,
                quantite REAL,
                ph REAL,
                mg REAL,
                proteine REAL,
                ag_satures REAL,
                densite REAL,
                extrait_sec REAL,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        # Génotypes détaillés
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genotypes (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                snp_name TEXT,
                genotype TEXT,
                chromosome TEXT,
                position INTEGER,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        # Phénotypes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phenotypes (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                trait TEXT,
                valeur REAL,
                date_mesure DATE,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        # Diagnostics maladies (optionnel)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostics (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                date DATE,
                maladie TEXT,
                symptomes TEXT,
                traitement TEXT,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        # ========== TABLES POUR LA NUTRITION ==========
        # Aliments disponibles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aliments (
                id INTEGER PRIMARY KEY,
                nom TEXT UNIQUE,
                type TEXT,
                uem REAL,
                pdin REAL,
                ms REAL,
                prix_kg REAL
            )
        """)
        
        # Rations types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rations (
                id INTEGER PRIMARY KEY,
                nom TEXT,
                etat_physio TEXT,
                description TEXT
            )
        """)
        
        # Composition des rations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ration_composition (
                id INTEGER PRIMARY KEY,
                ration_id INTEGER,
                aliment_id INTEGER,
                quantite_kg REAL,
                FOREIGN KEY (ration_id) REFERENCES rations(id),
                FOREIGN KEY (aliment_id) REFERENCES aliments(id)
            )
        """)
        
        # ========== TABLES POUR LA SANTÉ ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vaccinations (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                date_vaccin DATE,
                vaccin TEXT,
                rappel DATE,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soins (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                date_soin DATE,
                type TEXT,
                diagnostic TEXT,
                traitement TEXT,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        # ========== TABLES POUR LA REPRODUCTION ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chaleurs (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                date_debut DATE,
                date_fin DATE,
                methode_synchro TEXT,
                observation TEXT,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saillies (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                date_saillie DATE,
                male_id INTEGER,
                methode TEXT,
                resultat TEXT,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mises_bas (
                id INTEGER PRIMARY KEY,
                brebis_id INTEGER,
                date_mise_bas DATE,
                nb_agneaux INTEGER,
                poids_portee REAL,
                remarques TEXT,
                FOREIGN KEY (brebis_id) REFERENCES brebis(id)
            )
        """)
        
        self.conn.commit()
    
    def execute(self, query: str, params: tuple = ()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def fetchall(self, query: str, params: tuple = ()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def fetchone(self, query: str, params: tuple = ()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

# -----------------------------------------------------------------------------
# CLASSES MÉTIER (inchangées)
# -----------------------------------------------------------------------------
class OvinScience:
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def calcul_score_morpho(longueur: float, hauteur: float, poitrine: float, 
                          canon: float, bassin: float) -> float:
        try:
            indice_format = (longueur / hauteur) * 100 if hauteur > 0 else 0
            indice_corpulence = (poitrine / hauteur) * 100 if hauteur > 0 else 0
            
            score = 40
            if 100 <= indice_format <= 120: score += 20
            if 115 <= indice_corpulence <= 135: score += 20
            if canon > 7.0: score += 10
            if bassin > 18: score += 10
            
            return min(100, round(score, 2))
        except:
            return 0
    
    @staticmethod
    def calcul_score_mamelle(long_trayon: float, diametre: float,
                           symetrie: str, attache: str, forme: str) -> float:
        score = 5.0
        if 4 <= long_trayon <= 6: score += 1.5
        if 2 <= diametre <= 3: score += 1.5
        if symetrie == "Symétrique": score += 0.5
        if attache == "Solide": score += 0.5
        if forme == "Globuleuse": score += 0.5
        if attache != "Pendante": score += 0.5
        return min(10, round(score, 2))
    
    @staticmethod
    def estimer_composition(poids_vif: float, race: str, condition_corporelle: float) -> Dict:
        try:
            rendement = 0.48 if race == "Ouled Djellal" else 0.45 if race == "Sidahou" else 0.46
            rendement += (condition_corporelle - 3) * 0.01
            poids_carcasse = poids_vif * rendement
            
            if condition_corporelle >= 4:
                pct_viande, pct_graisse, pct_os = 0.55, 0.28, 0.17
            elif condition_corporelle <= 2:
                pct_viande, pct_graisse, pct_os = 0.62, 0.18, 0.20
            else:
                pct_viande, pct_graisse, pct_os = 0.58, 0.23, 0.19
            
            if race == "Ouled Djellal":
                pct_viande += 0.02
                pct_graisse -= 0.01
            
            return {
                "poids_vif": poids_vif,
                "poids_carcasse": round(poids_carcasse, 2),
                "rendement": round(rendement * 100, 1),
                "viande": {"kg": round(poids_carcasse * pct_viande, 2), "pct": round(pct_viande * 100, 1)},
                "graisse": {"kg": round(poids_carcasse * pct_graisse, 2), "pct": round(pct_graisse * 100, 1)},
                "os": {"kg": round(poids_carcasse * pct_os, 2), "pct": round(pct_os * 100, 1)},
                "decoupes": {
                    "gigot": round(poids_carcasse * 0.22, 2),
                    "epaule": round(poids_carcasse * 0.17, 2),
                    "cotelette": round(poids_carcasse * 0.14, 2),
                    "poitrine": round(poids_carcasse * 0.12, 2)
                },
                "qualite": {
                    "conformation": min(15, max(1, 8 + int((condition_corporelle - 3) * 1.5) + (2 if race == "Ouled Djellal" else 0))),
                    "gras": int(condition_corporelle)
                }
            }
        except Exception as e:
            return {"erreur": str(e)}
    
    @staticmethod
    def besoins_nutritionnels(poids: float, etat: str, lactation: float = 0) -> Dict:
        besoins = {
            "maintenance": {"uem": 0.5, "pdin": 45, "ms": 1.0},
            "gestation": {"uem": 0.7, "pdin": 70, "ms": 1.2},
            "lactation": {"uem": 1.2, "pdin": 120, "ms": 2.5},
            "tarie": {"uem": 0.55, "pdin": 50, "ms": 1.1},
            "engraissement": {"uem": 0.8, "pdin": 60, "ms": 1.5}
        }
        base = besoins.get("maintenance")
        for key in besoins:
            if key in etat.lower():
                base = besoins[key]
                break
        if lactation > 0:
            base["uem"] += lactation * 0.4
            base["pdin"] += lactation * 8
        return {k: round(v, 2) for k, v in base.items()}

class MachineLearning:
    @staticmethod
    def predire_lait(score_mam: float, score_morpho: float, race: str, age: int) -> Dict:
        base = 0.5
        if score_mam >= 8: base += 1.5
        elif score_mam >= 6: base += 0.8
        if score_morpho >= 80: base += 0.3
        if race == "Lacaune": base *= 1.3
        if 3 <= age <= 6: base *= 1.2
        return {
            "litres_jour": round(base, 2),
            "litres_lactation": round(base * 180, 2),
            "niveau": "Élite" if base > 1.5 else "Bon" if base > 1.0 else "Standard"
        }

class NCBIApi:
    def __init__(self):
        self.base_url = Config.NCBI_EUTILS_BASE
    
    def search_gene(self, gene_name: str, organism: str = "Ovis aries") -> List[Dict]:
        try:
            url = f"{self.base_url}/esearch.fcgi"
            params = {
                "db": "gene",
                "term": f"{gene_name}[Gene] AND {organism}[Organism]",
                "retmode": "json",
                "retmax": 5
            }
            with st.spinner(f"Recherche {gene_name} dans NCBI..."):
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
            gene_ids = data.get("esearchresult", {}).get("idlist", [])
            if gene_ids:
                return self.fetch_gene_details(gene_ids)
            return []
        except Exception as e:
            st.error(f"Erreur API NCBI: {e}")
            return []
    
    def fetch_gene_details(self, gene_ids: List[str]) -> List[Dict]:
        try:
            url = f"{self.base_url}/esummary.fcgi"
            params = {"db": "gene", "id": ",".join(gene_ids), "retmode": "json"}
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            results = []
            for gid in gene_ids:
                summary = data.get("result", {}).get(gid, {})
                results.append({
                    "gene_id": gid,
                    "name": summary.get("name", "N/A"),
                    "description": summary.get("description", "N/A"),
                    "chromosome": summary.get("chromosome", "N/A"),
                    "map_location": summary.get("maplocation", "N/A")
                })
            return results
        except Exception as e:
            st.error(f"Erreur détails gènes: {e}")
            return []
    
    def fetch_fasta(self, accession: str) -> Optional[str]:
        try:
            url = f"{self.base_url}/efetch.fcgi"
            params = {"db": "nucleotide", "id": accession, "rettype": "fasta", "retmode": "text"}
            response = requests.get(url, params=params, timeout=30)
            return response.text if response.status_code == 200 else None
        except Exception as e:
            st.error(f"Erreur FASTA: {e}")
            return None

class GenomicAnalyzer:
    def __init__(self):
        self.ncbi = NCBIApi()
    
    def analyze_race_profile(self, race: str) -> Dict:
        genes_race = Config.RACES.get(race, {}).get("genes", [])
        results = {
            "race": race,
            "genes": [],
            "score_reproduction": 0,
            "score_croissance": 0,
            "score_lait": 0,
            "recommandations": []
        }
        for gene in genes_race:
            info = Config.GENES_ECONOMIQUES.get(gene, {})
            results["genes"].append({
                "symbole": gene,
                "nom": info.get("nom", ""),
                "effet": info.get("effet", ""),
                "chromosome": info.get("chr", "")
            })
            if gene in ["BMP15", "GDF9", "BMPR1B"]:
                results["score_reproduction"] += 33
            if gene in ["MSTN", "IGF2", "GH"]:
                results["score_croissance"] += 33
            if gene in ["LALBA", "CSN3", "DGAT1"]:
                results["score_lait"] += 33
        results["score_reproduction"] = min(100, results["score_reproduction"])
        results["score_croissance"] = min(100, results["score_croissance"])
        results["score_lait"] = min(100, results["score_lait"])
        if results["score_reproduction"] > 70:
            results["recommandations"].append("✅ Excellente valeur reproductive")
        if results["score_croissance"] > 70:
            results["recommandations"].append("✅ Excellente conformation viande")
        if results["score_lait"] > 70:
            results["recommandations"].append("✅ Excellent potentiel laitier")
        return results

# -----------------------------------------------------------------------------
# PAGES EXISTANTES (inchangées, sauf page_nutrition qui sera remplacée)
# -----------------------------------------------------------------------------
# Les fonctions page_login, page_dashboard, page_genomique, page_composition,
# page_prediction sont conservées telles quelles. Pour gagner de la place,
# nous ne les réécrivons pas intégralement ici ; elles doivent être copiées
# depuis le code original. Dans la version finale, elles seront présentes.

# NOTE : Pour alléger la réponse, je ne recopie pas ces fonctions. 
# Vous devez les insérer ici.

# -----------------------------------------------------------------------------
# PAGE PHOTOGRAMMÉTRIE AMÉLIORÉE
# -----------------------------------------------------------------------------
def page_analyse():
    st.title("📸 Analyse Photogrammétrique")
    
    # Récupérer les brebis de l'utilisateur
    brebis_list = db.fetchall("""
        SELECT b.id, b.numero_id, b.nom, e.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """, (st.session_state.user_id,))
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}
    
    if not brebis_dict:
        st.warning("Aucune brebis disponible. Veuillez d'abord ajouter des brebis.")
        return
    
    selected_brebis = st.selectbox("Sélectionner la brebis", list(brebis_dict.keys()))
    brebis_id = brebis_dict[selected_brebis]
    
    # Récupération des infos de la brebis (âge, etc.)
    brebis_info = db.fetchone("SELECT date_naissance, race FROM brebis WHERE id=?", (brebis_id,))
    if brebis_info:
        date_naiss = datetime.strptime(brebis_info[0], "%Y-%m-%d").date()
        age_jours = (datetime.today().date() - date_naiss).days
        age_mois = age_jours // 30
        age_dents = "Inconnu"
        if age_mois < 12:
            age_dents = "Dents de lait"
        elif age_mois < 24:
            age_dents = "2 dents"
        elif age_mois < 36:
            age_dents = "4 dents"
        else:
            age_dents = "6 dents ou plus"
    else:
        age_mois = 0
        age_dents = "Inconnu"
    
    st.info(f"Âge estimé : {age_mois} mois ({age_dents})")
    
    tab1, tab2 = st.tabs(["📏 Morphométrie Corps", "🥛 Analyse Mamelles"])
    
    with tab1:
        st.subheader("Mesures corporelles")
        
        # Upload de plusieurs photos
        uploaded_files = st.file_uploader("Photos de profil (plusieurs acceptées)", 
                                          type=['jpg','png','jpeg'], accept_multiple_files=True)
        if uploaded_files:
            cols = st.columns(min(3, len(uploaded_files)))
            for i, file in enumerate(uploaded_files):
                with cols[i % 3]:
                    img = Image.open(file)
                    st.image(img, caption=f"Photo {i+1}", use_column_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            etalon = st.selectbox("Étalon de calibration", 
                                 list(Config.ETALONS.keys()),
                                 format_func=lambda x: Config.ETALONS[x]['nom'])
        with col2:
            # Choix de l'âge (soit dentition soit mois)
            mode_age = st.radio("Mode d'âge", ["Mois", "Dentition"])
            if mode_age == "Mois":
                age_saisi = st.number_input("Âge (mois)", min_value=0, value=age_mois)
            else:
                age_saisi_dent = st.selectbox("Dentition", ["Dents de lait", "2 dents", "4 dents", "6 dents ou plus"])
        
        longueur = st.number_input("Longueur corps (cm)", min_value=30.0, max_value=120.0, value=70.0)
        hauteur = st.number_input("Hauteur garrot (cm)", min_value=30.0, max_value=90.0, value=65.0)
        poitrine = st.number_input("Tour poitrine (cm)", min_value=40.0, max_value=130.0, value=80.0)
        canon = st.number_input("Circonf. canon (cm)", min_value=5.0, max_value=15.0, value=8.0)
        bassin = st.number_input("Largeur bassin (cm)", min_value=10.0, max_value=40.0, value=20.0)
        
        if st.button("🤖 Calculer score"):
            score = OvinScience.calcul_score_morpho(longueur, hauteur, poitrine, canon, bassin)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={'x': [0,1], 'y':[0,1]},
                title={'text': "Score Morphologique"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': Config.VERT if score>70 else Config.ORANGE if score>50 else Config.ROUGE},
                       'steps': [
                           {'range': [0,50], 'color': "lightgray"},
                           {'range': [50,70], 'color': "yellow"},
                           {'range': [70,100], 'color': "lightgreen"}]}
            ))
            st.plotly_chart(fig, use_container_width=True)
            
            # Diagnostic simple basé sur les photos (simulation)
            if uploaded_files:
                st.subheader("🔍 Diagnostic visuel")
                st.info("Analyse d'image simulée : pas de signes de maladie détectés.")
                # Ici on pourrait appeler un modèle, mais on reste simple.
    
    with tab2:
        st.subheader("Scoring mamelles")
        
        # Upload photo mamelle
        mamelle_file = st.file_uploader("Vue arrière mamelles", type=['jpg','png','jpeg'], key="mamelle_img")
        if mamelle_file:
            img_mam = Image.open(mamelle_file)
            st.image(img_mam, caption="Mamelle", width=300)
        
        col1, col2 = st.columns(2)
        with col1:
            long_trayon = st.number_input("Longueur trayon (cm)", min_value=1.0, max_value=15.0, value=5.0)
            diam_trayon = st.number_input("Diamètre trayon (cm)", min_value=0.5, max_value=5.0, value=2.5)
        with col2:
            symetrie = st.selectbox("Symétrie", ["Symétrique", "Asymétrique"])
            attache = st.selectbox("Attache", ["Solide", "Moyenne", "Pendante"])
            forme = st.selectbox("Forme", ["Globuleuse", "Bifide", "Poire"])
        
        if st.button("🥛 Calculer score mamelle"):
            score = OvinScience.calcul_score_mamelle(long_trayon, diam_trayon, symetrie, attache, forme)
            st.progress(score / 10)
            st.metric("Score mamelles", f"{score}/10")
            if score >= 8:
                st.success("✅ Excellente conformation mammaire")
            elif score >= 6:
                st.info("ℹ️ Bonne conformation")
            else:
                st.warning("⚠️ Conformation à améliorer")
            
            # Diagnostic mamelle simulé
            if mamelle_file:
                st.subheader("🔍 Diagnostic mammaire")
                if score < 6 or forme == "Bifide" or attache == "Pendante":
                    st.warning("Suspicion de problèmes mammaires (faible conformation). Consulter un vétérinaire.")
                else:
                    st.success("Aspect sain (simulation).")

# -----------------------------------------------------------------------------
# NOUVELLE PAGE SANTÉ
# -----------------------------------------------------------------------------
def page_sante():
    st.title("🏥 Suivi sanitaire et vaccinal")
    
    # Récupérer les brebis
    brebis_list = db.fetchall("""
        SELECT b.id, b.numero_id, b.nom, e.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """, (st.session_state.user_id,))
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}
    
    if not brebis_dict:
        st.warning("Aucune brebis disponible.")
        return
    
    selected = st.selectbox("Choisir une brebis", list(brebis_dict.keys()))
    bid = brebis_dict[selected]
    
    tab1, tab2 = st.tabs(["💉 Vaccinations", "🩺 Soins / Diagnostics"])
    
    with tab1:
        st.subheader("Carnet de vaccination")
        
        # Formulaire d'ajout
        with st.form("form_vaccin"):
            date_vaccin = st.date_input("Date du vaccin", value=datetime.today().date())
            vaccin = st.text_input("Nom du vaccin")
            rappel = st.date_input("Date de rappel (si applicable)", value=None)
            if st.form_submit_button("Ajouter"):
                db.execute(
                    "INSERT INTO vaccinations (brebis_id, date_vaccin, vaccin, rappel) VALUES (?, ?, ?, ?)",
                    (bid, date_vaccin.isoformat(), vaccin, rappel.isoformat() if rappel else None)
                )
                st.success("Vaccin enregistré")
                st.rerun()
        
        # Affichage historique
        vaccins = db.fetchall(
            "SELECT date_vaccin, vaccin, rappel FROM vaccinations WHERE brebis_id=? ORDER BY date_vaccin DESC",
            (bid,)
        )
        if vaccins:
            df = pd.DataFrame(vaccins, columns=["Date", "Vaccin", "Rappel"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun vaccin enregistré.")
    
    with tab2:
        st.subheader("Historique des soins")
        
        with st.form("form_soin"):
            date_soin = st.date_input("Date du soin", value=datetime.today().date())
            type_soin = st.selectbox("Type", ["Maladie", "Parasite", "Blessure", "Autre"])
            diagnostic = st.text_area("Diagnostic / Symptômes")
            traitement = st.text_area("Traitement administré")
            if st.form_submit_button("Enregistrer"):
                db.execute(
                    "INSERT INTO soins (brebis_id, date_soin, type, diagnostic, traitement) VALUES (?, ?, ?, ?, ?)",
                    (bid, date_soin.isoformat(), type_soin, diagnostic, traitement)
                )
                st.success("Soin enregistré")
                st.rerun()
        
        soins = db.fetchall(
            "SELECT date_soin, type, diagnostic, traitement FROM soins WHERE brebis_id=? ORDER BY date_soin DESC",
            (bid,)
        )
        if soins:
            df = pd.DataFrame(soins, columns=["Date", "Type", "Diagnostic", "Traitement"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun soin enregistré.")

# -----------------------------------------------------------------------------
# NOUVELLE PAGE REPRODUCTION
# -----------------------------------------------------------------------------
def page_reproduction():
    st.title("🤰 Gestion de la reproduction")
    
    brebis_list = db.fetchall("""
        SELECT b.id, b.numero_id, b.nom, e.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """, (st.session_state.user_id,))
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}
    
    if not brebis_dict:
        st.warning("Aucune brebis disponible.")
        return
    
    selected = st.selectbox("Choisir une brebis", list(brebis_dict.keys()))
    bid = brebis_dict[selected]
    
    tab1, tab2, tab3 = st.tabs(["🔥 Chaleurs", "🐏 Saillies", "🐑 Mises bas"])
    
    with tab1:
        st.subheader("Observations des chaleurs / synchronisation")
        with st.form("form_chaleur"):
            date_debut = st.date_input("Date de début", value=datetime.today().date())
            date_fin = st.date_input("Date de fin (optionnelle)", value=None)
            methode = st.selectbox("Méthode", ["Naturelle", "Progestagène", "Autre"])
            obs = st.text_area("Observations")
            if st.form_submit_button("Enregistrer"):
                db.execute(
                    "INSERT INTO chaleurs (brebis_id, date_debut, date_fin, methode_synchro, observation) VALUES (?, ?, ?, ?, ?)",
                    (bid, date_debut.isoformat(), date_fin.isoformat() if date_fin else None, methode, obs)
                )
                st.success("Chaleurs enregistrées")
                st.rerun()
        
        chaleurs = db.fetchall(
            "SELECT date_debut, date_fin, methode_synchro, observation FROM chaleurs WHERE brebis_id=? ORDER BY date_debut DESC",
            (bid,)
        )
        if chaleurs:
            df = pd.DataFrame(chaleurs, columns=["Début", "Fin", "Méthode", "Observations"])
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("Saillies / Inséminations")
        with st.form("form_saillie"):
            date_saillie = st.date_input("Date de saillie", value=datetime.today().date())
            male_id = st.text_input("Identifiant du bélier")
            methode = st.selectbox("Méthode", ["Naturelle", "Insémination artificielle"])
            resultat = st.selectbox("Résultat", ["En attente", "Gestante", "Non gestante"])
            if st.form_submit_button("Enregistrer"):
                db.execute(
                    "INSERT INTO saillies (brebis_id, date_saillie, male_id, methode, resultat) VALUES (?, ?, ?, ?, ?)",
                    (bid, date_saillie.isoformat(), male_id, methode, resultat)
                )
                st.success("Saillie enregistrée")
                st.rerun()
        
        saillies = db.fetchall(
            "SELECT date_saillie, male_id, methode, resultat FROM saillies WHERE brebis_id=? ORDER BY date_saillie DESC",
            (bid,)
        )
        if saillies:
            df = pd.DataFrame(saillies, columns=["Date", "Bélier", "Méthode", "Résultat"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Prédiction de mise bas pour la dernière saillie avec résultat "Gestante"
            last_gest = db.fetchone(
                "SELECT date_saillie FROM saillies WHERE brebis_id=? AND resultat='Gestante' ORDER BY date_saillie DESC",
                (bid,)
            )
            if last_gest:
                date_saillie = datetime.strptime(last_gest[0], "%Y-%m-%d").date()
                date_mb = date_saillie + timedelta(days=150)  # Durée moyenne gestation
                st.success(f"📅 Mise bas prévue autour du : {date_mb.strftime('%d/%m/%Y')}")
    
    with tab3:
        st.subheader("Mises bas enregistrées")
        with st.form("form_mb"):
            date_mb = st.date_input("Date de mise bas", value=datetime.today().date())
            nb_agneaux = st.number_input("Nombre d'agneaux", min_value=1, step=1)
            poids_portee = st.number_input("Poids total de la portée (kg)", min_value=0.0, step=0.1)
            remarques = st.text_area("Remarques")
            if st.form_submit_button("Enregistrer"):
                db.execute(
                    "INSERT INTO mises_bas (brebis_id, date_mise_bas, nb_agneaux, poids_portee, remarques) VALUES (?, ?, ?, ?, ?)",
                    (bid, date_mb.isoformat(), nb_agneaux, poids_portee, remarques)
                )
                st.success("Mise bas enregistrée")
                st.rerun()
        
        mbas = db.fetchall(
            "SELECT date_mise_bas, nb_agneaux, poids_portee, remarques FROM mises_bas WHERE brebis_id=? ORDER BY date_mise_bas DESC",
            (bid,)
        )
        if mbas:
            df = pd.DataFrame(mbas, columns=["Date", "Agneaux", "Poids portée (kg)", "Remarques"])
            st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# NOUVELLE PAGE NUTRITION AVANCÉE
# -----------------------------------------------------------------------------
def page_nutrition_avancee():
    st.title("🌾 Nutrition avancée et formulation")
    
    tab1, tab2, tab3 = st.tabs(["📦 Catalogue aliments", "📋 Rations types", "🧮 Calcul ration personnalisée"])
    
    with tab1:
        st.subheader("Gestion des aliments")
        
        # Formulaire d'ajout d'aliment
        with st.expander("➕ Ajouter un aliment"):
            with st.form("form_aliment"):
                nom = st.text_input("Nom de l'aliment")
                type_alim = st.selectbox("Type", ["Fourrage", "Concentré", "Minéral", "Autre"])
                uem = st.number_input("UEM (MJ/kg)", min_value=0.0, step=0.1, format="%.2f")
                pdin = st.number_input("PDIN (g/kg)", min_value=0.0, step=1.0)
                ms = st.number_input("Matière sèche (%)", min_value=0.0, max_value=100.0, value=85.0, step=1.0)
                prix = st.number_input("Prix (DA/kg)", min_value=0.0, step=1.0, format="%.2f")
                if st.form_submit_button("Ajouter"):
                    try:
                        db.execute(
                            "INSERT INTO aliments (nom, type, uem, pdin, ms, prix_kg) VALUES (?, ?, ?, ?, ?, ?)",
                            (nom, type_alim, uem, pdin, ms, prix)
                        )
                        st.success("Aliment ajouté")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Cet aliment existe déjà.")
        
        # Liste des aliments
        aliments = db.fetchall("SELECT id, nom, type, uem, pdin, ms, prix_kg FROM aliments")
        if aliments:
            df_alim = pd.DataFrame(aliments, columns=["ID", "Nom", "Type", "UEM", "PDIN", "MS%", "Prix DA/kg"])
            st.dataframe(df_alim, use_container_width=True, hide_index=True)
            
            # Modification de prix (flexibilité)
            with st.expander("💰 Modifier un prix"):
                choix = st.selectbox("Choisir un aliment", [f"{a[0]} - {a[1]}" for a in aliments])
                aid = int(choix.split(" - ")[0])
                nouveau_prix = st.number_input("Nouveau prix (DA/kg)", min_value=0.0, step=1.0)
                if st.button("Mettre à jour"):
                    db.execute("UPDATE aliments SET prix_kg=? WHERE id=?", (nouveau_prix, aid))
                    st.success("Prix mis à jour")
                    st.rerun()
        else:
            st.info("Aucun aliment enregistré. Commencez par en ajouter.")
    
    with tab2:
        st.subheader("Rations types par état physiologique")
        
        # Sélection d'un état
        etat_physio = st.selectbox("État physiologique", Config.ETATS_PHYSIO)
        
        # Vérifier si une ration existe déjà pour cet état
        ration_existante = db.fetchone("SELECT id, nom, description FROM rations WHERE etat_physio=?", (etat_physio,))
        if ration_existante:
            st.success(f"Ration existante : {ration_existante[1]}")
            # Afficher composition
            compo = db.fetchall("""
                SELECT a.nom, rc.quantite_kg, a.prix_kg
                FROM ration_composition rc
                JOIN aliments a ON rc.aliment_id = a.id
                WHERE rc.ration_id=?
            """, (ration_existante[0],))
            if compo:
                df_compo = pd.DataFrame(compo, columns=["Aliment", "Quantité (kg/jour)", "Prix/kg"])
                df_compo["Coût (DA/jour)"] = df_compo["Quantité (kg/jour)"] * df_compo["Prix/kg"]
                st.dataframe(df_compo, use_container_width=True, hide_index=True)
                total_journalier = df_compo["Coût (DA/jour)"].sum()
                st.metric("Coût total journalier", f"{total_journalier:.2f} DA")
            else:
                st.info("Cette ration n'a pas d'aliments associés.")
        else:
            st.info("Aucune ration définie pour cet état.")
        
        # Formulaire pour créer/modifier une ration
        with st.expander("⚙️ Configurer une ration pour cet état"):
            # Récupérer les aliments disponibles
            aliments = db.fetchall("SELECT id, nom FROM aliments")
            if not aliments:
                st.warning("Ajoutez d'abord des aliments.")
            else:
                # Si une ration existe déjà, on la modifie, sinon on crée
                if ration_existante:
                    ration_id = ration_existante[0]
                    st.markdown("**Modifier la ration existante**")
                else:
                    # Créer une nouvelle ration
                    nom_ration = st.text_input("Nom de la ration", value=f"Ration {etat_physio}")
                    desc = st.text_area("Description")
                    if st.button("Créer la ration"):
                        db.execute(
                            "INSERT INTO rations (nom, etat_physio, description) VALUES (?, ?, ?)",
                            (nom_ration, etat_physio, desc)
                        )
                        st.success("Ration créée, vous pouvez maintenant ajouter des aliments.")
                        st.rerun()
                    ration_id = None
                
                if ration_id:
                    # Ajouter des aliments à la ration
                    st.subheader("Ajouter un aliment à cette ration")
                    aliment_choix = st.selectbox("Choisir un aliment", [f"{a[0]} - {a[1]}" for a in aliments])
                    aid = int(aliment_choix.split(" - ")[0])
                    quantite = st.number_input("Quantité (kg/jour)", min_value=0.0, step=0.1, format="%.2f")
                    if st.button("Ajouter à la ration"):
                        # Vérifier si déjà présent
                        existing = db.fetchone(
                            "SELECT id FROM ration_composition WHERE ration_id=? AND aliment_id=?",
                            (ration_id, aid)
                        )
                        if existing:
                            db.execute(
                                "UPDATE ration_composition SET quantite_kg=? WHERE id=?",
                                (quantite, existing[0])
                            )
                        else:
                            db.execute(
                                "INSERT INTO ration_composition (ration_id, aliment_id, quantite_kg) VALUES (?, ?, ?)",
                                (ration_id, aid, quantite)
                            )
                        st.success("Aliment ajouté/modifié")
                        st.rerun()
                    
                    # Supprimer un aliment
                    with st.expander("🗑️ Supprimer un aliment de la ration"):
                        compo = db.fetchall("""
                            SELECT rc.id, a.nom FROM ration_composition rc
                            JOIN aliments a ON rc.aliment_id = a.id
                            WHERE rc.ration_id=?
                        """, (ration_id,))
                        if compo:
                            choix_suppr = st.selectbox("Aliment à retirer", [f"{c[0]} - {c[1]}" for c in compo])
                            suppr_id = int(choix_suppr.split(" - ")[0])
                            if st.button("Retirer"):
                                db.execute("DELETE FROM ration_composition WHERE id=?", (suppr_id,))
                                st.success("Aliment retiré")
                                st.rerun()
    
    with tab3:
        st.subheader("Calcul de ration personnalisée")
        
        # Sélection d'une brebis pour adapter les besoins
        brebis_list = db.fetchall("""
            SELECT b.id, b.numero_id, b.nom, b.etat_physio, b.poids_vif
            FROM brebis b
            JOIN elevages e ON b.elevage_id = e.id
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
        """, (st.session_state.user_id,))
        brebis_dict = {f"{b[0]} - {b[1]} {b[2]}": b[0] for b in brebis_list}
        
        if brebis_dict:
            choix = st.selectbox("Choisir une brebis (ou personnaliser)", ["Personnalisé"] + list(brebis_dict.keys()))
            if choix != "Personnalisé":
                bid = brebis_dict[choix]
                infos = db.fetchone("SELECT poids_vif, etat_physio FROM brebis WHERE id=?", (bid,))
                if infos:
                    poids_def = infos[0] or 50.0
                    etat_def = infos[1] or "Tarie"
                else:
                    poids_def = 50.0
                    etat_def = "Tarie"
            else:
                poids_def = 50.0
                etat_def = "Tarie"
            
            col1, col2 = st.columns(2)
            with col1:
                poids = st.number_input("Poids vif (kg)", min_value=10.0, max_value=150.0, value=poids_def)
            with col2:
                etat = st.selectbox("État physiologique", Config.ETATS_PHYSIO, index=Config.ETATS_PHYSIO.index(etat_def) if etat_def in Config.ETATS_PHYSIO else 0)
            
            lactation = st.number_input("Production laitière (L/j)", min_value=0.0, value=0.0, step=0.5)
            
            # Calcul des besoins
            besoins = OvinScience.besoins_nutritionnels(poids, etat, lactation)
            st.info(f"**Besoins journaliers** : UEM = {besoins['uem']} MJ, PDIN = {besoins['pdin']} g, MS = {besoins['ms']} kg")
            
            # Récupérer les aliments disponibles
            aliments = db.fetchall("SELECT id, nom, type, uem, pdin, ms, prix_kg FROM aliments")
            if not aliments:
                st.warning("Ajoutez d'abord des aliments.")
            else:
                st.subheader("Composition de la ration")
                # Permettre de choisir plusieurs aliments avec quantités
                ration_temp = {}
                for alim in aliments:
                    with st.expander(f"{alim[1]} ({alim[2]}) - {alim[6]} DA/kg"):
                        qte = st.number_input(f"Quantité (kg MS)", min_value=0.0, step=0.1, key=f"qte_{alim[0]}")
                        if qte > 0:
                            ration_temp[alim[0]] = {
                                "nom": alim[1],
                                "qte": qte,
                                "uem": alim[3],
                                "pdin": alim[4],
                                "ms": alim[5],
                                "prix": alim[6]
                            }
                
                if ration_temp and st.button("Calculer la ration"):
                    total_uem = sum(v["qte"] * v["uem"] for v in ration_temp.values())
                    total_pdin = sum(v["qte"] * v["pdin"] for v in ration_temp.values())
                    total_ms = sum(v["qte"] for v in ration_temp.values())
                    total_prix = sum(v["qte"] * v["prix"] for v in ration_temp.values())
                    
                    st.subheader("Résultats")
                    cola, colb, colc = st.columns(3)
                    cola.metric("UEM apportée", f"{total_uem:.2f} MJ", delta=f"{total_uem - besoins['uem']:.2f}")
                    colb.metric("PDIN apportée", f"{total_pdin:.2f} g", delta=f"{total_pdin - besoins['pdin']:.2f}")
                    colc.metric("MS apportée", f"{total_ms:.2f} kg", delta=f"{total_ms - besoins['ms']:.2f}")
                    
                    st.metric("Coût journalier", f"{total_prix:.2f} DA")
                    
                    # Vérification équilibre
                    if total_uem < besoins['uem'] * 0.9:
                        st.warning("⚠️ Apport énergétique insuffisant")
                    elif total_uem > besoins['uem'] * 1.1:
                        st.warning("⚠️ Excès d'énergie")
                    else:
                        st.success("✅ Énergie équilibrée")
                    
                    if total_pdin < besoins['pdin'] * 0.9:
                        st.warning("⚠️ Apport protéique insuffisant")
                    elif total_pdin > besoins['pdin'] * 1.1:
                        st.warning("⚠️ Excès de protéines")
                    else:
                        st.success("✅ Protéines équilibrées")
        else:
            st.info("Aucune brebis disponible. Vous pouvez utiliser 'Personnalisé'.")

# -----------------------------------------------------------------------------
# PAGE EXPORT (déjà définie)
# -----------------------------------------------------------------------------
# (La fonction page_export a été donnée précédemment, nous la gardons)

# -----------------------------------------------------------------------------
# SIDEBAR ET MAIN
# -----------------------------------------------------------------------------
def sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/sheep.png", width=80)
        st.title(f"🐑 {Config.APP_NAME}")
        st.caption(f"**{Config.LABORATOIRE}** v{Config.VERSION}")
        st.divider()
        
        if st.session_state.user_id:
            menu = st.radio(
                "Navigation",
                ["📊 Tableau de bord", 
                 "🐑 Gestion élevage",
                 "🧬 Génomique NCBI", 
                 "🥩 Composition", 
                 "📸 Photogrammétrie", 
                 "🔮 Prédictions", 
                 "🌾 Nutrition avancée",
                 "🥛 Production laitière",
                 "🧬 Génomique avancée",
                 "🏥 Santé",
                 "🤰 Reproduction",
                 "📤 Export données",
                 "🚪 Déconnexion"],
                label_visibility="collapsed"
            )
            
            st.divider()
            
            if st.button("💾 Sauvegarde rapide", use_container_width=True):
                st.download_button(
                    label="Télécharger JSON",
                    data=json.dumps({"user_id": st.session_state.user_id, "date": datetime.now().isoformat()}),
                    file_name=f"ovin_backup_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
            page_map = {
                "📊 Tableau de bord": "dashboard",
                "🐑 Gestion élevage": "gestion_elevage",
                "🧬 Génomique NCBI": "genomique",
                "🥩 Composition": "composition",
                "📸 Photogrammétrie": "analyse",
                "🔮 Prédictions": "prediction",
                "🌾 Nutrition avancée": "nutrition_avancee",
                "🥛 Production laitière": "production",
                "🧬 Génomique avancée": "genomique_avancee",
                "🏥 Santé": "sante",
                "🤰 Reproduction": "reproduction",
                "📤 Export données": "export",
                "🚪 Déconnexion": "logout"
            }
            
            selected_page = page_map.get(menu, "dashboard")
            
            if selected_page == "logout":
                st.session_state.user_id = None
                st.session_state.current_page = "login"
                st.rerun()
            elif selected_page != st.session_state.current_page:
                st.session_state.current_page = selected_page
                st.rerun()

def main():
    sidebar()
    
    if st.session_state.current_page == "login":
        page_login()
    elif st.session_state.current_page == "dashboard":
        page_dashboard()
    elif st.session_state.current_page == "genomique":
        page_genomique()
    elif st.session_state.current_page == "composition":
        page_composition()
    elif st.session_state.current_page == "analyse":
        page_analyse()
    elif st.session_state.current_page == "prediction":
        page_prediction()
    elif st.session_state.current_page == "nutrition_avancee":
        page_nutrition_avancee()
    elif st.session_state.current_page == "production":
        page_production()
    elif st.session_state.current_page == "genomique_avancee":
        page_genomique_avancee()
    elif st.session_state.current_page == "gestion_elevage":
        page_gestion_elevage()
    elif st.session_state.current_page == "sante":
        page_sante()
    elif st.session_state.current_page == "reproduction":
        page_reproduction()
    elif st.session_state.current_page == "export":
        page_export()

# -----------------------------------------------------------------------------
# POINT D'ENTRÉE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Initialisation de la base de données et de la session
    db = get_database()
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.current_page = "login"
    
    # Configuration de la page
    st.set_page_config(
        page_title="Ovin Manager Pro",
        page_icon="🐑",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    main()
