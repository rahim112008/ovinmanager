
import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import AnalysisModule from './components/AnalysisModule';
import Inventory from './components/Inventory';
import ProductionModule from './components/ProductionModule';
import HealthModule from './components/HealthModule';
import ReproductionModule from './components/ReproductionModule';
import StandardsModule from './components/StandardsModule';
import NutritionModule from './components/NutritionModule';
import BreederManager from './components/BreederManager';
import PresentationModule from './components/PresentationModule';
import ShareModule from './components/ShareModule';
import Login from './components/Login';
import { db } from './services/database';
import { Sheep, AnalysisResult, ProductionRecord, User, EtatPhysiologique, Dentition, Breeder } from './types';

const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [breeders, setBreeders] = useState<Breeder[]>([]);
  const [selectedBreederId, setSelectedBreederId] = useState<string>('');
  
  const [sheep, setSheep] = useState<Sheep[]>([]);
  const [production, setProduction] = useState<ProductionRecord[]>([]);
  const [loading, setLoading] = useState(true); 
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const initApp = async () => {
      try {
        const saved = localStorage.getItem('ovin_user');
        if (saved) {
          const user = JSON.parse(saved);
          setCurrentUser(user);
        }
        
        const savedBreeder = localStorage.getItem('ovin_breeder_id');
        if (savedBreeder) setSelectedBreederId(savedBreeder);

        if (navigator.storage && navigator.storage.persist) {
          await navigator.storage.persist();
        }
      } catch (e) {
        console.error("Erreur d'initialisation", e);
      } finally {
        setLoading(false);
      }
    };

    initApp();

    window.addEventListener('online', () => setIsOffline(false));
    window.addEventListener('offline', () => setIsOffline(true));
  }, []);

  useEffect(() => {
    if (currentUser) loadData();
  }, [currentUser, selectedBreederId]);

  const loadData = async () => {
    if (!currentUser) return;
    const bList = await db.getBreeders(currentUser.id);
    setBreeders(bList);

    const s = await db.getSheep(currentUser.id, selectedBreederId);
    const p = await db.getProduction(currentUser.id, selectedBreederId);
    
    setSheep(s);
    setProduction(p);
  };

  const handleSelectBreeder = (id: string) => {
    setSelectedBreederId(id);
    localStorage.setItem('ovin_breeder_id', id);
  };

  const handleLogin = (user: User) => {
    setCurrentUser(user);
    localStorage.setItem('ovin_user', JSON.stringify(user));
  };

  const handleLogout = () => {
    localStorage.removeItem('ovin_user');
    localStorage.removeItem('ovin_breeder_id');
    setCurrentUser(null);
    setSelectedBreederId('');
    setBreeders([]);
    setSheep([]);
    setProduction([]);
    setActiveTab('dashboard');
  };

  const handleSaveAnalysis = async (
    result: AnalysisResult, 
    imageUrl: string, 
    meta: { tagId: string, age: any, ageType: 'mois' | 'dentition', etat: EtatPhysiologique }
  ) => {
    if (!currentUser || !selectedBreederId) {
      alert("Veuillez d'abord sélectionner un éleveur.");
      return;
    }
    
    const newSheep: Sheep = {
      id: `OVN-${Math.random().toString(36).substr(2, 6).toUpperCase()}`,
      userId: currentUser.id,
      breederId: selectedBreederId,
      tagId: meta.tagId,
      nom: `Ovin_${meta.tagId}`,
      race: result.race,
      sexe: 'F',
      age_mois: meta.ageType === 'mois' ? meta.age as number : undefined,
      dentition: meta.ageType === 'dentition' ? meta.age as Dentition : undefined,
      poids: result.measurements?.poitrine ? Math.round(result.measurements.poitrine * 0.7) : 55,
      etat_physiologique: meta.etat,
      robe_couleur: result.robe_couleur,
      robe_qualite: result.robe_qualite,
      date_analyse: new Date().toISOString(),
      statut: 'actif',
      measurements: result.measurements || {},
      mammary_traits: result.mammary_traits || {},
      mammary_score: result.mammary_score,
      classification: result.classification,
      notes: result.feedback,
      imageUrl: imageUrl
    };

    await db.saveSheep(newSheep);
    await loadData();
    setActiveTab('inventory');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#1a237e] flex items-center justify-center p-6 text-center">
        <div>
          <div className="w-20 h-20 bg-white/10 rounded-[2rem] flex items-center justify-center mx-auto mb-6 animate-bounce shadow-2xl">
            <span className="text-4xl">🐏</span>
          </div>
          <h2 className="text-white font-black uppercase tracking-[0.3em] text-xs opacity-70">Ovin Manager Pro</h2>
          <p className="text-blue-300 font-black text-[11px] tracking-[0.1em] mt-2 normal-case">Laboratoire GenApAgiE</p>
          <div className="mt-6 flex justify-center gap-1">
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></div>
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse [animation-delay:0.2s]"></div>
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse [animation-delay:0.4s]"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!currentUser) return <Login onLogin={handleLogin} />;

  return (
    <Layout 
      activeTab={activeTab} 
      setActiveTab={setActiveTab} 
      sheep={sheep} 
      user={currentUser}
      breeders={breeders}
      selectedBreederId={selectedBreederId}
      onSelectBreeder={handleSelectBreeder}
      onLogout={handleLogout}
      isOffline={isOffline}
    >
      {activeTab === 'share' ? (
        <div className="space-y-12 pb-24">
          <ShareModule userId={currentUser.id} />
          <div className="border-t border-gray-100 pt-12">
            <PresentationModule />
          </div>
        </div>
      ) : !selectedBreederId && activeTab !== 'breeders' ? (
        <div className="py-20 text-center animate-fadeIn">
          <div className="w-24 h-24 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">👥</span>
          </div>
          <h2 className="text-2xl font-black text-gray-900">Sélectionnez un éleveur</h2>
          <p className="text-gray-500 max-w-sm mx-auto mt-2">Veuillez choisir une exploitation dans le menu latéral pour voir les données.</p>
          <button 
            onClick={() => setActiveTab('breeders')}
            className="mt-6 bg-[#1a237e] text-white px-8 py-4 rounded-2xl font-black shadow-xl"
          >Gérer les Éleveurs</button>
        </div>
      ) : (
        <>
          {activeTab === 'dashboard' && <Dashboard sheep={sheep} productionRecords={production} />}
          {activeTab === 'analysis' && <AnalysisModule onSave={handleSaveAnalysis} isOffline={isOffline} />}
          {activeTab === 'standards' && <StandardsModule />}
          {activeTab === 'inventory' && <Inventory breeders={breeders} selectedBreederId={selectedBreederId} sheep={sheep} onDelete={async (id) => { if(confirm("Supprimer ?")) { await db.deleteSheep(id); loadData(); }}} />}
          {activeTab === 'production' && <ProductionModule userId={currentUser.id} breederId={selectedBreederId} />}
          {activeTab === 'health' && <HealthModule userId={currentUser.id} breederId={selectedBreederId} />}
          {activeTab === 'reproduction' && <ReproductionModule userId={currentUser.id} breederId={selectedBreederId} />}
          {activeTab === 'nutrition' && <NutritionModule userId={currentUser.id} breederId={selectedBreederId} />}
          {activeTab === 'breeders' && <BreederManager userId={currentUser.id} onRefresh={loadData} />}
        </>
      )}
    </Layout>
  );
};

export default App;
