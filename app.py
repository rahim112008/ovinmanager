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
import os
import uuid
from scipy.optimize import linprog
import joblib
import random

# Machine Learning
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet

# Pour l'analyse exploratoire (optionnel)
try:
    from ydata_profiling import ProfileReport
    from streamlit_pandas_profiling import st_profile_report
    profiling_available = True
except ImportError:
    profiling_available = False
    # Pas de warning ici pour éviter les messages intempestifs)

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
PHOTO_DIR = "photos_brebis"
MODEL_DIR = "models"
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

class Config:
    APP_NAME = "Ovin Manager Pro"
    LABORATOIRE = "GenApAgiE"
    VERSION = "6.0"
    
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
# BASE DE DONNÉES
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
        
        # Ajout de la colonne poids_vif si elle n'existe pas
        cursor.execute("PRAGMA table_info(brebis)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'poids_vif' not in columns:
            cursor.execute("ALTER TABLE brebis ADD COLUMN poids_vif REAL")
        
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
        
        # Remplir la table aliments avec des données de base (marché algérien)
        aliments_init = [
            ("Orge", "Concentré", 1.1, 80, 86, 25),
            ("Maïs", "Concentré", 1.3, 70, 86, 30),
            ("Son de blé", "Concentré", 0.9, 120, 87, 18),
            ("Tourteau de soja", "Concentré", 1.2, 400, 88, 45),
            ("Foin de luzerne", "Fourrage", 0.6, 120, 85, 15),
            ("Foin d'avoine", "Fourrage", 0.5, 70, 85, 12),
            ("Paille", "Fourrage", 0.3, 20, 88, 5),
            ("CMV", "Minéral", 0, 0, 100, 80)
        ]
        for alim in aliments_init:
            try:
                cursor.execute("INSERT OR IGNORE INTO aliments (nom, type, uem, pdin, ms, prix_kg) VALUES (?, ?, ?, ?, ?, ?)", alim)
            except:
                pass
        
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
# FONCTION UTILITAIRE POUR LES PHOTOS
# -----------------------------------------------------------------------------
def save_uploaded_photo(uploaded_file):
    """Sauvegarde une photo uploadée et retourne le nom du fichier."""
    if uploaded_file is not None:
        ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(PHOTO_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filename
    return None

# -----------------------------------------------------------------------------
# FONCTION DE FILTRAGE PAR ÉLEVEUR
# -----------------------------------------------------------------------------
def filtrer_par_eleveur(query_base: str, params: list, join_eleveur: bool = True) -> tuple:
    """Ajoute une condition sur l'éleveur actif à la requête et retourne (query, params)."""
    if st.session_state.eleveur_id is not None:
        if join_eleveur:
            query_base += " AND el.id=?"
        else:
            query_base += " AND eleveur_id=?"
        params.append(st.session_state.eleveur_id)
    return query_base, tuple(params)

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
# FONCTIONS ML
# -----------------------------------------------------------------------------

def train_lait_model():
    """Entraîne un modèle RandomForest pour prédire la production laitière."""
    query = """
        SELECT p.quantite, b.race, b.date_naissance, 
               AVG(m.score_global) as score_morpho,
               AVG(m2.score_total) as score_mamelle,
               COUNT(DISTINCT p.id) as nb_mesures
        FROM productions p
        JOIN brebis b ON p.brebis_id = b.id
        LEFT JOIN mesures_morpho m ON b.id = m.brebis_id
        LEFT JOIN mesures_mamelles m2 ON b.id = m2.brebis_id
        GROUP BY b.id
        HAVING nb_mesures > 0
    """
    df = pd.read_sql_query(query, db.conn)
    if len(df) < 20:
        return None  # Pas assez de données
    
    # Features
    df['age'] = (datetime.now() - pd.to_datetime(df['date_naissance'])).dt.days / 365
    df = pd.get_dummies(df, columns=['race'], prefix='race')
    feature_cols = [c for c in df.columns if c not in ['quantite', 'date_naissance', 'nb_mesures']]
    X = df[feature_cols].fillna(0)
    y = df['quantite']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    
    # Sauvegarde
    joblib.dump(model, os.path.join(MODEL_DIR, 'lait_model.pkl'))
    joblib.dump(feature_cols, os.path.join(MODEL_DIR, 'lait_features.pkl'))
    return model, score

def predict_lait_ml(brebis_id):
    """Prédit la production laitière pour une brebis donnée en utilisant le modèle entraîné."""
    model_path = os.path.join(MODEL_DIR, 'lait_model.pkl')
    features_path = os.path.join(MODEL_DIR, 'lait_features.pkl')
    if not os.path.exists(model_path) or not os.path.exists(features_path):
        return None
    
    model = joblib.load(model_path)
    feature_cols = joblib.load(features_path)
    
    # Récupérer les infos de la brebis
    query = """
        SELECT b.race, b.date_naissance,
               AVG(m.score_global) as score_morpho,
               AVG(m2.score_total) as score_mamelle
        FROM brebis b
        LEFT JOIN mesures_morpho m ON b.id = m.brebis_id
        LEFT JOIN mesures_mamelles m2 ON b.id = m2.brebis_id
        WHERE b.id = ?
        GROUP BY b.id
    """
    row = db.fetchone(query, (brebis_id,))
    if not row:
        return None
    
    race, date_naiss, score_morpho, score_mamelle = row
    age = (datetime.now() - datetime.strptime(date_naiss, "%Y-%m-%d")).days / 365 if date_naiss else 0
    
    # Créer un DataFrame avec les bonnes colonnes
    data = {'score_morpho': score_morpho or 0, 'score_mamelle': score_mamelle or 0, 'age': age}
    # Encodage one-hot de la race
    for col in feature_cols:
        if col.startswith('race_'):
            data[col] = 1 if col == f"race_{race}" else 0
        elif col not in data:
            data[col] = 0
    
    X = pd.DataFrame([data])[feature_cols].fillna(0)
    pred = model.predict(X)[0]
    return pred

def cluster_brebis(df, n_clusters=3):
    """Applique un clustering KMeans sur les brebis."""
    features = ['prod_moy (L/j)', 'score_morpho', 'poids', 'viande_estimee (kg)']
    # Sélectionner les colonnes existantes
    avail = [f for f in features if f in df.columns]
    if len(avail) < 2:
        return None
    X = df[avail].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    return clusters, kmeans.cluster_centers_, avail

def detect_anomalies(df, contamination=0.1):
    """Détecte les anomalies avec IsolationForest."""
    features = ['prod_moy (L/j)', 'score_morpho', 'poids', 'viande_estimee (kg)']
    avail = [f for f in features if f in df.columns]
    if len(avail) < 2:
        return None
    X = df[avail].fillna(0)
    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(X)  # -1 pour anomalies, 1 pour normaux
    return preds

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
        ("🧠 IA & Data Mining", "Analyses avancées, clustering, anomalies", "ia", Config.ROUGE),
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
                        
                        local_info = Config.GENES_ECONOMIQUES.get(gene_search.upper())
                        if local_info:
                            st.info(f"**Effet économique:** {local_info['effet']}")
            else:
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
            
            fig = go.Figure(data=go.Scatterpolar(
                r=[analysis['score_reproduction'], analysis['score_croissance'], 
                   analysis['score_lait'], analysis['score_reproduction']],
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
            
            st.subheader("Gènes Majeurs")
            for gene in analysis['genes']:
                with st.expander(f"🧬 {gene['symbole']} - {gene['nom'][:40]}..."):
                    st.write(f"**Effet:** {gene['effet']}")
                    st.write(f"**Chromosome:** {gene['chromosome']}")
            
            if analysis['recommandations']:
                st.success("### ✅ Recommandations")
                for rec in analysis['recommandations']:
                    st.write(rec)
    
    with tab3:
        st.subheader("Base de données SNPs et QTN économiques")
        
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
        
        gene_detail = st.selectbox("Voir détails", [sym for sym, _ in genes_filtres])
        if gene_detail:
            info = Config.GENES_ECONOMIQUES[gene_detail]
            st.json(info)

def page_composition():
    st.title("🥩 Composition Corporelle Estimée")
    st.markdown("Estimation détaillée de la répartition viande/graisse/os basée sur les équations zootechniques")

    # Récupération des brebis selon l'éleveur actif
    params = [st.session_state.user_id]
    query_brebis = """
        SELECT b.id, b.numero_id, b.nom, b.race, e.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """
    query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
    brebis_list = db.fetchall(query_brebis, params)
    
    brebis_options = {f"{b[0]} - {b[1]} {b[2]} ({b[4]})": b[0] for b in brebis_list}
    brebis_options["Saisie manuelle (animal non enregistré)"] = None

    mode = st.radio("Mode de saisie", ["Sélectionner une brebis existante", "Saisie manuelle"])

    if mode == "Sélectionner une brebis existante":
        selected = st.selectbox("Choisir une brebis", list(brebis_options.keys()))
        brebis_id = brebis_options[selected]
        if brebis_id is not None:
            info = db.fetchone("SELECT poids_vif, race, etat_physio FROM brebis WHERE id=?", (brebis_id,))
            if info:
                poids_def = info[0] if info[0] is not None else 45.0
                race_def = info[1] if info[1] else "Autre"
                etat_def = info[2] if info[2] else "Tarie"
            else:
                poids_def = 45.0
                race_def = "Autre"
                etat_def = "Tarie"
        else:
            poids_def = 45.0
            race_def = "Autre"
            etat_def = "Tarie"
    else:
        brebis_id = None
        poids_def = 45.0
        race_def = "Autre"
        etat_def = "Tarie"

    col1, col2, col3 = st.columns(3)
    with col1:
        poids_vif = st.number_input("Poids vif (kg)", min_value=10.0, max_value=150.0, value=poids_def, step=0.5)
    with col2:
        race = st.selectbox("Race", list(Config.RACES.keys()), index=list(Config.RACES.keys()).index(race_def) if race_def in Config.RACES else 0)
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
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("🔪 Détails des découpes"):
            decoupes_data = {
                "Découpe": ["Gigot", "Épaule", "Côtelettes", "Poitrine"],
                "Poids (kg)": [comp['decoupes']['gigot'], comp['decoupes']['epaule'],
                              comp['decoupes']['cotelette'], comp['decoupes']['poitrine']],
                "% Carcasse": [22, 17, 14, 12]
            }
            df_decoupes = pd.DataFrame(decoupes_data)
            st.dataframe(df_decoupes, hide_index=True, use_container_width=True)

        if brebis_id is not None:
            if st.button("💾 Enregistrer cette composition dans la base"):
                db.execute("""
                    INSERT INTO composition_corporelle 
                    (brebis_id, date_estimation, poids_vif, poids_carcasse, rendement_carcasse,
                     poids_viande, pct_viande, poids_graisse, pct_graisse, poids_os, pct_os,
                     gigot_poids, epaule_poids, cotelette_poids)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    brebis_id, datetime.now().isoformat(),
                    poids_vif, comp['poids_carcasse'], comp['rendement'],
                    comp['viande']['kg'], comp['viande']['pct'],
                    comp['graisse']['kg'], comp['graisse']['pct'],
                    comp['os']['kg'], comp['os']['pct'],
                    comp['decoupes']['gigot'], comp['decoupes']['epaule'], comp['decoupes']['cotelette']
                ))
                st.success("Composition enregistrée pour cette brebis !")

    # Section de comparaison
    st.divider()
    st.subheader("🔍 Comparer plusieurs brebis")

    if len(brebis_list) >= 2:
        selected_ids = st.multiselect(
            "Choisir les brebis à comparer",
            options=list(brebis_options.keys()),
            default=list(brebis_options.keys())[:min(2, len(brebis_options))]
        )
        selected_ids = [brebis_options[id_str] for id_str in selected_ids if brebis_options[id_str] is not None]

        if len(selected_ids) >= 2:
            comp_data = []
            for bid in selected_ids:
                row = db.fetchone("""
                    SELECT poids_vif, poids_carcasse, rendement_carcasse,
                           poids_viande, poids_graisse, poids_os, date_estimation
                    FROM composition_corporelle
                    WHERE brebis_id=?
                    ORDER BY date_estimation DESC
                    LIMIT 1
                """, (bid,))
                if row:
                    name = db.fetchone("SELECT numero_id, nom FROM brebis WHERE id=?", (bid,))
                    label = f"{name[0]} {name[1]}" if name else f"Brebis {bid}"
                    comp_data.append({
                        "id": bid,
                        "nom": label,
                        "poids_vif": row[0],
                        "poids_carcasse": row[1],
                        "rendement": row[2],
                        "viande": row[3],
                        "graisse": row[4],
                        "os": row[5],
                        "date": row[6]
                    })
            if comp_data:
                df_comp = pd.DataFrame(comp_data)
                fig_comp = go.Figure()
                for animal in comp_data:
                    fig_comp.add_trace(go.Bar(
                        name=animal['nom'],
                        x=['Viande', 'Graisse', 'Os'],
                        y=[animal['viande'], animal['graisse'], animal['os']],
                        text=[f"{animal['viande']} kg", f"{animal['graisse']} kg", f"{animal['os']} kg"],
                        textposition='auto'
                    ))
                fig_comp.update_layout(
                    title="Comparaison des compositions (kg)",
                    barmode='group',
                    yaxis_title="Poids (kg)"
                )
                st.plotly_chart(fig_comp, use_container_width=True)

                st.dataframe(df_comp[['nom', 'poids_vif', 'poids_carcasse', 'rendement', 'viande', 'graisse', 'os']].round(2),
                           use_container_width=True, hide_index=True)
            else:
                st.warning("Aucune composition enregistrée pour ces brebis. Calculez d'abord une composition et enregistrez-la.")
    else:
        st.info("Ajoutez au moins deux brebis et enregistrez leurs compositions pour activer la comparaison.")

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
    
    if st.button("🔮 Prédire production (formule simple)"):
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
    
    st.divider()
    st.subheader("Prédiction avancée par modèle ML")
    
    # Vérifier si un modèle existe
    model_path = os.path.join(MODEL_DIR, 'lait_model.pkl')
    if os.path.exists(model_path):
        st.success("Un modèle ML est disponible.")
        # Sélectionner une brebis
        params = [st.session_state.user_id]
        query_brebis = """
            SELECT b.id, b.numero_id, b.nom, e.nom
            FROM brebis b
            JOIN elevages e ON b.elevage_id = e.id
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
        """
        query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
        brebis_list = db.fetchall(query_brebis, params)
        brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}
        
        if brebis_dict:
            selected = st.selectbox("Choisir une brebis", list(brebis_dict.keys()), key="ml_brebis")
            bid = brebis_dict[selected]
            if st.button("Prédire avec ML"):
                pred = predict_lait_ml(bid)
                if pred is not None:
                    st.metric("Production prédite (L/j)", f"{pred:.2f}")
                else:
                    st.warning("Impossible de faire la prédiction (données manquantes).")
        else:
            st.warning("Aucune brebis disponible.")
    else:
        st.info("Aucun modèle ML entraîné. Vous pouvez en entraîner un si vous avez suffisamment de données de production.")
        if st.button("Entraîner un modèle ML"):
            with st.spinner("Entraînement en cours..."):
                result = train_lait_model()
                if result is None:
                    st.error("Pas assez de données (minimum 20 brebis avec productions).")
                else:
                    model, score = result
                    st.success(f"Modèle entraîné avec un score R² de {score:.2f} sur le test.")

def page_analyse():
    st.title("📸 Analyse Photogrammétrique")

    # Récupérer les brebis selon l'éleveur actif
    params = [st.session_state.user_id]
    query_brebis = """
        SELECT b.id, b.numero_id, b.nom, e.nom, b.photo_profil, b.photo_mamelle
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """
    query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
    brebis_list = db.fetchall(query_brebis, params)
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}

    if not brebis_dict:
        st.warning("Aucune brebis disponible pour cet éleveur.")
        return

    selected_brebis = st.selectbox("Sélectionner la brebis", list(brebis_dict.keys()))
    brebis_id = brebis_dict[selected_brebis]

    # Récupérer les infos de la brebis
    brebis_info = db.fetchone("SELECT date_naissance, race, photo_profil, photo_mamelle FROM brebis WHERE id=?", (brebis_id,))
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
        profil_file = brebis_info[2]
        mamelle_file = brebis_info[3]
    else:
        age_mois = 0
        age_dents = "Inconnu"
        profil_file = None
        mamelle_file = None

    st.info(f"Âge estimé : {age_mois} mois ({age_dents})")

    # Afficher la photo de profil existante si disponible
    if profil_file and os.path.exists(os.path.join(PHOTO_DIR, profil_file)):
        st.image(os.path.join(PHOTO_DIR, profil_file), caption="Photo de profil existante", width=300)

    tab1, tab2 = st.tabs(["📏 Morphométrie Corps", "🥛 Analyse Mamelles"])

    with tab1:
        st.subheader("Mesures corporelles")

        # Option de capture via caméra ou upload
        source = st.radio("Source de l'image", ["Télécharger un fichier", "Prendre une photo"])
        uploaded_files = None
        camera_image = None
        if source == "Télécharger un fichier":
            uploaded_files = st.file_uploader("Photos de profil (plusieurs acceptées)", 
                                              type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        else:
            camera_image = st.camera_input("Prendre une photo")

        # Afficher les images
        if uploaded_files:
            cols = st.columns(min(3, len(uploaded_files)))
            for i, file in enumerate(uploaded_files):
                with cols[i % 3]:
                    img = Image.open(file)
                    st.image(img, caption=f"Photo {i+1}", use_column_width=True)
        if camera_image:
            st.image(camera_image, caption="Photo prise", use_column_width=True)

        # Saisie manuelle des mesures
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
        poitrine = st.number_input("Tour de poitrine (cm)", min_value=40.0, max_value=130.0, value=80.0)
        canon = st.number_input("Circonférence canon (cm)", min_value=5.0, max_value=15.0, value=8.0)
        bassin = st.number_input("Largeur bassin (cm)", min_value=10.0, max_value=40.0, value=20.0)

        # Estimation du poids à partir des mensurations (formule approximative)
        poids_estime = (longueur * poitrine * hauteur) / 3000
        st.info(f"Poids estimé à partir des mensurations : **{poids_estime:.1f} kg**")

        if st.button("🤖 Calculer score et analyser"):
            # Score morphologique
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

            # Sauvegarde dans la table mesures_morpho
            if st.button("💾 Enregistrer ces mesures pour suivi"):
                db.execute("""
                    INSERT INTO mesures_morpho 
                    (brebis_id, date_mesure, longueur_corps, hauteur_garrot, tour_poitrine,
                     circonference_canon, largeur_bassin, score_global)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    brebis_id, datetime.now().isoformat(),
                    longueur, hauteur, poitrine, canon, bassin, score
                ))
                st.success("Mesures enregistrées !")

            # Analyse d'image avancée (simulation)
            if uploaded_files or camera_image:
                st.subheader("🔍 Diagnostic visuel (simulation IA)")
                maladies = ["Aucune anomalie", "Légère boiterie", "Problème de mamelle", "État corporel faible"]
                diag = random.choices(maladies, weights=[0.7, 0.1, 0.1, 0.1])[0]
                etat_corporel = random.choice(["Maigre", "Idéal", "Gras"])
                st.write(f"**Diagnostic :** {diag}")
                st.write(f"**État corporel estimé :** {etat_corporel}")
                if diag != "Aucune anomalie":
                    st.warning(f"⚠️ Alerte : {diag} détecté. Consulter un vétérinaire.")
                else:
                    st.success("✅ Animal sain (simulation).")

    with tab2:
        st.subheader("Scoring mamelles")

        # Afficher la photo mamelle existante si disponible
        if mamelle_file and os.path.exists(os.path.join(PHOTO_DIR, mamelle_file)):
            st.image(os.path.join(PHOTO_DIR, mamelle_file), caption="Mamelle existante", width=300)

        # Nouvelle photo
        mamelle_source = st.radio("Source image mamelle", ["Télécharger", "Prendre photo"], key="mamelle_source")
        mamelle_file_upload = None
        mamelle_camera = None
        if mamelle_source == "Télécharger":
            mamelle_file_upload = st.file_uploader("Vue arrière mamelles", type=['jpg','png','jpeg'], key="mamelle_img")
        else:
            mamelle_camera = st.camera_input("Prendre photo mamelle", key="mamelle_camera")

        if mamelle_file_upload:
            img_mam = Image.open(mamelle_file_upload)
            st.image(img_mam, caption="Mamelle uploadée", width=300)
        if mamelle_camera:
            st.image(mamelle_camera, caption="Mamelle prise", width=300)

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

            # Sauvegarde dans mesures_mamelles
            if st.button("💾 Enregistrer mesures mamelles"):
                db.execute("""
                    INSERT INTO mesures_mamelles 
                    (brebis_id, date_mesure, longueur_trayon, diametre_trayon, symetrie, attache, forme, score_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    brebis_id, datetime.now().isoformat(),
                    long_trayon, diam_trayon, symetrie, attache, forme, score
                ))
                st.success("Mesures mamelles enregistrées !")

            # Diagnostic mammaire (simulation)
            if mamelle_file_upload or mamelle_camera:
                st.subheader("🔍 Diagnostic mammaire (simulation IA)")
                if score < 6 or forme == "Bifide" or attache == "Pendante":
                    st.warning("Suspicion de problèmes mammaires. Consulter un vétérinaire.")
                else:
                    st.success("Aspect sain (simulation).")

# -----------------------------------------------------------------------------
# PAGE GESTION ÉLEVAGE (identique à avant, mais nous devons la recopier pour être complet)
# -----------------------------------------------------------------------------
def page_gestion_elevage():
    st.title("🐑 Gestion des élevages")
        # --- Résumé de l'éleveur actif ---
    if st.session_state.eleveur_id is not None:
        # Récupérer les informations de l'éleveur
        eleveur = db.fetchone("SELECT nom, region FROM eleveurs WHERE id=?", (st.session_state.eleveur_id,))
        if eleveur:
            st.subheader(f"📊 Résumé de l'éleveur : {eleveur[0]} ({eleveur[1]})")
            
            # Statistiques globales
            nb_elevages = db.fetchone("SELECT COUNT(*) FROM elevages WHERE eleveur_id=?", (st.session_state.eleveur_id,))[0]
            nb_brebis = db.fetchone("""
                SELECT COUNT(*) FROM brebis b
                JOIN elevages e ON b.elevage_id = e.id
                WHERE e.eleveur_id=?
            """, (st.session_state.eleveur_id,))[0]
            
            prod_moy = db.fetchone("""
                SELECT AVG(p.quantite)
                FROM productions p
                JOIN brebis b ON p.brebis_id = b.id
                JOIN elevages e ON b.elevage_id = e.id
                WHERE e.eleveur_id=? AND p.date >= date('now', '-30 days')
            """, (st.session_state.eleveur_id,))[0]
            
            poids_moy = db.fetchone("""
                SELECT AVG(b.poids_vif)
                FROM brebis b
                JOIN elevages e ON b.elevage_id = e.id
                WHERE e.eleveur_id=?
            """, (st.session_state.eleveur_id,))[0]
            
            # Affichage des métriques
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🏡 Élevages", nb_elevages)
            col2.metric("🐑 Brebis", nb_brebis)
            col3.metric("🥛 Production moy. (L/j)", f"{prod_moy:.2f}" if prod_moy else "N/A")
            col4.metric("⚖️ Poids moy. (kg)", f"{poids_moy:.1f}" if poids_moy else "N/A")
            
            # Graphique : répartition des races
            races = db.fetchall("""
                SELECT b.race, COUNT(*) 
                FROM brebis b
                JOIN elevages e ON b.elevage_id = e.id
                WHERE e.eleveur_id=?
                GROUP BY b.race
            """, (st.session_state.eleveur_id,))
            if races:
                df_races = pd.DataFrame(races, columns=["Race", "Nombre"])
                fig = px.pie(df_races, values="Nombre", names="Race", title="Répartition des races")
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
    else:
        st.info("👈 Sélectionnez un éleveur dans la barre latérale pour voir un résumé.")
    tab1, tab2, tab3 = st.tabs(["👨‍🌾 Éleveurs", "🏡 Élevages", "🐑 Brebis"])
    
    # --- Onglet Éleveurs ---
    with tab1:
        st.subheader("Liste des éleveurs")
        
        with st.expander("➕ Ajouter un élevage", expanded=True):
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
        
        # Récupérer tous les éleveurs de l'utilisateur
        eleveurs_list = db.fetchall(
            "SELECT id, nom FROM eleveurs WHERE user_id=?", (st.session_state.user_id,)
        )
        # DEBUG : afficher le nombre d'éleveurs
        st.info(f"Nombre d'éleveurs trouvés : {len(eleveurs_list)}")
        
        eleveurs_dict = {f"{e[0]} - {e[1]}": e[0] for e in eleveurs_list}
        
        if not eleveurs_dict:
            st.warning("Vous devez d'abord ajouter un éleveur.")
        else:
            # Expandeur ouvert par défaut
            with st.expander("➕ Ajouter un élevage", expanded=True):
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
            
            # Ensuite, afficher la liste des élevages (filtrée par l'éleveur actif)
            params = [st.session_state.user_id]
            query = """
                SELECT e.id, e.nom, e.localisation, e.superficie, el.nom
                FROM elevages e
                JOIN eleveurs el ON e.eleveur_id = el.id
                WHERE el.user_id=?
            """
            query, params = filtrer_par_eleveur(query, params, join_eleveur=True)
            elevages = db.fetchall(query, params)
            
            if not elevages:
                st.info("Aucun élevage pour cet éleveur.")
            else:
                df = pd.DataFrame(elevages, columns=["ID", "Nom", "Localisation", "Superficie", "Éleveur"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # (Optionnel) suppression d'élevage...
    
       # --- Onglet Brebis ---
    with tab3:
        st.subheader("Liste des brebis")
        
        # Récupérer les élevages de l'éleveur sélectionné (pour formulaire d'ajout)
        params_elev = [st.session_state.user_id]
        query_elev = """
            SELECT e.id, e.nom, el.nom
            FROM elevages e
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
        """
        query_elev, params_elev = filtrer_par_eleveur(query_elev, params_elev, join_eleveur=True)
        elevages_list = db.fetchall(query_elev, params_elev)
        elevages_dict = {f"{e[0]} - {e[1]} ({e[2]})": e[0] for e in elevages_list}
        
        if not elevages_dict:
            st.warning("Aucun élevage pour cet éleveur. Veuillez d'abord ajouter un élevage.")
        else:
            # --- Formulaire d'ajout de brebis ---
            with st.expander("➕ Ajouter une brebis", expanded=False):
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
                    
                    submitted = st.form_submit_button("Ajouter")
                    if submitted:
                        # Vérifier si la colonne poids_vif existe
                        cursor = db.conn.execute("PRAGMA table_info(brebis)")
                        columns = [col[1] for col in cursor.fetchall()]
                        if 'poids_vif' not in columns:
                            db.execute("ALTER TABLE brebis ADD COLUMN poids_vif REAL")
                            st.info("Colonne poids_vif ajoutée automatiquement.")
                        
                        elevage_id = elevages_dict[elevage_choice]
                        profil_filename = save_uploaded_photo(photo_profil)
                        mamelle_filename = save_uploaded_photo(photo_mamelle)
                        
                        db.execute("""
                            INSERT INTO brebis 
                            (elevage_id, numero_id, nom, race, date_naissance, etat_physio, photo_profil, photo_mamelle, poids_vif)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            elevage_id, numero_id, nom_brebis, race, 
                            date_naissance.isoformat(), etat_physio,
                            profil_filename, mamelle_filename, poids_vif
                        ))
                        st.success("Brebis ajoutée")
                        st.rerun()
            
            # --- Liste des brebis de l'éleveur actif ---
            params_brebis = [st.session_state.user_id]
            query_brebis = """
                SELECT b.id, b.numero_id, b.nom, b.race, b.date_naissance, b.etat_physio, e.nom, b.poids_vif
                FROM brebis b
                JOIN elevages e ON b.elevage_id = e.id
                JOIN eleveurs el ON e.eleveur_id = el.id
                WHERE el.user_id=?
            """
            query_brebis, params_brebis = filtrer_par_eleveur(query_brebis, params_brebis, join_eleveur=True)
            brebis = db.fetchall(query_brebis, params_brebis)
            
            if brebis:
                df_brebis = pd.DataFrame(brebis, columns=["ID", "Numéro", "Nom", "Race", "Naissance", "État", "Élevage", "Poids vif (kg)"])
                st.dataframe(df_brebis, use_container_width=True, hide_index=True)
                
                # --- Sélection d'une brebis pour le suivi individuel ---
                st.divider()
                st.subheader("🐑 Suivi individuel")
                selected_brebis = st.selectbox("Choisir une brebis", [f"{b[0]} - {b[1]} {b[2]}" for b in brebis], key="suivi_select")
                bid = int(selected_brebis.split(" - ")[0])
                
                # Récupérer les infos de la brebis
                brebis_info = db.fetchone("SELECT numero_id, nom, race, date_naissance, poids_vif FROM brebis WHERE id=?", (bid,))
                if brebis_info:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Numéro", brebis_info[0])
                    col2.metric("Nom", brebis_info[1])
                    col3.metric("Race", brebis_info[2])
                    age = (datetime.now() - datetime.strptime(brebis_info[3], "%Y-%m-%d")).days // 365 if brebis_info[3] else 0
                    st.metric("Âge (ans)", age)
                    st.metric("Dernier poids connu", f"{brebis_info[4]} kg" if brebis_info[4] else "Non renseigné")
                
                # --- Onglets pour les différentes données ---
                tab_hist1, tab_hist2, tab_hist3, tab_hist4 = st.tabs(["📈 Poids", "🥛 Production", "📏 Morphométrie", "📝 Notes"])
                
                with tab_hist1:
                    # Historique des poids (depuis composition_corporelle et mesures_morpho? ou directement poids_vif?)
                    # On va utiliser les données de composition_corporelle
                    poids_data = db.fetchall("""
                        SELECT date_estimation, poids_vif FROM composition_corporelle 
                        WHERE brebis_id=? ORDER BY date_estimation
                    """, (bid,))
                    if poids_data:
                        df_poids = pd.DataFrame(poids_data, columns=["Date", "Poids (kg)"])
                        df_poids["Date"] = pd.to_datetime(df_poids["Date"])
                        fig_poids = px.line(df_poids, x="Date", y="Poids (kg)", title="Évolution du poids")
                        st.plotly_chart(fig_poids, use_container_width=True)
                    else:
                        st.info("Aucune donnée de poids historique.")
                    
                    # Formulaire pour ajouter un nouveau poids
                    with st.form("form_poids"):
                        new_poids = st.number_input("Nouveau poids (kg)", min_value=0.0, step=0.1)
                        if st.form_submit_button("Ajouter ce poids"):
                            # On insère dans composition_corporelle (avec des valeurs par défaut pour les autres champs)
                            db.execute("""
                                INSERT INTO composition_corporelle 
                                (brebis_id, date_estimation, poids_vif, poids_carcasse, rendement_carcasse,
                                 poids_viande, pct_viande, poids_graisse, pct_graisse, poids_os, pct_os,
                                 gigot_poids, epaule_poids, cotelette_poids)
                                VALUES (?, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                            """, (bid, datetime.now().isoformat(), new_poids))
                            st.success("Poids enregistré !")
                            st.rerun()
                
                with tab_hist2:
                    # Production laitière
                    prod_data = db.fetchall("""
                        SELECT date, quantite FROM productions WHERE brebis_id=? ORDER BY date
                    """, (bid,))
                    if prod_data:
                        df_prod = pd.DataFrame(prod_data, columns=["Date", "Lait (L)"])
                        df_prod["Date"] = pd.to_datetime(df_prod["Date"])
                        fig_prod = px.line(df_prod, x="Date", y="Lait (L)", title="Production laitière")
                        st.plotly_chart(fig_prod, use_container_width=True)
                    else:
                        st.info("Aucune donnée de production.")
                    
                    # Formulaire pour ajouter une production
                    with st.form("form_prod_suivi"):
                        date_prod = st.date_input("Date", value=datetime.today().date())
                        quantite = st.number_input("Quantité (L)", min_value=0.0, step=0.1)
                        if st.form_submit_button("Enregistrer production"):
                            db.execute("INSERT INTO productions (brebis_id, date, quantite) VALUES (?, ?, ?)",
                                      (bid, date_prod.isoformat(), quantite))
                            st.success("Production enregistrée !")
                            st.rerun()
                
                with tab_hist3:
                    # Mesures morphométriques
                    morpho_data = db.fetchall("""
                        SELECT date_mesure, longueur_corps, hauteur_garrot, tour_poitrine, 
                               circonference_canon, largeur_bassin, score_global
                        FROM mesures_morpho WHERE brebis_id=? ORDER BY date_mesure
                    """, (bid,))
                    if morpho_data:
                        df_morpho = pd.DataFrame(morpho_data, columns=["Date", "Longueur", "Hauteur", "Poitrine", "Canon", "Bassin", "Score"])
                        df_morpho["Date"] = pd.to_datetime(df_morpho["Date"])
                        st.dataframe(df_morpho.drop(columns=["Date"]), use_container_width=True, hide_index=True)
                        
                        # Évolution du score
                        fig_score = px.line(df_morpho, x="Date", y="Score", title="Évolution du score morphologique")
                        st.plotly_chart(fig_score, use_container_width=True)
                    else:
                        st.info("Aucune mesure morphométrique.")
                    
                    # Lien vers la page d'analyse (avec un bouton)
                    if st.button("📸 Aller à la photogrammétrie pour cette brebis"):
                        st.session_state.current_page = "analyse"
                        # On pourrait stocker l'ID de la brebis pour pré-sélectionner, mais c'est optionnel
                        st.rerun()
                
                with tab_hist4:
                    # Notes / diagnostics (table diagnostics)
                    diag_data = db.fetchall("""
                        SELECT date, maladie, symptomes, traitement FROM diagnostics WHERE brebis_id=? ORDER BY date DESC
                    """, (bid,))
                    if diag_data:
                        df_diag = pd.DataFrame(diag_data, columns=["Date", "Maladie", "Symptômes", "Traitement"])
                        st.dataframe(df_diag, use_container_width=True, hide_index=True)
                    else:
                        st.info("Aucune note de diagnostic.")
                    
                    # Formulaire pour ajouter une note
                    with st.form("form_diag"):
                        date_diag = st.date_input("Date", value=datetime.today().date())
                        maladie = st.text_input("Maladie / Observation")
                        symptomes = st.text_area("Symptômes")
                        traitement = st.text_area("Traitement")
                        if st.form_submit_button("Enregistrer"):
                            db.execute("""
                                INSERT INTO diagnostics (brebis_id, date, maladie, symptomes, traitement)
                                VALUES (?, ?, ?, ?, ?)
                            """, (bid, date_diag.isoformat(), maladie, symptomes, traitement))
                            st.success("Note enregistrée !")
                            st.rerun()
                
                # --- Boutons de suppression (à garder éventuellement) ---
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Supprimer cette brebis", key="del_brebis_suivi"):
                        photos = db.fetchone("SELECT photo_profil, photo_mamelle FROM brebis WHERE id=?", (bid,))
                        if photos:
                            for p in photos:
                                if p:
                                    try:
                                        os.remove(os.path.join(PHOTO_DIR, p))
                                    except:
                                        pass
                        db.execute("DELETE FROM brebis WHERE id=?", (bid,))
                        st.success("Brebis supprimée")
                        st.rerun()
                with col2:
                    if st.button("📋 Voir détails complets", key="details_brebis_suivi"):
                        b = db.fetchone("SELECT * FROM brebis WHERE id=?", (bid,))
                        cols = [col[0] for col in db.conn.execute("PRAGMA table_info(brebis)").fetchall()]
                        data = dict(zip(cols, b))
                        if data.get('photo_profil'):
                            data['photo_profil'] = f"Fichier: {data['photo_profil']}"
                        if data.get('photo_mamelle'):
                            data['photo_mamelle'] = f"Fichier: {data['photo_mamelle']}"
                        st.json(data)
            else:
                st.info("Aucune brebis enregistrée.")
# -----------------------------------------------------------------------------
# PAGE PRODUCTION LAITIÈRE (identique à avant, mais recopiée pour complétude)
# -----------------------------------------------------------------------------
def page_production():
    st.title("🥛 Production laitière et analyses biochimiques")
    
    tab1, tab2 = st.tabs(["📈 Suivi production", "🧪 Analyses biochimiques"])
    
    params = [st.session_state.user_id]
    query_brebis = """
        SELECT b.id, b.numero_id, b.nom, e.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """
    query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
    brebis_list = db.fetchall(query_brebis, params)
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}
    
    if not brebis_dict:
        st.warning("Aucune brebis disponible pour cet éleveur.")
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
        # Ici on veut la production de tous les éleveurs de l'utilisateur (pas filtré par éleveur actif)
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
# PAGE GÉNOMIQUE AVANCÉE (corrigée, avec les modifications)
# -----------------------------------------------------------------------------
def page_genomique_avancee():
    st.title("🧬 Génomique avancée")
    
    tab1, tab2, tab3 = st.tabs(["🔍 BLAST", "🧬 SNPs d'intérêt", "📊 GWAS"])
    
    # Récupérer les brebis de l'éleveur sélectionné (pour la sélection)
    params = [st.session_state.user_id]
    query_brebis = """
        SELECT b.id, b.numero_id, b.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """
    query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
    brebis_list = db.fetchall(query_brebis, params)
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

# -----------------------------------------------------------------------------
# PAGE SANTÉ (identique)
# -----------------------------------------------------------------------------
def page_sante():
    st.title("🏥 Suivi sanitaire et vaccinal")

    # Récupérer les brebis selon l'éleveur actif
    params = [st.session_state.user_id]
    query_brebis = """
        SELECT b.id, b.numero_id, b.nom, e.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """
    query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
    brebis_list = db.fetchall(query_brebis, params)
    brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}

    if not brebis_dict:
        st.warning("Aucune brebis disponible.")
        return

    # Sélection de la brebis
    selected = st.selectbox("Choisir une brebis", list(brebis_dict.keys()), key="sante_brebis")
    bid = brebis_dict[selected]

    # Récupération des données de la brebis
    brebis_infos = db.fetchone("SELECT nom, numero_id, date_naissance, race FROM brebis WHERE id=?", (bid,))
    if brebis_infos:
        nom, numero, naiss, race = brebis_infos
        age = (datetime.now() - datetime.strptime(naiss, "%Y-%m-%d")).days // 365 if naiss else 0
        st.info(f"**{nom}** ({numero}) - {race}, {age} ans")

    # --- Création des onglets ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📜 Historique", 
        "⏰ Rappels", 
        "📊 Statistiques", 
        "🤖 IA & Prédictions", 
        "📤 Export"
    ])

    # =========================================================================
    # Onglet 1 : Historique consolidé
    # =========================================================================
    with tab1:
        st.subheader("Historique des soins et vaccins")

        # Récupérer les vaccins
        vaccins = db.fetchall("""
            SELECT date_vaccin, vaccin, rappel, 'Vaccin' as type
            FROM vaccinations WHERE brebis_id=?
        """, (bid,))
        # Récupérer les soins
        soins = db.fetchall("""
            SELECT date_soin, diagnostic, traitement, type as type
            FROM soins WHERE brebis_id=?
        """, (bid,))

        # Fusionner et trier par date
        historique = []
        for v in vaccins:
            historique.append({
                "Date": v[0],
                "Type": v[3],
                "Description": f"{v[1]} (rappel le {v[2]})" if v[2] else v[1],
                "Détails": ""
            })
        for s in soins:
            historique.append({
                "Date": s[0],
                "Type": s[3],
                "Description": s[1],
                "Détails": s[2]
            })

        if historique:
            df_hist = pd.DataFrame(historique)
            df_hist["Date"] = pd.to_datetime(df_hist["Date"])
            df_hist = df_hist.sort_values("Date", ascending=False)

            # Filtre par type
            types = df_hist["Type"].unique().tolist()
            selected_types = st.multiselect("Filtrer par type", types, default=types)
            df_filtre = df_hist[df_hist["Type"].isin(selected_types)]

            st.dataframe(df_filtre, use_container_width=True, hide_index=True)

            # Graphique chronologique
            df_count = df_filtre.groupby([df_filtre["Date"].dt.to_period("M"), "Type"]).size().reset_index(name="Nombre")
            df_count["Date"] = df_count["Date"].astype(str)
            fig = px.bar(df_count, x="Date", y="Nombre", color="Type", title="Événements par mois")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun événement enregistré pour cette brebis.")

        # Formulaire d'ajout rapide (soin ou vaccin)
        with st.expander("➕ Ajouter un événement"):
            type_evt = st.radio("Type", ["Soin", "Vaccin"])
            if type_evt == "Vaccin":
                with st.form("form_vaccin_rapide"):
                    date_vaccin = st.date_input("Date du vaccin", value=datetime.today().date())
                    vaccin = st.text_input("Nom du vaccin")
                    rappel = st.date_input("Date de rappel (optionnelle)", value=None)
                    if st.form_submit_button("Enregistrer"):
                        db.execute(
                            "INSERT INTO vaccinations (brebis_id, date_vaccin, vaccin, rappel) VALUES (?, ?, ?, ?)",
                            (bid, date_vaccin.isoformat(), vaccin, rappel.isoformat() if rappel else None)
                        )
                        st.success("Vaccin enregistré")
                        st.rerun()
            else:
                with st.form("form_soin_rapide"):
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

    # =========================================================================
    # Onglet 2 : Rappels et alertes
    # =========================================================================
    with tab2:
        st.subheader("Rappels à venir")

        # Vaccins dont la date de rappel est dans le futur
        rappels = db.fetchall("""
            SELECT vaccin, rappel FROM vaccinations
            WHERE brebis_id=? AND rappel IS NOT NULL AND rappel >= date('now')
            ORDER BY rappel
        """, (bid,))

        if rappels:
            df_rappels = pd.DataFrame(rappels, columns=["Vaccin", "Date de rappel"])
            df_rappels["Jours restants"] = (pd.to_datetime(df_rappels["Date de rappel"]) - datetime.now()).dt.days
            st.dataframe(df_rappels, use_container_width=True, hide_index=True)

            # Alertes pour les rappels dans les 7 jours
            imminents = df_rappels[df_rappels["Jours restants"] <= 7]
            if not imminents.empty:
                st.warning("⚠️ Certains rappels sont imminents !")
                st.dataframe(imminents)
        else:
            st.info("Aucun rappel programmé.")

        # Traitements en cours (soins récents sans date de fin)
        # (On pourrait ajouter une colonne "date_fin" dans la table soins, mais par simplicité on prend les soins du dernier mois)
        soins_recents = db.fetchall("""
            SELECT date_soin, type, diagnostic, traitement
            FROM soins
            WHERE brebis_id=? AND date_soin >= date('now', '-30 days')
            ORDER BY date_soin DESC
        """, (bid,))
        if soins_recents:
            st.subheader("Traitements récents (mois en cours)")
            df_recents = pd.DataFrame(soins_recents, columns=["Date", "Type", "Diagnostic", "Traitement"])
            st.dataframe(df_recents, use_container_width=True, hide_index=True)

    # =========================================================================
    # Onglet 3 : Statistiques sanitaires
    # =========================================================================
    with tab3:
        st.subheader("Statistiques sanitaires")

        # Nombre de soins par type
        soins_stats = db.fetchall("""
            SELECT type, COUNT(*) FROM soins WHERE brebis_id=? GROUP BY type
        """, (bid,))
        if soins_stats:
            df_stats = pd.DataFrame(soins_stats, columns=["Type", "Nombre"])
            fig = px.pie(df_stats, values="Nombre", names="Type", title="Répartition des soins par type")
            st.plotly_chart(fig, use_container_width=True)

        # Évolution temporelle
        soins_temp = db.fetchall("""
            SELECT strftime('%Y-%m', date_soin) as mois, COUNT(*) 
            FROM soins WHERE brebis_id=?
            GROUP BY mois
            ORDER BY mois
        """, (bid,))
        if soins_temp:
            df_temp = pd.DataFrame(soins_temp, columns=["Mois", "Nombre"])
            fig2 = px.line(df_temp, x="Mois", y="Nombre", title="Évolution du nombre de soins")
            st.plotly_chart(fig2, use_container_width=True)

        # Taux de vaccination (ex: au moins un vaccin dans l'année)
        dernier_vaccin = db.fetchone("""
            SELECT MAX(date_vaccin) FROM vaccinations WHERE brebis_id=?
        """, (bid,))[0]
        if dernier_vaccin:
            jours_depuis = (datetime.now() - datetime.strptime(dernier_vaccin, "%Y-%m-%d")).days
            st.metric("Dernier vaccin", f"il y a {jours_depuis} jours")
        else:
            st.info("Aucun vaccin enregistré.")

    # =========================================================================
    # Onglet 4 : IA & Prédictions
    # =========================================================================
    with tab4:
        st.subheader("Intelligence Artificielle – Analyses prédictives")

        # 1. Prédiction de risque de maladie (modèle entraîné)
        model_risque_path = os.path.join(MODEL_DIR, 'risque_maladie.pkl')
        if os.path.exists(model_risque_path):
            model_risque = joblib.load(model_risque_path)
            # Récupérer les caractéristiques de la brebis pour la prédiction
            # (âge, race, production moyenne, poids, antécédents...)
            # À adapter selon les features disponibles
            st.info("Modèle de prédiction de risque disponible.")
            if st.button("Évaluer le risque pour cette brebis"):
                # Simulation (à remplacer par des vraies features)
                risque = np.random.choice(["Faible", "Modéré", "Élevé"], p=[0.6, 0.3, 0.1])
                st.metric("Risque estimé", risque)
        else:
            st.info("Aucun modèle de prédiction entraîné. Vous pouvez en entraîner un avec l'onglet IA.")

        # 2. Détection précoce d'anomalies (Isolation Forest)
        # Récupérer les dernières données de production et de poids
        prod_recentes = db.fetchall("""
            SELECT quantite FROM productions 
            WHERE brebis_id=? AND date >= date('now', '-60 days')
            ORDER BY date
        """, (bid,))
        poids_recents = db.fetchall("""
            SELECT poids_vif FROM composition_corporelle 
            WHERE brebis_id=? AND date_estimation >= date('now', '-60 days')
            ORDER BY date_estimation
        """, (bid,))

        if len(prod_recentes) >= 5 and len(poids_recents) >= 5:
            # Construire un vecteur de features (moyenne, variance, tendance...)
            # Pour simplifier, on prend les 5 dernières valeurs
            X_prod = np.array([p[0] for p in prod_recentes[-5:]]).reshape(1, -1)
            X_poids = np.array([p[0] for p in poids_recents[-5:]]).reshape(1, -1)

            # Entraîner un petit modèle Isolation Forest sur l'ensemble des brebis (fait dans la page IA)
            # Ici on utilisera un modèle pré-entraîné
            anomaly_model_path = os.path.join(MODEL_DIR, 'anomaly_prod.pkl')
            if os.path.exists(anomaly_model_path):
                model_anomaly = joblib.load(anomaly_model_path)
                pred = model_anomaly.predict(X_prod)
                if pred[0] == -1:
                    st.warning("⚠️ Anomalie détectée dans la production laitière récente.")
                else:
                    st.success("Production laitière normale.")
        else:
            st.info("Pas assez de données pour la détection d'anomalies.")

        # 3. Recommandations de vaccins (règles simples + ML optionnel)
        st.subheader("Recommandations vaccinales")
        # Règle de base : vaccin annuel contre les entérotoxémies
        dernier_vaccin_annuel = db.fetchone("""
            SELECT date_vaccin FROM vaccinations 
            WHERE brebis_id=? AND vaccin LIKE '%entéro%' OR vaccin LIKE '%annuel%'
            ORDER BY date_vaccin DESC LIMIT 1
        """, (bid,))
        if dernier_vaccin_annuel:
            date_dernier = datetime.strptime(dernier_vaccin_annuel[0], "%Y-%m-%d")
            if (datetime.now() - date_dernier).days > 365:
                st.warning("⚠️ Le vaccin annuel est à renouveler (plus d'un an).")
            else:
                mois_restants = 12 - ((datetime.now() - date_dernier).days // 30)
                st.info(f"Prochain rappel annuel dans environ {mois_restants} mois.")
        else:
            st.info("Aucun vaccin annuel enregistré. Il est recommandé de vacciner.")

        # Recommandation basée sur l'âge (jeunes)
        if age < 1:
            st.info("Les agneaux de moins d'un an doivent être vaccinés contre la pasteurellose.")

    # =========================================================================
    # Onglet 5 : Export
    # =========================================================================
    with tab5:
        st.subheader("Exporter l'historique")

        # Générer un CSV de tout l'historique
        if st.button("Générer le rapport CSV"):
            # Récupérer toutes les données
            vaccins_all = db.fetchall("""
                SELECT date_vaccin, vaccin, rappel FROM vaccinations WHERE brebis_id=?
            """, (bid,))
            soins_all = db.fetchall("""
                SELECT date_soin, type, diagnostic, traitement FROM soins WHERE brebis_id=?
            """, (bid,))

            # Créer un DataFrame
            data = []
            for v in vaccins_all:
                data.append({
                    "Date": v[0],
                    "Type": "Vaccin",
                    "Description": v[1],
                    "Rappel": v[2] if v[2] else "",
                    "Détails": ""
                })
            for s in soins_all:
                data.append({
                    "Date": s[0],
                    "Type": s[1],
                    "Description": s[2],
                    "Rappel": "",
                    "Détails": s[3]
                })
            if data:
                df_export = pd.DataFrame(data)
                df_export = df_export.sort_values("Date", ascending=False)
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f"sante_{numero}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Aucune donnée à exporter.")
# -----------------------------------------------------------------------------
# PAGE REPRODUCTION (identique)
# -----------------------------------------------------------------------------
def page_reproduction():
    st.title("🤰 Gestion de la reproduction")
    
    params = [st.session_state.user_id]
    query_brebis = """
        SELECT b.id, b.numero_id, b.nom, e.nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """
    query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
    brebis_list = db.fetchall(query_brebis, params)
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
# PAGE NUTRITION AVANCÉE (avec optimisation)
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

        # Récupérer les brebis de l'éleveur actif
        params = [st.session_state.user_id]
        query_brebis = """
            SELECT b.id, b.numero_id, b.nom, b.etat_physio, b.poids_vif
            FROM brebis b
            JOIN elevages e ON b.elevage_id = e.id
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
        """
        query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
        brebis_list = db.fetchall(query_brebis, params)
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
                # Deux modes : manuel ou optimisation automatique
                mode_ration = st.radio("Mode de composition", ["Manuel", "Optimisation automatique (coût minimum)"])

                if mode_ration == "Manuel":
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
                    # Optimisation automatique
                    st.subheader("Optimisation de la ration (coût minimum)")

                    # Préparer les données pour l'optimisation
                    n = len(aliments)
                    c = [a[6] for a in aliments]  # prix
                    # Matrice des contraintes A_ub * x <= b_ub
                    # On veut : somme(x_i * uem_i) >= besoin_uem  =>  -somme(...) <= -besoin
                    # De même pour PDIN
                    # Pour MS : somme(x_i * ms_i/100) <= besoin_ms (car ms est en %)
                    A_ub = []
                    b_ub = []
                    # UEM (>=)
                    A_ub.append([-a[3] for a in aliments])
                    b_ub.append(-besoins['uem'])
                    # PDIN (>=)
                    A_ub.append([-a[4] for a in aliments])
                    b_ub.append(-besoins['pdin'])
                    # MS (<=)
                    A_ub.append([a[5]/100 for a in aliments])  # convertir % en fraction
                    b_ub.append(besoins['ms'])

                    # Bornes : x_i >= 0
                    bounds = [(0, None) for _ in range(n)]

                    # Tolérance optionnelle : on peut ajouter des marges
                    tolerance = st.slider("Tolérance sur les besoins (%)", 0, 20, 10) / 100
                    # On ajuste les b_ub pour UEM et PDIN avec la tolérance
                    # UEM : on veut >= besoin*(1-tol) pour être sûr de couvrir
                    b_ub[0] = -besoins['uem'] * (1 - tolerance)
                    b_ub[1] = -besoins['pdin'] * (1 - tolerance)
                    # MS : on veut <= besoin*(1+tol) pour éviter excès
                    b_ub[2] = besoins['ms'] * (1 + tolerance)

                    # Résoudre
                    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

                    if res.success:
                        quantites = res.x
                        # Filtrer les aliments avec quantité > 0.01
                        ration_opt = []
                        for i, q in enumerate(quantites):
                            if q > 0.01:
                                ration_opt.append({
                                    "nom": aliments[i][1],
                                    "qte": q,
                                    "uem": aliments[i][3],
                                    "pdin": aliments[i][4],
                                    "ms": aliments[i][5],
                                    "prix": aliments[i][6]
                                })
                        if ration_opt:
                            df_opt = pd.DataFrame(ration_opt)
                            df_opt["Coût (DA/jour)"] = df_opt["qte"] * df_opt["prix"]
                            st.dataframe(df_opt[["nom", "qte", "Coût (DA/jour)"]].round(2), use_container_width=True, hide_index=True)
                            total_opt = df_opt["Coût (DA/jour)"].sum()
                            st.metric("Coût optimal journalier", f"{total_opt:.2f} DA")
                            # Vérification
                            uem_tot = sum(q * aliments[i][3] for i, q in enumerate(quantites))
                            pdin_tot = sum(q * aliments[i][4] for i, q in enumerate(quantites))
                            ms_tot = sum(q * aliments[i][5]/100 for i, q in enumerate(quantites))
                            st.write(f"UEM apportée : {uem_tot:.2f} MJ (besoin {besoins['uem']})")
                            st.write(f"PDIN apportée : {pdin_tot:.2f} g (besoin {besoins['pdin']})")
                            st.write(f"MS apportée : {ms_tot:.2f} kg (max {besoins['ms']* (1+tolerance):.2f})")
                        else:
                            st.warning("Aucun aliment sélectionné par l'optimisation.")
                    else:
                        st.error("Impossible de trouver une solution optimale. Vérifiez les contraintes ou ajoutez des aliments.")
        else:
            st.info("Aucune brebis disponible. Vous pouvez utiliser 'Personnalisé'.")

