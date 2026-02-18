# Pokepelago

Pokepelago is a Pokemon guessing game randomizer integrated with [Archipelago](https://archipelago.gg/). Unlock Pokemon by finding items in a multiworld, and then guess them in the Pokepelago web interface to send checks back to the server.

## Features

- **Guessing Game**: Unlock Pokemon silhouettes or names and guess them to progress.
- **Archipelago Integration**: Full sync with Archipelago servers. Received items unlock Pokemon; guessing them sends location checks.
- **Shadow Mode**: Configurable silhouetted Pokemon for an extra challenge.
- **Special Items**: 
    - **Master Ball**: Instantly guess a Pokemon even if not unlocked.
    - **Pokegear**: Remove shadows for a specific Pokemon.
    - **Pokedex**: Reveal the start of a Pokemon's name as a hint.
- **Logic Overhaul**: 
    - **Region Locking**: Requires finding Region Passes to guess Pokemon in that region.
    - **Type Locking**: Requires finding Type Unlocks to guess Pokemon of that type.
    - **Legendary Gating**: Requires guessing a set number of standard Pokemon before Legendaries become available.
- **Hint Support**: Server-side hints reveal Pokemon shadows even if you haven't found the item yet.
- **Widescreen & Masonry Layouts**: Customizable UI for different screen sizes.

---

## Getting Started

### 1. Web Client Setup
The web client is built with React, TypeScript, and Vite.

```bash
# Install dependencies
npm install

# Run the development server
npm run dev

# Build for production
npm run build
```

### 2. Archipelago World (.apworld)
To play with Archipelago, you need the `pokepelago.apworld` file.

#### Generating AP Data
The game requires metadata about types and legendary status for advanced logic.

```bash
# Requires requests library
python generate_ap_data.py
```
This script updates `apworld/pokepelago/items.py`, `apworld/pokepelago/locations.py`, and `apworld/pokepelago/data.py` using data from PokeAPI. It also prepares `src/data/pokemon_metadata.json` for the frontend.

#### Creating the .apworld file
The `.apworld` file is a zipped version of the `apworld/pokepelago` directory.

```bash
# From the project root:
python -c "import shutil; shutil.make_archive('pokepelago', 'zip', 'apworld', 'pokepelago'); import os; os.replace('pokepelago.zip', 'pokepelago.apworld')"
```
This creates `pokepelago.apworld` in your root directory. Place this file in your Archipelago `lib/worlds` directory.

---

## Configuration & Settings

### Archipelago Options (YAML)
These settings are defined in your player YAML file and affect the multiworld generation.

- **Generations (gen1-gen9)**: Enable or disable specific Pokemon generations.
- **Shadows**: 
  - `on` (Default): Unlocked Pokemon appear as silhouettes.
  - `off`: Unlocked Pokemon appear as `?` until hinted or guessed.
- **Goal**:
  - `total_pokemon` (Default): Win after guessing a specific number of Pokemon.
  - `percentage`: Win after guessing a percentage of all available Pokemon.
- **Goal Amount**: The target count or percentage for victory (Default: 50).
- **Starting Pokemon Count**: The number of random Pokemon unlocked at the start (Default: 5).

### Game UI Settings
Accessible via the Settings panel in the web interface.

- **Widescreen Mode**: Switches between fixed-width and full-width layout.
- **Fit Regions (Masonry)**: Packs regions densely to remove gaps.
- **Sprite Scaling**: Adjust the size of Pokemon sprites in their boxes.

---

## Development

- `src/context/GameContext.tsx`: Manages the Archipelago client connection and global game state.
- `src/components/DexGrid.tsx`: The main display for the Pokemon generations.
- `apworld/pokepelago/`: Python logic for the Archipelago world.

## Documentation
- [Network Protocol](ap_docs_network_protocol.md)
- [AP World API](ap_docs_world_api.md)
