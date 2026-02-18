
import React from 'react';

const PresentationModule: React.FC = () => {
  const sections = [
    {
      title: "1. Vision & Origine",
      icon: "🔬",
      content: "Ovin Manager Pro est une solution technologique conçue par le Laboratoire GenApAgiE pour moderniser le suivi zootechnique en Algérie. L'objectif est de transformer un simple smartphone en un outil de mesure biométrique de précision."
    },
    {
      title: "2. Structure Technique",
      icon: "🏗️",
      content: "L'application repose sur une architecture 'Offline-First' :",
      list: [
        "Interface : React.js pour une fluidité maximale.",
        "Intelligence : Google Gemini IA pour l'analyse d'images.",
        "Stockage : IndexedDB pour sauvegarder les données localement sans internet.",
        "PWA : Installation directe sur écran d'accueil comme une application native."
      ]
    },
    {
      title: "3. Système de Mensuration IA",
      icon: "📐",
      content: "La logique de mesure repose sur la calibration par objet témoin :",
      list: [
        "L'utilisateur place un objet connu (Bâton 1m, Pièce 100DA, Carte) à côté de l'animal.",
        "L'IA GenApAgiE identifie l'objet et calcule le ratio pixel/centimètre.",
        "Les points anatomiques sont détectés automatiquement pour extraire la hauteur, longueur et périmètre.",
        "Le poids est estimé via des corrélations morphométriques validées."
      ]
    },
    {
      title: "4. Input & Output des Données",
      icon: "🔄",
      content: "Flux d'informations du système :",
      list: [
        "Entrées (Inputs) : Photos (profil/arrière), N° boucle, âge dentaire, état physiologique, prix des aliments.",
        "Sorties (Outputs) : Mensurations précises, Score mammaire, Coût de ration journalier, Classement des élites génétiques."
      ]
    },
    {
      title: "5. Avantages & Limites",
      icon: "⚖️",
      content: "Analyse objective du système :",
      list: [
        "Avantages : Coût zéro matériel, utilisable en zone blanche (steppes), non-invasif pour l'animal, expertise IA immédiate.",
        "Limites : Sensibilité à la qualité photo (flou, angle), nécessite une calibration pour la précision millimétrique, dépendance à l'API Cloud pour l'analyse initiale."
      ]
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-fadeIn pb-24">
      <header className="text-center">
        <div className="inline-block bg-blue-50 p-4 rounded-3xl mb-4">
          <span className="text-4xl">📚</span>
        </div>
        <h2 className="text-4xl font-black text-gray-900 tracking-tight">Dossier de Présentation</h2>
        <p className="text-blue-600 font-bold tracking-widest mt-2 normal-case">Laboratoire GenApAgiE</p>
      </header>

      <div className="grid grid-cols-1 gap-8">
        {sections.map((s, i) => (
          <div key={i} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 hover:shadow-xl transition-all">
            <div className="flex items-start gap-6">
              <div className="text-4xl bg-gray-50 p-4 rounded-2xl">{s.icon}</div>
              <div className="flex-1">
                <h3 className="text-xl font-black text-gray-900 mb-3">{s.title}</h3>
                <p className="text-gray-600 leading-relaxed mb-4">{s.content}</p>
                {s.list && (
                  <ul className="space-y-2">
                    {s.list.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-sm text-gray-500">
                        <span className="text-blue-500 mt-1">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <footer className="bg-[#1a237e] text-white p-10 rounded-[3rem] text-center">
        <p className="text-[10px] font-black uppercase tracking-[0.3em] opacity-60 mb-4">Propriété Intellectuelle</p>
        <p className="text-lg font-medium">Ce système expert est le fruit des recherches du</p>
        <p className="text-2xl font-black mt-2 normal-case">Laboratoire GenApAgiE</p>
      </footer>
    </div>
  );
};

export default PresentationModule;
