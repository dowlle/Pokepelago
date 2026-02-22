import json
import os
import sys
# Mocking AP modules before importing pokepelago
from unittest.mock import MagicMock

class Toggle: pass
class Choice: pass
class Range: pass
class OptionSet: pass
class PerGameCommonOptions: pass

options_mock = MagicMock()
options_mock.Toggle = Toggle
options_mock.Choice = Choice
options_mock.Range = Range
options_mock.OptionSet = OptionSet
options_mock.PerGameCommonOptions = PerGameCommonOptions
sys.modules["Options"] = options_mock

sys.modules["BaseClasses"] = MagicMock()
class MockWorld:
    game = "pokepelago"
    def __init__(self, multiworld, player):
        self.multiworld = multiworld
        self.player = player
        
auto_world = MagicMock()
auto_world.World = MockWorld
sys.modules["worlds.AutoWorld"] = auto_world
sys.modules["worlds.LauncherComponents"] = MagicMock()

# Add apworld to path to import data
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "apworld"))
from pokepelago.data import pokemon_data

def parse_spoiler_txt(file_content):
    """Parses Archipelago spoiler.txt format into a structured dict similar to what spoiler.json provides."""
    data = {
        'options': {},
        'starting_items': [],
        'locations': {}
    }
    
    current_section = "Options"
    lines = file_content.splitlines()
    
    # Option mapping from TXT name to emulator key
    option_map = {
        "Enable Gen 1": "gen1",
        "Enable Gen 2": "gen2",
        "Enable Gen 3": "gen3",
        "Enable Gen 4": "gen4",
        "Enable Gen 5": "gen5",
        "Enable Gen 6": "gen6",
        "Enable Gen 7": "gen7",
        "Enable Gen 8": "gen8",
        "Enable Gen 9": "gen9",
        "Enable Dexsanity": "enable_dexsanity",
        "Enable Region Lock": "enable_region_lock",
        "Type Locks": "type_locks",
        "Type Lock Mode": "type_lock_mode",
        "Legendary Gating": "legendary_gating",
        "Goal": "goal",
        "Goal Amount": "goal_amount",
        "Goal Region": "goal_region",
        "Starting Pokemon Count": "starting_pokemon_count"
    }
    
    # Goal mapping
    goal_map = {
        "Any": 0,
        "Percentage": 1,
        "Region Completion": 2,
        "All Legendaries": 3
    }
    
    # Region mapping for Goal Region
    region_map = {
        "Kanto": 1, "Johto": 2, "Hoenn": 3, "Sinnoh": 4, "Unova": 5, 
        "Kalos": 6, "Alola": 7, "Galar": 8, "Paldea": 9
    }

    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line == "Starting Items:":
            current_section = "StartingItems"
            continue
        elif line == "Locations:":
            current_section = "Locations"
            continue
        elif line == "Playthrough:":
            current_section = "Playthrough"
            break
            
        if current_section == "Options":
            if ":" in line:
                key_txt, val_txt = [part.strip() for part in line.split(":", 1)]
                if key_txt in option_map:
                    key = option_map[key_txt]
                    # Parse value
                    val = val_txt
                    if val == "Yes" or val == "On": val = True
                    elif val == "No" or val == "Off": val = False
                    elif val == "Any": val = 0
                    elif val == "All": val = 1
                    elif key == "goal": val = goal_map.get(val, 0)
                    elif key == "goal_region": val = region_map.get(val, 1)
                    else:
                        try: val = int(val)
                        except: pass
                    data['options'][key] = val
                    
        elif current_section == "StartingItems":
            data['starting_items'].append(line)
            
        elif current_section == "Locations":
            if ":" in line:
                loc_name, item_name = [part.strip() for part in line.split(":", 1)]
                data['locations'][loc_name] = item_name
                
    return data

