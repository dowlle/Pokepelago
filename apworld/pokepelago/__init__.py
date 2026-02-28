from .items import item_table
from .locations import location_table
from .options import PokepelagoOptions
from worlds.AutoWorld import World
from BaseClasses import Region, Item, Location, Tutorial, ItemClassification, CollectionState
from worlds.LauncherComponents import Component, components, launch_subprocess, Type, icon_paths
from .data import pokemon_data

# Calculate item name groups for hints/logic
# Helper for region name (duplicate of class method but needed for static context)
def _get_region_name_static(dex_id):
    if 1 <= dex_id <= 151: return "Kanto"
    if 152 <= dex_id <= 251: return "Johto"
    if 252 <= dex_id <= 386: return "Hoenn"
    if 387 <= dex_id <= 493: return "Sinnoh"
    if 494 <= dex_id <= 649: return "Unova"
    if 650 <= dex_id <= 721: return "Kalos"
    if 722 <= dex_id <= 809: return "Alola"
    if 810 <= dex_id <= 905: return "Galar"
    if 906 <= dex_id <= 1025: return "Paldea"
    return "Unknown"

_pokemon_groups = {
    "Pokemon": set(item_table.keys() & {f"Pokemon #{dex_id}" for dex_id in pokemon_data})
}

for dex_id_str, p_data in pokemon_data.items():
    name = f"Pokemon #{dex_id_str}"
    if name not in item_table: continue
    
    # Types
    for t in p_data['types']:
        t_group = f"{t.capitalize()} Type Pokemon"
        if t_group not in _pokemon_groups: _pokemon_groups[t_group] = set()
        _pokemon_groups[t_group].add(name)
        
    # Region
    region = _get_region_name_static(int(dex_id_str))
    r_group = f"{region} Pokemon"
    if r_group not in _pokemon_groups: _pokemon_groups[r_group] = set()
    _pokemon_groups[r_group].add(name)

