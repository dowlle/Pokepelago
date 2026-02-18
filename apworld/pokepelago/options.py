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

class LogicMode(Choice):
    """The logic mode for the game. 'Dexsanity' requires finding the specific Pokemon item. 'Region Lock' requires finding the Region Pass."""
    display_name = "Logic Mode"
    option_dexsanity = 0
    option_region_lock = 1
    default = 0

class TypeLocks(Toggle):
    """If enabled, you must find the 'Type Unlock' item to guess Pokemon of that type. This can be combined with other modes."""
    display_name = "Type Locks"
    default = False

class LegendaryGating(Range):
    """The number of standard Pokemon required before Legendary locations become available."""
    display_name = "Legendary Gating"
    range_start = 0
    range_end = 100
    default = 0

class MasterBallCount(Range):
    """Number of Master Balls in the pool. Master Balls can instantly reveal a Pokemon."""
    display_name = "Master Ball Count"
    range_start = 0
    range_end = 20
    default = 5

class PokegearCount(Range):
    """Number of Pokegears in the pool. Pokegears reveal the true colors of a shadow."""
    display_name = "Pokegear Count"
    range_start = 0
    range_end = 20
    default = 5

class PokedexCount(Range):
    """Number of Pokedexes in the pool. Pokedexes reveal hints about the Pokemon name."""
    display_name = "Pokedex Count"
    range_start = 0
    range_end = 20
    default = 5

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
    logic_mode: LogicMode
    type_locks: TypeLocks
    legendary_gating: LegendaryGating
    master_ball_count: MasterBallCount
    pokegear_count: PokegearCount
    pokedex_count: PokedexCount
    goal: Goal
    goal_amount: GoalAmount
    goal_region: GoalRegion
    starting_pokemon_count: StartingPokemonCount
