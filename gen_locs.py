types = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Steel', 'Dark', 'Fairy']
regions = ['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar', 'Paldea']
start_id = 201026

print("    # Type Catch Sanity")
for t in types:
    for tier in [1, 5, 10]:
        print(f"    'Catch {tier} {t} Type Pokemon': {start_id},")
        start_id += 1

print("\n    # Region Catch Sanity")
for r in regions:
    for tier in [1, 5, 10, 25, 50]:
        print(f"    'Catch {tier} {r} Pokemon': {start_id},")
        start_id += 1
