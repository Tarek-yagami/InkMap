import * as d3 from 'd3'
import { useEffect, useRef, useState } from 'react'
import type { KnowledgeGraph } from '../types'

type Theme = 'dark' | 'light'

interface Palette {
  bg: string
  edge: string
  label: string
  nodeStroke: string
  haloOpacity: number
  haloBlur: string
  color: Record<string, string>
  fallback: string
}

const DARK: Palette = {
  bg: 'radial-gradient(ellipse at 50% 30%, #1b2333 0%, #10131c 70%)',
  edge: '#6b7690',
  label: '#e7ebf5',
  nodeStroke: '#0f1219',
  haloOpacity: 0.18,
  haloBlur: 'blur(6px)',
  color: {
    Technology: '#5ec8ff',
    Method: '#ff8a65',
    Concept: '#b48cff',
    Person: '#ffd166',
    Organization: '#4dd6b0',
    Dataset: '#ff6b9d',
  },
  fallback: '#7c8aa5',
}

const LIGHT: Palette = {
  bg: 'radial-gradient(ellipse at 50% 30%, #ffffff 0%, #f0ece1 70%)',
  edge: '#a39a86',
  label: '#24262b',
  nodeStroke: '#ffffff',
  haloOpacity: 0.16,
  haloBlur: 'blur(3px)',
  color: {
    Technology: '#1f7fb8',
    Method: '#c9552f',
    Concept: '#7c4fd1',
    Person: '#b9790f',
    Organization: '#188a6b',
    Dataset: '#c73e73',
  },
  fallback: '#8a93a3',
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string
  type: string
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  rel: string
}

interface Props {
  graph: KnowledgeGraph
}

export function GraphView({ graph }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [theme, setTheme] = useState<Theme>('dark')
  const paletteRef = useRef<Palette>(DARK)

  // Repaint on theme change without rebuilding the simulation - mirrors the
  // original render.py's paint()/setTheme() split.
  const paintRef = useRef<(() => void) | null>(null)
  useEffect(() => {
    paletteRef.current = theme === 'light' ? LIGHT : DARK
    paintRef.current?.()
  }, [theme])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const width = container.clientWidth
    const height = container.clientHeight

    const degree: Record<string, number> = {}
    graph.nodes.forEach((n) => (degree[n.name] = 0))
    graph.edges.forEach((e) => {
      degree[e.source] = (degree[e.source] || 0) + 1
      degree[e.target] = (degree[e.target] || 0) + 1
    })

    const nodes: SimNode[] = graph.nodes.map((n) => ({ id: n.name, type: n.type }))
    const links: SimLink[] = graph.edges.map((e) => ({ source: e.source, target: e.target, rel: e.relationship }))

    const svg = d3.select(container).append('svg').attr('viewBox', `0 0 ${width} ${height}`)
    const root = svg.append('g')
    svg.call(
      d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.3, 4]).on('zoom', (event) => root.attr('transform', event.transform)),
    )

    const sim = d3
      .forceSimulation<SimNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(80)
          .strength(0.55),
      )
      .force('charge', d3.forceManyBody().strength(-230))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide<SimNode>((d) => 10 + (degree[d.id] || 0) * 2))

    const link = root
      .append('g')
      .selectAll<SVGPathElement, SimLink>('path')
      .data(links)
      .join('path')
      .attr('stroke-width', 1)
      .attr('fill', 'none')

    const nodeG = root
      .append('g')
      .selectAll<SVGGElement, SimNode>('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'pointer')
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on('start', (_event, d) => {
            sim.alphaTarget(0.25).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (_event, d) => {
            sim.alphaTarget(0)
            d.fx = null
            d.fy = null
          }),
      )

    const halo = nodeG.append('circle').attr('r', (d) => 12 + (degree[d.id] || 0) * 2.4)
    const core = nodeG
      .append('circle')
      .attr('r', (d) => 5 + (degree[d.id] || 0) * 1.4)
      .attr('stroke-width', 1.2)
    const label = nodeG
      .append('text')
      .text((d) => d.id)
      .attr('font-size', 10)
      .attr('dy', -12)
      .attr('text-anchor', 'middle')
      .style('opacity', 0)
      .style('pointer-events', 'none')

    function paint() {
      const palette = paletteRef.current
      container!.style.background = palette.bg
      link.attr('stroke', palette.edge).attr('stroke-opacity', 0.35)
      halo
        .attr('fill', (d) => palette.color[d.type] || palette.fallback)
        .attr('opacity', palette.haloOpacity)
        .attr('filter', palette.haloBlur)
      core.attr('fill', (d) => palette.color[d.type] || palette.fallback).attr('stroke', palette.nodeStroke)
      label.attr('fill', palette.label)
    }
    paintRef.current = paint
    paint()

    nodeG
      .on('mouseenter', (_event, d) => {
        const palette = paletteRef.current
        const connected = new Set([d.id])
        links.forEach((l) => {
          const source = l.source as SimNode
          const target = l.target as SimNode
          if (source.id === d.id) connected.add(target.id)
          if (target.id === d.id) connected.add(source.id)
        })
        label.style('opacity', (n) => (connected.has(n.id) ? 1 : 0))
        link
          .attr('stroke-opacity', (l) => {
            const source = l.source as SimNode
            const target = l.target as SimNode
            return source.id === d.id || target.id === d.id ? 0.9 : 0.08
          })
          .attr('stroke', (l) => {
            const source = l.source as SimNode
            const target = l.target as SimNode
            return source.id === d.id || target.id === d.id ? palette.color[d.type] || palette.fallback : palette.edge
          })
      })
      .on('mouseleave', () => {
        label.style('opacity', 0)
        link.attr('stroke-opacity', 0.35).attr('stroke', paletteRef.current.edge)
      })

    sim.on('tick', () => {
      link.attr('d', (d) => {
        const source = d.source as SimNode
        const target = d.target as SimNode
        return `M${source.x},${source.y} L${target.x},${target.y}`
      })
      nodeG.attr('transform', (d) => `translate(${d.x},${d.y})`)
    })

    return () => {
      // React (especially Strict Mode's dev double-invoke) would otherwise
      // leak a running simulation and duplicate SVG content across re-runs.
      sim.stop()
      paintRef.current = null
      d3.select(container).selectAll('*').remove()
    }
  }, [graph])

  return (
    <div className="panel graph-panel">
      <div className="theme-toggle" role="group" aria-label="Theme">
        <button aria-pressed={theme === 'dark'} onClick={() => setTheme('dark')}>
          &#9789; Dark
        </button>
        <button aria-pressed={theme === 'light'} onClick={() => setTheme('light')}>
          &#9728; Light
        </button>
      </div>
      <div className="graph-canvas" ref={containerRef} />
    </div>
  )
}
