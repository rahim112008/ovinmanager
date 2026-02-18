
import React from 'react';
import { STANDARDS_RACES } from '../constants';

const StandardsModule: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-fadeIn pb-24">
      <header className="text-center">
        <h2 className="text-3xl font-black text-gray-900 tracking-tight">Méthodologie de Mensuration</h2>
        <p className="text-blue-600 font-bold normal-case">Protocole Scientifique GenApAgiE</p>
      </header>

      {/* Processus de mesure */}
      <section className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-gray-100">
        <h3 className="text-xl font-black text-gray-900 mb-8 flex items-center gap-3">
          <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm">?</span>
          Comment fonctionne la mesure par IA ?
        </h3>

        <div className="space-y-10">
          <div className="flex gap-6">
            <div className="text-3xl">1️⃣</div>
            <div>
              <h4 className="font-bold text-gray-800">Calibration Optique</h4>
              <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                L'IA identifie l'objet témoin (ex: pièce de 100 DA) pour établir un ratio <b>Pixels ↔ Centimètres</b>. Sans cet objet, la mesure reste une estimation proportionnelle basée sur les standards de la race.
              </p>
            </div>
          </div>

          <div className="flex gap-6">
            <div className="text-3xl">2️⃣</div>
            <div>
              <h4 className="font-bold text-gray-800">Segmentation Anatomique</h4>
              <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                L'algorithme de vision par ordinateur segmente l'animal et place des curseurs virtuels sur le garrot, la croupe, le sternum et les membres.
              </p>
            </div>
          </div>

          <div className="flex gap-6">
            <div className="text-3xl">3️⃣</div>
            <div>
              <h4 className="font-bold text-gray-800">Calcul de la Biométrie</h4>
              <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                Les distances Euclidiennes entre les points sont converties en unités réelles. Le périmètre thoracique est déduit par la profondeur de poitrine et la largeur de vue arrière (si disponible).
              </p>
            </div>
          </div>

          <div className="flex gap-6">
            <div className="text-3xl">4️⃣</div>
            <div>
              <h4 className="font-bold text-gray-800">Algorithme de Pesée</h4>
              <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                Le poids vif est calculé par corrélation morphométrique selon la formule : <br/>
                <code className="bg-gray-100 px-2 py-1 rounded text-blue-700 font-bold text-xs">Poids = (Tour de Poitrine² × Longueur) / 11800</code>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Standards par Race */}
      <section className="space-y-6">
        <h3 className="text-xl font-bold text-gray-900 px-4">Références Zootechniques (Algérie)</h3>
        <div className="overflow-hidden bg-white rounded-[2.5rem] border border-gray-100 shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 text-[10px] font-black uppercase text-gray-400 tracking-widest">
                <th className="px-6 py-4">Race</th>
                <th className="px-6 py-4">H. Garrot (cm)</th>
                <th className="px-6 py-4">Longueur (cm)</th>
                <th className="px-6 py-4">Poids Adulte (kg)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {Object.values(STANDARDS_RACES).map((race) => (
                <tr key={race.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 font-bold text-gray-800">{race.nom_complet}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{race.mensurations.hauteur_cm[0]}-{race.mensurations.hauteur_cm[1]}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{race.mensurations.longueur_cm[0]}-{race.mensurations.longueur_cm[1]}</td>
                  <td className="px-6 py-4 text-sm font-black text-blue-800">{race.poids_adulte.male[0]}-{race.poids_adulte.male[1]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="bg-blue-50 p-8 rounded-[2.5rem] border border-blue-100 text-center">
        <p className="text-xs text-blue-800 font-bold leading-relaxed">
          ⚠️ Note : Pour une précision optimale (±2cm), l'animal doit être pris en photo de profil strict, sur un sol plat, avec l'appareil photo à hauteur de l'animal (environ 70cm du sol).
        </p>
      </div>
    </div>
  );
};

export default StandardsModule;
