import React from 'react';
import { useGame } from '../context/GameContext';
import { Shield, Globe, Laptop, ArrowRight, Download, ExternalLink, Code2, Beaker } from 'lucide-react';

export const SplashScreen: React.FC = () => {
    const { setGameMode } = useGame();

    const NEW_CLIENT_URL = "https://dowlle.github.io/PokepelagoClient/";
    const NEW_APWORLD_URL = "https://github.com/dowlle/PokepelagoClient/releases";

    return (
        <div className="fixed inset-0 z-[100] bg-gray-950 overflow-y-auto font-sans flex items-center justify-center p-4">
            <div className="max-w-4xl w-full">
                {/* Relocation Header */}
                <div className="text-center mb-8 animate-in fade-in slide-in-from-top-4 duration-1000">
                    <h1 className="text-6xl font-black tracking-tighter mb-4 bg-gradient-to-r from-green-400 via-emerald-500 to-blue-500 bg-clip-text text-transparent">
                        Poképelago has Moved
                    </h1>
                    <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
                        We've migrated to a new, dedicated repository to improve development, testing, and your overall experience.
                    </p>
                </div>

                {/* Incompatibility Warning */}
                <div className="mb-8 p-6 bg-red-950/30 border border-red-500/30 rounded-3xl backdrop-blur-md animate-in fade-in zoom-in duration-700">
                    <div className="flex items-center gap-3 mb-3 text-red-400">
                        <Shield size={24} />
                        <h2 className="text-xl font-black uppercase tracking-tight">Incompatibility Warning</h2>
                    </div>
                    <p className="text-red-200/80 text-sm leading-relaxed">
                        <strong>Important:</strong> Games generated with the <strong>old APWorld</strong> are incompatible with the new client. If you have an active multi-world game using the previous version, you <strong>must</strong> continue using this legacy client to finish it.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-6 mb-12">
                    {/* New Repo Card */}
                    <a
                        href={NEW_CLIENT_URL}
                        target="_blank"
                        rel="noreferrer"
                        className="group relative flex flex-col p-8 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/30 hover:border-blue-500/50 rounded-3xl transition-all duration-500 hover:shadow-2xl hover:shadow-blue-900/40"
                    >
                        <div className="flex justify-between items-start mb-6">
                            <div className="p-4 bg-blue-600 rounded-2xl shadow-xl shadow-blue-900/20 group-hover:scale-110 transition-transform duration-500">
                                <Globe className="text-white" size={32} />
                            </div>
                            <ExternalLink className="text-blue-500 opacity-50 group-hover:opacity-100 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all" />
                        </div>
                        <h3 className="text-3xl font-black text-white mb-3">Launch New Client</h3>
                        <p className="text-blue-200/60 text-base leading-relaxed mb-6">
                            Access the latest version of the tracking client directly on GitHub Pages.
                        </p>
                        <div className="mt-auto flex items-center gap-2 text-blue-400 font-bold group-hover:gap-4 transition-all">
                            <span>Go to dowlle.github.io</span>
                            <ArrowRight size={18} />
                        </div>
                    </a>

                    {/* APWorld Release Card */}
                    <a
                        href={NEW_APWORLD_URL}
                        target="_blank"
                        rel="noreferrer"
                        className="group relative flex flex-col p-8 bg-purple-600/10 hover:bg-purple-600/20 border border-purple-500/30 hover:border-purple-500/50 rounded-3xl transition-all duration-500 hover:shadow-2xl hover:shadow-purple-900/40"
                    >
                        <div className="flex justify-between items-start mb-6">
                            <div className="p-4 bg-purple-600 rounded-2xl shadow-xl shadow-purple-900/20 group-hover:scale-110 transition-transform duration-500">
                                <Download className="text-white" size={32} />
                            </div>
                            <ExternalLink className="text-purple-500 opacity-50 group-hover:opacity-100 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all" />
                        </div>
                        <h3 className="text-3xl font-black text-white mb-3">Download APWorld</h3>
                        <p className="text-purple-200/60 text-base leading-relaxed mb-6">
                            Get the newest server logic, features, and fixes for your Archipelago generation.
                        </p>
                        <div className="mt-auto flex items-center gap-2 text-purple-400 font-bold group-hover:gap-4 transition-all">
                            <span>Get Latest Release</span>
                            <ArrowRight size={18} />
                        </div>
                    </a>
                </div>

                {/* Technical Reasons & Legacy Access */}
                <div className="grid md:grid-cols-3 gap-4 mb-12">
                    <div className="bg-gray-900/40 border border-gray-800/60 rounded-2xl p-6 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-3 text-emerald-400">
                            <Code2 size={20} />
                            <h4 className="font-bold text-sm">Official Fork</h4>
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            Now forked from the main Archipelago repo for better compatibility.
                        </p>
                    </div>
                    <div className="bg-gray-900/40 border border-gray-800/60 rounded-2xl p-6 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-3 text-amber-400">
                            <Beaker size={20} />
                            <h4 className="font-bold text-sm">Enhanced Testing</h4>
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            New environment makes coding and logic verification much easier.
                        </p>
                    </div>
                    <div className="bg-gray-900/40 border border-gray-800/60 rounded-2xl p-6 backdrop-blur-sm">
                        <div className="flex items-center gap-3 mb-3 text-blue-400">
                            <Laptop size={20} />
                            <h4 className="font-bold text-sm">Dedicated Client</h4>
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            A separate repo allows us to scale the client independently.
                        </p>
                    </div>
                </div>

                <div className="flex flex-col items-center gap-6">
                    <button
                        onClick={() => {
                            localStorage.setItem('pokepelago_last_splash', Date.now().toString());
                            setGameMode('standalone');
                        }}
                        className="group relative px-8 py-3 bg-gray-800/50 hover:bg-gray-700/80 border border-gray-700 hover:border-gray-500 rounded-full text-gray-300 hover:text-white text-sm font-bold transition-all duration-300 flex items-center gap-2 shadow-lg hover:shadow-gray-900/40"
                    >
                        <span>Continue with Legacy Client</span>
                        <ArrowRight size={16} className="opacity-50 group-hover:translate-x-1 group-hover:opacity-100 transition-all" />
                    </button>

                    <div className="flex flex-wrap justify-center gap-8 text-[10px] font-black uppercase tracking-[0.2em] text-gray-700">
                        <div className="flex items-center gap-2">
                            <Shield size={12} />
                            <span>Client-Side Storage Only</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