class PokepelagoWorld(World):
    """
    Pokepelago is a Pokemon guessing game where you unlock Pokemon to guess by finding them in the archipelago.
    """
    game = "pokepelago"
    options_dataclass = PokepelagoOptions
    options: PokepelagoOptions

    item_name_to_id = item_table
    location_name_to_id = location_table

    item_name_groups = _pokemon_groups

    # ID ranges
    # Items: 100001 - 101025
    # Locations: 200001 - 201025

    def __init__(self, multiworld, player):
        super(PokepelagoWorld, self).__init__(multiworld, player)
        self.dropped_dex_ids = set()

    def generate_early(self):
        # 1. Deadlock Prevention: if both Region and Type locks are active,
        # the player MUST start with at least 1 region and 1 type unlocked to make any guess.
        if self.options.enable_region_lock.value and self.options.type_locks.value:
            if self.options.starting_region_unlocks.value < 1:
                self.options.starting_region_unlocks.value = 1
            if self.options.starting_type_unlocks.value < 1:
                self.options.starting_type_unlocks.value = 1

        # 2. Calculate optimal drops for item pool balancing
        self._calculate_excess_and_drops()

        # 3. Calculate Win Condition Target early so we can refer to it
        goal_type = self.options.goal.value
        goal_amount = self.options.goal_amount.value
        total_possible = sum(1 for dex_id in pokemon_data if self._is_dex_id_enabled(int(dex_id)))

        if goal_type == 0:  # Any Pokemon
            self.required_catch_goal = min(goal_amount, total_possible)
        elif goal_type == 1:  # Percentage
            self.required_catch_goal = max(1, round((goal_amount / 100.0) * total_possible))
        else: # Region or Legendaries
            # Handled dynamically in set_rules via specific conditions
            self.required_catch_goal = -1

    def _calculate_excess_and_drops(self):
        # Calculate Logic Balance
        # Goal: Ensure Item Pool Size <= Total Locations.
        # Problem: Mandatory Items (Passes, Unlocks) and Special Items take up space.
        # If Dexsanity is ON, "Pokemon Items" fill ALL locations naturally.
        # Adding Mandatory/Special items creates an excess.
        # We must DROP Pokemon items (make them Free / Logic Exempt) to make room.

        total_enabled_locations = 0
        if self.options.enable_dexsanity.value:
            for start, end in self._get_enabled_gens():
                total_enabled_locations += (end - start + 1)
            
        # Add Extended Locations
        ext_count = self._count_enabled_extended_locations()
        total_enabled_locations += ext_count
            
        # 1. Mandatory Count (Passes + Unlocks)
        mandatory_count = 0
        if self.options.enable_region_lock.value:
            for gen_opt in [self.options.gen1, self.options.gen2, self.options.gen3, 
                            self.options.gen4, self.options.gen5, self.options.gen6, 
                            self.options.gen7, self.options.gen8, self.options.gen9]:
                if gen_opt.value:
                    mandatory_count += 1
        
        if self.options.type_locks.value:
            mandatory_count += 18
            
        # 2. Special items (Master Ball, Pokegear, Pokedex) are now weight-based
        # filler — no fixed counts, so special_count = 0.
        special_count = 0

        # 3. Handle Dropping
        # We need to drop (make Free/Filler) Pokemon items so that:
        # Number of Progression Items + Special Items <= Number of Locations
        # In this AP World, the pool consists of:
        # - Pokemon Items (Base ID pool)
        # - Special Items (Masterball, Pokegear, etc.)
        # - Mandatory Items (Region passes, Type unlocks)
        # 
        # Total item mass to place = len(enabled_ids) + special_count + mandatory_count
        # We drop items from `enabled_ids`.
        # When an item is dropped, its replacement is a Filler item (e.g. Master Ball, Trap, shiny upgrade).
        # But wait! If we drop a Pokemon item, it is NO LONGER progression. It becomes a Filler item.
        # But `create_items` creates EXACTLY `total_enabled_locations` items total.
        # If Dexsanity is ON, `len(enabled_ids)` is EXACTLY the number of base Pokemon locations.
        # Therefore, we just need to drop `special_count + mandatory_count` Pokemon items?
        # Not quite. We have `ext_count` Extended Locations as extra space.
        # So we have extra locations to absorb the mandatory/special items!
        
        enabled_ids = []
        for start, end in self._get_enabled_gens():
            enabled_ids.extend(range(start, end + 1))
            
        # Our base slots are either `len(enabled_ids)` (if dexsanity) or 0 (if no dexsanity).
        # Base items we generate are Pokemon 1..N.
        if self.options.enable_dexsanity.value:
            pokemon_item_count = len(enabled_ids)
        else:
            pokemon_item_count = 0 
            
        # Total items generated by create_items (before filler top-up)
        # = pokemon_item_count + special_count + mandatory_count
        
        # We need this to be <= total_enabled_locations
        excess = (pokemon_item_count + special_count + mandatory_count) - total_enabled_locations
        
        if excess > 0:
            # We must drop `excess` Pokemon items.
            self.multiworld.random.shuffle(enabled_ids)
            drops = min(excess, len(enabled_ids))
            self.dropped_dex_ids = set(enabled_ids[:drops])
        else:
            self.dropped_dex_ids = set()

    def _get_enabled_gens(self):
        enabled_gens = []
        if self.options.gen1.value: enabled_gens.append((1, 151))
        if self.options.gen2.value: enabled_gens.append((152, 251))
        if self.options.gen3.value: enabled_gens.append((252, 386))
        if self.options.gen4.value: enabled_gens.append((387, 493))
        if self.options.gen5.value: enabled_gens.append((494, 649))
        if self.options.gen6.value: enabled_gens.append((650, 721))
        if self.options.gen7.value: enabled_gens.append((722, 809))
        if self.options.gen8.value: enabled_gens.append((810, 905))
        if self.options.gen9.value: enabled_gens.append((906, 1025))
        return enabled_gens

    def _calculate_total_locations(self) -> int:
        """Calculate total locations without needing the region to already exist.
        Uses the same logic as create_regions(), safe to call from create_items()."""
        total = 0
        if self.options.enable_dexsanity.value:
            for start, end in self._get_enabled_gens():
                total += (end - start + 1)
        total += self._count_enabled_extended_locations()
        return total

    def get_filler_item_name(self) -> str:
        """Called by AP core to fill any remaining location gaps. Also used internally.
        Only non-progression items should be filler. Passes and Type Unlocks are
        progression items already placed as mandatory items — do NOT add extras here.
        Weights: Master Ball (high impact) > Pokegear / Pokedex (balanced) > Shiny Upgrade (cosmetic) > Traps
        """
        items  = ["Master Ball", "Pokegear", "Pokedex", "Shiny Upgrade", "Shuffle Trap", "Derpy Trap", "Release Trap"]
        weights = [25,            20,          20,        15,              10,             5,            5]
        return self.multiworld.random.choices(items, weights=weights, k=1)[0]

    def _is_dex_id_enabled(self, dex_id: int) -> bool:
        for start, end in self._get_enabled_gens():
            if start <= dex_id <= end:
                return True
        return False

    TRAP_ITEMS = {"Shuffle Trap", "Derpy Trap", "Release Trap"}
    USEFUL_ITEMS = {"Master Ball", "Pokegear", "Pokedex", "Shiny Upgrade"}

    def create_item(self, name: str) -> Item:
        item_id = item_table.get(name)
        if item_id is None:
            # Handle abstract / internal items
            if name == "Dex Entry":
                return Item(name, ItemClassification.progression, None, self.player)
            elif name == "Victory":
                return Item(name, ItemClassification.progression, None, self.player)
            
            # Weighted filler creates "Nothing" items
            if name == "Nothing":
                return Item(name, ItemClassification.filler, None, self.player)

            raise KeyError(f"Item '{name}' not found in item table")

        if name in self.TRAP_ITEMS:
            classification = ItemClassification.trap
        elif name in self.USEFUL_ITEMS:
            classification = ItemClassification.useful
        elif "Pass" in name or "Unlock" in name:
            classification = ItemClassification.progression_skip_balancing
        elif name.startswith("Pokemon #"):
            if self.options.enable_dexsanity.value:
                # Pokemon items MUST skip balancing so they aren't forcibly placed in late "Catch X" spheres,
                # which causes a circular dependency deadlock.
                classification = ItemClassification.progression_skip_balancing
            else:
                # If Dexsanity is OFF, the item itself just acts as a tracker/filler in the player's inventory
                # AP doesn't need to prioritize placing it because the "Event: Guessed X" locations handle the graph.
                classification = ItemClassification.filler
        else:
            classification = ItemClassification.filler
            
        return Item(name, classification, item_id, self.player)

    # collect_item override removed — Pokemon items are now classified as `progression`,
    # so AP's default collect_item already tracks them in prog_items automatically.
    # This means count_group("Pokemon") works correctly without any manual override.

    def create_items(self):
        enabled_items = []
        
        # 1. Determine which Pokemon Items are in the pool
        for name, item_id in item_table.items():
            # Skip special items, they are handled separately
            if item_id >= 106000:
                continue
            
            dex_id = item_id - 100000
            if self._is_dex_id_enabled(dex_id):
                # Check for dropped items (balancing)
                if dex_id in self.dropped_dex_ids:
                    continue

                # If Dexsanity is ON, we add the physical Pokemon items
                if self.options.enable_dexsanity.value:
                    item = self.create_item(name)
                    enabled_items.append(item)

        # 2. Virtual Event Tracking (If Dexsanity is OFF)
        dex_entry_items = []
        if not self.options.enable_dexsanity.value:
            # We create an abstract "Dex Entry" item for EVERY enabled Pokemon location
            # so the multiworld server can track guesses locally without cluttering the pool.
            for start_id, end_id in self._get_enabled_gens():
                for dex_id in range(start_id, end_id + 1):
                    # These items are internal only, so we give them no ID and classification progression
                    item = Item("Dex Entry", ItemClassification.progression, None, self.player)
                    dex_entry_items.append(item)


        # 3. Create Region Passes (if Region Lock enabled)
        region_passes = []
        if self.options.enable_region_lock.value:
            regions_info = [
                ("Gen 1", "Kanto Pass", self.options.gen1),
                ("Gen 2", "Johto Pass", self.options.gen2),
                ("Gen 3", "Hoenn Pass", self.options.gen3),
                ("Gen 4", "Sinnoh Pass", self.options.gen4),
                ("Gen 5", "Unova Pass", self.options.gen5),
                ("Gen 6", "Kalos Pass", self.options.gen6),
                ("Gen 7", "Alola Pass", self.options.gen7),
                ("Gen 8", "Galar Pass", self.options.gen8),
                ("Gen 9", "Paldea Pass", self.options.gen9),
            ]
            for gen_name, pass_name, gen_opt in regions_info:
                if gen_opt.value:
                    region_passes.append(self.create_item(pass_name))
        
        # 4. Create Type Unlocks (if Type Locks enabled)
        type_unlocks = []
        if self.options.type_locks.value:
            types_list = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 
                          'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Steel', 'Dark', 'Fairy']
            for t_name in types_list:
                item_name = f"{t_name} Unlock"
                type_unlocks.append(self.create_item(item_name))

        # 5. Handle Starting Inventory & Guarantees
        start_regions_count = self.options.starting_region_unlocks.value
        start_types_count = self.options.starting_type_unlocks.value
        start_pokemon_count = self.options.starting_pokemon_count.value

        # Safety floor: if Region Lock is on, the player must start with ≥1 region pass.
        if self.options.enable_region_lock.value and start_regions_count < 1:
            start_regions_count = 1
            
        if self.options.type_locks.value and start_types_count < 1:
            start_types_count = 1

        precollected = []
        
        available_region_passes = region_passes[:]
        available_type_unlocks = type_unlocks[:]
        available_pokemon_items = [i for i in enabled_items if "Pokemon #" in i.name]
        
        # A. Pre-collect Regions
        self.multiworld.random.shuffle(available_region_passes)
        for _ in range(min(len(available_region_passes), start_regions_count)):
            precollected.append(available_region_passes.pop())
            
        # B. Pre-collect Types
        self.multiworld.random.shuffle(available_type_unlocks)
        for _ in range(min(len(available_type_unlocks), start_types_count)):
            precollected.append(available_type_unlocks.pop())

        # C. Identify Starter Pokemon (Used later for pre_fill of passes)
        # We must identify `start_pokemon_count` locations that will be forced open.
        self.starter_dex_ids = []
        
        enabled_ids = []
        for start_id, end_id in self._get_enabled_gens():
            enabled_ids.extend(range(start_id, end_id + 1))
            
        self.multiworld.random.shuffle(enabled_ids)
        for _ in range(min(len(enabled_ids), start_pokemon_count)):
            self.starter_dex_ids.append(enabled_ids.pop())

        # Give the physical items if Dexsanity is ON so the player owns them instantly
        if self.options.enable_dexsanity.value:
            for dex_id in self.starter_dex_ids:
                starter_item_name = f"Pokemon #{dex_id}"
                for idx, item in enumerate(available_pokemon_items):
                    if item.name == starter_item_name:
                        precollected.append(available_pokemon_items.pop(idx))
                        break

        # D. Ensure Accessibility for Starters
        # If locks are active, the Starter Pokemon MUST have their requirements met by the starting inventory.
        if self.options.enable_region_lock.value or self.options.type_locks.value:
            current_regions = {i.name for i in precollected if "Pass" in i.name}
            current_types = {i.name for i in precollected if "Unlock" in i.name}
            
            for dex_id in self.starter_dex_ids:
                p_data = pokemon_data[str(dex_id)]
                
                # Check Region
                if self.options.enable_region_lock.value:
                    r_name = self._get_region_name(int(dex_id))
                    pass_name = f"{r_name} Pass"
                    if pass_name not in current_regions:
                        for idx, item in enumerate(available_region_passes):
                            if item.name == pass_name:
                                precollected.append(available_region_passes.pop(idx))
                                current_regions.add(pass_name)
                                break

                # Check Types (Any Mode)
                if self.options.type_locks.value:
                    p_types = p_data['types']
                    p_type_items = [f"{t.capitalize()} Unlock" for t in p_types]
                    
                    if not any(t in current_types for t in p_type_items):
                        self.multiworld.random.shuffle(p_type_items)
                        for t_name in p_type_items:
                            for idx, item in enumerate(available_type_unlocks):
                                if item.name == t_name:
                                    precollected.append(available_type_unlocks.pop(idx))
                                    current_types.add(t_name)
                                    break
                            if any(t in current_types for t in p_type_items): break

        # 6. Finalize Item Pool
        for item in precollected:
            self.multiworld.precollected_items[self.player].append(item)
            
        pool_items = []
        pool_items.extend(available_pokemon_items) 
        
        special_items = [i for i in enabled_items if "Pokemon #" not in i.name]
        pool_items.extend(special_items)
        
        pool_items.extend(available_region_passes)
        pool_items.extend(available_type_unlocks)
        
        # Add the Dex Entry Event items to the pool so they can be placed later
        pool_items.extend(dex_entry_items)
        
        # Top up the item pool to exactly match the number of locations.
        total_locations = self._calculate_total_locations()
        
        # Crucial adjustment: 'Events' (Dex Entries) occupy locations, so `pool_items` size MUST equal `total_locations`.
        needed_filler = total_locations - len(pool_items)

        filler_table = [
            ("Master Ball",    self.options.filler_weight_master_ball.value),
            ("Pokegear",       self.options.filler_weight_pokegear.value),
            ("Pokedex",        self.options.filler_weight_pokedex.value),
            ("Shiny Upgrade",  self.options.filler_weight_shiny_upgrade.value),
            ("Shuffle Trap",   self.options.filler_weight_shuffle_trap.value),
            ("Derpy Trap",     self.options.filler_weight_derpy_trap.value),
            ("Release Trap",   self.options.filler_weight_release_trap.value),
            (None,             self.options.filler_weight_nothing.value),
        ]
        filler_names = [name for name, _ in filler_table]
        filler_weights = [w for _, w in filler_table]

        if sum(filler_weights) == 0:
            filler_names = [None]
            filler_weights = [1]

        chosen = self.multiworld.random.choices(filler_names, weights=filler_weights, k=max(0, needed_filler))
        for name in chosen:
            if name is None:
                pool_items.append(self.create_item(self.get_filler_item_name()))
            else:
                pool_items.append(self.create_item(name))
        
        self.multiworld.itempool += pool_items

        import logging
        logging.info(f"[Pokepelago] Player {self.player} Locations: {total_locations} | Items in pool: {len(pool_items)} | Precollected: {len(precollected)}")


    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        # 1. Create Virtual Regions for logic mapping
        virtual_regions = {}
        regions_to_create = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea"]
        
        for r_name in regions_to_create:
            reg = Region(f"{r_name} Region", self.player, self.multiworld)
            virtual_regions[r_name] = reg
            self.multiworld.regions.append(reg)
            
            # Create Entrance from Menu
            ent = next((e for e in menu.exits if e.name == f"To {r_name}"), None)
            if not ent:
                from BaseClasses import Entrance
                ent = Entrance(self.player, f"To {r_name}", menu)
                menu.exits.append(ent)
            ent.connect(reg)

            # Assign Region Lock access rule to the Entrance
            if self.options.enable_region_lock.value:
                pass_name = f"{r_name} Pass"
                ent.access_rule = lambda state, pn=pass_name: state.has(pn, self.player)

        # 2. Legendary Gating Region
        leg_reg = None
        if self.options.legendary_gating.value > 0:
            leg_reg = Region("Legendary Encounters", self.player, self.multiworld)
            self.multiworld.regions.append(leg_reg)
            
            from BaseClasses import Entrance
            ent = Entrance(self.player, "To Legendaries", menu)
            menu.exits.append(ent)
            ent.connect(leg_reg)
            
            # We defer adding the exact access rule (checking counts) to `set_rules`

        # 3. Populate Locations into appropriate Regions
        
        for name, loc_id in location_table.items():
            if 200001 <= loc_id <= 201025:
                dex_id = loc_id - 200000
                if self._is_dex_id_enabled(dex_id):
                    # Determine target region
                    target_region = menu
                    is_legendary = pokemon_data[str(dex_id)]["is_legendary"]
                    
                    if dex_id in getattr(self, "starter_dex_ids", []):
                        # Starters ALWAYS stay in Menu and ALWAYS have NO regional/type locks
                        target_region = menu
                    elif leg_reg and is_legendary:
                        target_region = leg_reg
                    else:
                        r_name = self._get_region_name(dex_id)
                        target_region = virtual_regions[r_name]
                    
                    # If Dexsanity is ON, we add the base physical location
                    if self.options.enable_dexsanity.value:
                        loc = Location(self.player, name, loc_id, target_region)
                        target_region.locations.append(loc)
                    else:
                        # Event Generation for Dexsanity OFF
                        # We create a virtual event location instead of the standard physical one
                        event_loc = Location(self.player, f"Event: Guessed {name}", None, target_region)
                        target_region.locations.append(event_loc)
                        
                        # We don't place locked items here yet, we do that in set_rules or a later pass
                        # However, since AP needs events resolved immediately, we will do it now by extracting them from pool early.

            elif loc_id > 201025:
                if self._is_extended_location_enabled(name):
                    loc = Location(self.player, name, loc_id, menu)
                    menu.locations.append(loc)

        # Place Dex Entry items into their event locations
        if not self.options.enable_dexsanity.value:
            dex_entry_items = [i for i in self.multiworld.itempool if i.name == "Dex Entry" and i.player == self.player]
            dex_entry_index = 0
            
            for region in self.multiworld.regions:
                if region.player == self.player:
                    for loc in region.locations:
                        if loc.name.startswith("Event: Guessed "):
                            if dex_entry_index < len(dex_entry_items):
                                item = dex_entry_items[dex_entry_index]
                                loc.place_locked_item(item)
                                self.multiworld.itempool.remove(item)
                                dex_entry_index += 1
                                
                                # Setup Pokedex group
                                if "Pokedex" not in self.item_name_groups:
                                    self.item_name_groups["Pokedex"] = set()
                                self.item_name_groups["Pokedex"].add("Dex Entry")

        goal_loc = Location(self.player, "Goal Met", None, menu)
        menu.locations.append(goal_loc)
        victory_item = Item("Victory", ItemClassification.progression, None, self.player)
        goal_loc.place_locked_item(victory_item)

    def _count_enabled_extended_locations(self) -> int:
        count_locs = 0
        for name, loc_id in location_table.items():
            if loc_id > 201025:
                if self._is_extended_location_enabled(name):
                    count_locs += 1
        return count_locs

    def _is_extended_location_enabled(self, name: str) -> bool:
        parts = name.split()
        try:
            if "Type" in name:
                count = int(parts[1])
                t_name = parts[2]
                group_name = f"{t_name} Type Pokemon"
                
                possible = 0
                if group_name in self.item_name_groups:
                    for p_name in self.item_name_groups[group_name]:
                        try:
                            d_id = int(p_name.split("#")[1])
                            if self._is_dex_id_enabled(d_id):
                                possible += 1
                        except: pass
                return possible >= count
            else:
                count = int(parts[1])
                r_name = parts[2]
                group_name = f"{r_name} Pokemon"
                
                possible = 0
                if group_name in self.item_name_groups:
                        for p_name in self.item_name_groups[group_name]:
                            try:
                                d_id = int(p_name.split("#")[1])
                                if self._is_dex_id_enabled(d_id):
                                    possible += 1
                            except: pass
                return possible >= count
        except Exception as e:
            print(f"DEBUG EXCEPTION in {name}: {e}")
            return False

    def _get_region_name(self, dex_id: int) -> str:
        if 1 <= dex_id <= 151: return "Kanto"
        if 152 <= dex_id <= 251: return "Johto"
        if 252 <= dex_id <= 386: return "Hoenn"
        if 387 <= dex_id <= 493: return "Sinnoh"
        if 494 <= dex_id <= 649: return "Unova"
        if 650 <= dex_id <= 721: return "Kalos"
        if 722 <= dex_id <= 809: return "Alola"
        if 810 <= dex_id <= 905: return "Galar"
        if 906 <= dex_id <= 1025: return "Paldea"
        return "Unknown"

    def set_rules(self):
        enable_dexsanity = self.options.enable_dexsanity.value
        enable_region_lock = self.options.enable_region_lock.value
        use_type_locks = self.options.type_locks.value
        leg_gating = self.options.legendary_gating.value

        # --- Build per-Pokemon access rules ---
        # Each rule is: has(RegionPass) AND has_any(TypeUnlocks)
        # This is applied directly on each location — no Region Entrances.
        pokemon_base_reqs = {}  # dex_id -> lambda state: bool (full rule, used for Extended Locs when Dex=OFF)
        non_leg_reqs = []

        # --- Build per-Pokemon access rules ---
        # Each rule is: has(RegionPass) AND has_any(TypeUnlocks)
        # We only really need to check Type Unlocks here, because the Region Entrance 
        # inherently gates access to the locations physically inside the region.
        # However, checking both is perfectly safe.
        pokemon_base_reqs = {}  # dex_id -> lambda state: bool (full rule, used for Extended Locs when Dex=OFF)
        non_leg_reqs = []

        for dex_id_str, p_data in pokemon_data.items():
            dex_id = int(dex_id_str)
            if not self._is_dex_id_enabled(dex_id):
                continue

            region_pass = f"{self._get_region_name(dex_id)} Pass" if enable_region_lock else None
            t_unlocks = tuple(f"{t.capitalize()} Unlock" for t in p_data['types']) if use_type_locks else ()

            def make_req(rp, tus):
                def check(state, p=self.player):
                    if rp and not state.has(rp, p): return False
                    if tus and not state.has_any(tus, p): return False
                    return True
                return check

            pokemon_base_reqs[dex_id] = make_req(region_pass, t_unlocks)
            if not p_data['is_legendary']:
                non_leg_reqs.append(pokemon_base_reqs[dex_id])

        tracking_group = "Pokemon" if enable_dexsanity else "Pokedex"

        # Wrap legendary requirements with the legendary gating count
        if leg_gating > 0:
            for dex_id_str, p_data in pokemon_data.items():
                dex_id = int(dex_id_str)
                if p_data['is_legendary'] and dex_id in pokemon_base_reqs:
                    old_req = pokemon_base_reqs[dex_id]
                    def make_leg_req(base_r, nreqs, req_count, tk_group):
                        def check(state, p=self.player):
                            if not base_r(state): return False
                            if state.count_group(tk_group, p) < req_count: return False
                            return True
                        return check
                    pokemon_base_reqs[dex_id] = make_leg_req(old_req, non_leg_reqs, leg_gating, tracking_group)

            # Let's also enforce this rule on the Region Entrance to "Legendary Encounters"
            leg_ent = next((e for menu in self.multiworld.regions if menu.name == "Menu" for e in menu.exits if e.name == "To Legendaries"), None)
            if leg_ent:
                leg_ent.access_rule = lambda state, count=leg_gating, g=tracking_group: state.count_group(g, self.player) >= count

        # --- Apply rules to locations ---
        for loc in self.multiworld.get_locations(self.player):
            if loc.address is None and loc.name.startswith("Event: Guessed Catch "):
                # Event Locations for Dexsanity=OFF
                pkmn_name = loc.name.replace("Event: Guessed Catch ", "")
                # Find dex_id from pokemon_data
                dex_id = None
                for d_id_str, pd in pokemon_data.items():
                    if pd['name'] == pkmn_name:
                        dex_id = int(d_id_str)
                        break
                if dex_id and dex_id not in getattr(self, "starter_dex_ids", []):
                    # Apply rules if it's not a starter
                    loc.access_rule = pokemon_base_reqs[dex_id]
            
            elif loc.address is not None and 200001 <= loc.address <= 201025:
                # Base Physical Locations for Dexsanity=ON
                dex_id = loc.address - 200000
                if dex_id not in getattr(self, "starter_dex_ids", []):
                     loc.access_rule = pokemon_base_reqs.get(dex_id, lambda state: True)

            elif loc.address is not None and loc.address > 201025:
                # Extended Location ("Catch X Type/Region Pokemon")
                # Both ON and OFF can now use `has_group` safely because we built abstract Events!
                try:
                    d_id = int(name.split("#")[1])
                    if d_id in pokemon_base_reqs:
                        pokemon_group_ext_reqs[g].append(pokemon_base_reqs[d_id])
                except (IndexError, ValueError):
                    pass

        for loc in menu.locations:
            if loc.address <= 201025:
                # Base Location - Apply item_rule to prevent direct circular dependencies
                dex_id = loc.address - 200000
                forbidden_items = set()
                
                if enable_region_lock:
                    forbidden_items.add(f"{self._get_region_name(dex_id)} Pass")
                
                if use_type_locks and str(dex_id) in pokemon_data:
                    for t in pokemon_data[str(dex_id)]['types']:
                        forbidden_items.add(f"{t.capitalize()} Unlock")

                if forbidden_items:
                    loc.item_rule = lambda item, forbidden=forbidden_items: item.name not in forbidden
                
                # Apply access_rule — Now enabled because of the Safety Floor guarantee!
                # This ensures indirect circularities (A -> B -> A) are impossible.
                base_rule = pokemon_base_reqs.get(dex_id, lambda state: True)
                
                # Merge with Legendary Gating if applicable
                is_leg = pokemon_data[str(dex_id)]['is_legendary'] if str(dex_id) in pokemon_data else False
                if leg_gating > 0 and is_leg:
                    loc.access_rule = lambda state, b=base_rule, c=leg_gating: \
                        b(state) and state.has_group("Pokemon", self.player, c)
                else:
                    loc.access_rule = base_rule
            elif loc.address > 201025:
                # Extended Locations ("Catch X Type/Region Pokemon")
                
                # Apply item_rule to prevent circular dependencies on the extended location itself
                try:
                    parts = loc.name.split()
                    if "Type" in loc.name:
                        t_name = parts[2]
                        if use_type_locks:
                            forbidden = f"{t_name} Unlock"
                            loc.item_rule = lambda item, f=forbidden: item.name != f
                    else:
                        r_name = parts[2]
                        if enable_region_lock:
                            forbidden = f"{r_name} Pass"
                            loc.item_rule = lambda item, f=forbidden: item.name != f
                except Exception:
                    pass

                if enable_dexsanity:
                    # When Dexsanity is ON, Pokemon items ARE in the pool.
                    # Use AP's fast native has_group to gate extended locations
                    # based on how many Pokemon items the player has collected.
                    try:
                        parts = loc.name.split()
                        count = int(parts[1])
                        if "Type" in loc.name:
                            group_name = f"{parts[2]} Type Pokemon"
                        else:
                            group_name = f"{parts[2]} Pokemon"
                        loc.access_rule = lambda state, g=group_name, c=count: state.has_group(g, self.player, c)
                    except Exception:
                        loc.access_rule = lambda state: True
                # When Dexsanity is OFF, there are no Pokemon items in the pool,
                # so has_group would always return 0. Extended locations are the
                # ONLY locations in this mode and get filler/useful items.
                # No access rule needed — leave them freely accessible.

        # Victory condition
                    parts = loc.name.split()
                    count = int(parts[1])
                    group_name = f"{parts[2]} Type Pokemon" if "Type" in loc.name else f"{parts[2]} Pokemon"
                    loc.access_rule = lambda state, g=group_name, c=count: state.has_group(g, self.player, c)
                except Exception:
                    loc.access_rule = lambda state: True


        # --- Goal Met event location access rule ---
        goal_loc = self.multiworld.get_location("Goal Met", self.player)
        goal_type = self.options.goal.value

        def count_all_pokemon(state):
            return state.count_group(tracking_group, self.player)

        if goal_type in (0, 1):  # Any Pokemon or Percentage
            goal_loc.access_rule = lambda state: count_all_pokemon(state) >= self.required_catch_goal

        elif goal_type == 2:  # Region Completion
            region_id = self.options.goal_region.value
            region_name = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea"][region_id - 1]
            region_pokemon = [f"Pokemon #{d_id}" if enable_dexsanity else f"Event: Guessed Pokemon #{d_id}" 
                              for d_id, data in pokemon_data.items()
                              if self._get_region_name(int(d_id)) == region_name and self._is_dex_id_enabled(int(d_id))]
            
            # Since Event Tracking generates explicit locations/items, we can just check if we have the items we placed there
            # Physical items for dexsanity=ON, Event: Guessed locations logically holding Dex Entries for OFF
            if enable_dexsanity:
                goal_loc.access_rule = lambda state, pjs=region_pokemon: all(state.has(p, self.player) for p in pjs)
            else:
                 # In Dexsanity=OFF, the player doesn't have "Event: Guessed..." items.
                 # They have "Dex Entry" items, but they aren't uniquely named per Pokemon.
                 # Instead, we must rely on evaluating the base rules for all Pokemon in that region.
                 region_reqs = [pokemon_base_reqs[int(d_id)] for d_id, data in pokemon_data.items()
                           if self._get_region_name(int(d_id)) == region_name and self._is_dex_id_enabled(int(d_id))]
                 goal_loc.access_rule = lambda state, reqs=region_reqs: all(r(state) for r in reqs)

        elif goal_type == 3:  # All Legendaries
            leg_reqs = [pokemon_base_reqs[int(d_id)] for d_id, data in pokemon_data.items()
                        if data['is_legendary'] and self._is_dex_id_enabled(int(d_id))]
            
            if enable_dexsanity:
                legendaries = [f"Pokemon #{d_id}" for d_id, data in pokemon_data.items()
                               if data['is_legendary'] and self._is_dex_id_enabled(int(d_id))]
                goal_loc.access_rule = lambda state, legs=legendaries: all(state.has(l, self.player) for l in legs)
            else:
                goal_loc.access_rule = lambda state, reqs=leg_reqs: all(r(state) for r in reqs)

        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def pre_fill(self) -> None:
        """Pre-place Region Passes and Type Unlocks into initially-accessible locations.
        
        With the new architecture, Starter Locations are designated early on and have 
        NO access rules attached to them (they serve as the Sphere 0 logic anchor).
        We simply dump all the required passes into these specific slots.
        """
        from Fill import fill_restrictive, FillError

        key_items = [item for item in self.multiworld.itempool
                     if item.player == self.player and ("Pass" in item.name or "Unlock" in item.name)]
        if not key_items:
            return

        for item in key_items:
            self.multiworld.itempool.remove(item)

        # Step 1: Find the actual Starter Locations. 
        # These are the locations corresponding to `self.starter_dex_ids`
        starter_location_names = []
        for dex_id in getattr(self, "starter_dex_ids", []):
            try:
                pkmn_name = pokemon_data[str(dex_id)]['name']
                if self.options.enable_dexsanity.value:
                    starter_location_names.append(f"Catch {pkmn_name}")
                else:
                    starter_location_names.append(f"Event: Guessed Catch {pkmn_name}")
            except Exception:
                pass
                
        open_locations = [
            loc for loc in self.multiworld.get_unfilled_locations(self.player)
            if loc.name in starter_location_names
        ]
        
        # In incredibly rare cases / highly restricted seeds, we might not have enough starter locations for the keys.
        # Fall back to any open location if we need more room.
        base_state = self.multiworld.state.copy()
        if len(open_locations) < len(key_items):
            extra_locs = [
                loc for loc in self.multiworld.get_unfilled_locations(self.player)
                if loc.can_reach(base_state) and loc not in open_locations
            ]
            self.random.shuffle(extra_locs)
            needed = len(key_items) - len(open_locations)
            open_locations.extend(extra_locs[:needed])

        attempts_remaining = 2
        while attempts_remaining > 0:
            attempts_remaining -= 1
            locs_copy = open_locations.copy()
            items_copy = key_items.copy()
            self.random.shuffle(locs_copy)
            try:
                fill_restrictive(
                    self.multiworld, base_state, locs_copy, items_copy,
                    single_player_placement=True, lock=True,
                    name=f"Pokepelago Key Items P{self.player}"
                )
                break
            except FillError as exc:
                if attempts_remaining <= 0:
                    raise exc
                # Undo partial placement and retry
                import logging
                logging.debug(f"[Pokepelago] pre_fill attempt failed for P{self.player}, retrying.")
                for loc in open_locations:
                    if loc.locked:
                        loc.locked = False
                    if loc.item is not None and loc.item in key_items:
                        loc.item.location = None
                        loc.item = None


    def fill_slot_data(self) -> dict:
        return {
            "gen1": self.options.gen1.value,
            "gen2": self.options.gen2.value,
            "gen3": self.options.gen3.value,
            "gen4": self.options.gen4.value,
            "gen5": self.options.gen5.value,
            "gen6": self.options.gen6.value,
            "gen7": self.options.gen7.value,
            "gen8": self.options.gen8.value,
            "gen9": self.options.gen9.value,
            "enable_dexsanity": self.options.enable_dexsanity.value,
            "enable_region_lock": self.options.enable_region_lock.value,
            "type_locks": self.options.type_locks.value,
            "type_lock_mode": self.options.type_lock_mode.value,
            "legendary_gating": self.options.legendary_gating.value,
            "filler_weight_master_ball": self.options.filler_weight_master_ball.value,
            "filler_weight_pokegear": self.options.filler_weight_pokegear.value,
            "filler_weight_pokedex": self.options.filler_weight_pokedex.value,
            "filler_weight_shiny_upgrade": self.options.filler_weight_shiny_upgrade.value,
            "filler_weight_shuffle_trap": self.options.filler_weight_shuffle_trap.value,
            "filler_weight_derpy_trap": self.options.filler_weight_derpy_trap.value,
            "filler_weight_release_trap": self.options.filler_weight_release_trap.value,
            "filler_weight_nothing": self.options.filler_weight_nothing.value,
            "goal": self.options.goal.value,
            "goal_amount": self.options.goal_amount.value,
            "goal_region": self.options.goal_region.value,
            "starting_pokemon_count": self.options.starting_pokemon_count.value,
            "starting_type_unlocks": self.options.starting_type_unlocks.value,
            "starting_region_unlocks": self.options.starting_region_unlocks.value,
            "starter_dex_ids": getattr(self, "starter_dex_ids", []),
        }
