import React from 'react';
import type { PokemonRef } from '../types/pokemon';
import { getPokespriteUrl } from '../utils/pokesprite';

interface PokemonSlotProps {
    pokemon: PokemonRef;
    status: 'locked' | 'unlocked' | 'checked';
}

export const PokemonSlot: React.FC<PokemonSlotProps> = ({ pokemon, status }) => {
    const spriteUrl = getPokespriteUrl(pokemon.name);

    return (
        <div
            className={`
        w-12 h-12 rounded-sm flex items-center justify-center transition-all duration-300 relative group
        ${status === 'checked'
                    ? 'bg-green-900/40 border border-green-700/60'
                    : status === 'unlocked'
                        ? 'bg-yellow-900/30 border border-yellow-600/40'
                        : 'bg-gray-800/60 border border-gray-700/30'
                }
      `}
            title={status === 'checked' ? pokemon.name : `#${pokemon.id}`}
        >
            {status === 'checked' ? (
                <img
                    src={spriteUrl}
                    alt={pokemon.name}
                    className="w-10 h-10 object-contain"
                    style={{ imageRendering: 'pixelated' }}
                    loading="lazy"
                />
            ) : status === 'unlocked' ? (
                <span className="text-yellow-500 text-sm font-bold opacity-75">?</span>
            ) : (
                <span className="text-gray-700 text-[10px]">●</span>
            )}

            {/* Tooltip */}
            {status === 'checked' && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 text-xs text-white rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 pointer-events-none border border-gray-700">
                    {pokemon.name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </div>
            )}
        </div>
    );
};
