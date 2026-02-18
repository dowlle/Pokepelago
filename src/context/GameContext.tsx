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
    goal?: {
        type: 'total_pokemon' | 'percentage';
        amount: number;
    };
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
    goal?: {
        type: 'total_pokemon' | 'percentage';
        amount: number;
    };
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
    const [goal, setGoal] = useState<{ type: 'total_pokemon' | 'percentage'; amount: number } | undefined>();
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

    // Load initial data
    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true);
            const data = await fetchAllPokemon();
            setAllPokemon(data);
            setIsLoading(false);
        };
        loadData();
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

                // Goal setting
                if (slotData.goal !== undefined && slotData.goal_amount !== undefined) {
                    setGoal({
                        type: slotData.goal === 0 ? 'total_pokemon' : 'percentage',
                        amount: slotData.goal_amount
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
                    }
                });
            });

            // Handle Hints
            client.socket.on('printJSON', (packet) => {
                if (packet.type === 'Hint') {
                    const item = packet.item;
                    if (item && item.player === (client as any).slot && (item.item as number) >= ITEM_OFFSET && (item.item as number) < ITEM_OFFSET + 2000) {
                        const dexId = (item.item as number) - ITEM_OFFSET;
                        setHintedIds(prev => {
                            const next = new Set(prev);
                            next.add(dexId);
                            return next;
                        });
                    }
                }
            });

            // Handle LocationInfo (sometimes hints come this way or are mass-sent)
            client.socket.on('locationInfo', (packet) => {
                packet.locations.forEach(item => {
                    if (item.player === (client as any).slot && (item.item as number) >= ITEM_OFFSET && (item.item as number) < ITEM_OFFSET + 2000) {
                        const dexId = (item.item as number) - ITEM_OFFSET;
                        setHintedIds(prev => {
                            const next = new Set(prev);
                            next.add(dexId);
                            return next;
                        });
                    }
                });
            });

            await client.login(url, info.slotName, 'Pokepelago', {
                password: info.password,
                items: itemsHandlingFlags.all,
            });

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
        setUnlockedIds(new Set());
        setCheckedIds(new Set());
        setHintedIds(new Set());
    };

    const updateUiSettings = (newSettings: Partial<UISettings>) => {
        setUiSettings(prev => ({ ...prev, ...newSettings }));
    };

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
            goal
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
