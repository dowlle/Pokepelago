import React, { useEffect, useState, useRef } from 'react';
import { useGame } from '../context/GameContext';
import { X, ExternalLink, HelpCircle, MapPin, Sparkles, CheckCircle2 } from 'lucide-react';

export const PokemonDetails: React.FC = () => {
    const {
        selectedPokemonId,
        setSelectedPokemonId,
        allPokemon,
        unlockedIds,
        checkedIds,
        hintedIds,
        shinyIds,
        say,
        getLocationName
    } = useGame();

    const [details, setDetails] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [gifLoaded, setGifLoaded] = useState(false);
    const [hintSent, setHintSent] = useState(false);
    const gifRef = useRef<HTMLImageElement>(null);

    const pokemon = allPokemon.find(p => p.id === selectedPokemonId);

    useEffect(() => {
        if (selectedPokemonId) {
            setLoading(true);
            setGifLoaded(false);
            setHintSent(false);
            fetch(`https://pokeapi.co/api/v2/pokemon/${selectedPokemonId}`)
                .then(res => res.json())
                .then(data => {
                    setDetails(data);
                    setLoading(false);
                })
                .catch(err => {
                    console.error('Failed to fetch pokemon details', err);
                    setLoading(false);
                });
        } else {
            setDetails(null);
        }
    }, [selectedPokemonId]);

    if (!selectedPokemonId || !pokemon) return null;

    const isUnlocked = unlockedIds.has(selectedPokemonId);
    const isChecked = checkedIds.has(selectedPokemonId);
    const isHinted = hintedIds.has(selectedPokemonId);
    const isShiny = shinyIds.has(selectedPokemonId);

    // Only show name and real info if guessed (checked) AND GIF is loaded
    const showInfo = isChecked && gifLoaded;
    const showShadow = isUnlocked && !isChecked;

    const handleRequestHint = () => {
        say(`!hint Pokemon #${selectedPokemonId}`);
        setHintSent(true);
        setTimeout(() => setHintSent(false), 3000);
    };

    const displayName = showInfo
        ? pokemon.name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
        : showShadow ? '???' : '???';

    const showdownUrl = isShiny && isChecked
        ? `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/shiny/${selectedPokemonId}.gif`
        : `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/${selectedPokemonId}.gif`;

    // Location ID = National Dex ID + 200000
    const unlockLocationName = getLocationName(selectedPokemonId + 200000);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl relative animate-in zoom-in-95 duration-300">
                {/* Header */}
                <div className="absolute top-4 right-4 z-10">
                    <button
                        onClick={() => setSelectedPokemonId(null)}
                        className="p-2 bg-gray-800 hover:bg-gray-700 rounded-full text-gray-400 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Pokemon Display */}
                <div className={`h-48 flex items-center justify-center relative overflow-hidden ${isShiny && isChecked ? 'bg-gradient-to-b from-yellow-900/20 to-transparent' : 'bg-gray-800/20'}`}>
                    {loading && (
                        <div className="w-12 h-12 border-4 border-blue-500 rounded-full animate-spin border-t-transparent opacity-50 absolute z-0"></div>
                    )}

                    {isUnlocked || isChecked ? (
                        <div className="relative">
                            {isShiny && isChecked && (
                                <div className="absolute -inset-8 bg-yellow-500/10 blur-3xl animate-pulse rounded-full" />
                            )}
                            <img
                                ref={gifRef}
                                src={showdownUrl}
                                alt={pokemon.name}
                                onLoad={() => setGifLoaded(true)}
                                className={`
                                    w-32 h-32 object-contain relative z-10 transition-opacity duration-300
                                    ${showShadow ? 'brightness-0 opacity-40 contrast-100' : ''}
                                    ${gifLoaded ? 'opacity-100' : 'opacity-0'}
                                `}
                            />
                            {!gifLoaded && !loading && (
                                <div className="w-12 h-12 border-4 border-gray-700 rounded-full animate-spin border-t-transparent opacity-50 absolute inset-0 m-auto"></div>
                            )}
                        </div>
                    ) : (
                        <div className="w-32 h-32 bg-gray-800 rounded-full flex items-center justify-center opacity-20">
                            <HelpCircle size={64} className="text-gray-400" />
                        </div>
                    )}

                    <div className="absolute bottom-4 left-6">
                        <span className="text-4xl font-black text-white/5 opacity-40 select-none">#{selectedPokemonId}</span>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 pt-2 space-y-6">
                    <div className="flex justify-between items-end min-h-[50px]">
                        <div>
                            <h2 className="text-2xl font-black text-white uppercase tracking-tight flex items-center gap-2">
                                {displayName}
                                {isShiny && isChecked && gifLoaded && <Sparkles size={20} className="text-yellow-400" />}
                            </h2>
                            <p className="text-xs text-gray-500 font-mono">National Dex #{selectedPokemonId}</p>
                        </div>

                        <div className="flex gap-2">
                            {details?.types && showInfo && details.types.map((t: any) => (
                                <span
                                    key={t.type.name}
                                    className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-gray-800 border border-gray-700 text-gray-300 animate-in fade-in slide-in-from-right-2"
                                >
                                    {t.type.name}
                                </span>
                            ))}
                        </div>
                    </div>

                    {showInfo && details ? (
                        <div className="grid grid-cols-2 gap-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
                            <div className="bg-gray-800/40 rounded-xl p-3 border border-gray-800">
                                <span className="text-[10px] text-gray-500 uppercase font-black block mb-1">Dimensions</span>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Height</span>
                                    <span className="text-white font-bold">{details.height / 10}m</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Weight</span>
                                    <span className="text-white font-bold">{details.weight / 10}kg</span>
                                </div>
                            </div>
                            <div className="bg-gray-800/40 rounded-xl p-3 border border-gray-800">
                                <span className="text-[10px] text-gray-500 uppercase font-black block mb-1">Abilities</span>
                                <div className="space-y-0.5">
                                    {details.abilities.map((a: any) => (
                                        <div key={a.ability.name} className="flex justify-between text-xs">
                                            <span className="text-gray-400 capitalize">{a.ability.name.replace('-', ' ')}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="h-24 flex items-center justify-center bg-gray-800/10 rounded-xl border border-dashed border-gray-800">
                            <p className="text-xs text-gray-600 italic">
                                {!isChecked ? "Unlock and guess this Pokémon to reveal its data" : "Loading data..."}
                            </p>
                        </div>
                    )}

                    {/* AP Section */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between text-[10px] font-black uppercase text-gray-600 tracking-widest border-b border-gray-800 pb-2">
                            <span>Archipelago Data</span>
                        </div>

                        {isChecked && (
                            <div className="bg-green-900/10 border border-green-500/20 rounded-xl p-4 flex items-start gap-3 animate-in fade-in duration-500">
                                <CheckCircle2 size={18} className="text-green-500 mt-0.5" />
                                <div>
                                    <span className="text-[10px] text-green-500 font-bold uppercase block">Obtained</span>
                                    <p className="text-sm text-white font-medium">Unlocks: {unlockLocationName}</p>
                                </div>
                            </div>
                        )}

                        {isHinted && !isChecked && (
                            <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-xl p-4 flex items-start gap-3">
                                <MapPin size={18} className="text-indigo-400 mt-0.5" />
                                <div>
                                    <span className="text-[10px] text-indigo-400 font-bold uppercase block">Hint Location</span>
                                    <p className="text-sm text-white font-medium">Location found!</p>
                                    <p className="text-[10px] text-indigo-300/60 italic">Check your Archipelago Log for details.</p>
                                </div>
                            </div>
                        )}

                        {!isChecked && !isUnlocked && !isHinted && (
                            <div className="space-y-3">
                                <p className="text-[11px] text-gray-500">Don't know where this Pokémon is? Request a hint from the server.</p>
                                <button
                                    onClick={handleRequestHint}
                                    disabled={hintSent}
                                    className={`
                                        w-full py-3 transition-all rounded-xl text-xs font-black uppercase tracking-widest text-white shadow-lg flex items-center justify-center gap-2
                                        ${hintSent
                                            ? 'bg-green-600 shadow-green-900/20'
                                            : 'bg-blue-600 hover:bg-blue-500 active:scale-95 shadow-blue-900/20'}
                                    `}
                                >
                                    {hintSent ? <CheckCircle2 size={16} /> : <HelpCircle size={16} />}
                                    {hintSent ? 'Hint Requested!' : 'Request Hint'}
                                </button>
                                {hintSent && (
                                    <p className="text-[9px] text-center text-gray-500 italic">Check the log to see if you have enough hint points!</p>
                                )}
                            </div>
                        )}

                        {isUnlocked && !isChecked && (
                            <div className="bg-blue-900/10 border border-blue-500/20 rounded-xl p-4 flex items-middle gap-3">
                                <HelpCircle size={18} className="text-blue-400" />
                                <span className="text-xs text-blue-300/80 font-medium">Available to guess in the grid!</span>
                            </div>
                        )}
                    </div>

                    {showInfo && (
                        <div className="flex justify-center text-[10px]">
                            <a
                                href={`https://vgc.pokedata.ovh/pokemon/${selectedPokemonId}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-gray-500 hover:text-blue-400 flex items-center gap-1 transition-colors"
                            >
                                <ExternalLink size={10} />
                                VIEW ON VGC POKEDATA
                            </a>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
