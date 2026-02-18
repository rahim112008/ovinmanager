
import React, { useState, useEffect } from 'react';
import { db } from '../services/database';
import { HealthRecord, Sheep } from '../types';

// Fix: Add breederId prop to support multi-tenant filtering
const HealthModule: React.FC<{ userId: string, breederId: string }> = ({ userId, breederId }) => {
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [sheepList, setSheepList] = useState<Sheep[]>([]);
  const [form, setForm] = useState<Partial<HealthRecord>>({ type: 'VACCIN', description: '', produit: '' });

  // Fix: Add breederId to dependency array
  useEffect(() => {
    loadData();
  }, [userId, breederId]);

  const loadData = async () => {
    // Fix: Pass breederId to getHealth and getSheep for correct filtering
    const r = await db.getHealth(userId, breederId);
    const s = await db.getSheep(userId, breederId);
    setRecords(r);
    setSheepList(s);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.sheepId || !form.description) return;

    // Fix: Include breederId in addHealth record as required by HealthRecord type
    await db.addHealth({
      id: Math.random().toString(36).substr(2, 9),
      userId: userId,
      breederId: breederId,
      sheepId: form.sheepId as string,
      date: new Date().toISOString(),
      type: form.type as any,
      description: form.description as string,
      produit: form.produit
    });
    setForm({ type: 'VACCIN', description: '', produit: '' });
    loadData();
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <header>
        <h2 className="text-3xl font-black text-gray-900 tracking-tight">Carnet Sanitaire Numérique</h2>
        <p className="text-gray-500 font-medium">Suivez les vaccins, traitements et la santé globale de votre troupeau.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">🏥 Nouveau Soin</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-black text-gray-400 uppercase mb-1">Animal</label>
              <select 
                value={form.sheepId || ''}
                onChange={e => setForm({...form, sheepId: e.target.value})}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
              >
                <option value="">Sélectionner...</option>
                {sheepList.map(s => <option key={s.id} value={s.id}>{s.nom}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-black text-gray-400 uppercase mb-1">Type d'intervention</label>
              <select 
                value={form.type}
                onChange={e => setForm({...form, type: e.target.value as any})}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
              >
                <option value="VACCIN">Vaccination</option>
                <option value="TRAITEMENT">Traitement curatif</option>
                <option value="DEPARASITAGE">Déparasitage</option>
                <option value="EXAMEN">Examen de routine</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-black text-gray-400 uppercase mb-1">Produit / Médicament</label>
              <input 
                type="text" 
                value={form.produit || ''}
                onChange={e => setForm({...form, produit: e.target.value})}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
                placeholder="Ex: Ivermectine..."
              />
            </div>
            <div>
              <label className="block text-xs font-black text-gray-400 uppercase mb-1">Notes / Diagnostic</label>
              <textarea 
                value={form.description || ''}
                onChange={e => setForm({...form, description: e.target.value})}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
                rows={3}
              />
            </div>
            <button className="w-full bg-[#8B0000] text-white py-3 rounded-xl font-bold hover:bg-red-900 transition-all">
              Valider l'intervention
            </button>
          </form>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {records.slice().reverse().map(r => {
            const animal = sheepList.find(s => s.id === r.sheepId);
            return (
              <div key={r.id} className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 flex items-start gap-4">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl shrink-0 ${
                  r.type === 'VACCIN' ? 'bg-green-50 text-green-600' :
                  r.type === 'TRAITEMENT' ? 'bg-red-50 text-red-600' :
                  'bg-blue-50 text-blue-600'
                }`}>
                  {r.type === 'VACCIN' ? '💉' : r.type === 'TRAITEMENT' ? '💊' : '📋'}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-gray-900">{r.type} - {animal?.nom}</h4>
                      <p className="text-xs text-gray-400 font-bold">{new Date(r.date).toLocaleDateString()}</p>
                    </div>
                    {r.produit && <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-[10px] font-black uppercase">{r.produit}</span>}
                  </div>
                  <p className="mt-3 text-sm text-gray-600 leading-relaxed">{r.description}</p>
                </div>
              </div>
            );
          })}
          {records.length === 0 && (
            <div className="bg-white p-12 rounded-3xl text-center text-gray-400 italic">Historique vide.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthModule;
