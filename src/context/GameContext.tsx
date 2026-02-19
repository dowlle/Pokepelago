import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import type { PokemonRef } from '../types/pokemon';
import { GENERATIONS } from '../types/pokemon';
import { fetchAllPokemon } from '../services/pokeapi';
import { Client, itemsHandlingFlags } from 'archipelago.js';
import type {
    ConnectedPacket,
    ConnectionRefusedPacket,
    Item
} from 'archipelago.js';
import pokemonMetadata from '../data/pokemon_metadata.json';
import { getSprite, countSprites, generateSpriteKey } from '../services/spriteService';

export interface LogEntry {
    id: string;
    timestamp: number;
    type: 'item' | 'check' | 'hint' | 'chat' | 'system';
    text: string;
    color?: string; // CSS color or class
    parts?: LogPart[];
}

export interface LogPart {
    text: string;
    type?: 'player' | 'item' | 'location' | 'color';
    color?: string;
}

interface GameState {
    allPokemon: PokemonRef[];
    unlockedIds: Set<number>;
    checkedIds: Set<number>;
    hintedIds: Set<number>;
    isLoading: boolean;
    generationFilter: number[];
    uiSettings: UISettings;
    shadowsEnabled: boolean;
    shinyIds: Set<number>;
    logicMode: number;
    typeLocksEnabled: boolean;
    regionPasses: Set<string>;
    typeUnlocks: Set<string>;
    masterBalls: number;
    pokegears: number;
    pokedexes: number;
    goal?: {
        type: 'any_pokemon' | 'percentage' | 'region_completion' | 'all_legendaries';
        amount: number;
        region?: string;
    };
    logs: LogEntry[];
    gameMode: 'archipelago' | 'standalone' | null;
}

export interface UISettings {
    widescreen: boolean;
    masonry: boolean;
}

interface ConnectionInfo {
    hostname: string;
    port: number;
    slotName: string;
    password?: string;
}

