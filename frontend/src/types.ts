// Hand-written mirrors of backend/schemas.py and src/schema.py. Small,
// stable surface - manual sync is fine for now.

export interface GraphNode {
  name: string
  type: string
}

export interface GraphEdge {
  source: string
  target: string
  relationship: string
}

export interface KnowledgeGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface ProviderSummary {
  name: string
  models: string[]
}

export interface JobStatus {
  id: string
  status: 'running' | 'complete' | 'error'
  done: number
  total: number
  result: KnowledgeGraph | null
  error: string | null
}
