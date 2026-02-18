
import React, { useRef } from 'react';
import { db } from '../services/database';
import { Sheep, User, Breeder } from '../types';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  sheep: Sheep[];
  user: User;
  breeders: Breeder[];
  selectedBreederId: string;
  onSelectBreeder: (id: string) => void;
  onLogout: () => void;
  isOffline: boolean;
}

const Layout: React.FC<LayoutProps> = ({ 
  children, activeTab, setActiveTab, sheep, user, breeders, 
  selectedBreederId, onSelectBreeder, onLogout, isOffline 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const menuItems = [
    { id: 'dashboard', label: 'Tableau de Bord', icon: '📊' },
    { id: 'analysis', label: 'Analyse IA', icon: '📸' },
    { id: 'inventory', label: 'Inventaire', icon: '🐑' },
    { id: 'nutrition', label: 'Nutrition', icon: '🌾' },
    { id: 'health', label: 'Suivi Santé', icon: '🏥' },
    { id: 'reproduction', label: 'Reproduction', icon: '🐣' },
    { id: 'production', label: 'Production', icon: '🥛' },
    { id: 'breeders', label: 'Éleveurs', icon: '👥' },
    { id: 'share', label: 'Aide & Partage', icon: '📤' },
  ];

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          db.importData(event.target.result as string);
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <aside className="w-full md:w-64 bg-[#1a237e] text-white p-6 flex-shrink-0 flex flex-col shadow-2xl z-20">
        <div className="mb-8 text-center">
          <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg transform rotate-3">
             <span className="text-3xl">🐏</span>
          </div>
          <h1 className="text-xl font-black tracking-tight leading-none text-white uppercase">Ovin Manager</h1>
          <p className="text-[10px] text-blue-300 mt-2 tracking-widest font-bold opacity-90 italic normal-case">Laboratoire GenApAgiE</p>
        </div>

        {/* Sélecteur d'éleveur */}
        <div className="mb-6">
          <label className="text-[9px] font-black text-blue-300 uppercase tracking-widest block mb-2 px-2">Élevage Actif</label>
          <select 
            value={selectedBreederId}
            onChange={(e) => onSelectBreeder(e.target.value)}
            className="w-full bg-blue-900/50 border border-blue-700 text-sm font-bold p-3 rounded-xl outline-none focus:ring-1 focus:ring-blue-400"
          >
            <option value="">-- Sélection --</option>
            {breeders.map(b => (
              <option key={b.id} value={b.id}>{b.nom}</option>
            ))}
          </select>
        </div>
        
        <nav className="space-y-1 flex-1 overflow-y-auto pr-1">
          {menuItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                activeTab === item.id 
                ? 'bg-white text-[#1a237e] shadow-xl font-black translate-x-1' 
                : 'hover:bg-blue-800/50 text-blue-100'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-8 pt-4 border-t border-blue-800 space-y-3">
          <div className="flex items-center justify-between px-2 mb-2">
            <span className="text-[10px] font-black text-blue-300 uppercase tracking-tighter truncate max-w-[100px]">{user.username}</span>
            <button 
              onClick={onLogout} 
              className="bg-red-500/20 hover:bg-red-500 text-red-300 hover:text-white px-3 py-1.5 rounded-lg text-[9px] font-black uppercase transition-all border border-red-500/30"
            >
              Déconnexion
            </button>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <button onClick={() => db.exportFullBackup(user.id)} className="bg-blue-700/50 hover:bg-blue-600 text-white text-[9px] py-2.5 rounded-lg font-bold flex flex-col items-center justify-center gap-1 transition-all uppercase tracking-tighter">
              <span>💾</span> Export
            </button>
            
            <button onClick={() => fileInputRef.current?.click()} className="bg-gray-700/50 hover:bg-gray-600 text-white text-[9px] py-2.5 rounded-lg font-bold flex flex-col items-center justify-center gap-1 transition-all uppercase tracking-tighter">
              <span>📥</span> Import
            </button>
          </div>
          <input type="file" ref={fileInputRef} onChange={handleImport} className="hidden" accept=".json" />
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-12 bg-[#f8fafc]">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
