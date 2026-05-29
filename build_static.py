#!/usr/bin/env python3
"""Rebuild index.html with precomputed static positions and disabled force simulation."""

import json, os

os.chdir('/workspace/hermes-knowledge-graph')

# Load data with positions
with open('graph_data.json') as f:
    data = json.load(f)

json_payload = json.dumps(data, separators=(',', ':'))
print(f"JSON payload size: {len(json_payload)} bytes")

# Read current index.html
with open('index.html') as f:
    html = f.read()

# Find the GRAPH_DATA section using brace counting
def find_json_bounds(s, start_marker='const GRAPH_DATA = '):
    idx = s.find(start_marker)
    if idx < 0:
        raise ValueError(f"'{start_marker}' not found")
    json_start = idx + len(start_marker)
    brace = json_start
    depth = 0
    in_string = False
    escape = False
    while brace < len(s):
        c = s[brace]
        if escape:
            escape = False
        elif c == '\\\\':
            escape = True
        elif c == '"' and not escape:
            in_string = not in_string
        elif not in_string:
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return json_start, brace + 1
        brace += 1
    raise ValueError("Could not find matching brace")

start, end = find_json_bounds(html)
print(f"Found GRAPH_DATA at {start}-{end}")

# Replace JSON payload
new_html = html[:start] + json_payload + html[end:]
print(f"HTML size: {len(new_html)} bytes")

# Now patch the JS to disable simulation
# We'll make targeted replacements in the JS section

# 1. In rebuildGraph(), remove d3Force updates and d3ReheatSimulation
old_rebuild_if = """  if (graph) {
    graph.graphData({ nodes: visibleNodes, links: gEdges });
    graph.d3Force('charge').strength(-chargeStrength);
    graph.d3Force('link').distance(linkDist);
    graph.d3ReheatSimulation();
    return;
  }"""

new_rebuild_if = """  if (graph) {
    graph.graphData({ nodes: visibleNodes, links: gEdges });
    return;
  }"""

assert old_rebuild_if in new_html, "Could not find rebuildGraph if-block"
new_html = new_html.replace(old_rebuild_if, new_rebuild_if)

# 2. Replace graph initialization to disable simulation and skip onEngineStop zoom
old_init = """  graph = ForceGraph()(container)
    .graphData({ nodes: visibleNodes, links: gEdges })
    .nodeId('id')
    .nodeLabel(n => `${n.name} (${n.namespace})`)
    .nodeVal(nodeSize)
    .nodeColor(n => `#${n.color.toString(16).padStart(6,'0')}`)
    .linkColor(link => link.color || '#555')
    .linkWidth(link => link.width || 1)
    .linkDirectionalParticles(0)
    .backgroundColor('#0d0d14')
    .d3AlphaDecay(0.03)
    .d3VelocityDecay(0.3)
    .warmupTicks(200)
    .cooldownTicks(50)
    .onNodeClick(showDetail)
    .onBackgroundClick(() => hideDetail())
    .nodeCanvasObjectMode(() => 'after')
    .nodeCanvasObject((node, ctx) => {
      if (node.verified) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size + 2.5, 0, 2 * Math.PI);
        ctx.strokeStyle = '#4ecb71';
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
    })
    .onEngineStop(() => {
      if (!graphInitialized && graph) {
        graphInitialized = true;
        graph.zoomToFit(400, 120);
      }
    });"""

new_init = """  graph = ForceGraph()(container)
    .graphData({ nodes: visibleNodes, links: gEdges })
    .nodeId('id')
    .nodeLabel(n => `${n.name} (${n.namespace})`)
    .nodeVal(nodeSize)
    .nodeColor(n => `#${n.color.toString(16).padStart(6,'0')}`)
    .linkColor(link => link.color || '#555')
    .linkWidth(link => link.width || 1)
    .linkDirectionalParticles(0)
    .backgroundColor('#0d0d14')
    .d3AlphaDecay(1)
    .d3VelocityDecay(1)
    .warmupTicks(0)
    .cooldownTicks(0)
    .onNodeClick(showDetail)
    .onBackgroundClick(() => hideDetail())
    .nodeCanvasObjectMode(() => 'after')
    .nodeCanvasObject((node, ctx) => {
      if (node.verified) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size + 2.5, 0, 2 * Math.PI);
        ctx.strokeStyle = '#4ecb71';
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
    });
  // Static layout: zoom to fit after a brief delay so canvas has size
  setTimeout(() => {
    if (graph && !graphInitialized) {
      graphInitialized = true;
      graph.zoomToFit(400, 120);
    }
  }, 100);"""

assert old_init in new_html, "Could not find graph initialization block"
new_html = new_html.replace(old_init, new_init)

# Verify structure
assert '<script>' in new_html and '</script>' in new_html
assert '</body>' in new_html and '</html>' in new_html

# Verify positions are in data
assert '"x":' in new_html[:start+1000], "Positions not found in payload"

with open('index.html', 'w') as f:
    f.write(new_html)

print("Wrote index.html with static positions and frozen simulation.")
