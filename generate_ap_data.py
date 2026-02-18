import requests
import json

def generate_ap_data():
    print("Fetching Pokemon data...")
    # Get all pokemon up to 1025
    response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=1025")
    data = response.json()
    
    pokemon_data = {}
    for p in data['results']:
        p_id = int(p['url'].split('/')[-2])
        name = p['name']
        
        print(f"Processing #{p_id}: {name}...")
        
        # Get types
        p_resp = requests.get(p['url'])
        p_json = p_resp.json()
        types = [t['type']['name'] for t in p_json['types']]
        
        # Get species for legendary status
        s_resp = requests.get(p_json['species']['url'])
        s_json = s_resp.json()
        is_legendary = s_json['is_legendary'] or s_json['is_mythical']
        
        pokemon_data[p_id] = {
            'name': name,
            'types': types,
            'is_legendary': is_legendary
        }
        
    # Generate items.py
    with open("apworld/pokepelago/items.py", "w") as f:
        f.write("from BaseClasses import Item\n\n")
        f.write("class PokemonItem(Item):\n    game: str = \"pokepelago\"\n\n")
        f.write("item_table = {\n")
        for p_id in sorted(pokemon_data.keys()):
            clean_name = f"Pokemon #{p_id}"
            ap_id = 100000 + p_id
            f.write(f"    '{clean_name}': {ap_id},\n")
        f.write("    'Shiny Upgrade': 105000,\n")
        
        # Add special items manually as before
        f.write("\n    # Region Passes\n")
        for i, name in enumerate(['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar', 'Paldea'], 1):
            f.write(f"    '{name} Pass': {106000 + i},\n")
            
        f.write("\n    # Type Unlocks\n")
        types_list = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Steel', 'Dark', 'Fairy']
        for i, name in enumerate(types_list, 1):
            f.write(f"    '{name} Unlock': {106100 + i},\n")
            
        f.write("\n    # Special Items\n")
        f.write("    'Master Ball': 106201,\n")
        f.write("    'Pokegear': 106202,\n")
        f.write("    'Pokedex': 106203,\n")
        f.write("}\n")

    # Generate locations.py
    with open("apworld/pokepelago/locations.py", "w") as f:
        f.write("from BaseClasses import Location\n\n")
        f.write("class PokemonLocation(Location):\n    game: str = \"pokepelago\"\n\n")
        f.write("location_table = {\n")
        for p_id in sorted(pokemon_data.keys()):
            clean_name = f"Check #{p_id}"
            ap_id = 200000 + p_id
            f.write(f"    '{clean_name}': {ap_id},\n")
        f.write("}\n")
        
    # Generate data.py
    with open("apworld/pokepelago/data.py", "w") as f:
        f.write("pokemon_data = ")
        # Use repr() for valid Python or replace booleans in JSON string
        json_data = json.dumps(pokemon_data, indent=4)
        f.write(json_data.replace('true', 'True').replace('false', 'False'))
        f.write("\n")
        
    # Generate pokemon_metadata.json for frontend
    with open("src/data/pokemon_metadata.json", "w") as f:
        f.write(json.dumps(pokemon_data, indent=4))
        
    print("Generated items.py, locations.py, data.py, and pokemon_metadata.json")

if __name__ == "__main__":
    generate_ap_data()
