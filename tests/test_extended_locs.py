
import sys
import os
from unittest.mock import MagicMock

# MOCKING INFRASTRUCTURE
if "BaseClasses" not in sys.modules:
    base_classes = MagicMock()
    sys.modules["BaseClasses"] = base_classes
    
    class MockItem:
        def __init__(self, name, classification, code, player):
            self.name = name
            self.classification = classification
            self.code = code
            self.player = player
        def __repr__(self): return f"Item({self.name})"
            
    base_classes.Item = MockItem
    base_classes.ItemClassification = MagicMock()
    # Enum values
    base_classes.ItemClassification.progression = 1
    base_classes.ItemClassification.useful = 2
    base_classes.ItemClassification.filler = 4
    base_classes.ItemClassification.trap = 8
    
    class MockLocation:
        def __init__(self, player, name, address, parent):
            self.player = player
            self.name = name
            self.address = address
            self.parent_region = parent
            self.access_rule = lambda state: True
            self.item_rule = lambda item: True
            
    base_classes.Location = MockLocation
    
    class MockRegion:
        def __init__(self, name, player, multiworld, hint_text=None):
            self.name = name
            self.player = player
            self.multiworld = multiworld
            self.locations = []
            self.exits = []
            
    base_classes.Region = MockRegion
    base_classes.Tutorial = MagicMock()
    auto_world = MagicMock()
    # sys.modules["worlds"] = MagicMock() # This might conflict if worlds exists as namespace
    sys.modules["worlds.AutoWorld"] = auto_world
    
    class MockWorld:
        def __init__(self, multiworld, player):
            self.multiworld = multiworld
            self.player = player
    auto_world.World = MockWorld
    auto_world.AutoWorldRegister = MagicMock()

if "worlds.LauncherComponents" not in sys.modules:
    sys.modules["worlds.LauncherComponents"] = MagicMock()

if "Options" not in sys.modules:
    options_mock = MagicMock()
    sys.modules["Options"] = options_mock
    
    class MockOption:
        def __init__(self, value): self.value = value
    
    options_mock.Toggle = MockOption
    options_mock.Range = MockOption
    options_mock.Choice = MockOption
    options_mock.Option = MockOption
    # Also need PerGameCommonOptions?
    options_mock.PerGameCommonOptions = MagicMock

# PATH SETUP
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# IMPORTS
import unittest
from apworld.pokepelago import PokepelagoWorld
from apworld.pokepelago.options import PokepelagoOptions
from Options import Toggle, Range, Choice

class TestExtendedLocations(unittest.TestCase):
    def setUp(self):
        self.player = 1
        self.multiworld = MagicMock()
        self.multiworld.regions = []
        self.multiworld.itempool = []
        self.multiworld.precollected_items = {self.player: []}
        
        # Mock Region behavior
        class MockRegionObj:
             def __init__(self, name):
                 self.name = name
                 self.locations = []
        
        self.menu_region = MockRegionObj("Menu")
        self.multiworld.regions.append(self.menu_region)
        self.multiworld.get_region = MagicMock(return_value=self.menu_region)
        self.multiworld.random = MagicMock()
        self.multiworld.random.shuffle = MagicMock()
        
        # Setup Options
        self.options = MagicMock()
        self.options.gen1 = Toggle(True) # Kanto Enabled
        self.options.gen2 = Toggle(False)
        self.options.gen3 = Toggle(False)
        self.options.gen4 = Toggle(False)
        self.options.gen5 = Toggle(False)
        self.options.gen6 = Toggle(False)
        self.options.gen7 = Toggle(False)
        self.options.gen8 = Toggle(False)
        self.options.gen9 = Toggle(False) # Paldea Disabled
        
        self.options.enable_dexsanity = Toggle(True)
        self.options.enable_region_lock = Toggle(True)
        self.options.type_locks = Toggle(True)
        self.options.type_lock_mode = Choice(0)
        self.options.legendary_gating = Range(0)
        self.options.master_ball_count = Range(0)
        self.options.pokegear_count = Range(0)
        self.options.pokedex_count = Range(0)
        self.options.goal = Choice(0)
        self.options.goal_amount = Range(1)
        self.options.starting_pokemon_count = Range(0)
        self.options.starting_type_unlocks = Range(0)
        self.options.starting_region_unlocks = Range(0)
        
        self.world = PokepelagoWorld(self.multiworld, self.player)
        self.world.options = self.options
        # Manually bind multiworld again if needed (it is in __init__)

    def test_extended_locations_creation(self):
        # With Gen 1 Only:
        # Kanto Pokemon: 151
        # Paldea Pokemon: 0
        
        self.world.create_regions()
        
        # Check the newly created region (last one)
        new_region = self.multiworld.regions[-1]
        loc_names = [l.name for l in new_region.locations]
        
        self.assertIn("Catch 1 Kanto Pokemon", loc_names)
        self.assertIn("Catch 50 Kanto Pokemon", loc_names)
        self.assertNotIn("Catch 1 Paldea Pokemon", loc_names)
        
        # Type Checks
        self.assertIn("Catch 1 Fire Type Pokemon", loc_names)
        self.assertIn("Catch 10 Fire Type Pokemon", loc_names)
        
    def test_item_balance_no_drops(self):
        # Gen 1 Only, Dexsanity ON.
        # Excess should be 0 (or negative) because Extended Locations > Mandatory Items.
        
        self.world.generate_early()
        
        print(f"Dropped IDs: {len(self.world.dropped_dex_ids)}")
        self.assertEqual(len(self.world.dropped_dex_ids), 0, "Should NOT drop items with extended locations")

if __name__ == '__main__':
    unittest.main()
