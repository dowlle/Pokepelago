import React from 'react';
import type { PokemonRef } from '../types/pokemon';
import { getPokespriteUrl } from '../utils/pokesprite';
import { useGame } from '../context/GameContext';

interface PokemonSlotProps {
    pokemon: PokemonRef;
    status: 'locked' | 'unlocked' | 'checked' | 'shadow' | 'hint';
    isShiny?: boolean;
}

export const PokemonSlot: React.FC<PokemonSlotProps> = ({ pokemon, status, isShiny = false }) => {
    const { setSelectedPokemonId, isPokemonGuessable, usedPokegears } = useGame();
    const { canGuess, reason } = isPokemonGuessable(pokemon.id);
    const isPokegeared = usedPokegears.has(pokemon.id);

    const spriteUrl = getPokespriteUrl(pokemon.name, pokemon.id, isShiny);
    const [isLoaded, setIsLoaded] = React.useState(false);
    const [hasError, setHasError] = React.useState(false);

    // Reset load state when pokemon/url changes
    React.useEffect(() => {
        setIsLoaded(false);
        setHasError(false);
    }, [spriteUrl]);

    const isVisible = status === 'checked' || status === 'shadow' || status === 'hint';

    return (
        <div
            onClick={() => setSelectedPokemonId(pokemon.id)}
            className={`
        w-11 h-11 rounded-md flex items-center justify-center transition-all duration-300 relative group cursor-pointer hover:scale-110 active:scale-95
        ${status === 'checked'
                    ? 'bg-green-900/40 border border-green-700/60'
                    : status === 'shadow'
                        ? 'bg-blue-900/30 border border-blue-600/40'
                        : status === 'unlocked'
                            ? (canGuess ? 'bg-yellow-900/30 border border-yellow-600/40' : 'bg-gray-900/40 border border-gray-700/60 opacity-50 grayscale cursor-not-allowed')
                            : status === 'hint'
                                ? 'bg-indigo-950/40 border border-indigo-900/40 opacity-70'
                                : 'bg-gray-800/60 border border-gray-700/30'
                }
        ${isShiny && status !== 'locked' ? 'shadow-[0_0_10px_rgba(255,215,0,0.3)]' : ''}
        ${!canGuess && status !== 'locked' && status !== 'checked' ? 'opacity-40' : ''}
      `}
            title={!canGuess ? reason : (status === 'checked' ? pokemon.name : status === 'hint' ? `${pokemon.name} (Hinted)` : `#${pokemon.id}`)}
        >
            {isVisible && !hasError && (
                <div className="absolute inset-0 flex items-center justify-center overflow-visible pointer-events-none">
                    <img
                        src={spriteUrl}
                        alt={pokemon.name}
                        onLoad={() => setIsLoaded(true)}
                        onError={() => setHasError(true)}
                        className={`
                            w-12 h-12 object-contain z-10 scale-[1.1] transition-all duration-300
                            ${isLoaded ? 'opacity-100' : 'opacity-0'}
                            ${status === 'shadow' || status === 'hint'
                                ? (isPokegeared ? 'brightness-50 opacity-80' : 'brightness-0 contrast-100 opacity-60')
                                : ''}
                        `}
                        style={{ imageRendering: 'pixelated' }}
                    />
                </div>
            )}

            {(hasError || (isVisible && !isLoaded)) && (
                <span className="text-[10px] text-gray-600 font-mono z-0">
                    #{pokemon.id}
                </span>
            )}

            {/* Shiny sparkle indicator */}
            {isShiny && status === 'checked' && (
                <div className="absolute top-0.5 right-0.5 z-20 animate-pulse">
                    <span className="text-[10px] leading-none drop-shadow-[0_0_2px_rgba(255,215,0,0.8)]">✨</span>
                </div>
            )}

            {status === 'unlocked' && (
                <span className="text-yellow-500 text-lg font-bold opacity-75">?</span>
            )}

            {status === 'locked' && (
                <span className="text-gray-700 text-[8px]">●</span>
            )}

            {/* Tooltip */}
            {status === 'checked' && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 text-xs text-white rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 pointer-events-none border border-gray-700 shadow-xl">
                    {pokemon.name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </div>
            )}
        </div>
    );
};
