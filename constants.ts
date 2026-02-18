
import { BreedStandard, MorphoTrait, ReferenceObject } from './types';

export const ALGERIAN_FEED_INGREDIENTS = [
  { id: 'ORGE', name: 'Orge (Chaïr)', category: 'CONCENTRE', defaultPrice: 60 },
  { id: 'SON', name: 'Son de blé (Nokhala)', category: 'CONCENTRE', defaultPrice: 45 },
  { id: 'MAIS', name: 'Maïs jaune', category: 'CONCENTRE', defaultPrice: 85 },
  { id: 'SOJA', name: 'Tourteau de Soja', category: 'CONCENTRE', defaultPrice: 160 },
  { id: 'FOIN', name: 'Foin (Vesce-Avoine)', category: 'FOURRAGE', defaultPrice: 40 },
  { id: 'PAILLE', name: 'Paille (Tben)', category: 'FOURRAGE', defaultPrice: 25 },
  { id: 'CMV', name: 'CMV (Sels/Vitamines)', category: 'MINERAL', defaultPrice: 250 },
  { id: 'ALIMENT_COMPLET', name: 'Aliment Complet (Engraissement)', category: 'CONCENTRE', defaultPrice: 95 }
];

export const REFERENCE_OBJECTS: ReferenceObject[] = [
  { id: 'AUCUN', label: 'Aucun (Estimation)', dimension: '-', icon: '❓' },
  { id: 'BATON_1M', label: 'Bâton de 1 mètre', dimension: '100 cm', icon: '📏' },
  { id: 'FEUILLE_A4', label: 'Feuille A4', dimension: '21.0 x 29.7 cm', icon: '📄' },
  { id: 'PIECE_100DA', label: 'Pièce 100 DA', dimension: '2.95 cm', icon: '🪙' },
  { id: 'CARTE_BANCAIRE', label: 'Carte Bancaire', dimension: '8.56 x 5.4 cm', icon: '💳' }
];

export const MORPHO_TRAITS: MorphoTrait[] = [
  { id: 'longueur', label: 'Longueur du Corps', unit: 'cm', description: 'Pointe épaule à pointe fesse.', type: 'quantitative' },
  { id: 'hauteur', label: 'Hauteur au Garrot', unit: 'cm', description: 'Sol au sommet du garrot.', type: 'quantitative' },
  { id: 'poitrine', label: 'Tour de Poitrine', unit: 'cm', description: 'Périmètre thoracique.', type: 'quantitative' },
  { id: 'bassin', label: 'Largeur Bassin', unit: 'cm', description: 'Largeur aux hanches.', type: 'quantitative' },
  { id: 'profondeur', label: 'Profondeur Poitrine', unit: 'cm', description: 'Sternum au dos.', type: 'quantitative' },
  { id: 'canon', label: 'Tour de Canon', unit: 'cm', description: 'Périmètre de l\'os.', type: 'quantitative' }
];

export const MAMMARY_TRAITS: MorphoTrait[] = [
  { id: 'trayon_longueur', label: 'Longueur Trayons', unit: 'cm', description: 'Longueur moyenne.', type: 'quantitative' },
  { id: 'trayon_diametre', label: 'Diamètre Trayons', unit: 'cm', description: 'Base du trayon.', type: 'quantitative' },
  { id: 'inter_trayon', label: 'Espace Trayons', unit: 'cm', description: 'Distance entre les deux.', type: 'quantitative' },
  { id: 'volume_mammele', label: 'Volume Mammaire', unit: 'cm3', description: 'Estimation globale.', type: 'quantitative' },
  { id: 'symetrie', label: 'Symétrie', description: 'Équilibre des quartiers.', type: 'qualitative', options: ['Symétrique', 'Asymétrique'] },
  { id: 'attache', label: 'Attache', description: 'Solidité du maintien.', type: 'qualitative', options: ['Solide', 'Moyenne', 'Pendante'] },
  { id: 'forme', label: 'Forme', description: 'Conformation globale.', type: 'qualitative', options: ['Globuleuse', 'Bifide', 'En poire'] },
  { id: 'orientation', label: 'Orientation', description: 'Sortie des trayons.', type: 'qualitative', options: ['Verticale', 'Latérale', 'Divergente'] }
];

export const STANDARDS_RACES: Record<string, BreedStandard> = {
  'HAMRA': {
    id: 'HAMRA',
    nom_complet: 'Hamra (Rousse)',
    couleur: 'Rouge à marron',
    origines: ['Sud Algérien'],
    caracteristiques: ['Résistance extrême', 'Laitière'],
    poids_adulte: { femelle: [45, 60], male: [65, 85] },
    mensurations: { longueur_cm: [90, 120], hauteur_cm: [60, 80], tour_poitrine_cm: [90, 115], largeur_bassin_cm: [35, 48] }
  },
  'OUDA': {
    id: 'OUDA',
    nom_complet: 'Ouled Djellal (Blanche)',
    couleur: 'Blanche',
    origines: ['Steppes'],
    caracteristiques: ['Format imposant', 'Viande'],
    poids_adulte: { femelle: [55, 75], male: [75, 105] },
    mensurations: { longueur_cm: [100, 135], hauteur_cm: [75, 95], tour_poitrine_cm: [100, 135], largeur_bassin_cm: [40, 55] }
  },
  'SIDAHOU': {
    id: 'SIDAHOU',
    nom_complet: 'Sidahou',
    couleur: 'Tête noire, corps blanc',
    origines: ['Ouest'],
    caracteristiques: ['Rustique', 'Double fin'],
    poids_adulte: { femelle: [40, 55], male: [60, 80] },
    mensurations: { longueur_cm: [85, 115], hauteur_cm: [60, 75], tour_poitrine_cm: [85, 110], largeur_bassin_cm: [34, 45] }
  }
};
