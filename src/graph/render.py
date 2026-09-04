"""Renders a KnowledgeGraph as an interactive D3 force-directed graph ("Ink Bloom"):
glowing category halos, curved edges, labels revealed on hover, and a dark/light
toggle. Picked over a Cytoscape "paper" style and an ECharts dashboard style in a
side-by-side comparison; light mode is a deliberately different palette from dark,
not an inversion, since glow-via-blur reads as a muddy smudge on a light ground.
"""

import json

from src.schema import KnowledgeGraph


def _escape_for_script_tag(payload: str) -> str:
    # A node name or relationship containing the literal substring "</script>"
    # would otherwise prematurely close the embedding <script> tag.
    return payload.replace("</", "<\\/")


_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; font-family: "IBM Plex Sans", system-ui, sans-serif; }
  #wrap { position: relative; height: 100%; }
  #graph { width: 100%; height: 100%; }
  #graph svg { width: 100%; height: 100%; display: block; }
  #graph text { font-family: "IBM Plex Mono", monospace; }

  .theme-toggle {
    position: absolute; top: 12px; right: 12px; z-index: 10;
    display: flex; border: 1px solid rgba(140,140,140,0.35); border-radius: 999px;
    padding: 3px; gap: 2px; background: rgba(20,20,25,0.35); backdrop-filter: blur(4px);
  }
  .theme-toggle button {
    font-family: "IBM Plex Mono", monospace; font-size: 11px; border: none;
    background: transparent; color: #cfd3da; padding: 6px 12px; border-radius: 999px;
    cursor: pointer;
  }
  .theme-toggle button[aria-pressed="true"] { background: #7ea6d6; color: #10131c; }
  .theme-toggle button:focus-visible { outline: 2px solid #7ea6d6; outline-offset: 2px; }
</style>
</head>
<body>
  <div id="wrap">
    <div class="theme-toggle" role="group" aria-label="Theme">
      <button id="btn-dark" aria-pressed="true">&#9789; Dark</button>
      <button id="btn-light" aria-pressed="false">&#9728; Light</button>
    </div>
    <div id="graph"></div>
  </div>
<script>
  const NODES = __NODES__;
  const EDGES = __EDGES__;

  function degreeMap() {
    const deg = {};
    NODES.forEach((n) => (deg[n.id] = 0));
    EDGES.forEach((e) => {
      deg[e.source] = (deg[e.source] || 0) + 1;
      deg[e.target] = (deg[e.target] || 0) + 1;
    });
    return deg;
  }
  const DEGREE = degreeMap();

  const DARK = {
    bg: "radial-gradient(ellipse at 50% 30%, #1b2333 0%, #10131c 70%)",
    edge: "#6b7690", label: "#e7ebf5", nodeStroke: "#0f1219",
    haloOpacity: 0.18, haloBlur: "blur(6px)",
    color: {
      Technology: "#5ec8ff", Method: "#ff8a65", Concept: "#b48cff",
      Person: "#ffd166", Organization: "#4dd6b0", Dataset: "#ff6b9d",
    },
    fallback: "#7c8aa5",
  };
  const LIGHT = {
    bg: "radial-gradient(ellipse at 50% 30%, #ffffff 0%, #f0ece1 70%)",
    edge: "#a39a86", label: "#24262b", nodeStroke: "#ffffff",
    haloOpacity: 0.16, haloBlur: "blur(3px)",
    color: {
      Technology: "#1f7fb8", Method: "#c9552f", Concept: "#7c4fd1",
      Person: "#b9790f", Organization: "#188a6b", Dataset: "#c73e73",
    },
    fallback: "#8a93a3",
  };

  (function initGraph() {
    const container = document.getElementById("graph");
    const width = container.clientWidth, height = container.clientHeight;
    let palette = DARK;

    const svg = d3.select(container).append("svg").attr("viewBox", [0, 0, width, height]);
    const root = svg.append("g");
    svg.call(d3.zoom().scaleExtent([0.3, 4]).on("zoom", (e) => root.attr("transform", e.transform)));

    const nodes = NODES.map((n) => ({ ...n }));
    const links = EDGES.map((e) => ({ source: e.source, target: e.target, rel: e.rel }));

    const sim = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(80).strength(0.55))
      .force("charge", d3.forceManyBody().strength(-230))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide((d) => 10 + (DEGREE[d.id] || 0) * 2));

    const link = root.append("g").selectAll("path").data(links).join("path")
      .attr("stroke-width", 1).attr("fill", "none");

    const nodeG = root.append("g").selectAll("g").data(nodes).join("g")
      .style("cursor", "pointer")
      .call(d3.drag()
        .on("start", (e, d) => { sim.alphaTarget(0.25).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end", (e, d) => { sim.alphaTarget(0); d.fx = null; d.fy = null; }));

    const halo = nodeG.append("circle").attr("r", (d) => 12 + (DEGREE[d.id] || 0) * 2.4);
    const core = nodeG.append("circle").attr("r", (d) => 5 + (DEGREE[d.id] || 0) * 1.4).attr("stroke-width", 1.2);
    const label = nodeG.append("text")
      .text((d) => d.id)
      .attr("font-size", 10).attr("dy", -12).attr("text-anchor", "middle")
      .style("opacity", 0).style("pointer-events", "none");

    function paint() {
      container.style.background = palette.bg;
      link.attr("stroke", palette.edge).attr("stroke-opacity", 0.35);
      halo.attr("fill", (d) => palette.color[d.type] || palette.fallback)
        .attr("opacity", palette.haloOpacity).attr("filter", palette.haloBlur);
      core.attr("fill", (d) => palette.color[d.type] || palette.fallback).attr("stroke", palette.nodeStroke);
      label.attr("fill", palette.label);
    }
    paint();

    nodeG.on("mouseenter", function (e, d) {
      const connected = new Set([d.id]);
      links.forEach((l) => {
        if (l.source.id === d.id) connected.add(l.target.id);
        if (l.target.id === d.id) connected.add(l.source.id);
      });
      label.style("opacity", (n) => (connected.has(n.id) ? 1 : 0));
      link.attr("stroke-opacity", (l) => (l.source.id === d.id || l.target.id === d.id ? 0.9 : 0.08))
        .attr("stroke", (l) => (l.source.id === d.id || l.target.id === d.id ? (palette.color[d.type] || palette.fallback) : palette.edge));
    }).on("mouseleave", function () {
      label.style("opacity", 0);
      link.attr("stroke-opacity", 0.35).attr("stroke", palette.edge);
    });

    sim.on("tick", () => {
      link.attr("d", (d) => `M${d.source.x},${d.source.y} L${d.target.x},${d.target.y}`);
      nodeG.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    const darkBtn = document.getElementById("btn-dark");
    const lightBtn = document.getElementById("btn-light");
    function setTheme(name) {
      palette = name === "light" ? LIGHT : DARK;
      paint();
      darkBtn.setAttribute("aria-pressed", String(name === "dark"));
      lightBtn.setAttribute("aria-pressed", String(name === "light"));
    }
    darkBtn.addEventListener("click", () => setTheme("dark"));
    lightBtn.addEventListener("click", () => setTheme("light"));
  })();
</script>
</body>
</html>
"""


def render_html(graph: KnowledgeGraph) -> str:
    nodes = [{"id": node.name, "type": node.type} for node in graph.nodes]
    edges = [{"source": edge.source, "target": edge.target, "rel": edge.relationship} for edge in graph.edges]

    html = _TEMPLATE.replace("__NODES__", _escape_for_script_tag(json.dumps(nodes)))
    html = html.replace("__EDGES__", _escape_for_script_tag(json.dumps(edges)))
    return html
