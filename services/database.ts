
import { Sheep, HealthRecord, ProductionRecord, ReproductionRecord, NutritionRecord, User, Breeder, IngredientPrice } from "../types";

const DB_NAME = 'OvinManagerDB';
const DB_VERSION = 5; 
const STORES = {
  USERS: 'users',
  BREEDERS: 'breeders',
  PRICES: 'prices',
  SHEEP: 'sheep',
  HEALTH: 'health',
  PRODUCTION: 'production',
  REPRODUCTION: 'reproduction',
  NUTRITION: 'nutrition'
};

const openDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (e: any) => {
      const dbInstance = e.target.result;
      Object.values(STORES).forEach(store => {
        if (!dbInstance.objectStoreNames.contains(store)) {
          dbInstance.createObjectStore(store, { keyPath: 'id' });
        }
      });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
};

const getAll = async <T>(storeName: string): Promise<T[]> => {
  const dbInstance = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = dbInstance.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
};

const putItem = async <T>(storeName: string, item: T): Promise<void> => {
  const dbInstance = await openDB();
  return new Promise((resolve, reject) => {
    const transaction = dbInstance.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.put(item);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

export const db = {
  async createUser(user: User): Promise<void> { await putItem(STORES.USERS, user); },
  async getUserByUsername(username: string): Promise<User | null> {
    const users = await getAll<User>(STORES.USERS);
    return users.find(u => u.username === username) || null;
  },
  async getUserById(id: string): Promise<User | null> {
    const users = await getAll<User>(STORES.USERS);
    return users.find(u => u.id === id) || null;
  },

  async getBreeders(userId: string): Promise<Breeder[]> {
    const all = await getAll<Breeder>(STORES.BREEDERS);
    return all.filter(b => b.userId === userId);
  },
  async saveBreeder(item: Breeder): Promise<void> { await putItem(STORES.BREEDERS, item); },
  async deleteBreeder(id: string): Promise<void> {
    const dbInstance = await openDB();
    const transaction = dbInstance.transaction(STORES.BREEDERS, 'readwrite');
    transaction.objectStore(STORES.BREEDERS).delete(id);
  },

  async getPrices(breederId: string): Promise<IngredientPrice[]> {
    const all = await getAll<IngredientPrice>(STORES.PRICES);
    return all.filter(p => p.breederId === breederId);
  },
  async savePrice(item: IngredientPrice): Promise<void> { await putItem(STORES.PRICES, item); },

  async getSheep(userId: string, breederId?: string): Promise<Sheep[]> {
    const all = await getAll<Sheep>(STORES.SHEEP);
    return all.filter(s => s.userId === userId && (!breederId || s.breederId === breederId));
  },
  async saveSheep(item: Sheep): Promise<void> { await putItem(STORES.SHEEP, item); },
  async deleteSheep(id: string): Promise<void> {
    const dbInstance = await openDB();
    const transaction = dbInstance.transaction(STORES.SHEEP, 'readwrite');
    transaction.objectStore(STORES.SHEEP).delete(id);
  },

  async getProduction(userId: string, breederId?: string): Promise<ProductionRecord[]> {
    const all = await getAll<ProductionRecord>(STORES.PRODUCTION);
    return all.filter(r => r.userId === userId && (!breederId || r.breederId === breederId));
  },
  async addProduction(record: ProductionRecord): Promise<void> { await putItem(STORES.PRODUCTION, record); },

  async getHealth(userId: string, breederId?: string): Promise<HealthRecord[]> {
    const all = await getAll<HealthRecord>(STORES.HEALTH);
    return all.filter(r => r.userId === userId && (!breederId || r.breederId === breederId));
  },
  async addHealth(record: HealthRecord): Promise<void> { await putItem(STORES.HEALTH, record); },

  async getNutrition(userId: string, breederId?: string): Promise<NutritionRecord[]> {
    const all = await getAll<NutritionRecord>(STORES.NUTRITION);
    return all.filter(r => r.userId === userId && (!breederId || r.breederId === breederId));
  },
  async addNutrition(record: NutritionRecord): Promise<void> { await putItem(STORES.NUTRITION, record); },

  async getReproduction(userId: string, breederId?: string): Promise<ReproductionRecord[]> {
    const all = await getAll<ReproductionRecord>(STORES.REPRODUCTION);
    return all.filter(r => r.userId === userId && (!breederId || r.breederId === breederId));
  },
  async addReproduction(record: ReproductionRecord): Promise<void> { await putItem(STORES.REPRODUCTION, record); },

  async importData(jsonData: string): Promise<void> {
    try {
      const data = JSON.parse(jsonData);
      // Import des utilisateurs en premier pour permettre la connexion
      if (data.users && Array.isArray(data.users)) {
        for (const u of data.users) {
          await this.createUser(u);
        }
      }
      if (data.breeders) for (const b of data.breeders) await this.saveBreeder(b);
      if (data.sheep) for (const s of data.sheep) await this.saveSheep(s);
      if (data.prices) for (const p of data.prices) await this.savePrice(p);
      if (data.production) for (const r of data.production) await this.addProduction(r);
      if (data.health) for (const r of data.health) await this.addHealth(r);
      if (data.reproduction) for (const r of data.reproduction) await this.addReproduction(r);
      if (data.nutrition) for (const r of data.nutrition) await this.addNutrition(r);
      
      return Promise.resolve();
    } catch (e) {
      console.error("Failed to import data", e);
      throw e;
    }
  },

  async exportFullBackup(userId: string, returnBlob = false): Promise<any> {
    const user = await this.getUserById(userId);
    const breeders = await this.getBreeders(userId);
    const sheep = await this.getSheep(userId);
    const production = await this.getProduction(userId);
    const health = await this.getHealth(userId);
    const reproduction = await this.getReproduction(userId);
    const nutrition = await this.getNutrition(userId);
    const allPrices = await getAll<IngredientPrice>(STORES.PRICES);
    const prices = allPrices.filter(p => breeders.some(b => b.id === p.breederId));
    
    const data = {
      users: user ? [user] : [], // On force l'inclusion de l'utilisateur
      breeders,
      sheep,
      prices,
      production,
      health,
      reproduction,
      nutrition,
      exportDate: new Date().toISOString(),
      version: "3.0"
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const filename = `ovin_backup_${userId}_${new Date().toISOString().split('T')[0]}.json`;

    if (returnBlob) {
      return { blob, filename };
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
};
