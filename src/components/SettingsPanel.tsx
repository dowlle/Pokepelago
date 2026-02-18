import React, { useState } from 'react';
import { useGame } from '../context/GameContext';
import { GENERATIONS } from '../types/pokemon';
import { X, Server, Wifi, LayoutGrid, Maximize } from 'lucide-react';

interface SettingsPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ isOpen, onClose }) => {
    const { generationFilter, setGenerationFilter, connect, isConnected, connectionError, disconnect, uiSettings, updateUiSettings } = useGame();

    const [hostname, setHostname] = useState('archipelago.gg');
    const [port, setPort] = useState(38281);
    const [slotName, setSlotName] = useState('Player1');
    const [password, setPassword] = useState('');
    const [isConnecting, setIsConnecting] = useState(false);

    if (!isOpen) return null;

    const toggleGen = (index: number) => {
        setGenerationFilter((prev: number[]) => {
            if (prev.includes(index)) {
                if (prev.length === 1) return prev; // Keep at least one
                return prev.filter((i: number) => i !== index);
            }
            return [...prev, index];
        });
    };

    const selectAll = () => {
        setGenerationFilter(GENERATIONS.map((_: unknown, i: number) => i));
    };

    const deselectAll = () => {
        setGenerationFilter([0]);
    };

    const handleConnect = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsConnecting(true);
        await connect({ hostname, port, slotName, password });
        setIsConnecting(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-gray-700 flex flex-col max-h-[90vh]">
                <div className="p-6 border-b border-gray-700 flex justify-between items-center bg-gray-900/50">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Server className="text-blue-400" />
                        Settings
                    </h2>
                    <button onClick={onClose} className="p-1 hover:bg-gray-700 rounded-full text-gray-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="overflow-y-auto p-6 space-y-8">

                    {/* Connection Section */}
                    <section className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2">Archipelago Connection</h3>

                        {!isConnected ? (
                            <form onSubmit={handleConnect} className="space-y-4">
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="col-span-2">
                                        <label className="block text-xs text-gray-400 mb-1">Server</label>
                                        <input
                                            type="text"
                                            value={hostname}
                                            onChange={(e) => setHostname(e.target.value)}
                                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:border-blue-500 outline-none"
                                            placeholder="archipelago.gg"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-400 mb-1">Port</label>
                                        <input
                                            type="number"
                                            value={port}
                                            onChange={(e) => setPort(Number(e.target.value))}
                                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:border-blue-500 outline-none"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs text-gray-400 mb-1">Slot Name</label>
                                        <input
                                            type="text"
                                            value={slotName}
                                            onChange={(e) => setSlotName(e.target.value)}
                                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:border-blue-500 outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-400 mb-1">Password</label>
                                        <input
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:border-blue-500 outline-none"
                                        />
                                    </div>
                                </div>

                                {connectionError && (
                                    <div className="text-red-400 text-xs bg-red-900/20 p-2 rounded border border-red-900/50">
                                        {connectionError}
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={isConnecting}
                                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:text-gray-400 text-white rounded font-medium transition-colors flex items-center justify-center gap-2"
                                >
                                    {isConnecting ? 'Connecting...' : 'Connect'}
                                </button>
                            </form>
                        ) : (
                            <div className="bg-green-900/20 border border-green-800 rounded p-4 flex justify-between items-center">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-green-900/40 flex items-center justify-center text-green-400">
                                        <Wifi size={20} />
                                    </div>
                                    <div>
                                        <div className="font-bold text-green-400">Connected</div>
                                        <div className="text-xs text-gray-400">as {slotName}</div>
                                    </div>
                                </div>
                                <button
                                    onClick={disconnect}
                                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded border border-gray-700 transition-colors"
                                >
                                    Disconnect
                                </button>
                            </div>
                        )}
                    </section>

                    {/* Generations Section (only enabled if offline, otherwise synced from server settings) */}
                    <section className="space-y-4">
                        <div className="flex justify-between items-center border-b border-gray-700 pb-2">
                            <h3 className="text-lg font-semibold text-gray-200">Generations</h3>
                            {isConnected && (
                                <span className="text-xs text-blue-400 bg-blue-900/20 px-2 py-0.5 rounded border border-blue-900/40">Synced from Server</span>
                            )}
                        </div>

                        {!isConnected && (
                            <div className="flex justify-end space-x-2 text-sm mb-2">
                                <button onClick={selectAll} className="text-blue-400 hover:text-blue-300">Select All</button>
                                <span className="text-gray-600">|</span>
                                <button onClick={deselectAll} className="text-blue-400 hover:text-blue-300">Reset</button>
                            </div>
                        )}

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {GENERATIONS.map((gen, index) => {
                                const isSelected = generationFilter.includes(index);
                                return (
                                    <button
                                        key={gen.label}
                                        onClick={() => !isConnected && toggleGen(index)}
                                        disabled={isConnected}
                                        className={`
                      px-4 py-3 rounded-lg border text-left transition-all relative overflow-hidden
                      ${isSelected
                                                ? 'bg-blue-600/20 border-blue-500 text-blue-100'
                                                : 'bg-gray-700/50 border-gray-600 text-gray-400 hover:bg-gray-700'}
                      ${isConnected ? 'cursor-not-allowed opacity-80' : ''}
                    `}
                                    >
                                        <div className="font-medium relative z-10">{gen.label}</div>
                                        <div className="text-xs opacity-70 relative z-10">{gen.region} · #{gen.startId}-#{gen.endId}</div>
                                    </button>
                                );
                            })}
                        </div>
                    </section>

                    {/* Interface Section */}
                    <section className="space-y-4">
                        <h3 className="text-lg font-semibold text-gray-200 border-b border-gray-700 pb-2 flex items-center gap-2">
                            Interface
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <label className="flex items-center justify-between p-3 bg-gray-700/30 border border-gray-700 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors">
                                <div className="flex items-center gap-3">
                                    <Maximize size={18} className="text-purple-400" />
                                    <div>
                                        <div className="text-sm font-medium text-gray-200">Widescreen</div>
                                        <div className="text-[10px] text-gray-500">Use full page width</div>
                                    </div>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={uiSettings.widescreen}
                                    onChange={(e) => updateUiSettings({ widescreen: e.target.checked })}
                                    className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-purple-500 focus:ring-purple-500"
                                />
                            </label>

                            <label className="flex items-center justify-between p-3 bg-gray-700/30 border border-gray-700 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors">
                                <div className="flex items-center gap-3">
                                    <LayoutGrid size={18} className="text-emerald-400" />
                                    <div>
                                        <div className="text-sm font-medium text-gray-200">Fit Regions</div>
                                        <div className="text-[10px] text-gray-500">Remove gaps between regions</div>
                                    </div>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={uiSettings.masonry}
                                    onChange={(e) => updateUiSettings({ masonry: e.target.checked })}
                                    className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-emerald-500 focus:ring-emerald-500"
                                />
                            </label>
                        </div>
                    </section>
                </div>

                <div className="p-6 border-t border-gray-700 bg-gray-900/50 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};
