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
    regionLockEnabled: boolean;
    dexsanityEnabled: boolean;
    typeLocksEnabled: boolean;
    typeLockMode: number;
    legendaryGating: number;
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
        legendaryGatingCount?: number;
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
    const [regionLockEnabled, setRegionLockEnabled] = useState(false);
    const [dexsanityEnabled, setDexsanityEnabled] = useState(true);
    const [typeLocksEnabled, setTypeLocksEnabled] = useState(false);
    const [typeLockMode, setTypeLockMode] = useState(0); // 0=any, 1=all
    const [legendaryGating, setLegendaryGating] = useState(0);
    const [regionPasses, setRegionPasses] = useState<Set<string>>(new Set());
    const [typeUnlocks, setTypeUnlocks] = useState<Set<string>>(new Set());
    const [masterBalls, setMasterBalls] = useState(0);
    const [pokegears, setPokegears] = useState(0);
    const [pokedexes, setPokedexes] = useState(0);
    const [usedMasterBalls, setUsedMasterBalls] = useState<Set<number>>(() => {
        const saved = localStorage.getItem('pokepelago_usedMasterBalls');
        return saved ? new Set(JSON.parse(saved)) : new Set();
    });
    const [usedPokegears, setUsedPokegears] = useState<Set<number>>(() => {
        const saved = localStorage.getItem('pokepelago_usedPokegears');
        return saved ? new Set(JSON.parse(saved)) : new Set();
    });
    const [usedPokedexes, setUsedPokedexes] = useState<Set<number>>(() => {
        const saved = localStorage.getItem('pokepelago_usedPokedexes');
        return saved ? new Set(JSON.parse(saved)) : new Set();
    });

    // Save Used Items
    useEffect(() => {
        localStorage.setItem('pokepelago_usedMasterBalls', JSON.stringify(Array.from(usedMasterBalls)));
    }, [usedMasterBalls]);
    useEffect(() => {
        localStorage.setItem('pokepelago_usedPokegears', JSON.stringify(Array.from(usedPokegears)));
    }, [usedPokegears]);
    useEffect(() => {
        localStorage.setItem('pokepelago_usedPokedexes', JSON.stringify(Array.from(usedPokedexes)));
    }, [usedPokedexes]);
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

    // --- Extended Locations (Catch X Type/Region) Checking ---
    useEffect(() => {
        if (!clientRef.current || !isConnected || gameMode === 'standalone') return;

        const checkExtendedLocations = () => {
            const typeCounts: Record<string, number> = {};
            const regionCounts: Record<string, number> = {};

            // Count everything we've actively guessed so far
            Array.from(checkedIds).forEach(id => {
                if (id > 1025) return; // Only count base Pokemon locations

                const data = (pokemonMetadata as any)[id];
                if (!data) return;

                // Types
                data.types.forEach((t: string) => {
                    const cType = t.charAt(0).toUpperCase() + t.slice(1);
                    typeCounts[cType] = (typeCounts[cType] || 0) + 1;
                });

                // Region
                const region = GENERATIONS.find(g => id >= g.startId && id <= g.endId)?.region;
                if (region) {
                    regionCounts[region] = (regionCounts[region] || 0) + 1;
                }
            });

            // Map thresholds to Location IDs (from apworld/pokepelago/locations.py)
            // Type Sanity: 201026 to 201079
            const typesList = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Steel', 'Dark', 'Fairy'];
            const typeThresholds = [1, 5, 10];

            let baseTypeId = 201026;
            typesList.forEach(t => {
                const count = typeCounts[t] || 0;
                typeThresholds.forEach(thresh => {
                    if (count >= thresh) {
                        const localId = baseTypeId - LOCATION_OFFSET;
                        if (!checkedIds.has(localId)) {
                            // Only check if not already checked!
                            clientRef.current?.check(baseTypeId);
                            // Optimistically add it to prevent spamming
                            setCheckedIds(prev => new Set(prev).add(localId));
                        }
                    }
                    baseTypeId++;
                });
            });

            // Region Sanity: 201080 to 201124
            const regionsList = ['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar', 'Paldea'];
            const regionThresholds = [1, 5, 10, 25, 50];

            let baseRegionId = 201080;
            regionsList.forEach(r => {
                const count = regionCounts[r] || 0;
                regionThresholds.forEach(thresh => {
                    if (count >= thresh) {
                        const localId = baseRegionId - LOCATION_OFFSET;
                        if (!checkedIds.has(localId)) {
                            clientRef.current?.check(baseRegionId);
                            setCheckedIds(prev => new Set(prev).add(localId));
                        }
                    }
                    baseRegionId++;
                });
            });
        };

        checkExtendedLocations();
    }, [checkedIds, isConnected, gameMode, pokemonMetadata]);

    // --- Goal Checking ---
    useEffect(() => {
        if (!clientRef.current || !isConnected || gameMode !== 'archipelago' || !goal) return;

        let won = false;
        const guessedPokemonCount = Array.from(checkedIds).filter(id => id <= 1025).length;

        if (goal.type === 'any_pokemon' || goal.type === 'percentage') {
            won = guessedPokemonCount >= goal.amount;
        } else if (goal.type === 'region_completion' && goal.region) {
            // Count how many we have from this region
            let countInRegion = 0;
            let totalInRegion = 0;

            // Go through all pokemon to find total needed
            allPokemon.forEach(p => {
                const region = GENERATIONS.find(g => p.id >= g.startId && p.id <= g.endId)?.region;
                if (region === goal.region) {
                    totalInRegion++;
                    if (checkedIds.has(p.id)) countInRegion++;
                }
            });

            won = totalInRegion > 0 && countInRegion >= totalInRegion;
        } else if (goal.type === 'all_legendaries') {
            let countLegs = 0;
            let totalLegs = 0;

            allPokemon.forEach(p => {
                const data = (pokemonMetadata as any)[p.id];
                if (data?.is_legendary) {
                    totalLegs++;
                    if (checkedIds.has(p.id)) countLegs++;
                }
            });

            won = totalLegs > 0 && countLegs >= totalLegs;
        }

        if (won) {
            console.log("Goal met! Sending CLIENT_GOAL status.");
            clientRef.current.updateStatus(30); // 30 is ClientStatus.CLIENT_GOAL
        }
    }, [checkedIds, isConnected, gameMode, goal, allPokemon]);

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

        const protocolsToTry = info.hostname.includes('://') ? [''] : ['wss://', 'ws://'];
        let lastError: any = null;

        for (const protocol of protocolsToTry) {
            try {
                const client = new Client();
                clientRef.current = client;

                const url = `${protocol}${info.hostname}:${info.port}`;

                // Socket Event Handlers
                client.socket.on('connectionRefused', (packet: ConnectionRefusedPacket) => {
                    setConnectionError(`Connection refused: ${packet.errors?.join(', ') || 'Unknown error'}`);
                    setIsConnected(false);
                });

                client.socket.on('connected', (packet: ConnectedPacket) => {
                    console.log(`Connected to Archipelago via ${protocol || '(explicit protocol)'}!`, packet);
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

                    // Logic settings
                    setRegionLockEnabled(!!slotData.enable_region_lock);
                    setDexsanityEnabled(slotData.enable_dexsanity !== undefined ? !!slotData.enable_dexsanity : true);
                    setTypeLocksEnabled(!!slotData.type_locks);
                    setTypeLockMode(slotData.type_lock_mode ?? 0);
                    setLegendaryGating(slotData.legendary_gating ?? 0);

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
                    let recalculateItems = false;
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
                            setLogs(prev => [{
                                id: crypto.randomUUID(),
                                timestamp: Date.now(),
                                type: 'system',
                                text: `Received Type Unlock: ${typeName}`,
                                parts: [{ text: `Received Type Unlock: ${typeName}`, type: 'color', color: 'text-green-400' }]
                            }, ...prev]);
                        } else if (item.id === 106201 || item.id === 106202 || item.id === 106203) {
                            recalculateItems = true;
                        }
                    });

                    if (recalculateItems) {
                        setUsedMasterBalls(used => {
                            const totalServer = client.items.received.filter(i => i.id === 106201).length;
                            setMasterBalls(Math.max(0, totalServer - used.size));
                            return used;
                        });
                        setUsedPokegears(used => {
                            const totalServer = client.items.received.filter(i => i.id === 106202).length;
                            setPokegears(Math.max(0, totalServer - used.size));
                            return used;
                        });
                        setUsedPokedexes(used => {
                            const totalServer = client.items.received.filter(i => i.id === 106203).length;
                            setPokedexes(Math.max(0, totalServer - used.size));
                            return used;
                        });
                    }
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

                // Handle LocationInfo
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
                return; // Successfully connected! Exit loop.

            } catch (err: any) {
                console.warn(`Connection to ${protocol}${info.hostname}:${info.port} failed:`, err);
                lastError = err;

                if (clientRef.current) {
                    clientRef.current.socket.disconnect();
                }

                // If error is related to Archipelago denying login specifically (rather than a WebSocket transport failure), don't retry.
                const msg = err?.message || String(err);
                if (msg.includes('Invalid Slot') || msg.includes('Invalid Password') || msg.includes('Invalid Game') || msg.includes('Incompatible Version')) {
                    break;
                }
            }
        }

        console.error('All connection attempts failed', lastError);
        setConnectionError(lastError?.message || 'Failed to connect. The host may be offline or you might have a secure connection issue.');
        setIsConnected(false);
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
        if (gameMode === 'standalone') {
            const genIdx = GENERATIONS.findIndex(g => id >= g.startId && id <= g.endId);
            if (genIdx === -1 || !generationFilter.includes(genIdx)) {
                return { canGuess: false, reason: 'Generation not enabled in settings' };
            }
            return { canGuess: true };
        }

        // --- ARCHIPELAGO PROGRESSION ---
        // All checks are INDEPENDENT — a Pokemon may fail multiple simultaneously.
        // We return the first failing check so the UI shows the most important blocker.

        // 1. Legendary Gating: must collect N non-legendary Pokemon first
        if (legendaryGating > 0 && data.is_legendary) {
            const collected = unlockedIds.size;
            if (collected < legendaryGating) {
                return {
                    canGuess: false,
                    reason: `Legendary locked — collect ${legendaryGating - collected} more Pokémon first`,
                    legendaryGatingCount: legendaryGating - collected
                };
            }
        }

        // 2. Region Lock: must have the region pass for this Pokemon's generation
        if (regionLockEnabled) {
            const region = GENERATIONS.find(g => id >= g.startId && id <= g.endId)?.region;
            if (region && !regionPasses.has(region)) {
                return {
                    canGuess: false,
                    reason: `Requires ${region} Pass`,
                    missingRegion: region
                };
            }
        }

        // 3. Dexsanity: must have received the specific Pokemon item
        if (dexsanityEnabled && !unlockedIds.has(id)) {
            return {
                canGuess: false,
                reason: 'Requires Pokémon item',
                missingPokemon: true
            };
        }

        // 4. Type Lock: must have the required type unlock(s)
        if (typeLocksEnabled) {
            const pokemonTypes: string[] = data.types.map((t: string) => t.charAt(0).toUpperCase() + t.slice(1));
            const unlockedTypes = pokemonTypes.filter(t => typeUnlocks.has(t));
            const missingTypes = pokemonTypes.filter(t => !typeUnlocks.has(t));

            const blocked = typeLockMode === 1
                ? missingTypes.length > 0          // ALL mode: every type must be unlocked
                : unlockedTypes.length === 0;       // ANY mode: at least one type must be unlocked

            if (blocked) {
                const toShow = typeLockMode === 1 ? missingTypes : pokemonTypes;
                return {
                    canGuess: false,
                    reason: `Requires ${toShow.join(typeLockMode === 1 ? ' & ' : ' or ')} Unlock`,
                    missingTypes: toShow
                };
            }
        }

        return { canGuess: true };
    }, [gameMode, generationFilter, regionLockEnabled, dexsanityEnabled, regionPasses, typeLocksEnabled, typeLockMode, typeUnlocks, unlockedIds, legendaryGating]);

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
            regionLockEnabled,
            dexsanityEnabled,
            typeLocksEnabled,
            typeLockMode,
            legendaryGating,
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
