from .items import item_table
from .locations import location_table
from .options import PokepelagoOptions
from worlds.AutoWorld import World
from BaseClasses import Region, Item, Location, Tutorial, ItemClassification
from worlds.LauncherComponents import Component, components, launch_subprocess, Type, icon_paths

class PokepelagoWorld(World):
    """
    Pokepelago is a Pokemon guessing game where you unlock Pokemon to guess by finding them in the archipelago.
    """
    game = "Pokepelago"
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
        return Item(name, ItemClassification.progression, item_table[name], self.player)

    def create_items(self):
        enabled_items = []
        for name, item_id in item_table.items():
            dex_id = item_id - 100000
            if self._is_dex_id_enabled(dex_id):
                enabled_items.append(self.create_item(name))

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

    def set_rules(self):
        # Access rules: Guessing a Pokemon requires having found it first
        for loc in self.multiworld.get_region("Menu", self.player).locations:
            dex_id = loc.address - 200000
            item_name = f"Pokemon #{dex_id}"
            loc.access_rule = lambda state, i_name=item_name: state.has(i_name, self.player)

        # Victory condition
        goal_type = self.options.goal.value
        goal_amount = self.options.goal_amount.value

        if goal_type == 0:  # Total Pokemon
            # Ensure goal amount isn't impossible
            total_enabled = len(self.multiworld.get_region("Menu", self.player).locations)
            target = min(goal_amount, total_enabled)
            self.multiworld.completion_condition[self.player] = \
                lambda state, t=target: state.count_group("Pokemon", self.player) >= t
        else:  # Percentage
            total_enabled = len(self.multiworld.get_region("Menu", self.player).locations)
            target = max(1, int((goal_amount / 100.0) * total_enabled))
            self.multiworld.completion_condition[self.player] = \
                lambda state, t=target: state.count_group("Pokemon", self.player) >= t

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
            "goal": self.options.goal.value,
            "goal_amount": self.options.goal_amount.value,
            "starting_pokemon_count": self.options.starting_pokemon_count.value,
        }
