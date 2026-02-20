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
        self._calculate_excess_and_drops()

    def _calculate_excess_and_drops(self):
        # Calculate Logic Balance
        # Goal: Ensure Item Pool Size <= Total Locations.
        # Problem: Mandatory Items (Passes, Unlocks) and Special Items take up space.
        # If Dexsanity is ON, "Pokemon Items" fill ALL locations naturally.
        # Adding Mandatory/Special items creates an excess.
        # We must DROP Pokemon items (make them Free / Logic Exempt) to make room.

        total_enabled_locations = 0
        for start, end in self._get_enabled_gens():
            total_enabled_locations += (end - start + 1)
            
        # Add Extended Locations
        ext_count = self._count_enabled_extended_locations()
        # print(f"DEBUG: Extended Locations Count: {ext_count}")
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
            
        # 2. Special Count
        special_count = (self.options.master_ball_count.value + 
                         self.options.pokegear_count.value + 
                         self.options.pokedex_count.value)

        # 3. Starting Inventory Count (Removed from Pool)
        # These create "Holes" in the locations that can be filled by Mandatory/Special items.
        # We assume optimal filling, so we subtract from the "Injected Mass".
        
        # Determine actual removed count (clamped by availability)
        # Regions
        enabled_regions = 0
        if self.options.enable_region_lock.value:
            for gen_opt in [self.options.gen1, self.options.gen2, self.options.gen3,
                            self.options.gen4, self.options.gen5, self.options.gen6,
                            self.options.gen7, self.options.gen8, self.options.gen9]:
                if gen_opt.value: enabled_regions += 1

        start_regions = self.options.starting_region_unlocks.value
        # Mirror the safety floor from create_items: region lock requires ≥1 start region.
        if self.options.enable_region_lock.value and start_regions < 1:
            start_regions = 1
        start_regions = min(start_regions, enabled_regions)

        start_types = self.options.starting_type_unlocks.value
        start_types = min(start_types, 18) # 18 types
        
        start_pokemon = self.options.starting_pokemon_count.value
        start_pokemon = min(start_pokemon, total_enabled_locations)
        
        removed_count = start_regions + start_types + start_pokemon
        
        injected_count = mandatory_count + special_count
        
        # excess = how many items we injected beyond the "base" Pokemon locations.
        # ext_count is already included in total_enabled_locations, so we do NOT subtract it again.
        excess = injected_count - removed_count - ext_count
        
        if excess > 0:
            # Drop 'excess' Pokemon.
            # Get all IDs
            enabled_ids = []
            for start, end in self._get_enabled_gens():
                enabled_ids.extend(range(start, end + 1))
            
            self.multiworld.random.shuffle(enabled_ids)
            
            # Caution: Ensure we don't drop ALL pokemon if excess is huge (unlikely).
            drops = min(excess, len(enabled_ids))
            
            # Also, we should theoretically avoid dropping the "Starting Pokemon".
            # But we haven't selected Starting Pokemon yet.
            # If we drop ID #X, it won't be in the pool.
            # Can we select ID #X as Starting Pokemon later?
            # Start Pokemon are selected from "Available Pokemon Items".
            # If we exclude Dropped from "Available", then we won't select them.
            # Consistency achieved.
            
            self.dropped_dex_ids = set(enabled_ids[:drops])

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
        for start, end in self._get_enabled_gens():
            total += (end - start + 1)
        total += self._count_enabled_extended_locations()
        return total

    def get_filler_item_name(self) -> str:
        """Called by AP core to fill any remaining location gaps. Also used internally.
        Only non-progression items should be filler. Passes and Type Unlocks are
        progression items already placed as mandatory items — do NOT add extras here.
        Weights: Master Ball (high impact) > Pokegear / Pokedex (balanced) > Shiny Upgrade (cosmetic)
        """
        items  = ["Master Ball", "Pokegear", "Pokedex", "Shiny Upgrade"]
        weights = [35,            25,          25,        15]
        return self.multiworld.random.choices(items, weights=weights, k=1)[0]

    def _is_dex_id_enabled(self, dex_id: int) -> bool:
        for start, end in self._get_enabled_gens():
            if start <= dex_id <= end:
                return True
        return False

    def create_item(self, name: str) -> Item:
        # Pokemon items: progression when Dexsanity is on so AP's fill guarantees they
        #   land in accessible locations for the player who needs them to meet their goal.
        #   (Classification `useful` let AP place them anywhere, leaving player with 0 Pokemon.)
        # Passes/Unlocks: progression (they gate access rules for regions/types)
        # Special filler items: filler (cosmetic quality-of-life)
        FILLER_ITEMS = {"Master Ball", "Pokegear", "Pokedex", "Shiny Upgrade"}
        
        if name in FILLER_ITEMS:
            classification = ItemClassification.filler
        elif "Pass" in name or "Unlock" in name:
            # Passes and type unlocks are progression — they gate access rules.
            classification = ItemClassification.progression
        elif name.startswith("Pokemon #"):
            # Pokemon items are PROGRESSION when Dexsanity is ON.
            # AP must guarantee Pokemon items reach the player who needs them.
            # With starting_region_unlocks >= 1 enforced, fill won't deadlock.
            # When Dexsanity is OFF, Pokemon items aren't in the pool at all (see create_items).
            classification = ItemClassification.progression
        return Item(name, classification, item_table[name], self.player)

    # collect_item override removed — Pokemon items are now classified as `progression`,
    # so AP's default collect_item already tracks them in prog_items automatically.
    # This means count_group("Pokemon") works correctly without any manual override.

    def create_items(self):
        enabled_items = []
        
        # 1. Determine which Pokemon Items are in the pool
        # If Dexsanity is ON, they are Progression (unless excluded by other means?)
        # If Dexsanity is OFF, they are Useful/Filler (or still Progression? No, strict logic implies they are not needed).
        # But for 'Standard' AP, we usually keep them in pool.
        
        for name, item_id in item_table.items():
            # Skip special items, they are handled separately
            if item_id >= 106000:
                continue
            
            dex_id = item_id - 100000
            if self._is_dex_id_enabled(dex_id):
                # Check for dropped items (balancing)
                if dex_id in self.dropped_dex_ids:
                    continue

                # If Dexsanity is OFF, we don't want Pokemon items in the pool; we want filler.
                if not self.options.enable_dexsanity.value:
                    continue
                item = self.create_item(name)
                # Adjust classification based on Dexsanity
                if not self.options.enable_dexsanity.value:
                    item.classification = ItemClassification.useful # Or filler? Useful feels right for collection.
                enabled_items.append(item)

        # 2. Create Special Items
        for _ in range(self.options.master_ball_count.value):
            enabled_items.append(self.create_item("Master Ball"))
        for _ in range(self.options.pokegear_count.value):
            enabled_items.append(self.create_item("Pokegear"))
        for _ in range(self.options.pokedex_count.value):
            enabled_items.append(self.create_item("Pokedex"))

        # 3. Create Region Passes (if Region Lock enabled)
        # Note: Even if Region Lock is OFF, we might want them in pool as Filler? 
        # Or just don't create them. logic implies they don't exist if OFF.
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
        # Without it, ALL Check locations are locked behind passes that sit in the item pool.
        # AP's beatability sweep sees 0 reachable locations and aborts generation.
        if self.options.enable_region_lock.value and start_regions_count < 1:
            start_regions_count = 1

        precollected = []
        
        # Helper lists to manage available vs used
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

        # C. Pre-collect Pokemon (If Dexsanity)
        # If Dexsanity is ON, we MUST give the items to allow them to be guessable.
        # If Dexsanity is OFF, we don't need to give items access-wise, but options say "Starting Pokemon Count".
        # We will assume this means "Give Items" in both cases for consistency/Unlock feeling, 
        # OR just rely on logic for Dexsanity OFF.
        # Given the "Starting Pokemon Count" option exists, giving the items is safer.
        self.multiworld.random.shuffle(available_pokemon_items)
        starting_pokemon_items = []
        for _ in range(min(len(available_pokemon_items), start_pokemon_count)):
            item = available_pokemon_items.pop()
            starting_pokemon_items.append(item)
            precollected.append(item)
        
        # D. Ensure Accessibility
        # Only needed if locks are active.
        if self.options.enable_region_lock.value or self.options.type_locks.value:
            
            current_regions = {i.name for i in precollected if "Pass" in i.name}
            current_types = {i.name for i in precollected if "Unlock" in i.name}
            current_pokemon_items = {i.name for i in precollected if "Pokemon #" in i.name}
            
            # Identify which Pokemon we WANT to be accessible.
            # If Dexsanity ON: It's the `starting_pokemon_items`.
            # If Dexsanity OFF: It's ANY `start_pokemon_count` Pokemon.
            
            target_pokemon_data = [] # List of (dex_id, data)
            
            if self.options.enable_dexsanity.value:
                 # Check specific started pokemon
                for item in starting_pokemon_items:
                    dex_id = item.code - 100000
                    target_pokemon_data.append((str(dex_id), pokemon_data[str(dex_id)]))
            else:
                 # We need to find enough Pokemon that ARE accessible, or make them accessible.
                 # Strategy: Check currently accessible. If < count, force unlock for random enabled pokemon until >= count.
                 # PRIORITY: Prefer Pokemon that only need Type Unlocks (Region already unlocked).
                 
                 # 1. Identify Accessible and Candidates
                 accessible_count = 0
                 candidates_type_only = []
                 candidates_region_needed = []
                 
                 # Get all enabled IDs
                 enabled_ids = []
                 for start_id, end_id in self._get_enabled_gens():
                     enabled_ids.extend(range(start_id, end_id + 1))
                 
                 for dex_id in enabled_ids:
                     p_data = pokemon_data[str(dex_id)]
                     region_name = self._get_region_name(dex_id)
                     pass_name = f"{region_name} Pass"
                     
                     # Check Region Access
                     has_region = True
                     if self.options.enable_region_lock.value:
                         has_region = pass_name in current_regions
                     
                     # Check Type Access
                     has_type = True
                     if self.options.type_locks.value:
                         p_types = p_data['types']
                         p_type_items = [f"{t.capitalize()} Unlock" for t in p_types]
                         
                         if self.options.type_lock_mode.value == 0: # Any
                             has_type = any(t in current_types for t in p_type_items)
                         else: # All
                             has_type = all(t in current_types for t in p_type_items)
                     
                     if has_region and has_type:
                         accessible_count += 1
                     elif has_region and not has_type:
                         candidates_type_only.append((str(dex_id), p_data))
                     else:
                         candidates_region_needed.append((str(dex_id), p_data))
                         
                 # 2. Fill needed count
                 needed = start_pokemon_count - accessible_count
                 
                 if needed > 0:
                     self.multiworld.random.shuffle(candidates_type_only)
                     self.multiworld.random.shuffle(candidates_region_needed)
                     
                     # Prioritize Type Only
                     while needed > 0 and candidates_type_only:
                         target_pokemon_data.append(candidates_type_only.pop())
                         needed -= 1
                         
                     # Then Region Needed
                     while needed > 0 and candidates_region_needed:
                         target_pokemon_data.append(candidates_region_needed.pop())
                         needed -= 1

            # Force unlock for targets
            for d_id, p_data in target_pokemon_data:
                # Check Region
                if self.options.enable_region_lock.value:
                    r_name = self._get_region_name(int(d_id))
                    pass_name = f"{r_name} Pass"
                    if pass_name not in current_regions:
                        # Find the item object
                        # It might be in available_region_passes or already somewhere else?
                        # It should be in available_region_passes
                        found = False
                        for idx, item in enumerate(available_region_passes):
                            if item.name == pass_name:
                                precollected.append(available_region_passes.pop(idx))
                                current_regions.add(pass_name)
                                found = True
                                break
                        if not found and pass_name not in current_regions:
                             # Should not happen if logic is correct, unless region disabled but pokemon enabled (impossible by config?)
                             pass

                # Check Types
                if self.options.type_locks.value:
                    p_types = p_data['types']
                    # Convert to Item Names
                    p_type_items = [f"{t.capitalize()} Unlock" for t in p_types]
                    
                    # Check condition
                    satisfied = False
                    if self.options.type_lock_mode.value == 0: # Any
                        if any(t in current_types for t in p_type_items):
                            satisfied = True
                        else:
                            # Need to unlock one. Prefer available ones.
                            # Pick random type from p_types
                            self.multiworld.random.shuffle(p_type_items)
                            for t_name in p_type_items:
                                # Find in available
                                for idx, item in enumerate(available_type_unlocks):
                                    if item.name == t_name:
                                        precollected.append(available_type_unlocks.pop(idx))
                                        current_types.add(t_name)
                                        satisfied = True
                                        break
                                if satisfied: break
                                
                    else: # All
                        if all(t in current_types for t in p_type_items):
                            satisfied = True
                        else:
                            # Unlock ALL missing
                            for t_name in p_type_items:
                                if t_name not in current_types:
                                     for idx, item in enumerate(available_type_unlocks):
                                        if item.name == t_name:
                                            precollected.append(available_type_unlocks.pop(idx))
                                            current_types.add(t_name)
                                            break

        # 6. Finalize Item Pool
        for item in precollected:
            self.multiworld.precollected_items[self.player].append(item)
            
        pool_items = []
        pool_items.extend(available_pokemon_items) # Remaining pokemon
        
        # FIX: Include non-pokemon items from enabled_items (Master Ball etc)
        special_items = [i for i in enabled_items if "Pokemon #" not in i.name]
        pool_items.extend(special_items)
        
        pool_items.extend(available_region_passes) # Remaining regions
        pool_items.extend(available_type_unlocks) # Remaining types

        
        # Top up the item pool to exactly match the number of locations.
        # IMPORTANT: We use _calculate_total_locations() here because create_regions()
        # has NOT been called yet at this point—get_region("Menu") would return 0 locations.
        # NOTE: Do NOT count `precollected` here. Precollected items are given directly to
        # the player at game start — they do NOT occupy location slots. Every location must
        # be filled by an item in `pool_items`, regardless of how many items are precollected.
        total_locations = self._calculate_total_locations()
        needed_filler = total_locations - len(pool_items)

        for _ in range(max(0, needed_filler)):
            filler_name = self.get_filler_item_name()
            pool_items.append(self.create_item(filler_name))
        
        self.multiworld.itempool += pool_items

    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        for name, loc_id in location_table.items():
            if 200001 <= loc_id <= 201025:
                dex_id = loc_id - 200000
                if self._is_dex_id_enabled(dex_id):
                    loc = Location(self.player, name, loc_id, menu)
                    menu.locations.append(loc)
            elif loc_id > 201025:
                # Extended Locations (Catch X Type/Region)
                if self._is_extended_location_enabled(name):
                    loc = Location(self.player, name, loc_id, menu)
                    menu.locations.append(loc)

    def _count_enabled_extended_locations(self) -> int:
        count_locs = 0
        for name, loc_id in location_table.items():
            if loc_id > 201025:
                if self._is_extended_location_enabled(name):
                    count_locs += 1
        return count_locs

    def _is_extended_location_enabled(self, name: str) -> bool:
        if not self.options.enable_dexsanity.value:
            return False
            
        parts = name.split()
        try:
            if "Type" in name:
                # Catch {tier} {Type} Type Pokemon
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
                # print(f"DEBUG: {name} - Group: {group_name}, Possible: {possible}, Target: {count}")
                return possible >= count
            else:
                # Catch {tier} {Region} Pokemon
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
                # print(f"DEBUG: {name} - Group: {group_name}, Possible: {possible}, Target: {count}") 
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
        type_lock_mode = self.options.type_lock_mode.value # 0=Any, 1=All
        leg_gating = self.options.legendary_gating.value

        menu = self.multiworld.get_region("Menu", self.player)
        
        # Track underlying Pokemon locations to evaluate Extended Locations accurately
        pokemon_locations_by_group = {g: [] for g in self.item_name_groups}

        # First pass: Base Pokemon Locations
        for loc in menu.locations:
            if loc.address <= 201025:
                dex_id = loc.address - 200000
                p_data = pokemon_data.get(str(dex_id))
                
                predicates = []
                
                # NOTE: We intentionally do NOT add a Dexsanity rule here
                # (i.e., no `has("Pokemon #N")` requirement).
                # Reason: If we gate Check #N on `has("Pokemon #N")`, AP classifies Pokemon
                # items as `progression` to satisfy those gates. But with 386 progression items
                # and only 69 unconstrained extended locations in the world, AP has nowhere to
                # place them — creating a deadlock where the goal (collect N pokemon) is
                # unreachable through the solo beatability check.
                # The Dexsanity requirement is enforced by the GAME CLIENT. AP's job is only
                # to ensure the item exists in the pool and can be sent to the player.
                
                # Region Lock Rule
                if enable_region_lock:
                    region_name = self._get_region_name(dex_id)
                    predicates.append(lambda state, r=region_name: state.has(f"{r} Pass", self.player))
                
                # Dexsanity Rule
                # We MUST enforce this rule to prevent deadlocks where the generator places 
                # progression items in locations that require a Pokemon item the player doesn't have.
                # The availability of Extended Locations and starting inventory should prevent fill failures.
                if enable_dexsanity:
                     predicates.append(lambda state, i=dex_id: state.has(f"Pokemon #{i}", self.player))
                     
                # Type Lock Rule
                if use_type_locks and p_data:
                    types = p_data['types']
                    if type_lock_mode == 0: # Any
                        # has ANY of the types
                        predicates.append(lambda state, ts=types: any(state.has(f"{t.capitalize()} Unlock", self.player) for t in ts))
                    else: # All
                        # has ALL of the types
                        predicates.append(lambda state, ts=types: all(state.has(f"{t.capitalize()} Unlock", self.player) for t in ts))
                        
                # Legendary Gating Rule
                if leg_gating > 0 and p_data and p_data['is_legendary']:
                    predicates.append(lambda state, count=leg_gating: state.count_group("Pokemon", self.player) >= count)
                    
                # Set the combined rule
                if predicates:
                    loc.access_rule = lambda state, ps=predicates: all(p(state) for p in ps)
                else:
                    loc.access_rule = lambda state: True

                # Register location for Extended Locations evaluation
                name_item = f"Pokemon #{dex_id}"
                for g, items in self.item_name_groups.items():
                    if name_item in items:
                        if g not in pokemon_locations_by_group:
                            pokemon_locations_by_group[g] = []
                        pokemon_locations_by_group[g].append(loc)

        # Second pass: Extended Locations
        for loc in menu.locations:
            if loc.address > 201025:
                # Extended Locations ("Catch X Type/Region Pokemon")
                # We evaluate if the player can ACTUALLY reach (guess) X Pokemon of this group.
                # This perfectly mirrors the game client logic and prevents AP deadlocks/false Tracker flags.
                try:
                    parts = loc.name.split()
                    count = int(parts[1])
                    if "Type" in loc.name:
                        t_name = parts[2]
                        group_name = f"{t_name} Type Pokemon"
                    else:
                        r_name = parts[2]
                        group_name = f"{r_name} Pokemon"
                        
                    related_locs = pokemon_locations_by_group.get(group_name, [])
                    loc.access_rule = lambda state, locs=related_locs, c=count: sum(1 for l in locs if l.access_rule(state)) >= c
                except Exception:
                    # Fallback if name parsing fails
                    loc.access_rule = lambda state: True

        # Victory condition
        goal_type = self.options.goal.value
        goal_amount = self.options.goal_amount.value
        
        # Calculate max possible pokemon based on available locations
        total_enabled = sum(1 for loc in self.multiworld.get_region("Menu", self.player).locations if loc.address <= 201025)

        if goal_type == 0:  # Any Pokemon
            target = min(goal_amount, total_enabled)
            self.multiworld.completion_condition[self.player] = \
                lambda state, t=target: state.count_group("Pokemon", self.player) >= t
        elif goal_type == 1:  # Percentage
            target = max(1, round((goal_amount / 100.0) * total_enabled))
            self.multiworld.completion_condition[self.player] = \
                lambda state, t=target: state.count_group("Pokemon", self.player) >= t
        elif goal_type == 2: # Region Completion
            region_id = self.options.goal_region.value
            region_name = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea"][region_id - 1]
            
            # Count pokemon in this region
            region_pokemon = []
            for d_id, data in pokemon_data.items():
                if self._get_region_name(int(d_id)) == region_name:
                    region_pokemon.append(f"Pokemon #{d_id}")
            
            self.multiworld.completion_condition[self.player] = \
                lambda state, pjs=region_pokemon: all(state.has(p, self.player) for p in pjs)
        elif goal_type == 3: # All Legendaries
            legendaries = [f"Pokemon #{d_id}" for d_id, data in pokemon_data.items() if data['is_legendary'] and self._is_dex_id_enabled(int(d_id))]
            self.multiworld.completion_condition[self.player] = \
                lambda state, legs=legendaries: all(state.has(l, self.player) for l in legs)

    def fill_slot_data(self):
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
            "shadows": self.options.shadows.value,
            "enable_dexsanity": self.options.enable_dexsanity.value,
            "enable_region_lock": self.options.enable_region_lock.value,
            "type_locks": self.options.type_locks.value,
            "type_lock_mode": self.options.type_lock_mode.value,
            "legendary_gating": self.options.legendary_gating.value,
            "master_ball_count": self.options.master_ball_count.value,
            "pokegear_count": self.options.pokegear_count.value,
            "pokedex_count": self.options.pokedex_count.value,
            "goal": self.options.goal.value,
            "goal_amount": self.options.goal_amount.value,
            "goal_region": self.options.goal_region.value,
            "starting_pokemon_count": self.options.starting_pokemon_count.value,
            "starting_type_unlocks": self.options.starting_type_unlocks.value,
            "starting_region_unlocks": self.options.starting_region_unlocks.value,
        }
