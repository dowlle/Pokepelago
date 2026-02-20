import json
import re

with open('src/data/pokemon_metadata.json') as f:
    pdata = json.load(f)

with open('apworld/pokepelago/locations.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "'Check #" in line:
        m = re.search(r"'Check #(\d+)'", line)
        if m:
            pid = m.group(1)
            name = pdata[pid]['name'].replace('-', ' ').title()
            lines[i] = line.replace(f"Check #{pid}", f"Catch {name}")

with open('apworld/pokepelago/locations.py', 'w') as f:
    f.writelines(lines)
