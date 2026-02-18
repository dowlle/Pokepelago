from dataclasses import dataclass
from Options import Toggle, Choice, OptionSet, PerGameCommonOptions

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
