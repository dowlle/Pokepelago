import requests
import json

def generate_ap_data():
    print("Fetching Pokemon data...")
    response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=10000")
    data = response.json()
    
    results = []
    for p in data['results']:
        p_id = int(p['url'].split('/')[-2])
        if p_id > 10000:
            continue
        results.append((p_id, p['name']))
        
    print(f"Found {len(results)} pokemon.")
    
    # Generate items.py
    with open("apworld/pokepelago/items.py", "w") as f:
        f.write("from BaseClasses import Item\n\n")
        f.write("class PokemonItem(Item):\n    game: str = \"Pokepelago\"\n\n")
        f.write("item_table = {\n")
        for p_id, name in results:
            clean_name = f"Pokemon #{p_id}"
            ap_id = 100000 + p_id
            f.write(f"    '{clean_name}': {ap_id},\n")
        f.write("}\n")

    # Generate locations.py
    with open("apworld/pokepelago/locations.py", "w") as f:
        f.write("from BaseClasses import Location\n\n")
        f.write("class PokemonLocation(Location):\n    game: str = \"Pokepelago\"\n\n")
        f.write("location_table = {\n")
        for p_id, name in results:
            clean_name = f"Check #{p_id}"
            ap_id = 200000 + p_id
            f.write(f"    '{clean_name}': {ap_id},\n")
        f.write("}\n")
        
    print("Generated items.py and locations.py")

if __name__ == "__main__":
    generate_ap_data()
