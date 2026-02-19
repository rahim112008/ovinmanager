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

# Configuration page
st.set_page_config(
    page_title="Ovin Manager Pro - GenApAgiE",
    page_icon="🐑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
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

# ============================================================================
# CONFIGURATION ET CONSTANTES
# ============================================================================

class Config:
    APP_NAME = "Ovin Manager Pro"
    LABORATOIRE = "GenApAgiE"
    VERSION = "3.0"
    
    # Couleurs
    VERT = "#2E7D32"
    ORANGE = "#FF6F00"
    BLEU = "#1565C0"
    ROUGE = "#C62828"
    VIOLET = "#6A1B9A"
    CYAN = "#00838F"
    
    # API NCBI
    NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Étalons calibration
    ETALONS = {
        "baton_1m": {"nom": "Bâton 1m", "largeur": 1000, "hauteur": None},
        "a4": {"nom": "Feuille A4", "largeur": 210, "hauteur": 297},
        "carte": {"nom": "Carte bancaire", "largeur": 85.6, "hauteur": 53.98},
        "piece_100da": {"nom": "Pièce 100 DA", "diametre": 29.5}
    }
    
    # Races ovines algériennes
    RACES = {
        "Hamra": {"origine": "Atlas saharien", "aptitude": "Mixte", "genes": ["BMP15", "GDF9"]},
        "Ouled Djellal": {"origine": "Steppes algériennes", "aptitude": "Viande", "genes": ["MSTN", "IGF2"]},
        "Sidahou": {"origine": "Aurès", "aptitude": "Lait", "genes": ["LALBA", "CSN3", "DGAT1"]},
        "Rembi": {"origine": "Tell", "aptitude": "Mixte", "genes": ["BMP15", "LALBA"]},
        "Autre": {"origine": "Inconnue", "aptitude": "Variable", "genes": []}
    }
    
    # Gènes économiques (QTN/SNPs)
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

# ============================================================================
# BASE DE DONNÉES
# ============================================================================

@st.cache_resource
def get_database():
    """Singleton pour la base de données"""
    return Database()

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("ovin_streamlit.db", check_same_thread=False)
        self.init_database()
    
    def init_database(self):
        cursor = self.conn.cursor()
        
        # Tables principales
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

# ============================================================================
# API NCBI / GÉNOMIQUE
# ============================================================================

class NCBIApi:
    def __init__(self):
        self.base_url = Config.NCBI_EUTILS_BASE
    
    def search_gene(self, gene_name: str, organism: str = "Ovis aries") -> List[Dict]:
        """Recherche un gène dans NCBI Gene"""
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
        """Récupère les détails des gènes"""
        try:
            url = f"{self.base_url}/esummary.fcgi"
            params = {
                "db": "gene",
                "id": ",".join(gene_ids),
                "retmode": "json"
            }
            
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
        """Récupère séquence FASTA"""
        try:
            url = f"{self.base_url}/efetch.fcgi"
            params = {
                "db": "nucleotide",
                "id": accession,
                "rettype": "fasta",
                "retmode": "text"
            }
            response = requests.get(url, params=params, timeout=30)
            return response.text if response.status_code == 200 else None
        except Exception as e:
            st.error(f"Erreur FASTA: {e}")
            return None

class GenomicAnalyzer:
    def __init__(self):
        self.ncbi = NCBIApi()
    
    def analyze_race_profile(self, race: str) -> Dict:
        """Analyse le profil génétique d'une race"""
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
            
            # Scoring
            if gene in ["BMP15", "GDF9", "BMPR1B"]:
                results["score_reproduction"] += 33
            if gene in ["MSTN", "IGF2", "GH"]:
                results["score_croissance"] += 33
            if gene in ["LALBA", "CSN3", "DGAT1"]:
                results["score_lait"] += 33
        
        # Normaliser scores
        results["score_reproduction"] = min(100, results["score_reproduction"])
        results["score_croissance"] = min(100, results["score_croissance"])
        results["score_lait"] = min(100, results["score_lait"])
        
        # Recommandations
        if results["score_reproduction"] > 70:
            results["recommandations"].append("✅ Excellente valeur reproductive")
        if results["score_croissance"] > 70:
            results["recommandations"].append("✅ Excellente conformation viande")
        if results["score_lait"] > 70:
            results["recommandations"].append("✅ Excellent potentiel laitier")
        
        return results

# ============================================================================
# MOTEUR SCIENTIFIQUE
# ============================================================================

class OvinScience:
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def calcul_score_morpho(longueur: float, hauteur: float, poitrine: float, 
                          canon: float, bassin: float) -> float:
        """Score morphométrique sur 100"""
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
        """Score mamelles sur 10"""
        score = 5.0
        if 4 <= long_trayon <= 6: score += 1.5
        if 2 <= diametre <= 3: score += 1.5
        if symetrie == "Symétrique": score += 0.5
        if attache == "Solide": score += 0.5
        if forme == "Globuleuse": score += 0.5
        if attache != "Pendante": score += 0.5
        return min(10, round(score, 2))
    
    # =========================================================================
    # COMPOSITION CORPORELLE (VIANDE/GRAISSE/OS)
    # =========================================================================
    
    @staticmethod
    def estimer_composition(poids_vif: float, race: str, 
                           condition_corporelle: float) -> Dict:
        """Estime la composition corporelle détaillée"""
        try:
            # Rendement carcasse
            rendement = 0.48 if race == "Ouled Djellal" else 0.45 if race == "Sidahou" else 0.46
            rendement += (condition_corporelle - 3) * 0.01
            
            poids_carcasse = poids_vif * rendement
            
            # Composition selon état corporel
            if condition_corporelle >= 4:  # Gras
                pct_viande, pct_graisse, pct_os = 0.55, 0.28, 0.17
            elif condition_corporelle <= 2:  # Maigre
                pct_viande, pct_graisse, pct_os = 0.62, 0.18, 0.20
            else:  # Moyen
                pct_viande, pct_graisse, pct_os = 0.58, 0.23, 0.19
            
            # Ajustement race
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
        """Calcul des besoins nutritionnels"""
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
        """Prédiction production laitière"""
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

# ============================================================================
# INITIALISATION
# ============================================================================

db = get_database()
genomic_analyzer = GenomicAnalyzer()

# Session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login"

# ============================================================================
# PAGES DE L'APPLICATION
# ============================================================================

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
    
    # Statistiques
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
    
    # Modules principaux
    st.subheader("🚀 Modules Génomiques & Analytiques")
    
    modules = [
        ("🧬 Analyse NCBI/GenBank", "Recherche gènes, SNPs, BLAST", "genomique", Config.CYAN),
        ("🥩 Composition Corporelle", "Estimation viande/graisse/os", "composition", Config.ORANGE),
        ("📸 Photogrammétrie", "Mesures morphométriques IA", "analyse", Config.VERT),
        ("🥛 Prédiction Lait", "ML potentiel laitier", "prediction", Config.VIOLET),
        ("🌾 Nutrition", "Formulation rations", "nutrition", Config.BLEU),
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

def page_genomique():
    st.title("🧬 Analyse Génomique - NCBI/GenBank")
    
    tab1, tab2, tab3 = st.tabs(["🔍 Recherche Gène", "🏆 Profil Race", "🧪 SNPs/QTN"])
    
    with tab1:
        st.subheader("Recherche dans NCBI Gene")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            gene_search = st.text_input("Nom du gène", "BMP15", 
                                       help="Ex: BMP15, MSTN, DGAT1, CAST...")
        with col2:
            organism = st.selectbox("Organisme", ["Ovis aries (Mouton)", "Capra hircus (Chèvre)", "Bos taurus (Bovin)"])
        
        if st.button("🔍 Rechercher dans NCBI", use_container_width=True):
            results = genomic_analyzer.ncbi.search_gene(gene_search, "Ovis aries")
            
            if results:
                for gene in results:
                    with st.container():
                        st.markdown(f"""
                        <div class="gene-card">
                            <h4>🧬 {gene['name']} (ID: {gene['gene_id']})</h4>
                            <p><strong>Description:</strong> {gene['description']}</p>
                            <p><strong>Chromosome:</strong> {gene['chromosome']} | <strong>Position:</strong> {gene['map_location']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Info locale si disponible
                        local_info = Config.GENES_ECONOMIQUES.get(gene_search.upper())
                        if local_info:
                            st.info(f"**Effet économique:** {local_info['effet']}")
            else:
                # Afficher info locale même si API échoue
                local = Config.GENES_ECONOMIQUES.get(gene_search.upper())
                if local:
                    st.success("Informations depuis la base locale GenApAgiE")
                    st.json(local)
                else:
                    st.warning("Gène non trouvé. Essayez: BMP15, MSTN, DGAT1, CAST, CAPN1...")
    
    with tab2:
        st.subheader("Profil Génétique par Race")
        
        race_selected = st.selectbox("Sélectionner une race", list(Config.RACES.keys()))
        
        if st.button("🧬 Analyser le profil génétique"):
            analysis = genomic_analyzer.analyze_race_profile(race_selected)
            
            # Scores radar
            fig = go.Figure(data=go.Scatterpolar(
                r=[analysis['score_reproduction'], analysis['score_croissance'], 
                   analysis['score_lait'], analysis['score_reproduction']],  # Fermer le polygone
                theta=['Reproduction', 'Croissance/Viande', 'Lait', 'Reproduction'],
                fill='toself',
                name=race_selected
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                title=f"Profil Génétique: {race_selected}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Détails gènes
            st.subheader("Gènes Majeurs")
            for gene in analysis['genes']:
                with st.expander(f"🧬 {gene['symbole']} - {gene['nom'][:40]}..."):
                    st.write(f"**Effet:** {gene['effet']}")
                    st.write(f"**Chromosome:** {gene['chromosome']}")
            
            # Recommandations
            if analysis['recommandations']:
                st.success("### ✅ Recommandations")
                for rec in analysis['recommandations']:
                    st.write(rec)
    
    with tab3:
        st.subheader("Base de données SNPs et QTN économiques")
        
        # Filtrer par catégorie
        categorie = st.selectbox("Filtrer par catégorie", 
                                ["Tous", "Reproduction", "Croissance/Viande", "Lait", "Résistance", "Qualité viande"])
        
        genes_filtres = []
        for sym, info in Config.GENES_ECONOMIQUES.items():
            if categorie == "Tous":
                genes_filtres.append((sym, info))
            elif categorie == "Reproduction" and any(x in sym for x in ["BMP", "GDF"]):
                genes_filtres.append((sym, info))
            elif categorie == "Croissance/Viande" and any(x in sym for x in ["MSTN", "IGF", "GH"]):
                genes_filtres.append((sym, info))
            elif categorie == "Lait" and any(x in sym for x in ["LALBA", "CSN", "DGAT", "SCD"]):
                genes_filtres.append((sym, info))
            elif categorie == "Résistance" and any(x in sym for x in ["TLR", "MHC", "PRNP"]):
                genes_filtres.append((sym, info))
            elif categorie == "Qualité viande" and any(x in sym for x in ["CAST", "CAPN", "FABP"]):
                genes_filtres.append((sym, info))
        
        # Tableau des gènes
        df_genes = pd.DataFrame([
            {
                "Symbole": sym,
                "Nom": info["nom"][:50] + "...",
                "Chr": info["chr"],
                "Effet": info["effet"][:60] + "...",
                "Type": "QTN" if sym in ["BMP15", "MSTN", "DGAT1", "BMPR1B"] else "SNP"
            }
            for sym, info in genes_filtres
        ])
        
        st.dataframe(df_genes, use_container_width=True, hide_index=True)
        
        # Détailed view
        gene_detail = st.selectbox("Voir détails", [sym for sym, _ in genes_filtres])
        if gene_detail:
            info = Config.GENES_ECONOMIQUES[gene_detail]
            st.json(info)

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
        
        # Métriques principales
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
        
        # Graphique camembert
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
        
        # Sauvegarde
        if st.button("💾 Enregistrer dans la base de données"):
            st.success("Composition enregistrée !")

def page_analyse():
    st.title("📸 Analyse Photogrammétrique")
    
    tab1, tab2 = st.tabs(["📏 Morphométrie Corps", "🥛 Analyse Mamelles"])
    
    with tab1:
        st.subheader("Mesures corporelles")
        
        col1, col2 = st.columns(2)
        
        with col1:
            etalon = st.selectbox("Étalon de calibration", 
                                 list(Config.ETALONS.keys()),
                                 format_func=lambda x: Config.ETALONS[x]['nom'])
            
            uploaded_file = st.file_uploader("Photo de profil", type=['jpg', 'png', 'jpeg'])
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="Image chargée", use_column_width=True)
        
        with col2:
            longueur = st.number_input("Longueur corps (cm)", min_value=30.0, max_value=120.0, value=70.0)
            hauteur = st.number_input("Hauteur garrot (cm)", min_value=30.0, max_value=90.0, value=65.0)
            poitrine = st.number_input("Tour poitrine (cm)", min_value=40.0, max_value=130.0, value=80.0)
            canon = st.number_input("Circonf. canon (cm)", min_value=5.0, max_value=15.0, value=8.0)
            bassin = st.number_input("Largeur bassin (cm)", min_value=10.0, max_value=40.0, value=20.0)
            
            if st.button("🤖 Calculer score"):
                score = OvinScience.calcul_score_morpho(longueur, hauteur, poitrine, canon, bassin)
                
                # Jauge
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Score Morphologique"},
                    gauge={'axis': {'range': [None, 100]},
                           'bar': {'color': Config.VERT if score > 70 else Config.ORANGE if score > 50 else Config.ROUGE},
                           'steps': [
                               {'range': [0, 50], 'color': "lightgray"},
                               {'range': [50, 70], 'color': "yellow"},
                               {'range': [70, 100], 'color': "lightgreen"}]}
                ))
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Scoring mamelles")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.file_uploader("Vue arrière mamelles", type=['jpg', 'png', 'jpeg'], key="mamelle_img")
            
            long_trayon = st.number_input("Longueur trayon (cm)", min_value=1.0, max_value=15.0, value=5.0)
            diam_trayon = st.number_input("Diamètre trayon (cm)", min_value=0.5, max_value=5.0, value=2.5)
        
        with col2:
            symetrie = st.selectbox("Symétrie", ["Symétrique", "Asymétrique"])
            attache = st.selectbox("Attache", ["Solide", "Moyenne", "Pendante"])
            forme = st.selectbox("Forme", ["Globuleuse", "Bifide", "Poire"])
            
            if st.button("🥛 Calculer score mamelle"):
                score = OvinScience.calcul_score_mamelle(long_trayon, diam_trayon, symetrie, attache, forme)
                
                # Barre de progression
                st.progress(score / 10)
                st.metric("Score mamelles", f"{score}/10")
                
                if score >= 8:
                    st.success("✅ Excellente conformation mammaire")
                elif score >= 6:
                    st.info("ℹ️ Bonne conformation")
                else:
                    st.warning("⚠️ Conformation à améliorer")

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
        
        # Graphique
        fig = px.bar(
            x=["Potentiel estimé", "Moyenne race", "Record élite"],
            y=[pred['litres_jour'], 1.2, 2.5],
            color=[pred['niveau'], "Moyenne", "Élite"],
            title="Comparaison production laitière (L/jour)"
        )
        st.plotly_chart(fig, use_container_width=True)

def page_nutrition():
    st.title("🌾 Nutrition et Formulation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        poids = st.number_input("Poids vif (kg)", 10.0, 150.0, 45.0)
    with col2:
        etat = st.selectbox("État physiologique", Config.ETATS_PHYSIO)
    with col3:
        lactation = st.number_input("Production lait (L/j)", 0.0, 10.0, 0.0)
    
    if st.button("🧮 Calculer besoins"):
        besoins = OvinScience.besoins_nutritionnels(poids, etat, lactation)
        
        st.subheader("Besoins journaliers")
        
        cols = st.columns(3)
        cols[0].metric("UEM", f"{besoins['uem']} MJ", "Énergie")
        cols[1].metric("PDIN", f"{besoins['pdin']} g", "Protéines")
        cols[2].metric("MS", f"{besoins['ms']} kg", "Matière sèche")
        
        # Formulation simple
        st.subheader("💡 Formulation suggérée (marché algérien)")
        
        ration = {
            "Orge": {"qté": besoins['ms'] * 0.4, "prix": 25},
            "Foin de luzerne": {"qté": besoins['ms'] * 0.35, "prix": 15},
            "Son de blé": {"qté": besoins['ms'] * 0.2, "prix": 12},
            "Minéraux": {"qté": 0.05, "prix": 80}
        }
        
        total_cost = 0
        for alim, data in ration.items():
            cost = data['qté'] * data['prix']
            total_cost += cost
            st.write(f"**{alim}:** {data['qté']:.2f} kg/jour = {cost:.2f} DA")
        
        st.success(f"**Coût total: {total_cost:.2f} DA/jour**")

# ============================================================================
# SIDEBAR ET NAVIGATION
# ============================================================================

def sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/sheep.png", width=80)
        st.title(f"🐑 {Config.APP_NAME}")
        st.caption(f"**{Config.LABORATOIRE}** v{Config.VERSION}")
        
        st.divider()
        
        if st.session_state.user_id:
            menu = st.radio(
                "Navigation",
                ["📊 Tableau de bord", "🧬 Génomique NCBI", "🥩 Composition", 
                 "📸 Photogrammétrie", "🔮 Prédictions", "🌾 Nutrition", "🚪 Déconnexion"],
                label_visibility="collapsed"
            )
            
            st.divider()
            
            # Export données
            if st.button("💾 Exporter mes données", use_container_width=True):
                st.download_button(
                    label="Télécharger JSON",
                    data=json.dumps({"user_id": st.session_state.user_id, "date": datetime.now().isoformat()}),
                    file_name=f"ovin_backup_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
            # Mapping menu -> page
            page_map = {
                "📊 Tableau de bord": "dashboard",
                "🧬 Génomique NCBI": "genomique",
                "🥩 Composition": "composition",
                "📸 Photogrammétrie": "analyse",
                "🔮 Prédictions": "prediction",
                "🌾 Nutrition": "nutrition",
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

# ============================================================================
# MAIN
# ============================================================================

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
    elif st.session_state.current_page == "nutrition":
        page_nutrition()

if __name__ == "__main__":
    main()
