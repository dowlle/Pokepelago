import React from 'react';
import type { PokemonRef } from '../types/pokemon';
import { GENERATIONS } from '../types/pokemon';
import { useGame } from '../context/GameContext';
import { PokemonSlot } from './PokemonSlot';

export const DexGrid: React.FC = () => {
    const { allPokemon, unlockedIds, checkedIds, generationFilter } = useGame();

    // Build a map for quick lookups
    const pokemonById = React.useMemo(() => {
        const map = new Map<number, PokemonRef>();
        allPokemon.forEach(p => map.set(p.id, p));
        return map;
    }, [allPokemon]);

    const getStatus = (id: number): 'locked' | 'unlocked' | 'checked' => {
        if (checkedIds.has(id)) return 'checked';
        if (unlockedIds.has(id)) return 'unlocked';
        return 'locked';
    };

    return (
        <div className="flex flex-wrap gap-4 justify-center px-2 pb-32">
            {GENERATIONS.map((gen, genIdx) => {
                if (!generationFilter.includes(genIdx)) return null;

                // Build list of pokemon IDs in this generation
                const pokemonInGen: PokemonRef[] = [];
                for (let id = gen.startId; id <= gen.endId; id++) {
                    const p = pokemonById.get(id);
                    if (p) pokemonInGen.push(p);
                }

                const checkedCount = pokemonInGen.filter(p => checkedIds.has(p.id)).length;

                return (
                    <div
                        key={gen.label}
                        className="bg-gray-900/70 border border-gray-700/50 rounded-lg p-3 backdrop-blur-sm shadow-xl"
                        style={{ minWidth: '300px', maxWidth: '420px' }}
                    >
                        <div className="flex justify-between items-baseline mb-2">
                            <h3 className="text-sm font-bold text-gray-300">{gen.region}</h3>
                            <span className="text-xs text-gray-500">
                                {checkedCount}/{pokemonInGen.length}
                            </span>
                        </div>
                        <div className="flex flex-wrap gap-[2px]">
                            {pokemonInGen.map(p => (
                                <PokemonSlot key={p.id} pokemon={p} status={getStatus(p.id)} />
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};
