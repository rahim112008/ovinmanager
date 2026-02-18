
import React from 'react';
import { db } from '../services/database';

const ShareModule: React.FC<{ userId: string }> = ({ userId }) => {
  const appUrl = window.location.href;

  const handleShareApp = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Ovin Manager Pro - GenApAgiE',
          text: 'Découvrez mon application de suivi ovin par IA pour le laboratoire GenApAgiE.',
          url: appUrl,
        });
      } catch (err) {
        console.error('Erreur de partage', err);
      }
    } else {
      navigator.clipboard.writeText(appUrl);
      alert('Lien de l\'application copié dans le presse-papier !');
    }
  };

  const handleShareData = async () => {
    const data = await db.exportFullBackup(userId, true); // True pour obtenir le blob au lieu de télécharger
    if (data && navigator.share) {
      const file = new File([data.blob], data.filename, { type: 'application/json' });
      try {
        await navigator.share({
          files: [file],
          title: 'Données Ovin Manager Pro',
          text: 'Voici mes données de test pour l\'application Ovin Manager.',
        });
      } catch (err) {
        console.error('Erreur de partage de fichier', err);
        // Fallback: téléchargement classique si le partage de fichier échoue
        db.exportFullBackup(userId);
      }
    } else {
      db.exportFullBackup(userId);
      alert('Le fichier de données a été téléchargé. Envoyez-le par email à votre professeur.');
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fadeIn">
      <div className="text-center">
        <div className="inline-block bg-blue-50 p-6 rounded-[2.5rem] mb-4">
          <span className="text-5xl">📤</span>
        </div>
        <h2 className="text-3xl font-black text-gray-900 tracking-tight">Partager avec votre Professeur</h2>
        <p className="text-gray-500 mt-2">Envoyez l'application et vos données de test en quelques clics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Carte Partager l'URL */}
        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-blue-100 text-blue-700 rounded-2xl flex items-center justify-center text-3xl mb-4">🔗</div>
          <h3 className="font-black text-gray-900 mb-2">Lien de l'App</h3>
          <p className="text-xs text-gray-400 mb-6 flex-1">Permet à votre professeur d'ouvrir l'application sur son propre smartphone.</p>
          <button 
            onClick={handleShareApp}
            className="w-full bg-[#1a237e] text-white py-4 rounded-2xl font-black text-xs shadow-xl active:scale-95 transition-all"
          >
            PARTAGER LE LIEN
          </button>
        </div>

        {/* Carte Partager les Données */}
        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-green-100 text-green-700 rounded-2xl flex items-center justify-center text-3xl mb-4">📊</div>
          <h3 className="font-black text-gray-900 mb-2">Mes Données</h3>
          <p className="text-xs text-gray-400 mb-6 flex-1">Envoyez vos enregistrements (inventaire, analyses IA) pour qu'il puisse les importer.</p>
          <button 
            onClick={handleShareData}
            className="w-full bg-green-600 text-white py-4 rounded-2xl font-black text-xs shadow-xl active:scale-95 transition-all"
          >
            ENVOYER MES DONNÉES
          </button>
        </div>
      </div>

      {/* Guide Rapide */}
      <div className="bg-blue-900 text-white p-8 rounded-[2.5rem] shadow-2xl">
        <h4 className="font-black uppercase tracking-widest text-[10px] mb-4 opacity-60">Instructions pour le professeur</h4>
        <div className="space-y-4">
          <div className="flex gap-4">
            <span className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-[10px] font-black shrink-0">1</span>
            <p className="text-sm">Il ouvre le <b>Lien de l'App</b> sur son smartphone.</p>
          </div>
          <div className="flex gap-4">
            <span className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-[10px] font-black shrink-0">2</span>
            <p className="text-sm">Il télécharge vos <b>Données</b> que vous lui avez envoyées (fichier .json).</p>
          </div>
          <div className="flex gap-4">
            <span className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-[10px] font-black shrink-0">3</span>
            <p className="text-sm">Dans l'app, il clique sur <b>IMPORT</b> dans le menu et sélectionne votre fichier.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShareModule;
