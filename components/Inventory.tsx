
import React, { useState } from 'react';
import { Sheep, Breeder } from '../types';
import { MORPHO_TRAITS, MAMMARY_TRAITS } from '../constants';

interface InventoryProps {
  sheep: Sheep[];
  breeders?: Breeder[];
  selectedBreederId?: string;
  onDelete: (id: string) => void;
}

const Inventory: React.FC<InventoryProps> = ({ sheep, breeders, selectedBreederId, onDelete }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const currentBreeder = breeders?.find(b => b.id === selectedBreederId);

  const getEtatColor = (etat: string) => {
    if (etat.includes('GESTANTE')) return 'bg-purple-100 text-purple-700';
    switch(etat) {
      case 'ALLAITANTE': return 'bg-pink-100 text-pink-700';
      case 'TARIE': return 'bg-orange-100 text-orange-700';
      case 'EN_CROISSANCE': return 'bg-blue-100 text-blue-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const formatAge = (s: Sheep) => {
    if (s.dentition) return s.dentition.replace('_', ' ');
    return `${s.age_mois} mois`;
  };

  const downloadImage = (url: string, filename: string) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const filteredSheep = sheep.filter(s => 
    s.tagId.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.race.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fadeIn pb-24">
      {/* En-tête de l'inventaire contextuel */}
      <header className="bg-white p-8 rounded-[3rem] shadow-sm border border-gray-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">📂</span>
            <h2 className="text-3xl font-black text-gray-900 tracking-tight">Registre Biométrique</h2>
          </div>
          <p className="text-gray-500 font-medium">
            Élevage : <span className="text-[#1a237e] font-black uppercase">{currentBreeder?.nom || 'Non spécifié'}</span>
            <span className="mx-2 text-gray-300">|</span>
            Localité : <span className="font-bold text-gray-600 uppercase">{currentBreeder?.wilaya || '-'}</span>
          </p>
        </div>
        
        <div className="relative">
          <input 
            type="text" 
            placeholder="Rechercher une boucle..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-gray-50 border-none rounded-2xl px-6 py-4 text-sm font-bold w-full md:w-64 focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <span className="absolute right-4 top-1/2 -translate-y-1/2 opacity-20">🔍</span>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {filteredSheep.map((s) => (
          <div key={s.id} className="bg-white rounded-[3rem] overflow-hidden shadow-sm border border-gray-100 hover:shadow-2xl transition-all flex flex-col group border-b-4 border-b-blue-600">
            {/* Image et Badges */}
            <div className="aspect-video relative bg-gray-100 shrink-0 overflow-hidden">
              {s.imageUrl ? (
                <img src={s.imageUrl} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" alt={s.tagId} />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-4xl opacity-10">🐏</div>
              )}
              
              <div className="absolute top-6 left-6 flex flex-wrap gap-2">
                <span className={`px-3 py-1.5 rounded-full text-[10px] font-black uppercase shadow-lg backdrop-blur-md ${getEtatColor(s.etat_physiologique)}`}>
                  {s.etat_physiologique.replace('_', ' ')}
                </span>
                {s.mammary_score && (
                  <span className="px-3 py-1.5 rounded-full text-[10px] font-black uppercase shadow-lg bg-pink-600 text-white flex items-center gap-2">
                    ⭐ Score Mammaire: {s.mammary_score}/10
                  </span>
                )}
              </div>

              {s.imageUrl && (
                <button 
                  onClick={() => downloadImage(s.imageUrl!, `ovin_${s.tagId}.jpg`)}
                  className="absolute bottom-6 right-6 bg-white/90 hover:bg-white p-3 rounded-2xl text-[9px] font-black shadow-xl transition-all uppercase tracking-widest flex items-center gap-2"
                >
                  📥 Télécharger Photo
                </button>
              )}
            </div>
            
            <div className="p-8">
              {/* Infos de base */}
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h4 className="text-2xl font-black text-gray-900 leading-none mb-1">Boucle: {s.tagId}</h4>
                  <p className="text-[10px] text-gray-400 font-bold tracking-[0.2em] uppercase">{s.race} • Code {s.id}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-black text-[#1a237e] bg-blue-50 px-4 py-2 rounded-2xl border border-blue-100/50">{formatAge(s)}</p>
                </div>
              </div>

              {/* Sections de données side-by-side sur desktop */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Section Morphologie */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-6 h-6 bg-blue-900 text-white rounded-lg flex items-center justify-center text-[10px] font-black">📏</span>
                    <p className="text-[11px] font-black text-gray-900 uppercase tracking-widest">Morphométrie Corps</p>
                  </div>
                  
                  <div className="grid grid-cols-1 gap-2">
                    {Object.entries(s.measurements || {}).map(([key, value]) => {
                      const trait = MORPHO_TRAITS.find(t => t.id === key);
                      if (!value) return null;
                      return (
                        <div key={key} className="bg-gray-50/50 p-3 rounded-2xl flex justify-between items-center border border-gray-100">
                          <span className="text-[9px] text-gray-400 uppercase font-black">{trait?.label || key}</span>
                          <span className="text-xs font-black text-gray-900">{value} <span className="text-[9px] text-blue-400 font-normal">{trait?.unit || ''}</span></span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Section Mamelles */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-6 h-6 bg-pink-600 text-white rounded-lg flex items-center justify-center text-[10px] font-black">🥛</span>
                    <p className="text-[11px] font-black text-pink-700 uppercase tracking-widest">Examen Mammaire</p>
                  </div>
                  
                  <div className="grid grid-cols-1 gap-2">
                    {Object.entries(s.mammary_traits || {}).map(([key, value]) => {
                      const trait = MAMMARY_TRAITS.find(t => t.id === key);
                      if (!value) return null;
                      return (
                        <div key={key} className="bg-pink-50/20 p-3 rounded-2xl flex justify-between items-center border border-pink-100/30">
                          <span className="text-[9px] text-pink-400 uppercase font-black">{trait?.label || key}</span>
                          <span className="text-xs font-black text-pink-900">{value} <span className="text-[9px] text-pink-300 font-normal">{trait?.unit || ''}</span></span>
                        </div>
                      );
                    })}
                    {(!s.mammary_traits || Object.keys(s.mammary_traits).length === 0) && (
                      <div className="bg-gray-50 p-6 rounded-2xl text-center border border-dashed border-gray-200">
                        <p className="text-[10px] font-bold text-gray-300 uppercase">Pas de données mammaires</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Feedback Expert */}
              {s.notes && (
                <div className="mt-8 bg-blue-50/50 p-5 rounded-3xl border border-blue-100">
                  <p className="text-[9px] font-black text-blue-800 uppercase mb-2 tracking-widest">Observations Zootechniques</p>
                  <p className="text-xs text-gray-600 leading-relaxed italic">"{s.notes}"</p>
                </div>
              )}

              {/* Actions */}
              <div className="mt-8 flex gap-3 pt-6 border-t border-gray-50">
                <button 
                  onClick={() => onDelete(s.id)} 
                  className="bg-red-50 text-red-500 px-6 py-3 rounded-2xl text-[10px] font-black hover:bg-red-500 hover:text-white transition-all uppercase tracking-widest border border-red-100"
                >
                  Supprimer la fiche
                </button>
                <div className="flex-1"></div>
                <div className="text-[9px] font-black text-gray-300 uppercase self-center">Archivé le {new Date(s.date_analyse).toLocaleDateString()}</div>
              </div>
            </div>
          </div>
        ))}

        {filteredSheep.length === 0 && (
          <div className="col-span-full py-32 text-center bg-white rounded-[4rem] border-2 border-dashed border-gray-100 shadow-inner">
            <span className="text-6xl block mb-6 opacity-20">🐏</span>
            <h3 className="text-xl font-black text-gray-400 uppercase tracking-[0.3em]">Inventaire Vide</h3>
            <p className="text-gray-300 mt-2 text-sm font-bold">Aucune donnée trouvée pour cet éleveur ou cette recherche.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Inventory;