class PokepelagoEmulator:
    def __init__(self, spoiler_data, is_json=True):
        if is_json:
            # Parse JSON format
            self.spoiler = spoiler_data
            self.slot_data = next(iter(self.spoiler['slot_data'].values()))
            self.options = {k: v for k, v in self.slot_data.items()}
            
            self.location_to_item = {}
            for player_name, data in self.spoiler['locations'].items():
                for loc_name, item_info in data.items():
                    self.location_to_item[loc_name] = item_info if isinstance(item_info, str) else item_info['item']
            
            player_name = next(iter(self.spoiler['locations']))
            self.starting_inventory = self.spoiler['precollected_items'].get(player_name, [])
        else:
            # Parse from our own structured dict (txt parser output)
            self.options = spoiler_data['options']
            self.location_to_item = spoiler_data['locations']
            self.starting_inventory = spoiler_data['starting_items']
            
        # Game State
        self.inventory = set()
        self.caught_pokemon = set() 
        self.visited_locations = set()
        
        # Fill starting inventory
        for item_name in self.starting_inventory:
            self.collect(item_name)

    def _get_region(self, dex_id):
        idx = int(dex_id)
        if 1 <= idx <= 151: return "Kanto"
        if 152 <= idx <= 251: return "Johto"
        if 252 <= idx <= 386: return "Hoenn"
        if 387 <= idx <= 493: return "Sinnoh"
        if 494 <= idx <= 649: return "Unova"
        if 650 <= idx <= 721: return "Kalos"
        if 722 <= idx <= 809: return "Alola"
        if 810 <= idx <= 905: return "Galar"
        if 906 <= idx <= 1025: return "Paldea"
        return "Unknown"

    def can_access_pokemon(self, dex_id_str):
        p_data = pokemon_data[dex_id_str]
        
        # 1. Region Lock
        if self.options.get('enable_region_lock'):
            region = self._get_region(dex_id_str)
            if f"{region} Pass" not in self.inventory:
                return False
                
        # 2. Type Locks
        if self.options.get('type_locks'):
            p_types = p_data['types']
            unlocks = [f"{t.capitalize()} Unlock" for t in p_types]
            mode = self.options.get('type_lock_mode', 0) # 0=Any, 1=All
            
            if mode == 0:
                if not any(u in self.inventory for u in unlocks):
                    return False
            else:
                if not all(u in self.inventory for u in unlocks):
                    return False
                    
        # 3. Legendary Gating
        if p_data.get('is_legendary') and self.options.get('legendary_gating', 0) > 0:
            target = self.options['legendary_gating']
            non_leg_caught = sum(1 for d_id in self.caught_pokemon if not pokemon_data[d_id]['is_legendary'])
            if non_leg_caught < target:
                return False
                
        return True

    def collect(self, item_name):
        self.inventory.add(item_name)
        if item_name.startswith("Pokemon #"):
            dex_id = item_name.split("#")[1]
            self.caught_pokemon.add(dex_id)

    def run_sweep(self):
        stuck = False
        steps = 0
        while True:
            steps += 1
            added = False
            
            # Update Caught Pokemon automatically (simulating player discovery/guesses)
            # In Dexsanity ON, we get them as items.
            # In Dexsanity OFF, they are "caught" as soon as accessible.
            for dex_id in pokemon_data:
                if self.can_access_pokemon(dex_id):
                    if dex_id not in self.caught_pokemon:
                        self.caught_pokemon.add(dex_id)
                        added = True
            
            # Check Locations
            for loc_name, item_info in self.location_to_item.items():
                if loc_name in self.visited_locations:
                    continue
                
                # Check accessibility of location
                if self.can_access_location(loc_name):
                    self.visited_locations.add(loc_name)
                    # item_info is a name or a dict depending on spoiler version
                    item_name = item_info if isinstance(item_info, str) else item_info['item']
                    self.collect(item_name)
                    added = True
            
            if not added:
                break
        
        return self.is_goal_met()

    def can_access_location(self, loc_name):
        # Catch Locations
        if loc_name.startswith("Catch "):
            parts = loc_name.split()
            # "Catch 1 Normal Type Pokemon" or "Catch 50 Kanto Pokemon"
            if len(parts) >= 3 and parts[1].isdigit():
                count = int(parts[1])
                if "Type" in loc_name:
                    # parts: ['Catch', '1', 'Normal', 'Type', 'Pokemon']
                    t_name = parts[2].lower()
                    current = sum(1 for d_id in self.caught_pokemon if t_name in pokemon_data[d_id]['types'])
                else: 
                    # parts: ['Catch', '1', 'Kanto', 'Pokemon']
                    r_name = parts[2]
                    current = sum(1 for d_id in self.caught_pokemon if self._get_region(d_id) == r_name)
                return current >= count
            else:
                # "Catch Bulbasaur"
                p_name = loc_name[len("Catch "):].strip().lower()
                # Use a cached map for speed
                if not hasattr(self, '_name_to_id'):
                    self._name_to_id = {v['name'].lower(): k for k, v in pokemon_data.items()}
                
                dex_id = self._name_to_id.get(p_name)
                if dex_id:
                    return self.can_access_pokemon(dex_id)
                return False
        
        # Dexsanity Base Locations: "Pokemon #X"
        if loc_name.startswith("Pokemon #"):
            dex_id = loc_name.split("#")[1]
            return self.can_access_pokemon(dex_id)
            
        return True # Other locations

    def is_goal_met(self):
        goal_type = self.options.get('goal', 0)
        goal_amount = self.options.get('goal_amount', 0)
        
        # Calculate total possible for percentage
        total_enabled = 0
        for d_id in pokemon_data:
            # We need to know which gens are enabled...
            # This is in slot_data as gen1, gen2, etc.
            gen_num = self._get_gen_from_dex_id(d_id)
            if self.options.get(f"gen{gen_num}"):
                total_enabled += 1

        if goal_type == 0: # Any
            return len(self.caught_pokemon) >= goal_amount
        if goal_type == 1: # Percentage
            target = round((goal_amount / 100.0) * total_enabled)
            return len(self.caught_pokemon) >= target
        if goal_type == 2: # Region
            region_id = self.options.get('goal_region', 1)
            region_name = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea"][region_id - 1]
            region_total = [1 for d_id in pokemon_data if self._get_region(d_id) == region_name and self.options.get(f"gen{self._get_gen_from_dex_id(d_id)}")]
            region_caught = [d_id for d_id in self.caught_pokemon if self._get_region(d_id) == region_name]
            return len(region_caught) >= sum(region_total)
        if goal_type == 3: # All Legendaries
             total_legs = [1 for d_id in pokemon_data if pokemon_data[d_id]['is_legendary'] and self.options.get(f"gen{self._get_gen_from_dex_id(d_id)}")]
             caught_legs = [d_id for d_id in self.caught_pokemon if pokemon_data[d_id]['is_legendary']]
             return len(caught_legs) >= sum(total_legs)
             
        return False

    def _get_gen_from_dex_id(self, dex_id):
        idx = int(dex_id)
        if 1 <= idx <= 151: return 1
        if 152 <= idx <= 251: return 2
        if 252 <= idx <= 386: return 3
        if 387 <= idx <= 493: return 4
        if 494 <= idx <= 649: return 5
        if 650 <= idx <= 721: return 6
        if 722 <= idx <= 809: return 7
        if 810 <= idx <= 905: return 8
        if 906 <= idx <= 1025: return 9
        return 0
