
import React, { useState, useEffect } from 'react';
import { db } from '../services/database';
import { ReproductionRecord, Sheep } from '../types';

// Fix: Add breederId prop to support multi-tenant filtering
const ReproductionModule: React.FC<{ userId: string, breederId: string }> = ({ userId, breederId }) => {
  const [records, setRecords] = useState<ReproductionRecord[]>([]);
  const [females, setFemales] = useState<Sheep[]>([]);
  const [form, setForm] = useState({ sheepId: '', date_saillie: '' });

  // Fix: Add breederId to dependency array
  useEffect(() => {
    loadData();
  }, [userId, breederId]);

  const loadData = async () => {
    // Fix: Pass breederId to getReproduction and getSheep for correct filtering
    const r = await db.getReproduction(userId, breederId);
    const s = await db.getSheep(userId, breederId);
    setRecords(r);
    setFemales(s.filter(x => x.sexe === 'F'));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.sheepId || !form.date_saillie) return;

    const saillie = new Date(form.date_saillie);
    const agnelage = new Date(saillie);
    agnelage.setDate(agnelage.getDate() + 150); // Gestation ~150 days

    // Fix: Include breederId in addReproduction record as required by ReproductionRecord type
    await db.addReproduction({
      id: Math.random().toString(36).substr(2, 9),
      userId: userId,
      breederId: breederId,
      sheepId: form.sheepId,
      date_saillie: form.date_saillie,
      date_agnelage_prevue: agnelage.toISOString(),
      statut: 'GESTATION'
    });
    setForm({ sheepId: '', date_saillie: '' });
    loadData();
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <header>
        <h2 className="text-3xl font-black text-gray-900 tracking-tight">Suivi de la Reproduction</h2>
        <p className="text-gray-500 font-medium">Gérez les cycles de reproduction et prévoyez les agnelages.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 h-fit">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">🐣 Déclarer une Saillie</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-black text-gray-400 uppercase mb-1">Brebis concernée</label>
              <select 
                value={form.sheepId}
                onChange={e => setForm({...form, sheepId: e.target.value})}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
              >
                <option value="">Sélectionner...</option>
                {females.map(s => <option key={s.id} value={s.id}>{s.nom}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-black text-gray-400 uppercase mb-1">Date de la saillie</label>
              <input 
                type="date"
                value={form.date_saillie}
                onChange={e => setForm({...form, date_saillie: e.target.value})}
                className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
              />
            </div>
            <button className="w-full bg-purple-700 text-white py-3 rounded-xl font-bold hover:bg-purple-800 transition-all">
              Enregistrer Gestation
            </button>
          </form>
        </div>

        <div className="lg:col-span-2 bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100">
            <h3 className="font-bold">Calendrier des Agnelages Prévisibles</h3>
          </div>
          <div className="p-6 space-y-4">
            {records.map(r => {
              const animal = females.find(f => f.id === r.sheepId);
              const daysLeft = Math.ceil((new Date(r.date_agnelage_prevue).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
              
              return (
                <div key={r.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl border border-gray-200">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center font-black">
                      {animal?.nom.charAt(0)}
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-900">{animal?.nom}</h4>
                      <p className="text-xs text-gray-500 italic">Prévu le: {new Date(r.date_agnelage_prevue).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-black px-3 py-1 rounded-full uppercase ${daysLeft > 0 ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'}`}>
                      {daysLeft > 0 ? `J-${daysLeft}` : '⚠️ Terme dépassé'}
                    </span>
                  </div>
                </div>
              );
            })}
            {records.length === 0 && (
              <p className="text-center py-10 text-gray-400 italic">Aucune gestation en cours.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReproductionModule;
