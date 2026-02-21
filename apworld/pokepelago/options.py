from dataclasses import dataclass
from Options import Toggle, Choice, Range, OptionSet, PerGameCommonOptions

class EnableGen1(Toggle):
    """Enable Generation 1 Pokemon (Kanto)"""
    display_name = "Enable Gen 1"
    default = True

class EnableGen2(Toggle):
    """Enable Generation 2 Pokemon (Johto)"""
    display_name = "Enable Gen 2"
    default = True

class EnableGen3(Toggle):
    """Enable Generation 3 Pokemon (Hoenn)"""
    display_name = "Enable Gen 3"
    default = True

class EnableGen4(Toggle):
    """Enable Generation 4 Pokemon (Sinnoh)"""
    display_name = "Enable Gen 4"
    default = True
    
class EnableGen5(Toggle):
    """Enable Generation 5 Pokemon (Unova)"""
    display_name = "Enable Gen 5"
    default = True

class EnableGen6(Toggle):
    """Enable Generation 6 Pokemon (Kalos)"""
    display_name = "Enable Gen 6"
    default = True

class EnableGen7(Toggle):
    """Enable Generation 7 Pokemon (Alola)"""
    display_name = "Enable Gen 7"
    default = True

class EnableGen8(Toggle):
    """Enable Generation 8 Pokemon (Galar)"""
    display_name = "Enable Gen 8"
    default = True

class EnableGen9(Toggle):
    """Enable Generation 9 Pokemon (Paldea)"""
    display_name = "Enable Gen 9"
    default = True

class Shadows(Choice):
    """How to display unlocked but unguessed Pokemon. Shadows makes them silhouettes. Not Guessable means they stay hidden until hinted (or shadows enabled)."""
    display_name = "Shadows"
    option_off = 0
    option_on = 1
    default = 1

class EnableDexsanity(Toggle):
    """If enabled, you must find the specific Pokemon item to guess it."""
    display_name = "Enable Dexsanity"
    default = True

class EnableRegionLock(Toggle):
    """If enabled, you must find the Region Pass to guess Pokemon in that region."""
    display_name = "Enable Region Lock"
    default = False

class TypeLocks(Toggle):
    """If enabled, you must find the 'Type Unlock' item to guess Pokemon of that type. This can be combined with other modes."""
    display_name = "Type Locks"
    default = False

class TypeLockMode(Choice):
    """
    How Type Locks function for dual-type Pokemon.
    'Any': You can guess the Pokemon if you have ANY of its types unlocked.
    'All': You must have ALL of its types unlocked to guess it.
    """
    display_name = "Type Lock Mode"
    option_any = 0
    option_all = 1
    default = 0

class LegendaryGating(Range):
    """The number of standard Pokemon required before Legendary locations become available."""
    display_name = "Legendary Gating"
    range_start = 0
    range_end = 100
    default = 0

class Goal(Choice):
    """The goal of the game."""
    display_name = "Goal"
    option_any_pokemon = 0
    option_percentage = 1
    option_region_completion = 2
    option_all_legendaries = 3
    default = 0

class GoalAmount(Range):
    """The amount required for the any/percentage goal."""
    display_name = "Goal Amount"
    range_start = 1
    range_end = 1025
    default = 50

class GoalRegion(Choice):
    """The region required for 'region_completion' goal."""
    display_name = "Goal Region"
    option_kanto = 1
    option_johto = 2
    option_hoenn = 3
    option_sinnoh = 4
    option_unova = 5
    option_kalos = 6
    option_alola = 7
    option_galar = 8
    option_paldea = 9
    default = 1

class StartingPokemonCount(Range):
    """The number of Pokemon given to the player at the start."""
    display_name = "Starting Pokemon Count"
    range_start = 1
    range_end = 50
    default = 5

class StartingTypeUnlockCount(Range):
    """The minimum number of Type Unlocks to start with if Type Locks are enabled."""
    display_name = "Starting Type Unlock Count"
    range_start = 0
    range_end = 18
    default = 2

class StartingRegionUnlockCount(Range):
    """The minimum number of Region Passes to start with if Region Lock is enabled."""
    display_name = "Starting Region Unlock Count"
    range_start = 0
    range_end = 9
    default = 0

class FillerWeightMasterBall(Range):
    """Weight for Master Ball in the filler pool. Master Balls instantly reveal a Pokemon."""
    display_name = "Filler Weight: Master Ball"
    range_start = 0
    range_end = 100
    default = 10

class FillerWeightPokegear(Range):
    """Weight for Pokegear in the filler pool. Pokegears reveal the true colors of a shadow."""
    display_name = "Filler Weight: Pokegear"
    range_start = 0
    range_end = 100
    default = 10

class FillerWeightPokedex(Range):
    """Weight for Pokedex in the filler pool. Pokedexes reveal hints about the Pokemon name."""
    display_name = "Filler Weight: Pokedex"
    range_start = 0
    range_end = 100
    default = 10

class FillerWeightShinyUpgrade(Range):
    """Weight for Shiny Upgrade in the filler pool. Makes a random Pokemon shiny."""
    display_name = "Filler Weight: Shiny Upgrade"
    range_start = 0
    range_end = 100
    default = 5

class FillerWeightShuffleTrap(Range):
    """Weight for Shuffle Trap. Shuffles all Pokemon in the layout temporarily."""
    display_name = "Filler Weight: Shuffle Trap"
    range_start = 0
    range_end = 100
    default = 5

class FillerWeightDerpyTrap(Range):
    """Weight for Derpy Trap. Changes a Pokemon sprite to a derpy version."""
    display_name = "Filler Weight: Derpy Trap"
    range_start = 0
    range_end = 100
    default = 5

class FillerWeightReleaseTrap(Range):
    """Weight for Release Trap. One of your Pokemon visually runs away."""
    display_name = "Filler Weight: Release Trap"
    range_start = 0
    range_end = 100
    default = 5

class FillerWeightNothing(Range):
    """Weight for empty filler (no effect). Higher = more junk items."""
    display_name = "Filler Weight: Nothing"
    range_start = 0
    range_end = 100
    default = 50

@dataclass
class PokepelagoOptions(PerGameCommonOptions):
    gen1: EnableGen1
    gen2: EnableGen2
    gen3: EnableGen3
    gen4: EnableGen4
    gen5: EnableGen5
    gen6: EnableGen6
    gen7: EnableGen7
    gen8: EnableGen8
    gen9: EnableGen9
    shadows: Shadows
    enable_dexsanity: EnableDexsanity
    enable_region_lock: EnableRegionLock
    type_locks: TypeLocks
    type_lock_mode: TypeLockMode
    legendary_gating: LegendaryGating
    goal: Goal
    goal_amount: GoalAmount
    goal_region: GoalRegion
    starting_pokemon_count: StartingPokemonCount
    starting_type_unlocks: StartingTypeUnlockCount
    starting_region_unlocks: StartingRegionUnlockCount
    filler_weight_master_ball: FillerWeightMasterBall
    filler_weight_pokegear: FillerWeightPokegear
    filler_weight_pokedex: FillerWeightPokedex
    filler_weight_shiny_upgrade: FillerWeightShinyUpgrade
    filler_weight_shuffle_trap: FillerWeightShuffleTrap
    filler_weight_derpy_trap: FillerWeightDerpyTrap
    filler_weight_release_trap: FillerWeightReleaseTrap
    filler_weight_nothing: FillerWeightNothing


