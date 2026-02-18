
import React, { useState, useRef } from 'react';
import { db } from '../services/database';
import { User } from '../types';

interface LoginProps {
  onLogin: (user: User) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [farmName, setFarmName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (isRegister) {
      if (!username || !password || !farmName) {
        setError('Veuillez remplir tous les champs.');
        return;
      }
      const existing = await db.getUserByUsername(username);
      if (existing) {
        setError('Ce nom d\'utilisateur existe déjà sur cet appareil.');
        return;
      }
      const newUser: User = {
        id: Math.random().toString(36).substr(2, 9),
        username,
        passwordHash: btoa(password), 
        farmName,
        role: 'admin'
      };
      await db.createUser(newUser);
      onLogin(newUser);
    } else {
      const user = await db.getUserByUsername(username);
      if (!user) {
        setError("Compte introuvable. Utilisez le bouton d'importation ci-dessous si vous avez déjà un fichier de sauvegarde.");
      } else if (user.passwordHash === btoa(password)) {
        onLogin(user);
      } else {
        setError('Mot de passe incorrect.');
      }
    }
  };

  const handleImportBackup = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          if (event.target?.result) {
            await db.importData(event.target.result as string);
            setSuccess("✅ Données et compte restaurés ! Vous pouvez maintenant vous connecter avec vos anciens identifiants.");
            setError('');
          }
        } catch (err) {
          setError("Échec de l'importation. Le fichier est invalide.");
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="min-h-screen bg-[#1a237e] flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-64 h-64 bg-blue-600 rounded-full blur-[120px] opacity-30"></div>
      
      <div className="bg-white w-full max-w-md rounded-[2.5rem] shadow-2xl p-10 relative z-10 animate-fadeIn">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4 transform rotate-6">
            <span className="text-3xl">🐏</span>
          </div>
          <h1 className="text-xl font-black text-gray-900 uppercase tracking-tighter leading-none">Ovin Manager Pro</h1>
          <p className="text-[9px] text-gray-400 font-bold uppercase tracking-widest mt-2">Laboratoire GenApAgiE</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-2xl text-[10px] font-black mb-6 border border-red-100 flex items-center gap-3 animate-shake">
             <span>⚠️</span> {error}
          </div>
        )}

        {success && (
          <div className="bg-green-50 text-green-700 p-4 rounded-2xl text-[10px] font-black mb-6 border border-green-100 animate-fadeIn">
             {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input 
            type="text" 
            placeholder="Nom d'utilisateur"
            value={username} 
            onChange={e => setUsername(e.target.value)}
            className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-bold text-gray-800 outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input 
            type="password" 
            placeholder="Mot de passe"
            value={password} 
            onChange={e => setPassword(e.target.value)}
            className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-bold text-gray-800 outline-none focus:ring-2 focus:ring-blue-500"
          />

          {isRegister && (
            <input 
              type="text" 
              placeholder="Nom de l'Exploitation"
              value={farmName} 
              onChange={e => setFarmName(e.target.value)}
              className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-bold text-gray-800 animate-slideDown outline-none"
            />
          )}

          <button type="submit" className="w-full bg-blue-700 text-white py-5 rounded-2xl font-black text-xs shadow-xl hover:bg-blue-800 transition-all active:scale-95">
            {isRegister ? "CRÉER MON COMPTE" : "SE CONNECTER"}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-50 flex flex-col items-center gap-4">
          <button onClick={() => setIsRegister(!isRegister)} className="text-[10px] font-black text-blue-600 uppercase tracking-widest hover:underline">
            {isRegister ? "Déjà inscrit ? Se connecter" : "Nouvel éleveur ? S'inscrire ici"}
          </button>

          <div className="w-full bg-gray-50 rounded-2xl p-4 border border-dashed border-gray-200">
            <p className="text-[9px] text-gray-400 font-bold text-center mb-3 uppercase tracking-tighter">Restauration de compte</p>
            <button 
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full bg-white text-gray-600 py-3 rounded-xl text-[10px] font-black border border-gray-100 shadow-sm flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors"
            >
              📥 IMPORTER (.JSON)
            </button>
            <input type="file" ref={fileInputRef} onChange={handleImportBackup} className="hidden" accept=".json" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
