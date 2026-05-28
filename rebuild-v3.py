#!/usr/bin/env python3
"""Replace inline data in f72bed0 HTML with clean 821-node data."""
import json, re, os, subprocess

with open('/workspace/hermes-knowledge-graph/index.html') as f:
    h = f.read()

with open('/workspace/hermes-knowledge-graph/graph_data.json') as f:
    d = json.load(f)

# Find var D= and the matching close brace
data_start = h.find('var D={') + 6  # after 'var D='
depth = 1
i = data_start + 1  # past the '{'
in_str = False
while depth > 0 and i < len(h):
    c = h[i]
    if c == '"' and (i == 0 or h[i-1] != '\\'):
        in_str = not in_str
    elif not in_str:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
    i += 1
data_end_inclusive = i  # position after closing }

# Find start of var D=
vd_start = h.find('var D={')

pre = h[:vd_start]
post = h[data_end_inclusive:]  # everything after closing }

# Compact data
clean = json.dumps(d, separators=(',', ':'))

new_h = pre + 'var D=' + clean + ';\n' + post

# Update defaults
new_h = new_h.replace('let chargeStrength = 80', 'let chargeStrength = 200')

with open('/workspace/hermes-knowledge-graph/index.html', 'w') as f:
    f.write(new_h)

sz = os.path.getsize('/workspace/hermes-knowledge-graph/index.html')
print(f'HTML: {sz/1024:.0f}KB')

# Check features
for feat in ['tag-threshold', 'quality-bar', 'detail-badges', 'conn-list',
             'copy-qname', 'nodeCanvasObject', 'TAG_SHARED', 'toggle-all-btn',
             'chargeStrength = 200']:
    print(f'  {feat}: {"YES" if feat in new_h else "NO"}')

# Validate JS syntax
r = subprocess.run(['node', '-e', '''
const fs = require("fs");
const h = fs.readFileSync("/workspace/hermes-knowledge-graph/index.html", "utf8");
const si = h.indexOf("<script>", 100);
const ei = h.indexOf("</script>", si) + 9;
const s = h.slice(si, ei).replace("<script>", "").replace("</script>", "");
try { new Function(s); console.log("JS VALID"); }
catch(e) { console.log("JS ERROR:", e.message.slice(0,200)); }
'''], capture_output=True, text=True, timeout=10)
print(r.stdout.strip())
if r.stderr:
    print(r.stderr.strip()[:200])
