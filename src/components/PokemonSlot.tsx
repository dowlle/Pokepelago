import React from 'react';
import type { PokemonRef } from '../types/pokemon';
import { getPokespriteUrl } from '../utils/pokesprite';

interface PokemonSlotProps {
    pokemon: PokemonRef;
    status: 'locked' | 'unlocked' | 'checked';
}

export const PokemonSlot: React.FC<PokemonSlotProps> = ({ pokemon, status }) => {
    const spriteUrl = getPokespriteUrl(pokemon.name);
    const [isLoaded, setIsLoaded] = React.useState(false);

    // Reset load state when pokemon/url changes
    React.useEffect(() => {
        setIsLoaded(false);
    }, [spriteUrl]);

    return (
        <div
            className={`
        w-11 h-11 rounded-md flex items-center justify-center transition-all duration-300 relative group
        ${status === 'checked'
                    ? 'bg-green-900/40 border border-green-700/60'
                    : status === 'unlocked'
                        ? 'bg-yellow-900/30 border border-yellow-600/40'
                        : 'bg-gray-800/60 border border-gray-700/30'
                }
      `}
            title={status === 'checked' ? pokemon.name : `#${pokemon.id}`}
        >
            {status === 'checked' && (
                <div className="absolute inset-0 flex items-center justify-center overflow-visible pointer-events-none">
                    <img
                        src={spriteUrl}
                        alt={pokemon.name}
                        onLoad={() => setIsLoaded(true)}
                        className={`
                            w-14 h-14 object-contain z-10 scale-[1.3] transition-all duration-300
                            ${isLoaded ? 'opacity-100' : 'opacity-0'}
                            /* Compensate move-up because pokesprites are bottom-heavy in their frames */
                            -translate-y-[15%] text-transparent
                        `}
                        style={{ imageRendering: 'pixelated' }}
                    />
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
