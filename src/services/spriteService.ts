import { openDB, type IDBPDatabase } from 'idb';

const DB_NAME = 'pokepelago-sprites';
const STORE_NAME = 'sprites';

let dbPromise: Promise<IDBPDatabase<any>> | null = null;

const getDB = () => {
    if (!dbPromise) {
        dbPromise = openDB(DB_NAME, 1, {
            upgrade(db) {
                db.createObjectStore(STORE_NAME);
            },
        });
    }
    return dbPromise;
};

export const saveSprite = async (key: string, blob: Blob) => {
    const db = await getDB();
    await db.put(STORE_NAME, blob, key);
};

export const getSprite = async (key: string): Promise<Blob | undefined> => {
    const db = await getDB();
    return await db.get(STORE_NAME, key);
};

export const clearAllSprites = async () => {
    const db = await getDB();
    await db.clear(STORE_NAME);
};

export const countSprites = async (): Promise<number> => {
    const db = await getDB();
    return await db.count(STORE_NAME);
};

export const generateSpriteKey = (id: number, options: { shiny?: boolean; animated?: boolean }) => {
    const parts: (string | number)[] = [id];
    if (options.shiny) parts.push('shiny');
    if (options.animated) parts.push('animated');
    return parts.join('_');
};

export const importFromFiles = async (files: FileList | File[], onProgress?: (count: number) => void) => {
    // Expected file names: 1.png, 1_shiny.png, 1.gif, 1_shiny.gif, etc.
    // Or folders: static/1.png, shiny/1.png, animated/1.gif, animated/shiny_1.gif

    let importedCount = 0;

    for (const file of Array.from(files)) {
        const name = file.name;
        const path = (file as any).webkitRelativePath || name;

        let key = '';

        // Match patterns from download_sprites.py
        if (path.includes('static/')) {
            const id = parseInt(name.split('.')[0]);
            if (!isNaN(id)) key = generateSpriteKey(id, {});
        } else if (path.includes('shiny/')) {
            const id = parseInt(name.split('.')[0]);
            if (!isNaN(id)) key = generateSpriteKey(id, { shiny: true });
        } else if (path.includes('animated/')) {
            if (name.startsWith('shiny_')) {
                const id = parseInt(name.replace('shiny_', '').split('.')[0]);
                if (!isNaN(id)) key = generateSpriteKey(id, { shiny: true, animated: true });
            } else {
                const id = parseInt(name.split('.')[0]);
                if (!isNaN(id)) key = generateSpriteKey(id, { animated: true });
            }
        } else {
            // Flat file import
            const match = name.match(/^(\d+)(_shiny)?(_animated)?\.(png|gif)$/);
            if (match) {
                const id = parseInt(match[1]);
                const isShiny = !!match[2];
                const isAnimated = !!match[3] || name.endsWith('.gif');
                key = generateSpriteKey(id, { shiny: isShiny, animated: isAnimated });
            }
        }

        if (key) {
            await saveSprite(key, file);
            importedCount++;
            if (onProgress && importedCount % 10 === 0) {
                onProgress(importedCount);
            }
        }
    }

    return importedCount;
};
