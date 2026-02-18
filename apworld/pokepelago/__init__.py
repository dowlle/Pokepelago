from .items import item_table
from .locations import location_table
from .options import PokepelagoOptions
from worlds.AutoWorld import World
from BaseClasses import Region, Item, Location, Tutorial, ItemClassification
from worlds.LauncherComponents import Component, components, launch_subprocess, Type, icon_paths
from .data import pokemon_data

class PokepelagoWorld(World):
    """
    Pokepelago is a Pokemon guessing game where you unlock Pokemon to guess by finding them in the archipelago.
    """
    game = "pokepelago"
    options_dataclass = PokepelagoOptions
    options: PokepelagoOptions

    item_name_to_id = item_table
    location_name_to_id = location_table

    item_name_groups = {
        "Pokemon": set(item_table.keys())
    }

    # ID ranges
    # Items: 100001 - 101025
    # Locations: 200001 - 201025

    def _get_enabled_gens(self):
        enabled_gens = []
        if self.options.gen1: enabled_gens.append((1, 151))
        if self.options.gen2: enabled_gens.append((152, 251))
        if self.options.gen3: enabled_gens.append((252, 386))
        if self.options.gen4: enabled_gens.append((387, 493))
        if self.options.gen5: enabled_gens.append((494, 649))
        if self.options.gen6: enabled_gens.append((650, 721))
        if self.options.gen7: enabled_gens.append((722, 809))
        if self.options.gen8: enabled_gens.append((810, 905))
        if self.options.gen9: enabled_gens.append((906, 1025))
        return enabled_gens

    def _is_dex_id_enabled(self, dex_id: int) -> bool:
        for start, end in self._get_enabled_gens():
            if start <= dex_id <= end:
                return True
        return False

    def create_item(self, name: str) -> Item:
        classification = ItemClassification.progression
        if name in ["Master Ball", "Pokegear", "Pokedex", "Shiny Upgrade"]:
            classification = ItemClassification.useful
        return Item(name, classification, item_table[name], self.player)

    def create_items(self):
        enabled_items = []
        for name, item_id in item_table.items():
            # Skip special items, they are handled separately
            if item_id >= 106000:
                continue
            
            dex_id = item_id - 100000
            if self._is_dex_id_enabled(dex_id):
                enabled_items.append(self.create_item(name))

        # Add special items
        for _ in range(self.options.master_ball_count.value):
            enabled_items.append(self.create_item("Master Ball"))
        for _ in range(self.options.pokegear_count.value):
            enabled_items.append(self.create_item("Pokegear"))
        for _ in range(self.options.pokedex_count.value):
            enabled_items.append(self.create_item("Pokedex"))

        # Add Region Passes if region_lock is on
        if self.options.logic_mode == 1: # region_lock
            regions = [
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
            enabled_passes = []
            for gen_name, pass_name, gen_opt in regions:
                if gen_opt.value:
                    enabled_passes.append(self.create_item(pass_name))
            
            # Ensure at least one region is available at start
            if enabled_passes:
                start_pass = self.multiworld.random.choice(enabled_passes)
                self.multiworld.precollected_items[self.player].append(start_pass)
                enabled_passes.remove(start_pass)
                enabled_items += enabled_passes

        # Add Type Unlocks if type_locks is on
        if self.options.type_locks.value:
            types_list = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Steel', 'Dark', 'Fairy']
            starting_types = ["Water Unlock", "Fire Unlock", "Grass Unlock"]
            for t_name in types_list:
                item_name = f"{t_name} Unlock"
                if item_name in starting_types:
                    self.multiworld.precollected_items[self.player].append(self.create_item(item_name))
                else:
                    enabled_items.append(self.create_item(item_name))

        # Shuffle and pick starting items
        self.multiworld.random.shuffle(enabled_items)
        starting_count = min(len(enabled_items), self.options.starting_pokemon_count.value)
        
        removed_count = 0
        for _ in range(starting_count):
            item = enabled_items.pop()
            self.multiworld.precollected_items[self.player].append(item)
            removed_count += 1

        # Add filler items (Shiny Upgrades) to keep the pool balanced
        for _ in range(removed_count):
            enabled_items.append(self.create_item("Shiny Upgrade"))

        # Rest go into the pool
        self.multiworld.itempool += enabled_items

    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        for name, loc_id in location_table.items():
            dex_id = loc_id - 200000
            if self._is_dex_id_enabled(dex_id):
                loc = Location(self.player, name, loc_id, menu)
                menu.locations.append(loc)

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
        logic_mode = self.options.logic_mode.value
        use_type_locks = self.options.type_locks.value
        leg_gating = self.options.legendary_gating.value

        for loc in self.multiworld.get_region("Menu", self.player).locations:
            dex_id = loc.address - 200000
            p_data = pokemon_data.get(str(dex_id))
            
            # Use a list of predicates to combine later
            predicates = []
            
            # Logic Mode Rule
            if logic_mode == 0: # dexsanity
                predicates.append(lambda state, d=dex_id: state.has(f"Pokemon #{d}", self.player))
            else: # region_lock
                region_name = self._get_region_name(dex_id)
                predicates.append(lambda state, r=region_name: state.has(f"{r} Pass", self.player))
                
            # Type Lock Rule
            if use_type_locks and p_data:
                for t in p_data['types']:
                    predicates.append(lambda state, tn=t.capitalize(): state.has(f"{tn} Unlock", self.player))
                    
            # Legendary Gating Rule
            if leg_gating > 0 and p_data and p_data['is_legendary']:
                predicates.append(lambda state, count=leg_gating: state.count_group("Pokemon", self.player) >= count)
                
            # Set the combined rule
            loc.access_rule = lambda state, ps=predicates: all(p(state) for p in ps)

        # Victory condition
        goal_type = self.options.goal.value
        goal_amount = self.options.goal_amount.value

        if goal_type == 0:  # Any Pokemon
            target = goal_amount
            self.multiworld.completion_condition[self.player] = \
                lambda state, t=target: state.count_group("Pokemon", self.player) >= t
        elif goal_type == 1:  # Percentage
            total_enabled = len(self.multiworld.get_region("Menu", self.player).locations)
            target = max(1, int((goal_amount / 100.0) * total_enabled))
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
            "logic_mode": self.options.logic_mode.value,
            "type_locks": self.options.type_locks.value,
            "legendary_gating": self.options.legendary_gating.value,
            "master_ball_count": self.options.master_ball_count.value,
            "pokegear_count": self.options.pokegear_count.value,
            "pokedex_count": self.options.pokedex_count.value,
            "goal": self.options.goal.value,
            "goal_amount": self.options.goal_amount.value,
            "goal_region": self.options.goal_region.value,
            "starting_pokemon_count": self.options.starting_pokemon_count.value,
        }
