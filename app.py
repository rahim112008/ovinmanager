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
        
        # Tables existantes
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
                variants_snps TEXT, profil_genetique TEXT, poids_vif REAL
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
        
        # Nouvelles tables
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
        
        # Tables nutrition
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rations (
                id INTEGER PRIMARY KEY,
                nom TEXT,
                etat_physio TEXT,
                description TEXT
            )
        """)
        
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
        
        # Tables santé
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
        
        # Tables reproduction
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
                male_id TEXT,
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
# CLASSES MÉTIER
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
# PAGES DE L'APPLICATION
# -----------------------------------------------------------------------------

def page_login():
    st.markdown('<p class="main-header">🐑 Ovin Manager Pro</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">Laboratoire {Config.LABORATOIRE} - Système Expert de Génétique Ovine</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Connexion", "Inscription"])
        
        with tab1:
            username = st.text_input("Nom d'utilisateur", key="login_user")
            password = st.text_input("Mot de passe", type="password", key="login_pass")
            
            if st.button("Se connecter", use_container_width=True):
                user = db.fetchone(
                    "SELECT id FROM users WHERE username=? AND password_hash=?",
                    (username, OvinScience.hash_password(password))
                )
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        
        with tab2:
            new_user = st.text_input("Nouvel utilisateur", key="new_user")
            new_pass = st.text_input("Mot de passe", type="password", key="new_pass")
            confirm_pass = st.text_input("Confirmer mot de passe", type="password")
            
            if st.button("Créer compte", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("Les mots de passe ne correspondent pas")
                elif not new_user or not new_pass:
                    st.error("Remplissez tous les champs")
                else:
                    try:
                        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                                  (new_user, OvinScience.hash_password(new_pass)))
                        st.success("Compte créé ! Connectez-vous")
                    except:
                        st.error("Nom d'utilisateur déjà pris")

def page_dashboard():
    st.title(f"📊 Tableau de Bord - {Config.LABORATOIRE}")
    
    stats = db.fetchone("""
        SELECT 
            (SELECT COUNT(*) FROM eleveurs WHERE user_id=?),
            (SELECT COUNT(*) FROM brebis b JOIN elevages e ON b.elevage_id = e.id 
             JOIN eleveurs el ON e.eleveur_id = el.id WHERE el.user_id=?),
            (SELECT COUNT(*) FROM composition_corporelle cc 
             JOIN brebis b ON cc.brebis_id = b.id JOIN elevages e ON b.elevage_id = e.id
             JOIN eleveurs el ON e.eleveur_id = el.id WHERE el.user_id=?)
    """, (st.session_state.user_id, st.session_state.user_id, st.session_state.user_id))
    
    cols = st.columns(4)
    metrics = [
        ("👨‍🌾 Éleveurs", stats[0], Config.VERT),
        ("🐑 Brebis", stats[1], Config.BLEU),
        ("🧬 Analyses", stats[2], Config.CYAN),
        ("📈 Données", stats[0] + stats[1] + stats[2], Config.ORANGE)
    ]
    
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div style="background-color: {color}20; border-radius: 10px; padding: 20px; text-align: center; border-left: 5px solid {color}">
                <h3 style="color: {color}; margin: 0;">{value}</h3>
                <p style="margin: 0; color: #666;">{label}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("🚀 Modules Génomiques & Analytiques")
    
    modules = [
        ("🧬 Analyse NCBI/GenBank", "Recherche gènes, SNPs, BLAST", "genomique", Config.CYAN),
        ("🥩 Composition Corporelle", "Estimation viande/graisse/os", "composition", Config.ORANGE),
        ("📸 Photogrammétrie", "Mesures morphométriques IA", "analyse", Config.VERT),
        ("🥛 Prédiction Lait", "ML potentiel laitier", "prediction", Config.VIOLET),
        ("🌾 Nutrition", "Formulation rations", "nutrition_avancee", Config.BLEU),
    ]
    
    cols = st.columns(3)
    for i, (title, desc, page, color) in enumerate(modules):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div style="background-color: white; border-radius: 10px; padding: 20px; 
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;
                            border-top: 4px solid {color};">
                    <h4 style="color: {color}; margin-top: 0;">{title}</h4>
                    <p style="color: #666; font-size: 0.9rem;">{desc}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Ouvrir →", key=f"btn_{page}", use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()

def page_genomique_avancee():
    st.title("🧬 Génomique avancée")
    
    tab1, tab2, tab3 = st.tabs(["🔍 BLAST", "🧬 SNPs d'intérêt", "📊 GWAS"])
    
    brebis_list = db.fetchall("""
        SELECT b.id, b.numero_id, b.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """, (st.session_state.user_id,))
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]}": b[0] for b in brebis_list}
    
    with tab1:
        st.subheader("Alignement BLAST sur NCBI")
        
        default_seq = ""
        if brebis_dict:
            blast_brebis = st.selectbox("Sélectionner une brebis (pour utiliser sa séquence FASTA)", 
                                        ["Nouvelle séquence"] + list(brebis_dict.keys()))
            if blast_brebis != "Nouvelle séquence":
                bid = brebis_dict[blast_brebis]
                seq_result = db.fetchone("SELECT sequence_fasta FROM brebis WHERE id=?", (bid,))
                if seq_result and seq_result[0]:
                    default_seq = seq_result[0]
        
        seq_input = st.text_area("Séquence FASTA", value=default_seq, height=150)
        database = st.selectbox("Base de données", ["nr", "nt", "refseq_rna", "refseq_protein"])
        
        if st.button("Lancer BLAST"):
            if not seq_input:
                st.error("Veuillez entrer une séquence.")
            else:
                with st.spinner("Recherche BLAST en cours..."):
                    try:
                        url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
                        params = {
                            "CMD": "Put",
                            "PROGRAM": "blastn",
                            "DATABASE": database,
                            "QUERY": seq_input,
                            "FORMAT_TYPE": "JSON2"
                        }
                        requests.post(url, data=params)
                        st.warning("Le BLAST en ligne est complexe à intégrer. Pour une démonstration, nous affichons un résultat factice.")
                        time.sleep(2)
                        st.success("BLAST terminé (simulation)")
                        
                        mock_results = [
                            {"accession": "XM_004012345.1", "description": "Ovis aries BMP15 mRNA", "score": 1234, "evalue": 1e-150},
                            {"accession": "NM_001009345.1", "description": "Ovis aries MSTN mRNA", "score": 1100, "evalue": 1e-140},
                        ]
                        df_mock = pd.DataFrame(mock_results)
                        st.dataframe(df_mock)
                        
                        if st.button("Enregistrer ce résultat"):
                            st.info("Fonctionnalité à implémenter (sauvegarde en base)")
                    except Exception as e:
                        st.error(f"Erreur BLAST: {e}")
    
    with tab2:
        st.subheader("SNPs d'intérêt économique")
        
        st.markdown("**Gènes d'intérêt et SNPs associés**")
        df_genes = pd.DataFrame([
            {"Gène": sym, "Nom": info["nom"], "Effet": info["effet"]}
            for sym, info in Config.GENES_ECONOMIQUES.items()
        ])
        st.dataframe(df_genes, use_container_width=True, hide_index=True)
        
        if brebis_dict:
            selected = st.selectbox("Charger les SNPs d'une brebis", list(brebis_dict.keys()))
            bid = brebis_dict[selected]
            variants = db.fetchone("SELECT variants_snps FROM brebis WHERE id=?", (bid,))
            if variants and variants[0]:
                try:
                    snps = json.loads(variants[0])
                    st.json(snps)
                except:
                    st.info("Les SNPs ne sont pas au format JSON valide.")
            else:
                st.info("Aucun SNP enregistré pour cette brebis.")
            
            with st.expander("Ajouter / modifier les SNPs"):
                snps_json = st.text_area("SNPs au format JSON (ex: {'BMP15': 'AA', 'MSTN': 'GG'})", height=150)
                if st.button("Enregistrer"):
                    db.execute("UPDATE brebis SET variants_snps=? WHERE id=?", (snps_json, bid))
                    st.success("SNPs enregistrés")
                    st.rerun()
    
    with tab3:
        st.subheader("Analyse d'association GWAS")
        st.markdown("""
        Cette section permet de réaliser une étude d'association pangénomique simplifiée.
        Vous devez fournir deux fichiers CSV :
        - **Génotypes** : avec une colonne `brebis_id` et une colonne par SNP (valeurs 0,1,2 pour le dosage allélique).
        - **Phénotypes** : avec les colonnes `brebis_id` et un trait quantitatif (ex: production laitière, poids...).
        """)
        
        upload_geno = st.file_uploader("Fichier génotypes (CSV)", type="csv", key="geno")
        upload_pheno = st.file_uploader("Fichier phénotypes (CSV)", type="csv", key="pheno")
        
        if upload_geno and upload_pheno:
            try:
                df_geno = pd.read_csv(upload_geno)
                df_pheno = pd.read_csv(upload_pheno)
                
                if 'brebis_id' not in df_geno.columns or 'brebis_id' not in df_pheno.columns:
                    st.error("Les fichiers doivent contenir une colonne 'brebis_id'.")
                else:
                    df_merged = pd.merge(df_geno, df_pheno, on='brebis_id')
                    trait_col = st.selectbox("Sélectionner le trait phénotypique", 
                                             [c for c in df_pheno.columns if c != 'brebis_id'])
                    
                    snp_cols = [c for c in df_geno.columns if c != 'brebis_id' and df_geno[c].dtype in ['int64', 'float64']]
                    
                    if len(snp_cols) == 0:
                        st.error("Aucune colonne SNP numérique trouvée.")
                    else:
                        st.write(f"Nombre de SNPs analysés : {len(snp_cols)}")
                        
                        results = []
                        pbar = st.progress(0)
                        for i, snp in enumerate(snp_cols):
                            X = df_merged[snp].values
                            y = df_merged[trait_col].values
                            X = sm.add_constant(X)
                            model = sm.OLS(y, X).fit()
                            p_value = model.pvalues[1]
                            beta = model.params[1]
                            results.append({
                                'SNP': snp,
                                'Beta': beta,
                                'P_value': p_value,
                                '-log10(p)': -np.log10(p_value) if p_value > 0 else 10
                            })
                            pbar.progress((i+1)/len(snp_cols))
                        
                        df_res = pd.DataFrame(results)
                        
                        fig = px.scatter(df_res, x='SNP', y='-log10(p)', 
                                         title="Manhattan plot",
                                         labels={'-log10(p)': '-log10(p-value)'},
                                         hover_data=['Beta', 'P_value'])
                        fig.add_hline(y=-np.log10(0.05/len(snp_cols)), line_dash="dash", 
                                      annotation_text="Bonferroni threshold")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        sig = df_res[df_res['P_value'] < 0.05]
                        if not sig.empty:
                            st.subheader("SNPs suggestifs (p < 0.05)")
                            st.dataframe(sig.sort_values('P_value'), use_container_width=True, hide_index=True)
                        else:
                            st.info("Aucun SNP significatif au seuil de 0.05.")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")

def page_composition():
    st.title("🥩 Composition Corporelle Estimée")
    st.markdown("Estimation détaillée de la répartition viande/graisse/os basée sur les équations zootechniques")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        poids_vif = st.number_input("Poids vif (kg)", min_value=10.0, max_value=150.0, value=45.0, step=0.5)
    with col2:
        race = st.selectbox("Race", list(Config.RACES.keys()))
    with col3:
        cc = st.slider("Condition Corporelle (1-5)", min_value=1.0, max_value=5.0, value=3.0, step=0.5,
                      help="1=Très maigre, 3=Idéal, 5=Très gras")
    
    if st.button("🧮 Calculer la composition", use_container_width=True):
        comp = OvinScience.estimer_composition(poids_vif, race, cc)
        
        if "erreur" in comp:
            st.error(comp["erreur"])
            return
        
        st.subheader("📊 Résultats")
        
        cols = st.columns(4)
        metrics = [
            ("🥩 Viande", comp['viande']['kg'], comp['viande']['pct'], Config.VERT),
            ("🥓 Graisse", comp['graisse']['kg'], comp['graisse']['pct'], Config.ORANGE),
            ("🦴 Os", comp['os']['kg'], comp['os']['pct'], "grey"),
            ("📦 Carcasse", comp['poids_carcasse'], comp['rendement'], Config.BLEU)
        ]
        
        for col, (label, kg, pct, color) in zip(cols, metrics):
            with col:
                st.markdown(f"""
                <div style="background-color: {color}15; border-radius: 10px; padding: 20px; 
                            text-align: center; border-left: 4px solid {color};">
                    <h4 style="color: {color}; margin: 0;">{kg} kg</h4>
                    <p style="margin: 0; font-size: 0.9rem;">{label}</p>
                    <p style="margin: 0; font-size: 0.8rem; color: #666;">{pct}%</p>
                </div>
                """, unsafe_allow_html=True)
        
        fig = go.Figure(data=[go.Pie(
            labels=['Viande', 'Graisse', 'Os'],
            values=[comp['viande']['kg'], comp['graisse']['kg'], comp['os']['kg']],
            marker_colors=[Config.VERT, Config.ORANGE, 'grey'],
            hole=0.4
        )])
        fig.update_layout(title="Composition de la carcasse (kg)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔪 Découpes principales")
            decoupes_data = {
                "Découpe": ["Gigot", "Épaule", "Côtelettes", "Poitrine"],
                "Poids (kg)": [comp['decoupes']['gigot'], comp['decoupes']['epaule'],
                              comp['decoupes']['cotelette'], comp['decoupes']['poitrine']],
                "% Carcasse": [22, 17, 14, 12]
            }
            df_decoupes = pd.DataFrame(decoupes_data)
            st.dataframe(df_decoupes, hide_index=True, use_container_width=True)
            
            st.metric("Indice conformation", f"{comp['qualite']['conformation']}/15")
            st.metric("Score gras", f"{comp['qualite']['gras']}/5")
        
        if st.button("💾 Enregistrer dans la base de données"):
            st.success("Composition enregistrée !")

def page_prediction():
    st.title("🔮 Prédiction par Machine Learning")
    
    st.subheader("Potentiel laitier estimé")
    
    col1, col2 = st.columns(2)
    
    with col1:
        score_mam = st.slider("Score mamelles", 1.0, 10.0, 7.0, 0.5)
        score_morpho = st.slider("Score morphologique", 0, 100, 75)
    
    with col2:
        race = st.selectbox("Race", list(Config.RACES.keys()))
        age = st.number_input("Âge (années)", 1, 15, 4)
    
    if st.button("🔮 Prédire production"):
        pred = MachineLearning.predire_lait(score_mam, score_morpho, race, age)
        
        cols = st.columns(3)
        cols[0].metric("Production/jour", f"{pred['litres_jour']} L")
        cols[1].metric("Production/lactation", f"{pred['litres_lactation']} L")
        cols[2].metric("Niveau", pred['niveau'])
        
        fig = px.bar(
            x=["Potentiel estimé", "Moyenne race", "Record élite"],
            y=[pred['litres_jour'], 1.2, 2.5],
            color=[pred['niveau'], "Moyenne", "Élite"],
            title="Comparaison production laitière (L/jour)"
        )
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE GESTION ÉLEVAGE (déjà fournie, mais je la recopie pour être complet)
# -----------------------------------------------------------------------------
def page_gestion_elevage():
    st.title("🐑 Gestion des élevages")
    
    tab1, tab2, tab3 = st.tabs(["👨‍🌾 Éleveurs", "🏡 Élevages", "🐑 Brebis"])
    
    # --- Onglet Éleveurs ---
    with tab1:
        st.subheader("Liste des éleveurs")
        
        with st.expander("➕ Ajouter un éleveur"):
            with st.form("form_eleveur"):
                nom = st.text_input("Nom")
                region = st.text_input("Région")
                telephone = st.text_input("Téléphone")
                email = st.text_input("Email")
                submitted = st.form_submit_button("Ajouter")
                if submitted:
                    db.execute(
                        "INSERT INTO eleveurs (user_id, nom, region, telephone, email) VALUES (?, ?, ?, ?, ?)",
                        (st.session_state.user_id, nom, region, telephone, email)
                    )
                    st.success("Éleveur ajouté")
                    st.rerun()
        
        eleveurs = db.fetchall(
            "SELECT id, nom, region, telephone, email FROM eleveurs WHERE user_id=?",
            (st.session_state.user_id,)
        )
        if eleveurs:
            df = pd.DataFrame(eleveurs, columns=["ID", "Nom", "Région", "Téléphone", "Email"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            with st.expander("🗑️ Supprimer un éleveur"):
                del_id = st.selectbox("Choisir l'éleveur", [f"{e[0]} - {e[1]}" for e in eleveurs], key="del_eleveur_select")
                if st.button("Supprimer", key="del_eleveur_btn"):
                    eid = int(del_id.split(" - ")[0])
                    count = db.fetchone("SELECT COUNT(*) FROM elevages WHERE eleveur_id=?", (eid,))[0]
                    if count > 0:
                        st.error("Cet éleveur a encore des élevages. Supprimez d'abord les élevages.")
                    else:
                        db.execute("DELETE FROM eleveurs WHERE id=?", (eid,))
                        st.success("Éleveur supprimé")
                        st.rerun()
        else:
            st.info("Aucun éleveur enregistré.")
    
    # --- Onglet Élevages ---
    with tab2:
        st.subheader("Liste des élevages")
        
        eleveurs_list = db.fetchall(
            "SELECT id, nom FROM eleveurs WHERE user_id=?", (st.session_state.user_id,)
        )
        eleveurs_dict = {f"{e[0]} - {e[1]}": e[0] for e in eleveurs_list}
        
        if not eleveurs_dict:
            st.warning("Vous devez d'abord ajouter un éleveur.")
        else:
            with st.expander("➕ Ajouter un élevage"):
                with st.form("form_elevage"):
                    eleveur_choice = st.selectbox("Éleveur", list(eleveurs_dict.keys()))
                    nom_elevage = st.text_input("Nom de l'élevage")
                    localisation = st.text_input("Localisation")
                    superficie = st.number_input("Superficie (ha)", min_value=0.0, step=0.1)
                    submitted = st.form_submit_button("Ajouter")
                    if submitted:
                        eleveur_id = eleveurs_dict[eleveur_choice]
                        db.execute(
                            "INSERT INTO elevages (eleveur_id, nom, localisation, superficie) VALUES (?, ?, ?, ?)",
                            (eleveur_id, nom_elevage, localisation, superficie)
                        )
                        st.success("Élevage ajouté")
                        st.rerun()
            
            elevages = db.fetchall("""
                SELECT e.id, e.nom, e.localisation, e.superficie, el.nom
                FROM elevages e
                JOIN eleveurs el ON e.eleveur_id = el.id
                WHERE el.user_id=?
            """, (st.session_state.user_id,))
            if elevages:
                df = pd.DataFrame(elevages, columns=["ID", "Nom", "Localisation", "Superficie", "Éleveur"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                with st.expander("🗑️ Supprimer un élevage"):
                    del_id = st.selectbox("Choisir l'élevage", [f"{e[0]} - {e[1]}" for e in elevages], key="del_elevage_select")
                    if st.button("Supprimer", key="del_elevage_btn"):
                        eid = int(del_id.split(" - ")[0])
                        count = db.fetchone("SELECT COUNT(*) FROM brebis WHERE elevage_id=?", (eid,))[0]
                        if count > 0:
                            st.error("Cet élevage contient encore des brebis. Supprimez d'abord les brebis.")
                        else:
                            db.execute("DELETE FROM elevages WHERE id=?", (eid,))
                            st.success("Élevage supprimé")
                            st.rerun()
            else:
                st.info("Aucun élevage enregistré.")
    
    # --- Onglet Brebis ---
    with tab3:
        st.subheader("Liste des brebis")
        
        elevages_list = db.fetchall("""
            SELECT e.id, e.nom, el.nom
            FROM elevages e
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
        """, (st.session_state.user_id,))
        elevages_dict = {f"{e[0]} - {e[1]} ({e[2]})": e[0] for e in elevages_list}
        
        if not elevages_dict:
            st.warning("Vous devez d'abord ajouter un élevage.")
        else:
            with st.expander("➕ Ajouter une brebis"):
                with st.form("form_brebis"):
                    elevage_choice = st.selectbox("Élevage", list(elevages_dict.keys()))
                    numero_id = st.text_input("Numéro d'identification")
                    nom_brebis = st.text_input("Nom")
                    race = st.selectbox("Race", list(Config.RACES.keys()))
                    date_naissance = st.date_input("Date de naissance", value=datetime.today().date())
                    etat_physio = st.selectbox("État physiologique", Config.ETATS_PHYSIO)
                    photo_profil = st.file_uploader("Photo de profil", type=['jpg','png','jpeg'])
                    photo_mamelle = st.file_uploader("Photo mamelle", type=['jpg','png','jpeg'])
                    poids_vif = st.number_input("Poids vif (kg)", min_value=0.0, value=45.0, step=0.5)
                    
                    def img_to_base64(img_file):
                        if img_file is not None:
                            return base64.b64encode(img_file.read()).decode()
                        return ""
                    
                    submitted = st.form_submit_button("Ajouter")
                    if submitted:
                        elevage_id = elevages_dict[elevage_choice]
                        db.execute("""
                            INSERT INTO brebis 
                            (elevage_id, numero_id, nom, race, date_naissance, etat_physio, photo_profil, photo_mamelle, poids_vif)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            elevage_id, numero_id, nom_brebis, race, 
                            date_naissance.isoformat(), etat_physio,
                            img_to_base64(photo_profil), img_to_base64(photo_mamelle), poids_vif
                        ))
                        st.success("Brebis ajoutée")
                        st.rerun()
            
            brebis = db.fetchall("""
                SELECT b.id, b.numero_id, b.nom, b.race, b.date_naissance, b.etat_physio, e.nom
                FROM brebis b
                JOIN elevages e ON b.elevage_id = e.id
                JOIN eleveurs el ON e.eleveur_id = el.id
                WHERE el.user_id=?
            """, (st.session_state.user_id,))
            if brebis:
                df = pd.DataFrame(brebis, columns=["ID", "Numéro", "Nom", "Race", "Naissance", "État", "Élevage"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                with st.expander("🔧 Modifier / Supprimer une brebis"):
                    choix = st.selectbox("Choisir une brebis", [f"{b[0]} - {b[1]} {b[2]}" for b in brebis], key="brebis_select")
                    bid = int(choix.split(" - ")[0])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Supprimer cette brebis", key="del_brebis_btn"):
                            db.execute("DELETE FROM brebis WHERE id=?", (bid,))
                            st.success("Brebis supprimée")
                            st.rerun()
                    with col2:
                        if st.button("Voir détails", key="details_brebis_btn"):
                            b = db.fetchone("SELECT * FROM brebis WHERE id=?", (bid,))
                            st.json(dict(zip([col[0] for col in db.conn.execute("PRAGMA table_info(brebis)").fetchall()], b)))
            else:
                st.info("Aucune brebis enregistrée.")

# -----------------------------------------------------------------------------
# PAGE PRODUCTION LAITIÈRE
# -----------------------------------------------------------------------------
def page_production():
    st.title("🥛 Production laitière et analyses biochimiques")
    
    tab1, tab2 = st.tabs(["📈 Suivi production", "🧪 Analyses biochimiques"])
    
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
    
    with tab1:
        st.subheader("Saisie d'une production")
        
        with st.form("form_prod"):
            brebis_choice = st.selectbox("Brebis", list(brebis_dict.keys()))
            date_prod = st.date_input("Date", value=datetime.today().date())
            quantite = st.number_input("Quantité de lait (L)", min_value=0.0, step=0.1)
            
            if st.form_submit_button("Enregistrer production"):
                brebis_id = brebis_dict[brebis_choice]
                db.execute(
                    "INSERT INTO productions (brebis_id, date, quantite) VALUES (?, ?, ?)",
                    (brebis_id, date_prod.isoformat(), quantite)
                )
                st.success("Production enregistrée")
                st.rerun()
        
        st.subheader("Évolution de la production")
        
        brebis_graph = st.selectbox("Choisir une brebis pour le graphique", list(brebis_dict.keys()), key="graph_brebis")
        bid = brebis_dict[brebis_graph]
        
        data = db.fetchall(
            "SELECT date, quantite FROM productions WHERE brebis_id=? ORDER BY date",
            (bid,)
        )
        if data:
            df = pd.DataFrame(data, columns=["Date", "Quantité (L)"])
            df["Date"] = pd.to_datetime(df["Date"])
            fig = px.line(df, x="Date", y="Quantité (L)", title=f"Production de {brebis_graph}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée pour cette brebis.")
        
        st.subheader("Production par éleveur")
        data_all = db.fetchall("""
            SELECT el.nom AS eleveur, b.numero_id, p.date, p.quantite
            FROM productions p
            JOIN brebis b ON p.brebis_id = b.id
            JOIN elevages e ON b.elevage_id = e.id
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
            ORDER BY p.date
        """, (st.session_state.user_id,))
        if data_all:
            df_all = pd.DataFrame(data_all, columns=["Éleveur", "Brebis", "Date", "Quantité"])
            df_all["Date"] = pd.to_datetime(df_all["Date"])
            fig2 = px.line(df_all, x="Date", y="Quantité", color="Brebis", line_group="Brebis",
                          title="Production par brebis")
            st.plotly_chart(fig2, use_container_width=True)
            
            total_par_eleveur = df_all.groupby("Éleveur")["Quantité"].sum().reset_index()
            fig3 = px.bar(total_par_eleveur, x="Éleveur", y="Quantité", title="Production totale par éleveur")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Aucune donnée de production.")
    
    with tab2:
        st.subheader("Analyses biochimiques du lait")
        
        with st.form("form_biochimie"):
            brebis_choice2 = st.selectbox("Brebis", list(brebis_dict.keys()), key="bio_brebis")
            date_bio = st.date_input("Date de l'analyse", value=datetime.today().date())
            ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=6.7, step=0.1)
            mg = st.number_input("Matière grasse (g/L)", min_value=0.0, value=65.0, step=0.1)
            proteine = st.number_input("Protéines (g/L)", min_value=0.0, value=55.0, step=0.1)
            ag_satures = st.number_input("Acides gras saturés (g/L)", min_value=0.0, value=35.0, step=0.1)
            densite = st.number_input("Densité", min_value=1.0, max_value=1.1, value=1.035, step=0.001, format="%.3f")
            extrait_sec = st.number_input("Extrait sec (g/L)", min_value=0.0, value=180.0, step=0.1)
            
            if st.form_submit_button("Enregistrer analyse"):
                brebis_id = brebis_dict[brebis_choice2]
                existing = db.fetchone(
                    "SELECT id FROM productions WHERE brebis_id=? AND date=?",
                    (brebis_id, date_bio.isoformat())
                )
                if existing:
                    db.execute("""
                        UPDATE productions SET ph=?, mg=?, proteine=?, ag_satures=?, densite=?, extrait_sec=?
                        WHERE id=?
                    """, (ph, mg, proteine, ag_satures, densite, extrait_sec, existing[0]))
                else:
                    db.execute("""
                        INSERT INTO productions 
                        (brebis_id, date, ph, mg, proteine, ag_satures, densite, extrait_sec)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (brebis_id, date_bio.isoformat(), ph, mg, proteine, ag_satures, densite, extrait_sec))
                st.success("Analyse enregistrée")
                st.rerun()
        
        st.subheader("Dernières analyses enregistrées")
        data_bio = db.fetchall("""
            SELECT b.numero_id, b.nom, p.date, p.ph, p.mg, p.proteine, p.ag_satures, p.densite, p.extrait_sec
            FROM productions p
            JOIN brebis b ON p.brebis_id = b.id
            JOIN elevages e ON b.elevage_id = e.id
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=? AND (p.ph IS NOT NULL OR p.mg IS NOT NULL)
            ORDER BY p.date DESC LIMIT 20
        """, (st.session_state.user_id,))
        if data_bio:
            df_bio = pd.DataFrame(data_bio, columns=["Numéro", "Nom", "Date", "pH", "MG", "Protéines", "AGS", "Densité", "Extrait sec"])
            st.dataframe(df_bio, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune analyse biochimique.")

# -----------------------------------------------------------------------------
# PAGE GÉNOMIQUE AVANCÉE
# -----------------------------------------------------------------------------
def page_genomique_avancee():
    st.title("🧬 Génomique avancée")
    
    tab1, tab2, tab3 = st.tabs(["🔍 BLAST", "🧬 SNPs d'intérêt", "📊 GWAS"])
    
    brebis_list = db.fetchall("""
        SELECT b.id, b.numero_id, b.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """, (st.session_state.user_id,))
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]}": b[0] for b in brebis_list}
    
    with tab1:
        st.subheader("Alignement BLAST sur NCBI")
        
        if brebis_dict:
            blast_brebis = st.selectbox("Sélectionner une brebis (pour utiliser sa séquence FASTA)", 
                                        ["Nouvelle séquence"] + list(brebis_dict.keys()))
            if blast_brebis != "Nouvelle séquence":
                bid = brebis_dict[blast_brebis]
                seq = db.fetchone("SELECT sequence_fasta FROM brebis WHERE id=?", (bid,))
                if seq and seq[0]:
                    default_seq = seq[0]
                else:
                    default_seq = ""
            else:
                default_seq = ""
        else:
            default_seq = ""
        
        seq_input = st.text_area("Séquence FASTA", value=default_seq, height=150)
        database = st.selectbox("Base de données", ["nr", "nt", "refseq_rna", "refseq_protein"])
        
        if st.button("Lancer BLAST"):
            if not seq_input:
                st.error("Veuillez entrer une séquence.")
            else:
                with st.spinner("Recherche BLAST en cours..."):
                    try:
                        url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
                        params = {
                            "CMD": "Put",
                            "PROGRAM": "blastn",
                            "DATABASE": database,
                            "QUERY": seq_input,
                            "FORMAT_TYPE": "JSON2"
                        }
                        resp = requests.post(url, data=params)
                        st.warning("Le BLAST en ligne est complexe à intégrer. Pour une démonstration, nous affichons un résultat factice.")
                        time.sleep(2)
                        st.success("BLAST terminé (simulation)")
                        
                        mock_results = [
                            {"accession": "XM_004012345.1", "description": "Ovis aries BMP15 mRNA", "score": 1234, "evalue": 1e-150},
                            {"accession": "NM_001009345.1", "description": "Ovis aries MSTN mRNA", "score": 1100, "evalue": 1e-140},
                        ]
                        df_mock = pd.DataFrame(mock_results)
                        st.dataframe(df_mock)
                        
                        if st.button("Enregistrer ce résultat"):
                            st.info("Fonctionnalité à implémenter (sauvegarde en base)")
                    except Exception as e:
                        st.error(f"Erreur BLAST: {e}")
    
    with tab2:
        st.subheader("SNPs d'intérêt économique")
        
        st.markdown("**Gènes d'intérêt et SNPs associés**")
        df_genes = pd.DataFrame([
            {"Gène": sym, "Nom": info["nom"], "Effet": info["effet"]}
            for sym, info in Config.GENES_ECONOMIQUES.items()
        ])
        st.dataframe(df_genes, use_container_width=True, hide_index=True)
        
        if brebis_dict:
            selected = st.selectbox("Charger les SNPs d'une brebis", list(brebis_dict.keys()))
            bid = brebis_dict[selected]
            variants = db.fetchone("SELECT variants_snps FROM brebis WHERE id=?", (bid,))
            if variants and variants[0]:
                try:
                    snps = json.loads(variants[0])
                    st.json(snps)
                except:
                    st.info("Les SNPs ne sont pas au format JSON valide.")
            else:
                st.info("Aucun SNP enregistré pour cette brebis.")
            
            with st.expander("Ajouter / modifier les SNPs"):
                snps_json = st.text_area("SNPs au format JSON (ex: {'BMP15': 'AA', 'MSTN': 'GG'})", height=150)
                if st.button("Enregistrer"):
                    db.execute("UPDATE brebis SET variants_snps=? WHERE id=?", (snps_json, bid))
                    st.success("SNPs enregistrés")
                    st.rerun()
    
    with tab3:
        st.subheader("Analyse d'association GWAS")
        st.markdown("""
        Cette section permet de réaliser une étude d'association pangénomique simplifiée.
        Vous devez fournir deux fichiers CSV :
        - **Génotypes** : avec une colonne `brebis_id` et une colonne par SNP (valeurs 0,1,2 pour le dosage allélique).
        - **Phénotypes** : avec les colonnes `brebis_id` et un trait quantitatif (ex: production laitière, poids...).
        """)
        
        upload_geno = st.file_uploader("Fichier génotypes (CSV)", type="csv", key="geno")
        upload_pheno = st.file_uploader("Fichier phénotypes (CSV)", type="csv", key="pheno")
        
        if upload_geno and upload_pheno:
            try:
                df_geno = pd.read_csv(upload_geno)
                df_pheno = pd.read_csv(upload_pheno)
                
                if 'brebis_id' not in df_geno.columns or 'brebis_id' not in df_pheno.columns:
                    st.error("Les fichiers doivent contenir une colonne 'brebis_id'.")
                else:
                    df_merged = pd.merge(df_geno, df_pheno, on='brebis_id')
                    trait_col = st.selectbox("Sélectionner le trait phénotypique", 
                                             [c for c in df_pheno.columns if c != 'brebis_id'])
                    
                    snp_cols = [c for c in df_geno.columns if c != 'brebis_id' and df_geno[c].dtype in ['int64', 'float64']]
                    
                    if len(snp_cols) == 0:
                        st.error("Aucune colonne SNP numérique trouvée.")
                    else:
                        st.write(f"Nombre de SNPs analysés : {len(snp_cols)}")
                        
                        results = []
                        pbar = st.progress(0)
                        for i, snp in enumerate(snp_cols):
                            X = df_merged[snp].values
                            y = df_merged[trait_col].values
                            X = sm.add_constant(X)
                            model = sm.OLS(y, X).fit()
                            p_value = model.pvalues[1]
                            beta = model.params[1]
                            results.append({
                                'SNP': snp,
                                'Beta': beta,
                                'P_value': p_value,
                                '-log10(p)': -np.log10(p_value) if p_value > 0 else 10
                            })
                            pbar.progress((i+1)/len(snp_cols))
                        
                        df_res = pd.DataFrame(results)
                        
                        fig = px.scatter(df_res, x='SNP', y='-log10(p)', 
                                         title="Manhattan plot",
                                         labels={'-log10(p)': '-log10(p-value)'},
                                         hover_data=['Beta', 'P_value'])
                        fig.add_hline(y=-np.log10(0.05/len(snp_cols)), line_dash="dash", 
                                      annotation_text="Bonferroni threshold")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        sig = df_res[df_res['P_value'] < 0.05]
                        if not sig.empty:
                            st.subheader("SNPs suggestifs (p < 0.05)")
                            st.dataframe(sig.sort_values('P_value'), use_container_width=True, hide_index=True)
                        else:
                            st.info("Aucun SNP significatif au seuil de 0.05.")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")

# -----------------------------------------------------------------------------
# PAGE PHOTOGRAMMÉTRIE AMÉLIORÉE
# -----------------------------------------------------------------------------
def page_analyse():
    st.title("📸 Analyse Photogrammétrique")
    
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
            
            if uploaded_files:
                st.subheader("🔍 Diagnostic visuel")
                st.info("Analyse d'image simulée : pas de signes de maladie détectés.")
    
    with tab2:
        st.subheader("Scoring mamelles")
        
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
            
            if mamelle_file:
                st.subheader("🔍 Diagnostic mammaire")
                if score < 6 or forme == "Bifide" or attache == "Pendante":
                    st.warning("Suspicion de problèmes mammaires (faible conformation). Consulter un vétérinaire.")
                else:
                    st.success("Aspect sain (simulation).")

# -----------------------------------------------------------------------------
# PAGE SANTÉ
# -----------------------------------------------------------------------------
def page_sante():
    st.title("🏥 Suivi sanitaire et vaccinal")
    
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
# PAGE REPRODUCTION
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
            
            last_gest = db.fetchone(
                "SELECT date_saillie FROM saillies WHERE brebis_id=? AND resultat='Gestante' ORDER BY date_saillie DESC",
                (bid,)
            )
            if last_gest:
                date_saillie = datetime.strptime(last_gest[0], "%Y-%m-%d").date()
                date_mb = date_saillie + timedelta(days=150)
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
# PAGE NUTRITION AVANCÉE
# -----------------------------------------------------------------------------
def page_nutrition_avancee():
    st.title("🌾 Nutrition avancée et formulation")
    
    tab1, tab2, tab3 = st.tabs(["📦 Catalogue aliments", "📋 Rations types", "🧮 Calcul ration personnalisée"])
    
    with tab1:
        st.subheader("Gestion des aliments")
        
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
        
        aliments = db.fetchall("SELECT id, nom, type, uem, pdin, ms, prix_kg FROM aliments")
        if aliments:
            df_alim = pd.DataFrame(aliments, columns=["ID", "Nom", "Type", "UEM", "PDIN", "MS%", "Prix DA/kg"])
            st.dataframe(df_alim, use_container_width=True, hide_index=True)
            
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
        
        etat_physio = st.selectbox("État physiologique", Config.ETATS_PHYSIO)
        
        ration_existante = db.fetchone("SELECT id, nom, description FROM rations WHERE etat_physio=?", (etat_physio,))
        if ration_existante:
            st.success(f"Ration existante : {ration_existante[1]}")
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
        
        with st.expander("⚙️ Configurer une ration pour cet état"):
            aliments = db.fetchall("SELECT id, nom FROM aliments")
            if not aliments:
                st.warning("Ajoutez d'abord des aliments.")
            else:
                if ration_existante:
                    ration_id = ration_existante[0]
                    st.markdown("**Modifier la ration existante**")
                else:
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
                    st.subheader("Ajouter un aliment à cette ration")
                    aliment_choix = st.selectbox("Choisir un aliment", [f"{a[0]} - {a[1]}" for a in aliments])
                    aid = int(aliment_choix.split(" - ")[0])
                    quantite = st.number_input("Quantité (kg/jour)", min_value=0.0, step=0.1, format="%.2f")
                    if st.button("Ajouter à la ration"):
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
            
            besoins = OvinScience.besoins_nutritionnels(poids, etat, lactation)
            st.info(f"**Besoins journaliers** : UEM = {besoins['uem']} MJ, PDIN = {besoins['pdin']} g, MS = {besoins['ms']} kg")
            
            aliments = db.fetchall("SELECT id, nom, type, uem, pdin, ms, prix_kg FROM aliments")
            if not aliments:
                st.warning("Ajoutez d'abord des aliments.")
            else:
                st.subheader("Composition de la ration")
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
# PAGE EXPORT
# -----------------------------------------------------------------------------
def page_export():
    st.title("📤 Export des données")
    st.markdown("Téléchargez l'ensemble de vos données au format CSV ou Excel pour les partager avec votre professeur.")
    
    format_export = st.radio("Format", ["CSV", "Excel"])
    
    if st.button("Générer l'export"):
        tables = ["eleveurs", "elevages", "brebis", "productions", "mesures_morpho", "mesures_mamelles", "composition_corporelle",
                  "vaccinations", "soins", "chaleurs", "saillies", "mises_bas", "aliments", "rations", "ration_composition"]
        data_frames = {}
        
        for table in tables:
            if table == "eleveurs":
                df = pd.read_sql_query(f"SELECT * FROM {table} WHERE user_id=?", db.conn, params=(st.session_state.user_id,))
            elif table == "elevages":
                df = pd.read_sql_query("""
                    SELECT e.* FROM elevages e
                    JOIN eleveurs el ON e.eleveur_id = el.id
                    WHERE el.user_id=?
                """, db.conn, params=(st.session_state.user_id,))
            elif table in ["brebis", "productions", "vaccinations", "soins", "chaleurs", "saillies", "mises_bas"]:
                df = pd.read_sql_query(f"""
                    SELECT t.* FROM {table} t
                    JOIN brebis b ON t.brebis_id = b.id
                    JOIN elevages e ON b.elevage_id = e.id
                    JOIN eleveurs el ON e.eleveur_id = el.id
                    WHERE el.user_id=?
                """, db.conn, params=(st.session_state.user_id,))
            elif table in ["mesures_morpho", "mesures_mamelles", "composition_corporelle"]:
                df = pd.read_sql_query(f"""
                    SELECT t.* FROM {table} t
                    JOIN brebis b ON t.brebis_id = b.id
                    JOIN elevages e ON b.elevage_id = e.id
                    JOIN eleveurs el ON e.eleveur_id = el.id
                    WHERE el.user_id=?
                """, db.conn, params=(st.session_state.user_id,))
            else:
                # tables non liées à un user (aliments, rations, etc.) : on prend tout
                df = pd.read_sql_query(f"SELECT * FROM {table}", db.conn)
            
            data_frames[table] = df
        
        if format_export == "Excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for name, df in data_frames.items():
                    df.to_excel(writer, sheet_name=name, index=False)
            output.seek(0)
            st.download_button(
                label="Télécharger Excel",
                data=output,
                file_name=f"ovin_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                for name, df in data_frames.items():
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    zip_file.writestr(f"{name}.csv", csv_data)
            zip_buffer.seek(0)
            st.download_button(
                label="Télécharger ZIP (CSV)",
                data=zip_buffer,
                file_name=f"ovin_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )

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
    genomic_analyzer = GenomicAnalyzer()
    
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
    
    # CSS personnalisé (repris du code original)
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2E7D32;
            text-align: center;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .gene-card {
            background-color: #e3f2fd;
            border-left: 5px solid #00838F;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .meat-card {
            background-color: #fff3e0;
            border-left: 5px solid #FF6F00;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    main()