interface GameContextType extends GameState {
    unlockPokemon: (id: number) => void;
    checkPokemon: (id: number) => void;
    setGenerationFilter: React.Dispatch<React.SetStateAction<number[]>>;
    updateUiSettings: (settings: Partial<UISettings>) => void;
    isConnected: boolean;
    connectionError: string | null;
    connect: (info: ConnectionInfo) => Promise<void>;
    disconnect: () => void;
    addLog: (entry: Omit<LogEntry, 'id' | 'timestamp'>) => void;
    say: (text: string) => void;
    connectionInfo: ConnectionInfo;
    setConnectionInfo: React.Dispatch<React.SetStateAction<ConnectionInfo>>;
    selectedPokemonId: number | null;
    setSelectedPokemonId: (id: number | null) => void;
    getLocationName: (locationId: number) => string;
    isPokemonGuessable: (id: number) => {
        canGuess: boolean;
        reason?: string;
        missingRegion?: string;
        missingTypes?: string[];
        missingPokemon?: boolean;
    };
    useMasterBall: (pokemonId: number) => void;
    usePokegear: (pokemonId: number) => void;
    usePokedex: (pokemonId: number) => void;
    usedMasterBalls: Set<number>;
    usedPokegears: Set<number>;
    usedPokedexes: Set<number>;
    spriteCount: number;
    gameMode: 'archipelago' | 'standalone' | null;
    setGameMode: (mode: 'archipelago' | 'standalone' | null) => void;
    refreshSpriteCount: () => Promise<void>;
    getSpriteUrl: (id: number, options?: { shiny?: boolean; animated?: boolean }) => Promise<string | null>;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

// ID Offsets (must match apworld)
const ITEM_OFFSET = 100000;
const LOCATION_OFFSET = 200000;

export const GameProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [allPokemon, setAllPokemon] = useState<PokemonRef[]>([]);
    const [unlockedIds, setUnlockedIds] = useState<Set<number>>(new Set());
    const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());
    const [hintedIds, setHintedIds] = useState<Set<number>>(new Set());
    const [shinyIds, setShinyIds] = useState<Set<number>>(new Set());
    const [shadowsEnabled, setShadowsEnabled] = useState(false);
    const [goal, setGoal] = useState<GameState['goal'] | undefined>();
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [selectedPokemonId, setSelectedPokemonId] = useState<number | null>(null);
    const [logicMode, setLogicMode] = useState(0);
    const [typeLocksEnabled, setTypeLocksEnabled] = useState(false);
    const [regionPasses, setRegionPasses] = useState<Set<string>>(new Set());
    const [typeUnlocks, setTypeUnlocks] = useState<Set<string>>(new Set());
    const [masterBalls, setMasterBalls] = useState(0);
    const [pokegears, setPokegears] = useState(0);
    const [pokedexes, setPokedexes] = useState(0);
    const [usedMasterBalls, setUsedMasterBalls] = useState<Set<number>>(new Set());
    const [usedPokegears, setUsedPokegears] = useState<Set<number>>(new Set());
    const [usedPokedexes, setUsedPokedexes] = useState<Set<number>>(new Set());
    const [spriteCount, setSpriteCount] = useState(0);
    const [gameMode, setGameModeState] = useState<'archipelago' | 'standalone' | null>(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.has('splash')) return null;
        return localStorage.getItem('pokepelago_gamemode') as any || null;
    });

    const setGameMode = useCallback((mode: 'archipelago' | 'standalone' | null) => {
        setGameModeState(mode);
        if (mode) {
            localStorage.setItem('pokepelago_gamemode', mode);
        } else {
            localStorage.removeItem('pokepelago_gamemode');
        }
    }, []);

    const refreshSpriteCount = useCallback(async () => {
        const count = await countSprites();
        setSpriteCount(count);
    }, []);

    const getSpriteUrl = useCallback(async (id: number, options: { shiny?: boolean; animated?: boolean } = {}) => {
        const key = generateSpriteKey(id, options);
        const blob = await getSprite(key);
        if (blob) {
            return URL.createObjectURL(blob);
        }
        return null;
    }, []);

    useEffect(() => {
        refreshSpriteCount();
    }, [refreshSpriteCount]);

    const getLocationName = useCallback((locationId: number) => {
        if (!clientRef.current) return `Location #${locationId}`;
        return clientRef.current.package.lookupLocationName(clientRef.current.game, locationId) || `Location #${locationId}`;
    }, []);

    const [connectionInfo, setConnectionInfo] = useState<ConnectionInfo>(() => {
        const saved = localStorage.getItem('pokepelago_connection');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error('Failed to parse saved connection info', e);
            }
        }
        return {
            hostname: 'archipelago.gg',
            port: 38281,
            slotName: 'Player1',
            password: ''
        };
    });
    const [isLoading, setIsLoading] = useState(true);
    const [generationFilter, setGenerationFilter] = useState<number[]>(
        GENERATIONS.map((_, i) => i)
    );

    const [isConnected, setIsConnected] = useState(false);
    const [connectionError, setConnectionError] = useState<string | null>(null);
    const [uiSettings, setUiSettings] = useState<UISettings>(() => {
        const saved = localStorage.getItem('pokepelago_ui');
        return saved ? JSON.parse(saved) : { widescreen: false, masonry: false };
    });

    const clientRef = useRef<Client | null>(null);

    // Save UI settings
    useEffect(() => {
        localStorage.setItem('pokepelago_ui', JSON.stringify(uiSettings));
    }, [uiSettings]);

    // Save Connection Info
    useEffect(() => {
        localStorage.setItem('pokepelago_connection', JSON.stringify(connectionInfo));
    }, [connectionInfo]);

    // Load initial data and auto-connect
    useEffect(() => {
        const loadDataAndConnect = async () => {
            setIsLoading(true);
            const data = await fetchAllPokemon();
            setAllPokemon(data);
            setIsLoading(false);

            // Auto-reconnect if previously connected AND mode is archipelago
            const wasConnected = localStorage.getItem('pokepelago_connected') === 'true';
            const savedConnection = localStorage.getItem('pokepelago_connection');
            const savedMode = localStorage.getItem('pokepelago_gamemode');

            if (savedMode === 'archipelago' && wasConnected && savedConnection) {
                try {
                    const info = JSON.parse(savedConnection);
                    connect(info);
                } catch (e) {
                    console.error('Auto-connect failed', e);
                }
            }
        };
        loadDataAndConnect();
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (clientRef.current) {
                clientRef.current.socket.disconnect();
            }
        };
    }, []);

    const unlockPokemon = useCallback((id: number) => {
        setUnlockedIds(prev => {
            if (prev.has(id)) return prev;
            const next = new Set(prev);
            next.add(id);
            return next;
        });
    }, []);

    const checkPokemon = useCallback((id: number) => {
        setCheckedIds(prev => {
            if (prev.has(id)) return prev;
            const next = new Set(prev);
            next.add(id);
            return next;
        });

        // Send check to Archipelago
        if (clientRef.current && isConnected) {
            const locationId = LOCATION_OFFSET + id;
            clientRef.current.check(locationId);
        }
    }, [isConnected]);

    const addLog = useCallback((entry: Omit<LogEntry, 'id' | 'timestamp'>) => {
        setLogs(prev => [
            {
                ...entry,
                id: Math.random().toString(36).substring(7),
                timestamp: Date.now()
            },
            ...prev.slice(0, 99) // Keep last 100
        ]);
    }, []);

    const say = useCallback((text: string) => {
        if (clientRef.current && isConnected) {
            clientRef.current.messages.say(text);
        }
    }, [isConnected]);

    const connect = async (info: ConnectionInfo) => {
        setConnectionError(null);
        setIsConnected(false);

        try {
            const client = new Client();
            clientRef.current = client;

            const protocol = info.hostname.includes('://') ? '' : 'ws://';
            const url = `${protocol}${info.hostname}:${info.port}`;

            // Socket Event Handlers
            client.socket.on('connectionRefused', (packet: ConnectionRefusedPacket) => {
                setConnectionError(`Connection refused: ${packet.errors?.join(', ') || 'Unknown error'}`);
                setIsConnected(false);
            });

            client.socket.on('connected', (packet: ConnectedPacket) => {
                console.log('Connected to Archipelago!', packet);
                setIsConnected(true);
                setConnectionError(null);

                // Sync already checked locations
                const checkedLocs = packet.checked_locations || [];
                const newChecked = new Set<number>();
                checkedLocs.forEach((locId: number) => {
                    if (locId >= LOCATION_OFFSET && locId < LOCATION_OFFSET + 2000) {
                        newChecked.add(locId - LOCATION_OFFSET);
                    }
                });
                setCheckedIds(newChecked);

                // Sync already received items (fully reconstruct unlockedIds)
                const receivedItems = client.items.received;
                const newUnlocked = new Set<number>();
                receivedItems.forEach((item) => {
                    if (item.id >= ITEM_OFFSET && item.id < ITEM_OFFSET + 2000) {
                        newUnlocked.add(item.id - ITEM_OFFSET);
                    }
                });
                setUnlockedIds(newUnlocked);

                // Reconstruct shinyIds from received items count
                const shinyCount = receivedItems.filter(i => i.id === 105000).length;
                if (shinyCount > 0) {
                    const receivedPokemonIds = Array.from(newUnlocked);
                    setShinyIds(new Set(receivedPokemonIds.slice(0, shinyCount)));
                }

                // Handle slot data for settings
                const slotData = packet.slot_data as any || {};

                // Gen filters
                const newFilter: number[] = [];
                if (slotData.gen1) newFilter.push(0);
                if (slotData.gen2) newFilter.push(1);
                if (slotData.gen3) newFilter.push(2);
                if (slotData.gen4) newFilter.push(3);
                if (slotData.gen5) newFilter.push(4);
                if (slotData.gen6) newFilter.push(5);
                if (slotData.gen7) newFilter.push(6);
                if (slotData.gen8) newFilter.push(7);
                if (slotData.gen9) newFilter.push(8);

                if (newFilter.length > 0) {
                    setGenerationFilter(newFilter);
                }

                // Shadows setting
                setShadowsEnabled(!!slotData.shadows);

                // New Logic settings
                setLogicMode(slotData.logic_mode || 0);
                setTypeLocksEnabled(!!slotData.type_locks);

                // Goal setting
                if (slotData.goal !== undefined && slotData.goal_amount !== undefined) {
                    const goalTypes: ('any_pokemon' | 'percentage' | 'region_completion' | 'all_legendaries')[] =
                        ['any_pokemon', 'percentage', 'region_completion', 'all_legendaries'];
                    const regions = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea"];
                    setGoal({
                        type: goalTypes[slotData.goal] || 'any_pokemon',
                        amount: slotData.goal_amount,
                        region: slotData.goal_region ? regions[slotData.goal_region - 1] : undefined
                    });
                }
            });

            // Handle items via ItemsManager
            client.items.on('itemsReceived', (items: Item[]) => {
                items.forEach((item) => {
                    if (item.id >= ITEM_OFFSET && item.id < ITEM_OFFSET + 2000) {
                        const dexId = item.id - ITEM_OFFSET;
                        unlockPokemon(dexId);
                    } else if (item.id === 105000) {
                        // Shiny Upgrade
                        setUnlockedIds(unlocked => {
                            const pokemonIds = Array.from(unlocked);
                            setShinyIds(prev => {
                                const next = new Set(prev);
                                // Apply to the next unlocked pokemon that isn't shiny yet
                                const targetIdx = prev.size;
                                if (targetIdx < pokemonIds.length) {
                                    next.add(pokemonIds[targetIdx]);
                                }
                                return next;
                            });
                            return unlocked;
                        });
                    } else if (item.id >= 106001 && item.id <= 106009) {
                        const regions = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea"];
                        const regionName = regions[item.id - 106001];
                        setRegionPasses(prev => new Set(prev).add(regionName));
                    } else if (item.id >= 106101 && item.id <= 106118) {
                        const types = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Steel', 'Dark', 'Fairy'];
                        const typeName = types[item.id - 106101];
                        setTypeUnlocks(prev => new Set(prev).add(typeName));
                    } else if (item.id === 106201) {
                        setMasterBalls(prev => prev + 1);
                    } else if (item.id === 106202) {
                        setPokegears(prev => prev + 1);
                    } else if (item.id === 106203) {
                        setPokedexes(prev => prev + 1);
                    }
                });
            });

            // Generic log capturing
            client.socket.on('printJSON', (packet) => {
                if (packet.type === 'Hint') {
                    const item = packet.item as any;
                    if (item && item.receiving_player === client.players.self.slot && (item.item as number) >= ITEM_OFFSET && (item.item as number) < ITEM_OFFSET + 2000) {
                        const dexId = (item.item as number) - ITEM_OFFSET;
                        setHintedIds(prev => {
                            const next = new Set(prev);
                            next.add(dexId);
                            return next;
                        });
                    }
                }

                if (packet.data) {
                    const parts: LogPart[] = packet.data.map((p: any) => {
                        let text = p.text || '';
                        let type = p.type || 'color';

                        // Resolve IDs if possible using helper maps
                        if (p.type === 'player_id') {
                            const pid = parseInt(p.text);
                            text = client.players.findPlayer(pid)?.alias || `Player ${pid}`;
                            type = 'player';
                        } else if (p.type === 'item_id') {
                            const iid = parseInt(p.text);
                            const player = client.players.findPlayer(p.player);
                            text = client.package.lookupItemName(player?.game || client.game, iid) || `Item ${iid}`;
                            type = 'item';
                        } else if (p.type === 'location_id') {
                            const lid = parseInt(p.text);
                            const player = client.players.findPlayer(p.player);
                            text = client.package.lookupLocationName(player?.game || client.game, lid) || `Location ${lid}`;
                            type = 'location';
                        }

                        return { text, type, color: p.color };
                    });

                    addLog({
                        type: packet.type === 'Hint' ? 'hint' : packet.type === 'ItemSend' ? 'item' : packet.type === 'Chat' ? 'chat' : 'system',
                        text: parts.map(p => p.text).join(''),
                        parts
                    });
                }
            });

            // Handle LocationInfo (sometimes hints come this way or are mass-sent)
            client.socket.on('locationInfo', (packet) => {
                packet.locations.forEach(item => {
                    if (item.player === client.players.self.slot && (item.item as number) >= ITEM_OFFSET && (item.item as number) < ITEM_OFFSET + 2000) {
                        const dexId = (item.item as number) - ITEM_OFFSET;
                        setHintedIds(prev => {
                            const next = new Set(prev);
                            next.add(dexId);
                            return next;
                        });
                    }
                });
            });

            await client.login(url, info.slotName, 'pokepelago', {
                password: info.password,
                items: itemsHandlingFlags.all,
            });

            localStorage.setItem('pokepelago_connected', 'true');

        } catch (err: any) {
            console.error('Connection failed', err);
            setConnectionError(err.message || 'Failed to connect');
            setIsConnected(false);
        }
    };

    const disconnect = () => {
        if (clientRef.current) {
            clientRef.current.socket.disconnect();
            clientRef.current = null;
        }
        setIsConnected(false);
        localStorage.setItem('pokepelago_connected', 'false');
        setUnlockedIds(new Set());
        setCheckedIds(new Set());
        setHintedIds(new Set());
    };

    const updateUiSettings = (newSettings: Partial<UISettings>) => {
        setUiSettings(prev => ({ ...prev, ...newSettings }));
    };

    const useMasterBall = useCallback((pokemonId: number) => {
        if (masterBalls > 0) {
            setMasterBalls(prev => prev - 1);
            setUsedMasterBalls(prev => new Set(prev).add(pokemonId));
            checkPokemon(pokemonId);
            addLog({
                type: 'system',
                text: `Used a Master Ball on Pokemon #${pokemonId}!`
            });
        }
    }, [masterBalls, checkPokemon, addLog]);

    const usePokegear = useCallback((pokemonId: number) => {
        if (pokegears > 0) {
            setPokegears(prev => prev - 1);
            setUsedPokegears(prev => new Set(prev).add(pokemonId));
            addLog({
                type: 'system',
                text: `Used a Pokegear on Pokemon #${pokemonId}!`
            });
        }
    }, [pokegears, addLog]);

    const usePokedex = useCallback((pokemonId: number) => {
        if (pokedexes > 0) {
            setPokedexes(prev => prev - 1);
            setUsedPokedexes(prev => new Set(prev).add(pokemonId));
            addLog({
                type: 'system',
                text: `Used a Pokedex on Pokemon #${pokemonId}!`
            });
        }
    }, [pokedexes, addLog]);

    const isPokemonGuessable = useCallback((id: number) => {
        const data = (pokemonMetadata as any)[id];
        if (!data) return { canGuess: true };

        // --- STANDALONE PROGRESSION ---
        // Standalone mode is "free play" restricted only by generation settings
        if (gameMode === 'standalone') {
            const genIdx = GENERATIONS.findIndex(g => id >= g.startId && id <= g.endId);
            if (genIdx === -1 || !generationFilter.includes(genIdx)) {
                return {
                    canGuess: false,
                    reason: "Generation not enabled in settings"
                };
            }
            return { canGuess: true };
        }

        // --- ARCHIPELAGO PROGRESSION ---
        // 1. Region Check
        if (logicMode === 1) { // Region Lock
            const region = GENERATIONS.find(g => id >= g.startId && id <= g.endId)?.region;
            if (region && !regionPasses.has(region)) {
                return {
                    canGuess: false,
                    reason: `Requires ${region} Pass`,
                    missingRegion: region
                };
            }
        } else {
            // In Dexsanity mode (0), if not in unlockedIds, can't guess
            if (!unlockedIds.has(id)) {
                return {
                    canGuess: false,
                    reason: "Requires Pokémon item",
                    missingPokemon: true
                };
            }
        }

        // 2. Type Check
        if (typeLocksEnabled) {
            const missingTypes = data.types.filter((t: string) => !typeUnlocks.has(t.charAt(0).toUpperCase() + t.slice(1)));
            if (missingTypes.length > 0) {
                const formattedTypes = missingTypes.map((t: string) => t.charAt(0).toUpperCase() + t.slice(1));
                return {
                    canGuess: false,
                    reason: `Requires ${formattedTypes.join(' & ')} Unlock`,
                    missingTypes: formattedTypes
                };
            }
        }

        return { canGuess: true };
    }, [gameMode, generationFilter, logicMode, regionPasses, typeLocksEnabled, typeUnlocks, unlockedIds]);

    return (
        <GameContext.Provider value={{
            allPokemon,
            unlockedIds,
            checkedIds,
            hintedIds,
            shinyIds,
            isLoading,
            generationFilter,
            setGenerationFilter,
            unlockPokemon,
            checkPokemon,
            uiSettings,
            updateUiSettings,
            isConnected,
            connectionError,
            connect,
            disconnect,
            shadowsEnabled,
            goal,
            logs,
            addLog,
            say,
            connectionInfo,
            setConnectionInfo,
            selectedPokemonId,
            setSelectedPokemonId,
            getLocationName,
            logicMode,
            typeLocksEnabled,
            regionPasses,
            typeUnlocks,
            masterBalls,
            pokegears,
            pokedexes,
            useMasterBall,
            usePokegear,
            usePokedex,
            usedMasterBalls,
            usedPokegears,
            usedPokedexes,
            spriteCount,
            refreshSpriteCount,
            getSpriteUrl,
            isPokemonGuessable,
            gameMode,
            setGameMode
        }}>
            {children}
        </GameContext.Provider>
    );
};

export const useGame = () => {
    const context = useContext(GameContext);
    if (!context) {
        throw new Error('useGame must be used within a GameProvider');
    }
    return context;
};
