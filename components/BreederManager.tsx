
import React, { useState, useEffect } from 'react';
import { db } from '../services/database';
import { Breeder } from '../types';

interface BreederManagerProps {
  userId: string;
  onRefresh: () => void;
}

const BreederManager: React.FC<BreederManagerProps> = ({ userId, onRefresh }) => {
  const [breeders, setBreeders] = useState<Breeder[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ nom: '', wilaya: '', telephone: '' });

  useEffect(() => { load(); }, []);

  const load = async () => {
    const list = await db.getBreeders(userId);
    setBreeders(list);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nom) return;
    const newBreeder: Breeder = {
      id: `BRD-${Math.random().toString(36).substr(2, 6).toUpperCase()}`,
      userId,
      nom: form.nom,
      wilaya: form.wilaya,
      telephone: form.telephone,
      dateCreation: new Date().toISOString()
    };
    await db.saveBreeder(newBreeder);
    setForm({ nom: '', wilaya: '', telephone: '' });
    setShowAdd(false);
    load();
    onRefresh();
  };

  const handleDelete = async (id: string) => {
    if (confirm("Supprimer cet éleveur ? Attention : ses animaux resteront mais ne seront plus accessibles via ce profil.")) {
      await db.deleteBreeder(id);
      load();
      onRefresh();
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-black text-gray-900 tracking-tight">Gestion des Éleveurs</h2>
          <p className="text-gray-500 font-medium">Liste de vos clients et exploitations suivies.</p>
        </div>
        <button 
          onClick={() => setShowAdd(!showAdd)}
          className="bg-blue-700 text-white px-6 py-3 rounded-2xl font-black text-sm shadow-xl hover:bg-blue-800 transition-all"
        >
          {showAdd ? 'ANNULER' : '+ AJOUTER ÉLEVEUR'}
        </button>
      </header>

      {showAdd && (
        <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-blue-100 max-w-lg mx-auto">
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="font-black text-gray-900 text-center mb-4">Nouvel Éleveur</h3>
            <input 
              placeholder="Nom de l'éleveur" 
              value={form.nom} onChange={e => setForm({...form, nom: e.target.value})}
              className="w-full bg-gray-50 p-4 rounded-2xl font-bold border-none outline-none"
            />
            <input 
              placeholder="Wilaya / Localité" 
              value={form.wilaya} onChange={e => setForm({...form, wilaya: e.target.value})}
              className="w-full bg-gray-50 p-4 rounded-2xl font-bold border-none outline-none"
            />
            <input 
              placeholder="Téléphone" 
              value={form.telephone} onChange={e => setForm({...form, telephone: e.target.value})}
              className="w-full bg-gray-50 p-4 rounded-2xl font-bold border-none outline-none"
            />
            <button className="w-full bg-green-600 text-white py-4 rounded-2xl font-black">ENREGISTRER</button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {breeders.map(b => (
          <div key={b.id} className="bg-white p-6 rounded-[2.5rem] border border-gray-100 shadow-sm hover:shadow-xl transition-all relative group">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 bg-blue-50 text-blue-700 rounded-2xl flex items-center justify-center text-2xl font-black">
                {b.nom.charAt(0)}
              </div>
              <div>
                <h4 className="font-black text-gray-900 leading-none">{b.nom}</h4>
                <p className="text-[10px] text-gray-400 font-bold uppercase mt-1 tracking-widest">{b.wilaya || 'Algérie'}</p>
              </div>
            </div>
            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2 text-xs text-gray-500 font-medium">
                <span>📞</span> {b.telephone || 'Non renseigné'}
              </div>
              <div className="flex items-center gap-2 text-[10px] text-gray-400 font-bold uppercase">
                <span>📅</span> Inscrit le {new Date(b.dateCreation).toLocaleDateString()}
              </div>
            </div>
            <div className="pt-4 border-t border-gray-50 flex gap-2">
              <button 
                onClick={() => handleDelete(b.id)}
                className="flex-1 py-3 bg-red-50 text-red-600 rounded-xl text-[10px] font-black uppercase opacity-0 group-hover:opacity-100 transition-all"
              >Supprimer</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BreederManager;
