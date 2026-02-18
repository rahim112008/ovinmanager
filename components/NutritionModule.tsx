
import React, { useState, useEffect } from 'react';
import { db } from '../services/database';
import { NutritionRecord, Sheep, IngredientPrice } from '../types';
import { ALGERIAN_FEED_INGREDIENTS } from '../constants';
import { GoogleGenAI } from "@google/genai";

const NutritionModule: React.FC<{ userId: string, breederId: string }> = ({ userId, breederId }) => {
  const [records, setRecords] = useState<NutritionRecord[]>([]);
  const [sheepList, setSheepList] = useState<Sheep[]>([]);
  const [prices, setPrices] = useState<IngredientPrice[]>([]);
  const [activeSubTab, setActiveSubTab] = useState<'daily' | 'prices' | 'calculator'>('daily');
  const [loadingIA, setLoadingIA] = useState(false);

  // Formulaire Ration
  const [rationForm, setRationForm] = useState({
    sheepId: '',
    objectif: 'ENTRETIEN' as any,
    selectedIngredients: [] as { name: string, quantity_kg: number }[]
  });

  useEffect(() => {
    loadData();
  }, [userId, breederId]);

  const loadData = async () => {
    const r = await db.getNutrition(userId, breederId);
    const s = await db.getSheep(userId, breederId);
    const p = await db.getPrices(breederId);
    
    setRecords(r);
    setSheepList(s);
    
    if (p.length === 0) {
      // Initialiser les prix par défaut si vide
      const initialPrices = ALGERIAN_FEED_INGREDIENTS.map(f => ({
        id: `${breederId}-${f.id}`,
        breederId,
        name: f.name,
        pricePerUnit: f.defaultPrice,
        category: f.category as any
      }));
      for (const ip of initialPrices) await db.savePrice(ip);
      setPrices(initialPrices);
    } else {
      setPrices(p);
    }
  };

  const handleUpdatePrice = async (id: string, newPrice: number) => {
    const item = prices.find(p => p.id === id);
    if (item) {
      const updated = { ...item, pricePerUnit: newPrice };
      await db.savePrice(updated);
      setPrices(prices.map(p => p.id === id ? updated : p));
    }
  };

  const handleAddIngredientToRation = (name: string) => {
    if (!rationForm.selectedIngredients.find(i => i.name === name)) {
      setRationForm({
        ...rationForm,
        selectedIngredients: [...rationForm.selectedIngredients, { name, quantity_kg: 0 }]
      });
    }
  };

  const handleUpdateIngredientQty = (name: string, qty: number) => {
    setRationForm({
      ...rationForm,
      selectedIngredients: rationForm.selectedIngredients.map(i => i.name === name ? { ...i, quantity_kg: qty } : i)
    });
  };

  const calculateTotalCost = () => {
    return rationForm.selectedIngredients.reduce((total, item) => {
      const p = prices.find(pr => pr.name === item.name)?.pricePerUnit || 0;
      return total + (p * item.quantity_kg);
    }, 0);
  };

  const handleSaveRation = async () => {
    if (!rationForm.sheepId || rationForm.selectedIngredients.length === 0) return;
    
    const ingredientsWithCost = rationForm.selectedIngredients.map(i => {
      const p = prices.find(pr => pr.name === i.name)?.pricePerUnit || 0;
      return { ...i, cost: p * i.quantity_kg };
    });

    const totalCost = calculateTotalCost();

    await db.addNutrition({
      id: Math.random().toString(36).substr(2, 9),
      userId,
      breederId,
      sheepId: rationForm.sheepId,
      date: new Date().toISOString(),
      rationName: `Ration ${rationForm.objectif}`,
      ingredients: ingredientsWithCost,
      totalCost,
      objectif: rationForm.objectif
    });

    setRationForm({ sheepId: '', objectif: 'ENTRETIEN', selectedIngredients: [] });
    setActiveSubTab('daily');
    loadData();
  };

  const askIANutrition = async () => {
    setLoadingIA(true);
    const animal = sheepList.find(s => s.id === rationForm.sheepId);
    if (!animal) return;

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const prompt = `En tant qu'expert en nutrition ovine algérienne, suggère une ration optimale pour une brebis de race ${animal.race}, poids ${animal.poids}kg, état ${animal.etat_physiologique}. 
      Objectif: ${rationForm.objectif}.
      Aliments disponibles et prix (DA/kg): ${prices.map(p => `${p.name}: ${p.pricePerUnit}DA`).join(', ')}.
      Donne uniquement les quantités journalières recommandées en KG pour chaque ingrédient.
      Réponds en JSON uniquement avec un tableau d'objets {name: string, quantity_kg: number}.`;

      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: prompt
      });

      const suggested = JSON.parse(response.text);
      setRationForm({ ...rationForm, selectedIngredients: suggested });
    } catch (e) {
      alert("Erreur IA Nutrition. Veuillez saisir manuellement.");
    } finally {
      setLoadingIA(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn pb-20">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-black text-gray-900 tracking-tight">Expert Nutrition Ovine</h2>
          <p className="text-gray-500 font-medium">Gestion des coûts et optimisation des rations algériennes.</p>
        </div>
        <div className="flex bg-white p-1 rounded-2xl shadow-sm border border-gray-100">
          <button onClick={() => setActiveSubTab('daily')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase transition-all ${activeSubTab === 'daily' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400'}`}>Suivi Consommation</button>
          <button onClick={() => setActiveSubTab('calculator')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase transition-all ${activeSubTab === 'calculator' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400'}`}>Calculateur / IA</button>
          <button onClick={() => setActiveSubTab('prices')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase transition-all ${activeSubTab === 'prices' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400'}`}>Prix Marché</button>
        </div>
      </header>

      {activeSubTab === 'prices' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fadeIn">
          {prices.map(p => (
            <div key={p.id} className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex justify-between items-center">
              <div>
                <p className="text-[10px] font-black text-blue-400 uppercase">{p.category}</p>
                <h4 className="font-bold text-gray-900">{p.name}</h4>
              </div>
              <div className="text-right">
                <input 
                  type="number"
                  value={p.pricePerUnit}
                  onChange={(e) => handleUpdatePrice(p.id, parseFloat(e.target.value))}
                  className="w-20 bg-gray-50 border-none text-right font-black text-blue-900 rounded-lg p-2 outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-[10px] font-bold text-gray-400 ml-1 uppercase">DA/kg</span>
              </div>
            </div>
          ))}
          <div className="md:col-span-2 lg:col-span-3 bg-blue-50 p-6 rounded-3xl border border-blue-100">
            <p className="text-xs text-blue-800 font-medium italic">💡 Astuce : 1 Quintal = 100 kg. Si l'orge est à 6000 DA le quintal, saisissez 60 DA ici.</p>
          </div>
        </div>
      )}

      {activeSubTab === 'calculator' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-fadeIn">
          <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-gray-100 space-y-6">
            <h3 className="text-lg font-black text-gray-900 flex items-center gap-2">🧮 Formulation de la Ration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-black text-gray-400 uppercase ml-2 block mb-1">Choix de l'animal</label>
                <select 
                  value={rationForm.sheepId}
                  onChange={e => setRationForm({...rationForm, sheepId: e.target.value})}
                  className="w-full bg-gray-50 p-4 rounded-2xl font-bold border-none outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">-- Sélectionner l'animal --</option>
                  {sheepList.map(s => <option key={s.id} value={s.id}>{s.nom} ({s.tagId} - {s.etat_physiologique})</option>)}
                </select>
              </div>

              <div>
                <label className="text-[10px] font-black text-gray-400 uppercase ml-2 block mb-1">Objectif Zootechnique</label>
                <select 
                  value={rationForm.objectif}
                  onChange={e => setRationForm({...rationForm, objectif: e.target.value as any})}
                  className="w-full bg-gray-50 p-4 rounded-2xl font-bold border-none outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ENTRETIEN">Entretien / Repos</option>
                  <option value="ENGRAISSEMENT">Engraissement (Viande)</option>
                  <option value="GESTATION">Gestation (Fin de terme)</option>
                  <option value="LACTATION">Lactation (Production Lait)</option>
                </select>
              </div>

              <div className="pt-4">
                <label className="text-[10px] font-black text-gray-400 uppercase ml-2 block mb-2">Ajouter Ingrédients du Marché</label>
                <div className="flex flex-wrap gap-2">
                  {prices.map(p => (
                    <button 
                      key={p.id}
                      onClick={() => handleAddIngredientToRation(p.name)}
                      className="px-3 py-2 bg-gray-100 hover:bg-blue-100 rounded-xl text-[10px] font-black text-gray-600 transition-all"
                    >+ {p.name}</button>
                  ))}
                </div>
              </div>

              {rationForm.selectedIngredients.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-gray-50">
                  {rationForm.selectedIngredients.map(item => (
                    <div key={item.name} className="flex items-center justify-between gap-4 bg-gray-50 p-3 rounded-2xl">
                      <span className="text-xs font-bold text-gray-700 flex-1">{item.name}</span>
                      <div className="flex items-center gap-2">
                        <input 
                          type="number" step="0.1"
                          value={item.quantity_kg}
                          onChange={(e) => handleUpdateIngredientQty(item.name, parseFloat(e.target.value))}
                          className="w-20 bg-white border border-gray-200 rounded-lg p-2 text-right font-black text-blue-900"
                        />
                        <span className="text-[10px] font-bold text-gray-400 uppercase">kg</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-4 pt-6">
              <button 
                onClick={askIANutrition}
                disabled={!rationForm.sheepId || loadingIA}
                className="flex-1 bg-purple-600 text-white py-4 rounded-2xl font-black text-xs shadow-lg hover:bg-purple-700 transition-all flex items-center justify-center gap-2"
              >
                {loadingIA ? 'CONSEIL IA...' : '✨ SUGGESTION IA'}
              </button>
              <button 
                onClick={handleSaveRation}
                className="flex-1 bg-green-600 text-white py-4 rounded-2xl font-black text-xs shadow-lg hover:bg-green-700 transition-all"
              >
                ✅ VALIDER RATION
              </button>
            </div>
          </div>

          <div className="space-y-6">
             <div className="bg-[#1a237e] text-white p-8 rounded-[2.5rem] shadow-2xl relative overflow-hidden">
                <div className="relative z-10">
                  <p className="text-blue-200 text-[10px] font-black uppercase tracking-widest mb-2">Estimation Coût de Revient</p>
                  <h3 className="text-5xl font-black">{calculateTotalCost().toFixed(2)} <span className="text-xl">DA</span></h3>
                  <p className="text-blue-100 opacity-60 text-xs mt-2 uppercase font-bold italic">Coût par animal / par jour</p>
                </div>
                <div className="absolute right-[-20px] bottom-[-20px] opacity-10 text-[120px] pointer-events-none">💰</div>
             </div>

             <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100">
                <h4 className="font-black text-gray-900 mb-4 uppercase text-sm tracking-tight">Répartition de la Ration</h4>
                <div className="space-y-3">
                  {rationForm.selectedIngredients.map(item => {
                    const cost = (prices.find(p => p.name === item.name)?.pricePerUnit || 0) * item.quantity_kg;
                    const percent = calculateTotalCost() > 0 ? (cost / calculateTotalCost() * 100).toFixed(0) : 0;
                    return (
                      <div key={item.name} className="space-y-1">
                        <div className="flex justify-between text-[10px] font-black uppercase">
                          <span>{item.name}</span>
                          <span>{percent}%</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-600" style={{ width: `${percent}%` }}></div>
                        </div>
                      </div>
                    );
                  })}
                  {rationForm.selectedIngredients.length === 0 && <p className="text-center text-gray-400 text-xs py-10 italic">Aucun ingrédient sélectionné</p>}
                </div>
             </div>
          </div>
        </div>
      )}

      {activeSubTab === 'daily' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
             {records.slice().reverse().map(r => {
               const animal = sheepList.find(s => s.id === r.sheepId);
               return (
                 <div key={r.id} className="bg-white p-6 rounded-[2.5rem] border border-gray-100 shadow-sm relative group">
                    <div className="absolute top-6 right-6 text-xs font-black text-green-600 bg-green-50 px-3 py-1 rounded-full">{r.totalCost.toFixed(1)} DA/j</div>
                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">{new Date(r.date).toLocaleDateString()}</p>
                    <h4 className="font-black text-gray-900 mb-3">{animal?.nom || 'Inconnu'} <span className="text-[10px] opacity-40">({r.objectif})</span></h4>
                    <div className="space-y-2">
                       {r.ingredients.map((ing, idx) => (
                         <div key={idx} className="flex justify-between text-xs">
                           <span className="text-gray-500">{ing.name}</span>
                           <span className="font-bold text-gray-800">{ing.quantity_kg} kg</span>
                         </div>
                       ))}
                    </div>
                 </div>
               );
             })}
             {records.length === 0 && (
               <div className="md:col-span-3 py-20 text-center bg-white rounded-[3rem] border-2 border-dashed border-gray-100">
                  <span className="text-4xl mb-4 block">🌾</span>
                  <p className="text-gray-400 font-bold uppercase text-xs tracking-widest">Aucune ration archivée pour cet éleveur.</p>
               </div>
             )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NutritionModule;