# -----------------------------------------------------------------------------
# PAGE EXPORT (identique)
# -----------------------------------------------------------------------------
def page_export():
    st.title("📤 Export des données")
    st.markdown("Téléchargez l'ensemble de vos données au format CSV ou Excel pour les partager avec votre professeur.")
    
    format_export = st.radio("Format", ["CSV (dossier compressé)", "Excel (fichier unique)"])
    inclure_photos = st.checkbox("Inclure les photos dans l'archive (pour CSV uniquement)", value=True)
    
    if st.button("Générer l'export"):
        # Liste des tables à exporter (dans l'ordre)
        all_tables = [
            "eleveurs", "elevages", "brebis", 
            "productions", "mesures_morpho", "mesures_mamelles", "composition_corporelle",
            "vaccinations", "soins", "chaleurs", "saillies", "mises_bas",
            "aliments", "rations", "ration_composition"
        ]
        
        # Obtenir la liste des tables réellement présentes dans la base
        cursor = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        data_frames = {}
        
        for table in all_tables:
            # Déterminer les colonnes de la table (si elle existe)
            if table in existing_tables:
                cursor = db.conn.execute(f"PRAGMA table_info({table})")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
            else:
                # Si la table n'existe pas, on définit des colonnes par défaut (on peut laisser vide)
                # Pour éviter l'erreur, on passe
                st.warning(f"La table {table} n'existe pas. Elle sera ignorée.")
                data_frames[table] = pd.DataFrame()
                continue
            
            # Créer un dataframe vide avec ces colonnes
            df_empty = pd.DataFrame(columns=columns)
            
            try:
                # Remplir avec les données de l'utilisateur selon le type de table
                if table == "eleveurs":
                    df_data = pd.read_sql_query(f"SELECT * FROM {table} WHERE user_id=?", db.conn, params=(st.session_state.user_id,))
                elif table == "elevages":
                    df_data = pd.read_sql_query("""
                        SELECT e.* FROM elevages e
                        JOIN eleveurs el ON e.eleveur_id = el.id
                        WHERE el.user_id=?
                    """, db.conn, params=(st.session_state.user_id,))
                elif table == "brebis":
                    df_data = pd.read_sql_query("""
                        SELECT b.* FROM brebis b
                        JOIN elevages e ON b.elevage_id = e.id
                        JOIN eleveurs el ON e.eleveur_id = el.id
                        WHERE el.user_id=?
                    """, db.conn, params=(st.session_state.user_id,))
                elif table in ["productions", "vaccinations", "soins", "chaleurs", "saillies", "mises_bas"]:
                    df_data = pd.read_sql_query(f"""
                        SELECT t.* FROM {table} t
                        JOIN brebis b ON t.brebis_id = b.id
                        JOIN elevages e ON b.elevage_id = e.id
                        JOIN eleveurs el ON e.eleveur_id = el.id
                        WHERE el.user_id=?
                    """, db.conn, params=(st.session_state.user_id,))
                elif table in ["mesures_morpho", "mesures_mamelles", "composition_corporelle"]:
                    df_data = pd.read_sql_query(f"""
                        SELECT t.* FROM {table} t
                        JOIN brebis b ON t.brebis_id = b.id
                        JOIN elevages e ON b.elevage_id = e.id
                        JOIN eleveurs el ON e.eleveur_id = el.id
                        WHERE el.user_id=?
                    """, db.conn, params=(st.session_state.user_id,))
                else:
                    # tables globales
                    df_data = pd.read_sql_query(f"SELECT * FROM {table}", db.conn)
                
                # Concaténer le vide avec les données (si les colonnes correspondent)
                # On utilise concat pour garder l'ordre des colonnes
                df_combined = pd.concat([df_empty, df_data], ignore_index=True)
                data_frames[table] = df_combined
            except Exception as e:
                st.error(f"Erreur lors de l'export de la table {table}: {e}")
                data_frames[table] = df_empty  # au moins les colonnes
        
        # Générer le fichier selon le format
        if format_export.startswith("Excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for name, df in data_frames.items():
                    # Limiter le nom de l'onglet à 31 caractères
                    sheet_name = name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            output.seek(0)
            st.download_button(
                label="📥 Télécharger Excel",
                data=output,
                file_name=f"ovin_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:  # CSV
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                for name, df in data_frames.items():
                    if not df.empty:
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        zip_file.writestr(f"{name}.csv", csv_data)
                    else:
                        # Même vide, on peut créer un fichier avec juste les en-têtes
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        zip_file.writestr(f"{name}.csv", csv_data)
                # Ajouter les photos si demandé
                if inclure_photos and os.path.exists(PHOTO_DIR):
                    for root, dirs, files in os.walk(PHOTO_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zip_file.write(file_path, arcname=os.path.join("photos", file))
            zip_buffer.seek(0)
            st.download_button(
                label="📥 Télécharger ZIP (CSV + photos)",
                data=zip_buffer,
                file_name=f"ovin_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )

# -----------------------------------------------------------------------------
# PAGE ÉLITE ET COMPARAISON (inchangée)
# -----------------------------------------------------------------------------
def page_elite():
    st.title("🏆 Élite et comparaison")
    
    # Récupérer les brebis selon le contexte (éleveur sélectionné ou tous)
    params = [st.session_state.user_id]
    query_brebis = """
        SELECT b.id, b.numero_id, b.nom, b.race, b.date_naissance, b.poids_vif,
               e.nom as elevage_nom, el.nom as eleveur_nom
        FROM brebis b
        JOIN elevages e ON b.elevage_id = e.id
        JOIN eleveurs el ON e.eleveur_id = el.id
        WHERE el.user_id=?
    """
    query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
    brebis = db.fetchall(query_brebis, params)
    
    if not brebis:
        st.warning("Aucune brebis trouvée pour le contexte sélectionné.")
        return
    
    df = pd.DataFrame(brebis, columns=["id", "numero", "nom", "race", "naissance", "poids", "elevage", "eleveur"])
    
    # Production laitière moyenne des 30 derniers jours
    prod_moy = []
    for bid in df["id"]:
        prod = db.fetchone("""
            SELECT AVG(quantite) FROM productions 
            WHERE brebis_id=? AND date >= date('now', '-30 days')
        """, (bid,))
        prod_moy.append(prod[0] if prod and prod[0] else 0)
    df["prod_moy (L/j)"] = prod_moy
    
    # Dernier score morphologique
    score_morpho = []
    for bid in df["id"]:
        score = db.fetchone("""
            SELECT score_global FROM mesures_morpho 
            WHERE brebis_id=? ORDER BY date_mesure DESC LIMIT 1
        """, (bid,))
        score_morpho.append(score[0] if score else 0)
    df["score_morpho"] = score_morpho
    
    # Estimation simple de la viande
    df["viande_estimee (kg)"] = df["poids"] * 0.45
    
    # Dernière composition enregistrée (rendement)
    rendement = []
    for bid in df["id"]:
        comp = db.fetchone("""
            SELECT rendement_carcasse FROM composition_corporelle 
            WHERE brebis_id=? ORDER BY date_estimation DESC LIMIT 1
        """, (bid,))
        rendement.append(comp[0] if comp else None)
    df["rendement (%)"] = rendement
    
    # Affichage du tableau
    st.subheader("📊 Tableau des brebis")
    colonnes_affichees = ["numero", "nom", "eleveur", "elevage", "race", "poids", "prod_moy (L/j)", "score_morpho", "viande_estimee (kg)", "rendement (%)"]
    st.dataframe(df[colonnes_affichees].round(2))
    
    # Classement
    st.subheader("🏆 Classement")
    critere = st.selectbox("Critère de classement", 
                           ["prod_moy (L/j)", "score_morpho", "viande_estimee (kg)", "poids", "rendement (%)"])
    top_n = st.slider("Nombre de brebis à afficher", 5, 50, 10)
    ascending = st.checkbox("Ordre croissant", False)
    
    # Conversion explicite en numérique et suppression des lignes sans valeur
    df[critere] = pd.to_numeric(df[critere], errors='coerce')
    df_class = df[df[critere].notna()].copy()
    if df_class.empty:
        st.warning(f"Aucune valeur numérique valide pour le critère {critere}.")
    else:
        if ascending:
            top = df_class.nsmallest(top_n, critere)
        else:
            top = df_class.nlargest(top_n, critere)
        st.dataframe(top[["numero", "nom", "eleveur", "elevage", critere]].round(2))
        
        fig = px.bar(top, x="nom", y=critere, color="eleveur", title=f"Top {top_n} - {critere}")
        st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison entre éleveurs (si tous sélectionnés)
    if st.session_state.eleveur_id is None and len(df["eleveur"].unique()) > 1:
        st.subheader("📈 Comparaison par éleveur")
        numeric_cols = ["prod_moy (L/j)", "score_morpho", "poids", "viande_estimee (kg)", "rendement (%)"]
        df_eleveur = df.groupby("eleveur")[numeric_cols].mean().reset_index()
        for col in numeric_cols:
            df_eleveur[col] = pd.to_numeric(df_eleveur[col], errors='coerce').fillna(0)
        st.dataframe(df_eleveur.round(2))
        
        fig2 = px.bar(df_eleveur, x="eleveur", y=["prod_moy (L/j)", "score_morpho", "rendement (%)"], 
                     barmode="group", title="Performances moyennes par éleveur")
        st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------------------------------------------
# NOUVELLE PAGE IA & DATA MINING
# -----------------------------------------------------------------------------
def page_ia():
    st.title("🧠 Intelligence Artificielle & Data Mining")
    st.markdown("Analyses avancées basées sur les données de votre élevage.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Prédiction laitière avancée",
        "🔍 Détection d'anomalies",
        "📊 Clustering des brebis",
        "📂 Analyse exploratoire (import)"
    ])

    # --- Onglet 1 : Prédiction laitière avancée ---
    with tab1:
        st.subheader("Prédiction de production laitière par modèle ML")
        # Vérifier si un modèle existe
        model_path = os.path.join(MODEL_DIR, 'lait_model.pkl')
        if os.path.exists(model_path):
            st.success("Un modèle ML est disponible.")
            # Sélectionner une brebis
            params = [st.session_state.user_id]
            query_brebis = """
                SELECT b.id, b.numero_id, b.nom, e.nom
                FROM brebis b
                JOIN elevages e ON b.elevage_id = e.id
                JOIN eleveurs el ON e.eleveur_id = el.id
                WHERE el.user_id=?
            """
            query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
            brebis_list = db.fetchall(query_brebis, params)
            brebis_dict = {f"{b[0]} - {b[1]} {b[2]} ({b[3]})": b[0] for b in brebis_list}
            
            if brebis_dict:
                selected = st.selectbox("Choisir une brebis", list(brebis_dict.keys()), key="ia_brebis")
                bid = brebis_dict[selected]
                if st.button("Prédire avec ML"):
                    pred = predict_lait_ml(bid)
                    if pred is not None:
                        st.metric("Production prédite (L/j)", f"{pred:.2f}")
                    else:
                        st.warning("Impossible de faire la prédiction (données manquantes).")
            else:
                st.warning("Aucune brebis disponible.")
        else:
            st.info("Aucun modèle ML entraîné. Vous pouvez en entraîner un si vous avez suffisamment de données de production.")
            if st.button("Entraîner un modèle ML"):
                with st.spinner("Entraînement en cours..."):
                    result = train_lait_model()
                    if result is None:
                        st.error("Pas assez de données (minimum 20 brebis avec productions).")
                    else:
                        model, score = result
                        st.success(f"Modèle entraîné avec un score R² de {score:.2f} sur le test.")

    # --- Onglet 2 : Détection d'anomalies ---
    with tab2:
        st.subheader("Détection d'anomalies (Isolation Forest)")
        # Récupérer les données nécessaires
        params = [st.session_state.user_id]
        query_brebis = """
            SELECT b.id, b.numero_id, b.nom, b.poids_vif,
                   AVG(p.quantite) as prod_moy,
                   AVG(m.score_global) as score_morpho
            FROM brebis b
            LEFT JOIN productions p ON b.id = p.brebis_id AND p.date >= date('now', '-30 days')
            LEFT JOIN mesures_morpho m ON b.id = m.brebis_id
            JOIN elevages e ON b.elevage_id = e.id
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
            GROUP BY b.id
        """
        query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
        df = pd.read_sql_query(query_brebis, db.conn, params=params)
        if df.empty:
            st.warning("Aucune donnée disponible.")
        else:
            # Remplir les NaN
            df['viande_estimee'] = df['poids_vif'] * 0.45
            df['prod_moy'] = df['prod_moy'].fillna(0)
            df['score_morpho'] = df['score_morpho'].fillna(0)
            
            # Détection
            features = ['prod_moy', 'score_morpho', 'poids_vif', 'viande_estimee']
            X = df[features].fillna(0)
            model = IsolationForest(contamination=0.1, random_state=42)
            preds = model.fit_predict(X)
            df['anomalie'] = preds
            anomalies = df[df['anomalie'] == -1]
            st.write(f"**{len(anomalies)}** brebis potentiellement anormales détectées.")
            if not anomalies.empty:
                st.dataframe(anomalies[['numero_id', 'nom', 'prod_moy', 'score_morpho', 'poids_vif']])
            else:
                st.success("Aucune anomalie détectée.")

        # --- Onglet 3 : Clustering des brebis ---
    with tab3:
        st.subheader("Clustering des brebis (K-Means)")
        # Récupérer les données
        params = [st.session_state.user_id]
        query_brebis = """
            SELECT b.id, b.numero_id, b.nom, b.poids_vif,
                   AVG(p.quantite) as prod_moy,
                   AVG(m.score_global) as score_morpho
            FROM brebis b
            LEFT JOIN productions p ON b.id = p.brebis_id AND p.date >= date('now', '-30 days')
            LEFT JOIN mesures_morpho m ON b.id = m.brebis_id
            JOIN elevages e ON b.elevage_id = e.id
            JOIN eleveurs el ON e.eleveur_id = el.id
            WHERE el.user_id=?
            GROUP BY b.id
        """
        query_brebis, params = filtrer_par_eleveur(query_brebis, params, join_eleveur=True)
        df = pd.read_sql_query(query_brebis, db.conn, params=params)
        
        if df.empty:
            st.warning("Aucune donnée disponible pour le clustering.")
        else:
            df['viande_estimee'] = df['poids_vif'] * 0.45
            df['prod_moy'] = df['prod_moy'].fillna(0)
            df['score_morpho'] = df['score_morpho'].fillna(0)
            
            n_brebis = len(df)
            max_clusters = min(5, n_brebis)  # on ne peut pas avoir plus de clusters que de brebis
            if max_clusters < 2:
                st.warning(f"Pas assez de brebis ({n_brebis}) pour effectuer un clustering (minimum 2).")
            else:
                n_clusters = st.slider("Nombre de clusters", 2, max_clusters, min(3, max_clusters))
                
                features = ['prod_moy', 'score_morpho', 'poids_vif', 'viande_estimee']
                X = df[features].fillna(0)
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(X_scaled)
                df['cluster'] = clusters
                
                # Affichage 3D
                fig = px.scatter_3d(df, x='prod_moy', y='score_morpho', z='poids_vif', color='cluster',
                                     hover_data=['numero_id', 'nom'], title="Clusters des brebis")
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques par cluster
                st.dataframe(df.groupby('cluster')[features].mean().round(2))

       # --- Onglet 4 : Analyse exploratoire (import) ---
    with tab4:
        st.subheader("Analyse exploratoire d'un fichier externe")
        uploaded_file = st.file_uploader("Choisir un fichier CSV ou Excel", type=['csv', 'xlsx'])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.success("Fichier chargé avec succès.")
                st.dataframe(df.head())
                
                if profiling_available:
                    analyse_mode = st.radio("Type d'analyse", ["Statistiques descriptives", "Rapport complet (ydata-profiling)"])
                else:
                    st.info("Module ydata-profiling non installé. Utilisation des statistiques descriptives.")
                    analyse_mode = "Statistiques descriptives"
                
                if analyse_mode == "Statistiques descriptives":
                    st.subheader("Statistiques descriptives")
                    st.dataframe(df.describe(include='all').transpose())
                    st.subheader("Informations sur les colonnes")
                    buffer = io.StringIO()
                    df.info(buf=buffer)
                    st.text(buffer.getvalue())
                else:
                    if profiling_available:
                        if st.button("Générer le rapport d'analyse"):
                            with st.spinner("Génération du rapport..."):
                                profile = ProfileReport(df, title="Rapport d'analyse", explorative=True)
                                st_profile_report(profile)
                    else:
                        st.warning("Le module ydata-profiling n'est pas disponible. Cette option ne devrait pas apparaître.")
            except Exception as e:
                st.error(f"Erreur de lecture : {e}")

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
            # --- Sélection de l'éleveur actif ---
            eleveurs = db.fetchall(
                "SELECT id, nom FROM eleveurs WHERE user_id=? ORDER BY nom",
                (st.session_state.user_id,)
            )
            eleveurs_options = {"Tous les éleveurs": None}
            eleveurs_options.update({f"{e[1]} (ID {e[0]})": e[0] for e in eleveurs})
            
            current = st.session_state.get("eleveur_id", None)
            default_index = 0
            for i, (label, eid) in enumerate(eleveurs_options.items()):
                if eid == current:
                    default_index = i
                    break
            
            selected_label = st.selectbox(
                "👨‍🌾 Éleveur actif",
                options=list(eleveurs_options.keys()),
                index=default_index,
                key="eleveur_selector"
            )
            st.session_state.eleveur_id = eleveurs_options[selected_label]
            st.divider()
            # --- Fin sélection éleveur ---
            
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
                 "🏆 Élite et comparaison",
                 "🧠 IA & Data Mining",
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
                "🏆 Élite et comparaison": "elite",
                "🧠 IA & Data Mining": "ia",
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
    elif st.session_state.current_page == "elite":
        page_elite()
    elif st.session_state.current_page == "ia":
        page_ia()

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
        st.session_state.eleveur_id = None
    
    # Configuration de la page
    st.set_page_config(
        page_title="Ovin Manager Pro",
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
    
    main()
