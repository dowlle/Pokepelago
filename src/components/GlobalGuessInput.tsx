import React, { useState, useRef, useEffect } from 'react';
import { useGame } from '../context/GameContext';
import type { PokemonRef } from '../types/pokemon';
import { formatPokemonName } from '../types/pokemon';

export const GlobalGuessInput: React.FC = () => {
    const { allPokemon, unlockedIds, checkedIds, checkPokemon } = useGame();
    const [guess, setGuess] = useState('');
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error' | 'already'; name: string } | null>(null);
    const [suggestions, setSuggestions] = useState<PokemonRef[]>([]);
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-clear feedback
    useEffect(() => {
        if (feedback) {
            const timer = setTimeout(() => setFeedback(null), 2000);
            return () => clearTimeout(timer);
        }
    }, [feedback]);

    // Build suggestions as user types
    useEffect(() => {
        if (guess.length < 2) {
            setSuggestions([]);
            return;
        }
        const lower = guess.toLowerCase().trim();
        const matches = allPokemon
            .filter(p => {
                const displayName = p.name.replace(/-/g, ' ');
                return (displayName.includes(lower) || p.name.includes(lower))
                    && unlockedIds.has(p.id)
                    && !checkedIds.has(p.id);
            })
            .slice(0, 8);
        setSuggestions(matches);
    }, [guess, allPokemon, unlockedIds, checkedIds]);

    const attemptGuess = (name: string) => {
        const normalised = name.toLowerCase().trim();
        // Find matching pokemon
        const match = allPokemon.find(p => {
            const baseName = p.name.toLowerCase();
            const displayName = baseName.replace(/-/g, ' ');
            return baseName === normalised || displayName === normalised;
        });

        if (!match) {
            setFeedback({ type: 'error', name: normalised });
            return;
        }

        if (checkedIds.has(match.id)) {
            setFeedback({ type: 'already', name: formatPokemonName(match.name) });
            setGuess('');
            setSuggestions([]);
            return;
        }

        if (!unlockedIds.has(match.id)) {
            // Correct name, but not yet unlocked
            setFeedback({ type: 'error', name: normalised });
            return;
        }

        // Success!
        checkPokemon(match.id);
        setFeedback({ type: 'success', name: formatPokemonName(match.name) });
        setGuess('');
        setSuggestions([]);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!guess.trim()) return;
        attemptGuess(guess);
    };

    const handleSuggestionClick = (pokemon: PokemonRef) => {
        attemptGuess(pokemon.name);
        inputRef.current?.focus();
    };



    return (
        <div className="fixed top-0 left-0 right-0 z-30 bg-gray-950/95 backdrop-blur-md border-b border-gray-800">
            <div className="max-w-screen-xl mx-auto flex items-center gap-3 px-4 py-3">
                {/* Logo */}
                <h1 className="text-xl font-black tracking-tight bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent whitespace-nowrap hidden sm:block">
                    Poképelago
                </h1>

                {/* Input */}
                <form onSubmit={handleSubmit} className="flex-1 relative max-w-md">
                    <div className="flex items-center gap-2">
                        <span className="text-gray-400 text-sm whitespace-nowrap">Name a Pokémon:</span>
                        <input
                            ref={inputRef}
                            type="text"
                            value={guess}
                            onChange={(e) => setGuess(e.target.value)}
                            placeholder=""
                            className="flex-1 px-3 py-1.5 bg-gray-800 border border-gray-600 rounded text-white text-sm outline-none focus:border-green-500 transition-colors"
                            autoComplete="off"
                            spellCheck={false}
                        />
                    </div>

                    {/* Suggestions dropdown */}
                    {suggestions.length > 0 && (
                        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg overflow-hidden shadow-xl z-40">
                            {suggestions.map(p => (
                                <button
                                    key={p.id}
                                    type="button"
                                    onClick={() => handleSuggestionClick(p)}
                                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-700 transition-colors text-gray-200 flex justify-between items-center"
                                >
                                    <span>{formatPokemonName(p.name)}</span>
                                    <span className="text-gray-500 text-xs">#{p.id}</span>
                                </button>
                            ))}
                        </div>
                    )}
                </form>

                {/* Stats */}
                <div className="flex items-center gap-4 text-sm whitespace-nowrap">
                    <span className="text-green-400 font-bold">{checkedIds.size}</span>
                    <span className="text-gray-500">/</span>
                    <span className="text-gray-300">{allPokemon.length}</span>
                </div>

                {/* Feedback toast */}
                {feedback && (
                    <div className={`absolute top-full left-1/2 -translate-x-1/2 mt-2 px-4 py-2 rounded-lg text-sm font-medium shadow-lg transition-all animate-fade-in ${feedback.type === 'success' ? 'bg-green-600 text-white' :
                        feedback.type === 'already' ? 'bg-yellow-600 text-white' :
                            'bg-red-600 text-white'
                        }`}>
                        {feedback.type === 'success' && `✓ ${feedback.name}!`}
                        {feedback.type === 'already' && `Already guessed ${feedback.name}`}
                        {feedback.type === 'error' && `✗ Not found or not unlocked`}
                    </div>
                )}
            </div>
        </div>
    );
};
