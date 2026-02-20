# Poképelago

Poképelago is a Pokémon guessing game randomizer integrated with [Archipelago](https://archipelago.gg/). Unlock Pokémon by finding items in a multiworld, and then guess them in the Poképelago web interface to send checks back to the server and help your friends!

**Play Now:** [https://dowlle.github.io/Pokepelago/](https://dowlle.github.io/Pokepelago/)

---

## Getting Started (For Players)

### 1. Download the Sprites
Due to copyright protections and our community guidelines, **this repository does not host, provide, or promote the ripping of any Nintendo properties or official assets.** All sprites must be sourced and imported entirely by the user.

You have several options to obtain compatible sprites:
1. **Supply your own**: Create or source your own `.png` or `.gif` sprites. They must be named by their National Dex number (e.g., `1.png`, `25.png`, `1025.png`).
2. **Community Projects**: Keep an eye out for ongoing community-driven projects aimed at creating custom, original sprite sets for the game.
3. **Public Repositories**: You can download public archives like the [PokeAPI Sprites Repository](https://github.com/PokeAPI/sprites/archive/refs/heads/master.zip) as a ZIP file at your own risk.

**To import your sprites (Optional but recommended):**
1. If you downloaded a ZIP file, extract it to a folder on your computer.
2. Open Poképelago in your browser.
3. On the start screen or in the settings panel, click the **"Upload Sprites Folder"** button.
4. Select the extracted folder (`sprites-master` or similar). Your browser will ask for permission to read these files. It will automatically find the necessary standard, shiny, and animated sprites.
5. Poképelago will securely store these images in your browser's local storage for future use!

*Note: You can play the game without downloading any sprites. The game will simply use text-based placeholders instead of images.*

### 2. Connect to Archipelago
Once your sprites are loaded, you're ready to join a multiworld!

1. Generate an Archipelago multiworld game using the `pokepelago.apworld` file (see the generation instructions if you are the host).
2. Open Poképelago and choose **"Play Archipelago"**.
3. In the settings panel (gear icon) or the top bar, enter your Archipelago connection details:
   - **Hostname:** e.g., `archipelago.gg` or `localhost`
   - **Port:** (Provided by your host)
   - **Slot Name:** (Your player name in the YAML file)
   - **Password:** (If your room has one)
4. Click **Connect**!

### 3. How to Play
- **Guessing Game**: As you receive "Pokemon #..." items from the multiworld, their silhouettes (or empty boxes) will appear in the grid. Type their names in the top bar to guess them!
- **Extended Checks**: Keep an eye on your goal! Catching specific types or regions of Pokémon might unleash even more checks into the multiworld (e.g., "Catch 10 Water Type Pokemon").
- **Special Items**:
    - **Master Ball**: Instantly guess a Pokémon even if you haven't received its item yet.
    - **Pokegear**: Remove the shadow for a specific Pokémon to see its true colors.
    - **Pokedex**: Reveal the start of a Pokémon's name as a hint.
- **Advanced Logic**: Your host may have enabled Region Locks (requiring you to find a "Kanto Pass" before guessing Kanto Pokémon) or Type Locks (requiring you to find "Water Unlock" before guessing Water types).

---

## Hosting a Game (For Organizers)

To generate a multiworld with Poképelago, you need the `.apworld` file and player YAML files.

1. Download `pokepelago.apworld` from the latest release (or build it from source).
2. Place it in your Archipelago installation's `lib/worlds` folder.
3. Collect the `pokepelago.yaml` files created by your players and place them in your `Players` folder.

### Creating a YAML File (For Players)
Players should create their own YAML file to configure their settings for the game and send it to the host. 
You can base your ruleset off the [Standard Poképelago YAML](https://github.com/dowlle/Pokepelago/blob/main/pokepelago.yaml).

### Archipelago Options (YAML)
- **Generations (gen1-gen9)**: Enable or disable specific Pokémon generations.
- **Goal**: Win by guessing a specific number of Pokémon, a percentage of the Dex, completing a region, or catching all Legendaries.
- **Logic Locks**: Enable Region Locks, Dexsanity, Type Locks, and Legendary Gating for complex routing. Please be aware that type locks and region locks are untested and may not work as intended. Please do not use them in a real game.

---

## Development

Poképelago's web client is built with React, TypeScript, and Vite.

### Local Setup
```bash
# Install dependencies
npm install

# Run the development server
npm run dev

# Build for production
npm run build
```

### Building the .apworld file
The `.apworld` file is a zipped version of the `apworld/pokepelago` directory. From the project root, run:
```bash
python -c "import os, zipfile; zipfile.ZipFile('pokepelago.apworld', 'w', zipfile.ZIP_DEFLATED).write('apworld/pokepelago', 'apworld/pokepelago')"
```
*(Or use whatever internal script you prefer to ZIP the directory without `.pyc` files).*
