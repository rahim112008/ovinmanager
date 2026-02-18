
import React, { useState, useEffect } from 'react';
import { db } from '../services/database';
import { ProductionRecord, Sheep } from '../types';

const ProductionModule: React.FC<{ userId: string, breederId: string }> = ({ userId, breederId }) => {
  const [records, setRecords] = useState<ProductionRecord[]>([]);
  const [sheepList, setSheepList] = useState<Sheep[]>([]);
  const [newRecord, setNewRecord] = useState({ 
    sheepId: '', 
    quantite: 0,
    mg: 0,
    mp: 0,
    lactose: 0
  });

  useEffect(() => { loadData(); }, [breederId]);

  const loadData = async () => {
    const r = await db.getProduction(userId, breederId);
    const s = await db.getSheep(userId, breederId);
    setRecords(r);
    setSheepList(s.filter(x => x.sexe === 'F'));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRecord.sheepId) return;

    await db.addProduction({
      id: Math.random().toString(36).substr(2, 9),
      userId: userId,
      breederId: breederId,
      sheepId: newRecord.sheepId,
      date: new Date().toISOString(),
      quantite_litres: newRecord.quantite,
      taux_butyreux: newRecord.mg,
      taux_proteique: newRecord.mp,
      lactose: newRecord.lactose
    });
    setNewRecord({ sheepId: '', quantite: 0, mg: 0, mp: 0, lactose: 0 });
    loadData();
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <header>
        <h2 className="text-3xl font-black text-gray-900 tracking-tight">Production Laitière</h2>
        <p className="text-gray-500 font-medium">Enregistrement par traite individuelle.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold mb-4">🥛 Nouvelle Traite</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <select 
              value={newRecord.sheepId}
              onChange={e => setNewRecord({...newRecord, sheepId: e.target.value})}
              className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
            >
              <option value="">Sélectionner Brebis...</option>
              {sheepList.map(s => <option key={s.id} value={s.id}>{s.nom} ({s.tagId})</option>)}
            </select>
            <input 
              type="number" step="0.1" placeholder="Quantité (L)"
              value={newRecord.quantite || ''}
              onChange={e => setNewRecord({...newRecord, quantite: parseFloat(e.target.value)})}
              className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm"
            />
            <div className="grid grid-cols-3 gap-2">
              <input type="number" step="0.1" placeholder="MG %" value={newRecord.mg || ''} onChange={e => setNewRecord({...newRecord, mg: parseFloat(e.target.value)})} className="bg-gray-50 p-2 rounded-xl text-xs" />
              <input type="number" step="0.1" placeholder="MP %" value={newRecord.mp || ''} onChange={e => setNewRecord({...newRecord, mp: parseFloat(e.target.value)})} className="bg-gray-50 p-2 rounded-xl text-xs" />
              <input type="number" step="0.1" placeholder="Lactose" value={newRecord.lactose || ''} onChange={e => setNewRecord({...newRecord, lactose: parseFloat(e.target.value)})} className="bg-gray-50 p-2 rounded-xl text-xs" />
            </div>
            <button className="w-full bg-blue-900 text-white py-3 rounded-xl font-bold">Enregistrer</button>
          </form>
        </div>

        <div className="lg:col-span-2 bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 text-[10px] font-black uppercase text-gray-400">
              <tr>
                <th className="px-6 py-4">Brebis</th>
                <th className="px-6 py-4">Litres</th>
                <th className="px-6 py-4">Qualité</th>
              </tr>
            </thead>
            <tbody>
              {records.slice().reverse().map(r => {
                const animal = sheepList.find(s => s.id === r.sheepId);
                return (
                  <tr key={r.id} className="border-t border-gray-50">
                    <td className="px-6 py-4">
                      <p className="text-sm font-bold">{animal?.nom || 'Inconnu'}</p>
                      <p className="text-[9px] text-gray-400">{animal?.tagId}</p>
                    </td>
                    <td className="px-6 py-4 text-sm font-black text-blue-800">{r.quantite_litres}L</td>
                    <td className="px-6 py-4 text-xs font-mono">{r.taux_butyreux}% | {r.taux_proteique}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ProductionModule;
