
import React, { useState, useRef } from 'react';
import { analyzeSheepImage } from '../services/geminiService';
import { AnalysisResult, Race, ReferenceObjectType, AnalysisMode, EtatPhysiologique, Dentition } from '../types';
import { STANDARDS_RACES, MORPHO_TRAITS, REFERENCE_OBJECTS, MAMMARY_TRAITS } from '../constants';

interface AnalysisModuleProps {
  onSave: (result: AnalysisResult, imageUrl: string, metadata: { tagId: string, age: any, ageType: 'mois'|'dentition', etat: EtatPhysiologique }) => void;
  isOffline: boolean;
}

const AnalysisModule: React.FC<AnalysisModuleProps> = ({ onSave, isOffline }) => {
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);
  const [image, setImage] = useState<string | null>(null);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('PROFILE');
  const [refObject, setRefObject] = useState<ReferenceObjectType>('AUCUN');
  const [selectedTraits, setSelectedTraits] = useState<string[]>([]);

  // Métadonnées manuelles
  const [metadata, setMetadata] = useState({
    tagId: '',
    ageType: 'mois' as 'mois' | 'dentition',
    ageValue: '' as string | number,
    etat: 'VIDE' as EtatPhysiologique
  });
  
  const [formData, setFormData] = useState<Partial<AnalysisResult>>({
    race: 'HAMRA',
    robe_couleur: '',
    measurements: {},
    mammary_traits: {},
    mammary_score: 0,
    feedback: ''
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const currentTraits = analysisMode === 'PROFILE' ? MORPHO_TRAITS : MAMMARY_TRAITS;

  // Initialiser les traits sélectionnés au changement de mode
  React.useEffect(() => {
    setSelectedTraits(currentTraits.map(t => t.id));
  }, [analysisMode]);

  const toggleTrait = (id: string) => {
    setSelectedTraits(prev => 
      prev.includes(id) ? prev.filter(t => t.id !== id) : [...prev, id]
    );
  };

  const handleAnalysis = async () => {
    if (!image) return;
    if (isOffline) {
      alert("L'analyse IA nécessite une connexion internet.");
      return;
    }
    setLoading(true);
    try {
      // On passe uniquement les traits sélectionnés au prompt via le contexte si nécessaire (ici géré par le prompt global)
      const result = await analyzeSheepImage(image, analysisMode, formData.race as Race, refObject);
      
      // Filtrer les résultats selon la sélection de l'utilisateur
      const filteredMeasurements = { ...result.measurements };
      const filteredMammary = { ...result.mammary_traits };
      
      setFormData(prev => ({
        ...prev,
        ...result,
        measurements: filteredMeasurements,
        mammary_traits: filteredMammary
      }));
    } catch (e) {
      alert("Erreur IA. Veuillez vérifier votre connexion et l'angle de la photo.");
    } finally {
      setLoading(false);
    }
  };

  const updateField = (category: 'measurements' | 'mammary_traits', traitId: string, val: any) => {
    setFormData(prev => ({
      ...prev,
      [category]: { ...(prev[category] as any), [traitId]: val }
    }));
  };

  const validateStep1 = () => {
    if (!metadata.tagId) return alert("Veuillez entrer un ID/N° de boucle.");
    if (!metadata.ageValue) return alert("Veuillez renseigner l'âge ou la dentition.");
    setStep(2);
  };

  if (step === 1) {
    return (
      <div className="max-w-2xl mx-auto animate-fadeIn">
        <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-gray-100">
          <div className="text-center mb-8">
            <span className="text-4xl bg-blue-50 p-4 rounded-3xl inline-block mb-4">🆔</span>
            <h2 className="text-2xl font-black text-gray-900">Nouvelle Analyse Biométrique</h2>
            <p className="text-gray-400 text-xs font-bold uppercase tracking-widest mt-1">Identification & État Physiologique</p>
          </div>

          <div className="space-y-6">
            <div>
              <label className="text-[10px] font-black text-gray-400 uppercase block mb-2 ml-2 tracking-widest">Boucle d'oreille / ID</label>
              <input 
                type="text"
                value={metadata.tagId}
                onChange={e => setMetadata({...metadata, tagId: e.target.value.toUpperCase()})}
                className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-bold text-gray-800 focus:ring-2 focus:ring-blue-500 outline-none placeholder:text-gray-300"
                placeholder="Ex: HAM-2024-001"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] font-black text-gray-400 uppercase block mb-2 ml-2 tracking-widest">Mode de Datation</label>
                <div className="flex bg-gray-100 p-1 rounded-2xl">
                  <button 
                    onClick={() => setMetadata({...metadata, ageType: 'mois', ageValue: ''})}
                    className={`flex-1 py-3 rounded-xl text-[10px] font-black transition-all ${metadata.ageType === 'mois' ? 'bg-white shadow-sm text-blue-900' : 'text-gray-400'}`}
                  >ÂGE (MOIS)</button>
                  <button 
                    onClick={() => setMetadata({...metadata, ageType: 'dentition', ageValue: ''})}
                    className={`flex-1 py-3 rounded-xl text-[10px] font-black transition-all ${metadata.ageType === 'dentition' ? 'bg-white shadow-sm text-blue-900' : 'text-gray-400'}`}
                  >DENTITION</button>
                </div>
              </div>
              <div>
                <label className="text-[10px] font-black text-gray-400 uppercase block mb-2 ml-2 tracking-widest">Valeur de l'âge</label>
                {metadata.ageType === 'mois' ? (
                  <input 
                    type="number"
                    value={metadata.ageValue}
                    onChange={e => setMetadata({...metadata, ageValue: parseInt(e.target.value)})}
                    className="w-full bg-gray-50 border-none rounded-2xl px-6 py-3 font-bold text-gray-800 outline-none"
                    placeholder="Nb de mois"
                  />
                ) : (
                  <select 
                    value={metadata.ageValue}
                    onChange={e => setMetadata({...metadata, ageValue: e.target.value})}
                    className="w-full bg-gray-50 border-none rounded-2xl px-6 py-3 font-bold text-gray-800 outline-none"
                  >
                    <option value="">Sélectionner...</option>
                    <option value="0_DENT">0 dent (Agneau)</option>
                    <option value="2_DENTS">2 dents (Lait)</option>
                    <option value="4_DENTS">4 dents</option>
                    <option value="6_DENTS">6 dents</option>
                    <option value="8_DENTS">8 dents (Adulte)</option>
                  </select>
                )}
              </div>
            </div>

            <div>
              <label className="text-[10px] font-black text-gray-400 uppercase block mb-2 ml-2 tracking-widest">État Physiologique Actuel</label>
              <select 
                value={metadata.etat}
                onChange={e => setMetadata({...metadata, etat: e.target.value as EtatPhysiologique})}
                className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-bold text-gray-800 outline-none"
              >
                <option value="VIDE">Vierge / Vide</option>
                <option value="GESTANTE_DEBUT">Gestation (Début)</option>
                <option value="GESTANTE_FIN">Gestation (Terme)</option>
                <option value="ALLAITANTE">Allaitante / En traite</option>
                <option value="TARIE">Phase de Tarissement</option>
                <option value="EN_CROISSANCE">Agneau en croissance</option>
              </select>
            </div>

            <button 
              onClick={validateStep1}
              className="w-full bg-[#1a237e] text-white py-5 rounded-3xl font-black text-sm shadow-xl hover:bg-blue-800 transition-all mt-4 flex items-center justify-center gap-3"
            >
              Étape suivante : Capture IA ➔
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fadeIn pb-24">
      {/* Header avec sélecteur de mode */}
      <header className="bg-white p-6 rounded-[2.5rem] shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex items-center gap-4">
          <button onClick={() => setStep(1)} className="p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-all text-xl shadow-sm">⬅</button>
          <div>
            <h2 className="text-xl font-black text-gray-900 tracking-tight leading-none">Analyse de l'Animal</h2>
            <p className="text-[10px] font-black text-blue-600 uppercase tracking-widest mt-1">🆔 {metadata.tagId}</p>
          </div>
        </div>

        <div className="flex bg-gray-100 p-1.5 rounded-3xl w-full md:w-auto">
          <button 
            onClick={() => setAnalysisMode('PROFILE')}
            className={`flex-1 md:flex-none px-8 py-3 rounded-2xl text-[10px] font-black uppercase transition-all flex items-center justify-center gap-2 ${analysisMode === 'PROFILE' ? 'bg-white shadow-md text-[#1a237e]' : 'text-gray-400'}`}
          >
            📏 Corps (Profil)
          </button>
          <button 
            onClick={() => setAnalysisMode('MAMMARY')}
            className={`flex-1 md:flex-none px-8 py-3 rounded-2xl text-[10px] font-black uppercase transition-all flex items-center justify-center gap-2 ${analysisMode === 'MAMMARY' ? 'bg-white shadow-md text-pink-700' : 'text-gray-400'}`}
          >
            🥛 Mamelles (Arrière)
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Colonne de gauche : Capture et Options */}
        <div className="lg:col-span-4 space-y-6">
          <section className="bg-white p-6 rounded-[2.5rem] border border-gray-100 shadow-sm">
            <h3 className="text-[10px] font-black text-gray-400 uppercase mb-4 tracking-widest">1. Source de la Photo</h3>
            
            <div className="grid grid-cols-2 gap-3 mb-4">
              <button 
                onClick={() => {
                  fileInputRef.current?.setAttribute('capture', 'environment');
                  fileInputRef.current?.click();
                }}
                className="bg-blue-50 hover:bg-blue-100 p-4 rounded-2xl flex flex-col items-center gap-2 transition-all border border-blue-100/50"
              >
                <span className="text-2xl">📸</span>
                <span className="text-[9px] font-black text-blue-800 uppercase">Appareil</span>
              </button>
              <button 
                onClick={() => {
                  fileInputRef.current?.removeAttribute('capture');
                  fileInputRef.current?.click();
                }}
                className="bg-purple-50 hover:bg-purple-100 p-4 rounded-2xl flex flex-col items-center gap-2 transition-all border border-purple-100/50"
              >
                <span className="text-2xl">🖼️</span>
                <span className="text-[9px] font-black text-purple-800 uppercase">Galerie</span>
              </button>
            </div>

            <div className="aspect-square bg-gray-50 border-2 border-dashed border-gray-200 rounded-[2rem] flex flex-col items-center justify-center overflow-hidden relative group">
              {image ? (
                <img src={image} className="w-full h-full object-cover" alt="Sheep" />
              ) : (
                <div className="text-center p-6">
                  <span className="text-4xl opacity-20 block mb-4">📸</span>
                  <p className="text-[10px] font-black text-gray-300 uppercase tracking-widest">Aucune image sélectionnée</p>
                </div>
              )}
            </div>
            
            <input type="file" ref={fileInputRef} onChange={e => {
              const file = e.target.files?.[0];
              if(file) {
                const r = new FileReader();
                r.onload = () => setImage(r.result as string);
                r.readAsDataURL(file);
              }
            }} className="hidden" accept="image/*" />
            
            <button 
              onClick={handleAnalysis} 
              disabled={loading || !image || isOffline}
              className={`w-full mt-6 py-5 rounded-3xl font-black text-xs text-white shadow-2xl transition-all flex items-center justify-center gap-3 ${loading ? 'bg-gray-400 animate-pulse' : (analysisMode === 'MAMMARY' ? 'bg-pink-600' : 'bg-[#1a237e]')}`}
            >
              {loading ? (
                <>🌀 CALCUL IA EN COURS...</>
              ) : (
                <>🔍 ANALYSER MAINTENANT</>
              )}
            </button>
          </section>

          <section className="bg-white p-6 rounded-[2.5rem] border border-gray-100 shadow-sm">
            <h3 className="text-[10px] font-black text-gray-400 uppercase mb-4 tracking-widest">2. Calibration (Optionnel)</h3>
            <div className="grid grid-cols-1 gap-2">
              {REFERENCE_OBJECTS.map(obj => (
                <button
                  key={obj.id}
                  onClick={() => setRefObject(obj.id)}
                  className={`flex items-center gap-3 p-3 rounded-xl border transition-all text-left ${refObject === obj.id ? 'bg-blue-600 border-blue-600 text-white' : 'bg-gray-50 border-transparent text-gray-600 hover:bg-gray-100'}`}
                >
                  <span className="text-xl">{obj.icon}</span>
                  <div>
                    <p className="text-[10px] font-black leading-none">{obj.label}</p>
                    <p className="text-[8px] font-bold opacity-70 mt-1 uppercase">{obj.dimension}</p>
                  </div>
                </button>
              ))}
            </div>
          </section>
        </div>

        {/* Colonne de droite : Résultats et sélection des traits */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-white p-8 rounded-[3rem] border border-gray-100 shadow-xl">
            <div className="flex justify-between items-center mb-8 pb-4 border-b border-gray-50">
               <h3 className="text-lg font-black text-gray-900 tracking-tight">Données Biométriques : {analysisMode === 'PROFILE' ? 'Profil Corporel' : 'Examen Mammaire'}</h3>
               <div className="flex items-center gap-2">
                 <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                 <span className="text-[10px] font-black text-green-600 uppercase">IA Active</span>
               </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div>
                <label className="text-[10px] font-black text-gray-400 uppercase block mb-2 ml-2 tracking-widest">Standard de Race</label>
                <select 
                  value={formData.race} 
                  onChange={e => setFormData({...formData, race: e.target.value as Race})}
                  className="w-full bg-gray-50 p-4 rounded-2xl font-bold text-sm border-none outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {Object.keys(STANDARDS_RACES).map(r => <option key={r} value={r}>{STANDARDS_RACES[r].nom_complet}</option>)}
                </select>
              </div>
              
              {analysisMode === 'MAMMARY' && (
                <div className="bg-pink-50/30 p-4 rounded-3xl border border-pink-100 flex items-center justify-between">
                   <div>
                     <p className="text-[9px] font-black text-pink-400 uppercase tracking-widest">Score Mammaire Global</p>
                     <p className="text-[10px] text-pink-300 italic">Basé sur la conformation</p>
                   </div>
                   <input 
                     type="number" step="0.5" max="10" min="0"
                     value={formData.mammary_score || 0}
                     onChange={e => setFormData({...formData, mammary_score: parseFloat(e.target.value)})}
                     className="bg-white border-2 border-pink-200 w-20 p-2 rounded-xl text-center font-black text-pink-900 text-lg outline-none"
                   />
                </div>
              )}
            </div>

            <div className="space-y-6">
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest px-2">Liste des Caractères à Mesurer / Valider</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {currentTraits.map(trait => {
                  const category = analysisMode === 'PROFILE' ? 'measurements' : 'mammary_traits';
                  const value = (formData[category] as any)?.[trait.id] || '';
                  const isSelected = selectedTraits.includes(trait.id);

                  return (
                    <div 
                      key={trait.id} 
                      className={`p-4 rounded-[1.5rem] border-2 transition-all ${isSelected ? (analysisMode === 'MAMMARY' ? 'border-pink-200 bg-pink-50/20' : 'border-blue-100 bg-blue-50/10') : 'border-gray-50 bg-gray-50/50 opacity-60'}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <input 
                            type="checkbox" 
                            checked={isSelected} 
                            onChange={() => toggleTrait(trait.id)}
                            className="w-5 h-5 rounded-lg border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className={`text-[10px] font-black uppercase tracking-tight ${isSelected ? 'text-gray-900' : 'text-gray-400'}`}>{trait.label}</span>
                        </div>
                        {trait.unit && <span className="text-[8px] font-black text-blue-400 bg-blue-50 px-2 py-1 rounded-full">{trait.unit}</span>}
                      </div>

                      {trait.type === 'quantitative' ? (
                        <div className="relative">
                          <input 
                            type="number" step="0.1" value={value} 
                            onChange={e => updateField(category, trait.id, parseFloat(e.target.value))}
                            disabled={!isSelected}
                            className={`w-full bg-white border border-gray-200 rounded-xl p-3 font-black text-sm outline-none transition-all ${!isSelected ? 'bg-gray-100 text-gray-300' : 'text-gray-900 focus:border-blue-500'}`} 
                          />
                        </div>
                      ) : (
                        <select 
                          value={value} 
                          onChange={e => updateField(category, trait.id, e.target.value)}
                          disabled={!isSelected}
                          className={`w-full bg-white border border-gray-200 rounded-xl p-3 font-black text-sm outline-none transition-all ${!isSelected ? 'bg-gray-100 text-gray-300' : 'text-gray-900 focus:border-blue-500'}`}
                        >
                          <option value="">Non évalué</option>
                          {trait.options?.map(o => <option key={o} value={o}>{o}</option>)}
                        </select>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-10 pt-8 border-t border-gray-50 flex flex-col md:flex-row gap-4">
               <div className="flex-1 bg-gray-50 p-6 rounded-2xl border border-gray-100">
                  <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Observations de l'Expert IA</p>
                  <textarea 
                    value={formData.feedback}
                    onChange={e => setFormData({...formData, feedback: e.target.value})}
                    className="w-full bg-transparent border-none text-xs font-medium text-gray-700 outline-none resize-none h-20"
                    placeholder="L'analyse automatique affichera ses commentaires ici..."
                  />
               </div>
               
               <button 
                onClick={() => onSave(formData as AnalysisResult, image || '', { 
                  tagId: metadata.tagId, 
                  age: metadata.ageValue, 
                  ageType: metadata.ageType, 
                  etat: metadata.etat 
                })}
                className={`md:w-64 text-white py-5 rounded-[2rem] font-black text-xs shadow-2xl transition-all uppercase tracking-widest ${analysisMode === 'MAMMARY' ? 'bg-pink-700 hover:bg-pink-800' : 'bg-green-600 hover:bg-green-700'}`}
              >
                ✅ Finaliser & Archiver
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisModule;
