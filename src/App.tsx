import React from 'react';
import { GameProvider, useGame } from './context/GameContext';
import { DexGrid } from './components/DexGrid';
import { GlobalGuessInput } from './components/GlobalGuessInput';
import { SettingsPanel } from './components/SettingsPanel';
import { Settings, Wifi, WifiOff } from 'lucide-react';

const GameContent: React.FC = () => {
  const { allPokemon, unlockedIds, checkedIds, unlockPokemon, isLoading, isConnected } = useGame();
  const [isSettingsOpen, setIsSettingsOpen] = React.useState(false);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-green-500 rounded-full animate-spin border-t-transparent"></div>
          <span className="text-gray-400">Loading Pokédex...</span>
        </div>
      </div>
    );
  }

  // Debug: unlock random Pokemon
  const unlockRandom = () => {
    if (allPokemon.length === 0) return;
    const eligible = allPokemon.filter(p => !unlockedIds.has(p.id));
    if (eligible.length === 0) return;
    const pick = eligible[Math.floor(Math.random() * eligible.length)];
    unlockPokemon(pick.id);
  };

  const unlockBatch = () => {
    // Unlock 10 random pokemon
    const eligible = allPokemon.filter(p => !unlockedIds.has(p.id));
    const count = Math.min(10, eligible.length);
    const shuffled = [...eligible].sort(() => Math.random() - 0.5);
    shuffled.slice(0, count).forEach(p => unlockPokemon(p.id));
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans">
      <GlobalGuessInput />

      {/* Toolbar - below the guess input  */}
      <div className="fixed top-[52px] left-0 right-0 z-20 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-screen-xl mx-auto flex items-center justify-between px-4 py-2">
          <div className="flex items-center gap-3">
            {/* Connection status */}
            <div className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded ${isConnected ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
              {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
              {isConnected ? 'Connected' : 'Offline'}
            </div>

            <span className="text-xs text-gray-500">
              Unlocked: <span className="text-yellow-400 font-bold">{unlockedIds.size}</span>
              {' · '}
              Checked: <span className="text-green-400 font-bold">{checkedIds.size}</span>
              {' / '}
              {allPokemon.length}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-1.5 hover:bg-gray-800 rounded transition-colors text-gray-400 hover:text-white"
              title="Settings"
            >
              <Settings size={16} />
            </button>
          </div>
        </div>
      </div>

      <SettingsPanel isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />

      {/* Main grid area */}
      <main className="pt-[100px] max-w-screen-xl mx-auto">
        <DexGrid />

        {/* Debug Controls */}
        <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-gray-800 z-20">
          <div className="max-w-screen-xl mx-auto flex items-center justify-between px-4 py-2">
            <span className="text-xs text-gray-500 uppercase tracking-wider font-bold">Debug</span>
            <div className="flex gap-2">
              <button
                onClick={unlockRandom}
                className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-xs transition-colors border border-gray-700"
              >
                Unlock 1
              </button>
              <button
                onClick={unlockBatch}
                className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-xs transition-colors border border-gray-700"
              >
                Unlock 10
              </button>
              <button
                onClick={() => unlockPokemon(25)}
                className="px-3 py-1 bg-yellow-900/50 hover:bg-yellow-900/80 text-yellow-200 rounded text-xs transition-colors border border-yellow-700/50"
              >
                Unlock Pikachu
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <GameProvider>
      <GameContent />
    </GameProvider>
  );
};

export default App;
