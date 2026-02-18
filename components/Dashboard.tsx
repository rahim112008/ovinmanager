
import React, { useState } from 'react';
import { Sheep, ProductionRecord } from '../types';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface DashboardProps {
  sheep: Sheep[];
  productionRecords: ProductionRecord[];
}

const COLORS = ['#1a237e', '#8B0000', '#2E7D32', '#6a1b9a', '#FF4500', '#555'];

const Dashboard: React.FC<DashboardProps> = ({ sheep, productionRecords }) => {
  const [showInstallHelp, setShowInstallHelp] = useState(true);

  // Calcul de la répartition par race
  const breedData = sheep.reduce((acc: any, s) => {
    acc[s.race] = (acc[s.race] || 0) + 1;
    return acc;
  }, {});

  const pieData = Object.keys(breedData).map(key => ({
    name: key,
    value: breedData[key]
  }));

  const avgWeight = sheep.length ? (sheep.reduce((acc, s) => acc + s.poids, 0) / sheep.length).toFixed(1) : 0;

  const eliteSheep = sheep
    .filter(s => s.sexe === 'F')
    .map(s => {
      const records = productionRecords.filter(r => r.sheepId === s.id);
      if (records.length === 0) return null;
      const avgQty = records.reduce((sum, r) => sum + r.quantite_litres, 0) / records.length;
      const avgMG = records.reduce((sum, r) => sum + r.taux_butyreux, 0) / records.length;
      const avgMP = records.reduce((sum, r) => sum + r.taux_proteique, 0) / records.length;
      const score = (avgQty * 10) + (avgMG + avgMP);
      return { ...s, avgQty, avgMG, avgMP, score };
    })
    .filter((s): s is any => s !== null)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  return (
    <div className="space-y-8 animate-fadeIn pb-10">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black text-gray-900 tracking-tight">Ovin Analytics</h2>
          <p className="text-gray-500 font-medium">Tableau de bord de sélection zootechnique.</p>
        </div>
      </header>

      {/* Guide d'installation rapide */}
      {showInstallHelp && (
        <div className="bg-gradient-to-r from-blue-700 to-blue-900 rounded-[2rem] p-6 text-white shadow-2xl relative overflow-hidden">
          <button 
            onClick={() => setShowInstallHelp(false)}
            className="absolute top-4 right-4 text-white/50 hover:text-white"
          >✕</button>
          <div className="relative z-10 flex flex-col md:flex-row items-center gap-6">
            <div className="text-4xl bg-white/10 p-4 rounded-2xl">📱</div>
            <div>
              <h4 className="font-black text-lg uppercase mb-1">Installer sur votre Smartphone</h4>
              <p className="text-xs text-blue-100 opacity-90 max-w-xl">
                Pour utiliser l'app sans internet et de façon permanente : 
                <br/>• <b>Android</b> : Cliquez sur les 3 points (⋮) puis "Installer l'application".
                <br/>• <b>iPhone</b> : Cliquez sur "Partager" (↑) puis "Sur l'écran d'accueil".
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Cartes statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Effectif Total', value: sheep.length, icon: '🐑', color: 'blue' },
          { label: 'Moyenne Troupeau', value: `${avgWeight} kg`, icon: '⚖️', color: 'red' },
          { label: 'Production Totale', value: `${productionRecords.reduce((s,r) => s+r.quantite_litres, 0).toFixed(0)} L`, icon: '🥛', color: 'pink' },
          { label: 'Potentiel Élites', value: eliteSheep.length, icon: '👑', color: 'amber' },
        ].map((stat, i) => (
          <div key={i} className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl bg-gray-50 shadow-inner">
              {stat.icon}
            </div>
            <div>
              <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest">{stat.label}</p>
              <p className="text-2xl font-black text-gray-900">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8">
          <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-gray-100 relative overflow-hidden h-full">
            <div className="absolute top-0 right-0 p-10 opacity-5 pointer-events-none">
              <span className="text-[120px]">👑</span>
            </div>
            <div className="flex flex-col sm:flex-row justify-between sm:items-end gap-4 mb-8">
              <div>
                <h3 className="text-2xl font-black text-gray-900 mb-1">Top 5 Élites Laitières</h3>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-widest">Meilleurs potentiels génétiques du troupeau</p>
              </div>
            </div>
            <div className="space-y-4">
              {eliteSheep.length > 0 ? eliteSheep.map((s, idx) => (
                <div key={s.id} className="group flex flex-col sm:flex-row items-start sm:items-center gap-4 p-5 bg-gray-50 hover:bg-white hover:shadow-xl hover:scale-[1.01] rounded-3xl border border-transparent hover:border-blue-100 transition-all">
                  <div className="flex items-center gap-4 flex-1">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-lg ${idx === 0 ? 'bg-amber-100 text-amber-700 shadow-amber-100 shadow-lg' : 'bg-white text-gray-400 border border-gray-100'}`}>
                      {idx === 0 ? '🥇' : `#${idx + 1}`}
                    </div>
                    <div>
                      <h4 className="font-black text-gray-900 text-base">{s.nom}</h4>
                      <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">{s.race} • {s.id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 w-full sm:w-auto">
                    <div className="flex-1 sm:w-28 px-4 py-2 bg-blue-900 text-white rounded-2xl shadow-lg shadow-blue-100 text-center">
                      <p className="text-sm font-black">{s.avgQty.toFixed(2)} <span className="text-[10px]">L/j</span></p>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="py-20 text-center space-y-4">
                  <p className="text-gray-400 font-medium italic">Utilisez le module "Production" pour classer vos brebis.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-8">
          <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100">
            <h3 className="text-lg font-black text-gray-900 mb-6 uppercase tracking-tight">Répartition par Race</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} innerRadius={60} outerRadius={85} paddingAngle={10} dataKey="value">
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} strokeWidth={0} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
