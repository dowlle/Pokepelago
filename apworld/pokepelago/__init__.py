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

    # ID ranges
    # Items: 100001 - 101025
    # Locations: 200001 - 201025

    def create_item(self, name: str) -> Item:
        return Item(name, ItemClassification.progression, item_table[name], self.player)

    def create_items(self):
        # Determine which gens are enabled
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

        # Filter items based on ID (which we derived from dex number)
        # item_id = 100000 + dex_id
        for name, item_id in item_table.items():
            dex_id = item_id - 100000
            
            is_enabled = False
            for start, end in enabled_gens:
                if start <= dex_id <= end:
                    is_enabled = True
                    break
            
            if is_enabled:
                self.multiworld.itempool.append(self.create_item(name))

    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        # Determine which gens are enabled (same logic as create_items)
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

        for name, loc_id in location_table.items():
            # location_id = 200000 + dex_id
            dex_id = loc_id - 200000
            
            is_enabled = False
            for start, end in enabled_gens:
                if start <= dex_id <= end:
                    is_enabled = True
                    break
            
            if is_enabled:
                loc = Location(self.player, name, loc_id, menu)
                menu.locations.append(loc)

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
        }
