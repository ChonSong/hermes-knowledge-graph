import json, subprocess

with open('graph_data.json') as f:
    d = json.load(f)

h = subprocess.run(['git', 'show', '9f98ff1:index.html'], capture_output=True, text=True).stdout

clean = json.dumps(d, separators=(',', ':'))

# Find const GRAPH_DATA =
old = 'const GRAPH_DATA = '
start = h.find(old)
if start < 0:
    print('ERROR: const GRAPH_DATA not found')
    exit(1)

data_start = start + len(old)
# Find matching end brace
import re
# The data is a JSON object followed by a semicolon
# Find the first }; after data_start
end_match = re.search(r'};', h[data_start:])
if not end_match:
    print('ERROR: Could not find }; after GRAPH_DATA')
    exit(1)

data_end = data_start + end_match.end()

# Replace the data
new_h = h[:data_start] + clean + h[data_end-1:]  # -1 to keep the semicolon from the original

# Update charge
new_h = new_h.replace('let chargeStrength = 80', 'let chargeStrength = 200')

with open('index.html', 'w') as f:
    f.write(new_h)

print(f'HTML: {len(new_h)/1024:.0f}KB')
print(f'const GRAPH_DATA at: {new_h.find("const GRAPH_DATA = ")}')
print(f'charge=200: {"chargeStrength = 200" in new_h}')

# Verify by extracting and parsing
vd = new_h.find('const GRAPH_DATA = ')
sc = new_h.find('};', vd)
data_json = new_h[vd + len('const GRAPH_DATA = '):sc + 1]
parsed = json.loads(data_json)
print(f'Data: {len(parsed["nodes"])} nodes, {len(parsed["edges"])} edges')
print('All OK')
