
import os

file_path = 'apworld/pokepelago/locations.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

# Remove the faulty line if present
# It was "    'Catch 1025 Paldea Pokemon': 201025,\n"
# And potentially the closing brace if it was removed.
# Actually I replaced the last line with that, so the closing brace '}' is GONE unless I included it.
# Check the diff block from step 413:
# -    'Check #1025': 201025,
# +    'Catch 1025 Paldea Pokemon': 201025,
# }
# The closing brace was preserved in the diff context but might not be in the file if I messed up replacement chunk? 
# The replacement content was `    'Catch 1025 Paldea Pokemon': 201025,\n}`
# No, look at step 412: 
# ReplacementContent: `    'Catch 1025 Paldea Pokemon': 201025,\n}`
# TargetContent: `    'Check #1025': 201025,\n}`
# So the closing brace is THERE.

# I need to revert logic:
# 1. Find line with 'Catch 1025 Paldea Pokemon': 201025,
# 2. Replace with 'Check #1025': 201025,
# 3. Before the closing '}', insert new locations.

new_lines = []
for line in lines:
    if "'Catch 1025 Paldea Pokemon': 201025," in line:
        new_lines.append("    'Check #1025': 201025,\n")
    else:
        new_lines.append(line)

# Generate new locations
types = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Steel', 'Dark', 'Fairy']
regions = ['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar', 'Paldea']
start_id = 201026

appended_content = []
appended_content.append("\n    # Type Catch Sanity\n")
for t in types:
    for tier in [1, 5, 10]:
        appended_content.append(f"    'Catch {tier} {t} Type Pokemon': {start_id},\n")
        start_id += 1

appended_content.append("\n    # Region Catch Sanity\n")
for r in regions:
    for tier in [1, 5, 10, 25, 50]:
        appended_content.append(f"    'Catch {tier} {r} Pokemon': {start_id},\n")
        start_id += 1

# Insert before last '}'
# Find last closing brace
last_brace_index = -1
for i in range(len(new_lines) - 1, -1, -1):
    if '}' in new_lines[i]:
        last_brace_index = i
        break

if last_brace_index != -1:
    # Insert before
    new_lines[last_brace_index:last_brace_index] = appended_content

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("Successfully appended locations.")
