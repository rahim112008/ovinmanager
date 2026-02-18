
export type Race = 'HAMRA' | 'OUDA' | 'SIDAHOU' | 'BERBERE' | 'CROISE' | 'INCONNU';
export type EtatPhysiologique = 
  | 'VIDE' 
  | 'GESTANTE_DEBUT' 
  | 'GESTANTE_FIN' 
  | 'ALLAITANTE' 
  | 'TARIE' 
  | 'EN_CROISSANCE';

export type Dentition = '0_DENT' | '2_DENTS' | '4_DENTS' | '6_DENTS' | '8_DENTS';

export type ReferenceObjectType = 'AUCUN' | 'BATON_1M' | 'FEUILLE_A4' | 'PIECE_100DA' | 'CARTE_BANCAIRE';
export type AnalysisMode = 'PROFILE' | 'MAMMARY';

export interface User {
  id: string;
  username: string;
  passwordHash: string;
  farmName: string;
  role: 'admin' | 'worker';
}

export interface Breeder {
  id: string;
  userId: string;
  nom: string;
  wilaya: string;
  telephone: string;
  photoUrl?: string;
  dateCreation: string;
}

export interface IngredientPrice {
  id: string;
  breederId: string;
  name: string;
  pricePerUnit: number; // DA par kg
  category: 'CONCENTRE' | 'FOURRAGE' | 'MINERAL';
}

export interface Sheep {
  id: string;
  userId: string;
  breederId: string;
  nom: string;
  tagId: string;
  race: Race;
  sexe: 'F' | 'M';
  age_mois?: number;
  dentition?: Dentition;
  poids: number;
  etat_physiologique: EtatPhysiologique;
  robe_couleur: string;
  robe_qualite: string;
  date_analyse: string;
  statut: 'actif' | 'reforme' | 'vendu';
  measurements: Record<string, number | string>;
  mammary_traits?: Record<string, number | string>;
  mammary_score?: number;
  classification?: string;
  notes?: string;
  imageUrl?: string;
}

export interface NutritionRecord {
  id: string;
  userId: string;
  breederId: string;
  sheepId: string;
  date: string;
  rationName: string;
  ingredients: { name: string, quantity_kg: number, cost: number }[];
  totalCost: number;
  objectif: 'ENTRETIEN' | 'ENGRAISSEMENT' | 'LACTATION' | 'GESTATION';
}

export interface ProductionRecord {
  id: string;
  userId: string;
  breederId: string;
  sheepId: string;
  date: string;
  quantite_litres: number;
  taux_butyreux: number;
  taux_proteique: number;
  lactose: number;
}

export interface HealthRecord {
  id: string;
  userId: string;
  breederId: string;
  sheepId: string;
  date: string;
  type: 'VACCIN' | 'TRAITEMENT' | 'DEPARASITAGE' | 'EXAMEN';
  description: string;
  produit?: string;
}

export interface ReproductionRecord {
  id: string;
  userId: string;
  breederId: string;
  sheepId: string;
  date_saillie: string;
  date_agnelage_prevue: string;
  statut: 'GESTATION' | 'TERMINE';
}

export interface MorphoTrait {
  id: string;
  label: string;
  unit?: string;
  description: string;
  type: 'quantitative' | 'qualitative';
  options?: string[];
}

// Added BreedStandard to fix constants.ts error
export interface BreedStandard {
  id: string;
  nom_complet: string;
  couleur: string;
  origines: string[];
  caracteristiques: string[];
  poids_adulte: { femelle: number[], male: number[] };
  mensurations: { 
    longueur_cm: number[], 
    hauteur_cm: number[], 
    tour_poitrine_cm: number[], 
    largeur_bassin_cm: number[] 
  };
}

// Added ReferenceObject to fix constants.ts error
export interface ReferenceObject {
  id: ReferenceObjectType;
  label: string;
  dimension: string;
  icon: string;
}

export interface AnalysisResult {
  race: Race;
  robe_couleur: string;
  robe_qualite: string;
  measurements?: Record<string, number>;
  mammary_traits?: Record<string, number | string>;
  mammary_score?: number;
  classification: string;
  feedback: string;
}
