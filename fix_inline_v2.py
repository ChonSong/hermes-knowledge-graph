import json, subprocess, re

with open('graph_data.json') as f:
    d = json.load(f)

h = subprocess.run(['git', 'show', '9f98ff1:index.html'], capture_output=True, text=True).stdout

clean = json.dumps(d, separators=(',', ':'))

# Find const GRAPH_DATA = { using proper brace counting
marker = 'const GRAPH_DATA = '
start = h.find(marker)
if start == -1:
    print('ERROR: const GRAPH_DATA not found')
    exit(1)

data_start = start + len(marker)
depth = 1
i = data_start + 1
in_str = False
esc = False
while depth > 0 and i < len(h):
    c = h[i]
    if esc:
        esc = False
    elif c == '\\':
        esc = True
    elif c == '"':
        in_str = not in_str
    elif not in_str:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
    i += 1

# i now points to char after the closing }
# The data assignment ends with ';' after the }
while i < len(h) and h[i] in ' \t\n':
    i += 1
if i < len(h) and h[i] == ';':
    i += 1

data_end = i

# Verify
post = h[data_end:data_end+200]
print(f'Before data: {repr(h[start-30:start])}')
print(f'After data: {repr(post)}')

# Build new HTML
new_html = h[:data_start] + clean + ';' + h[data_end:]

# Verify structure
assert 'const { nodes, edges, ns_colors, edge_types, edge_filter_default, namespace_order } = GRAPH_DATA;' in new_html

# Set charge
new_html = re.sub(r'chargeStrength\s*=\s*\d+', 'chargeStrength = 200', new_html)

with open('index.html', 'w') as f:
    f.write(new_html)

print(f'HTML: {len(new_html)//1024}KB')
print('const GRAPH_DATA at:', new_html.find('const GRAPH_DATA = '))
print('charge=200:', 'chargeStrength = 200' in new_html)
print('destructuring:', 'const { nodes, edges, ns_colors, edge_types, edge_filter_default, namespace_order } = GRAPH_DATA;' in new_html)
