// Typed client for the compiler web API.

export interface Token {
  type: string
  value: string
  line: number
  col: number
}

export interface AstNode {
  type: string
  line: number
  col: number
  fields: Record<string, unknown>
  children: AstNode[]
}

export interface SymbolInfo {
  name: string
  type: string
  scope: number
  ir_name: string
  array_size?: number
}

export interface ApiError {
  error: true
  phase: string
  message: string
  line: number | null
  col: number | null
}

export interface CompileResult {
  tokens: Token[]
  ast: AstNode
  symbols: SymbolInfo[]
  ir: { opcode: string; dest: string | null; src1: string | null; src2: string | null }[]
  ir_text: string
}

export interface DiffLine {
  type: 'kept' | 'removed' | 'added'
  text: string
}

export interface OptimizeResult {
  pass_order: string[]
  optimized_ir_text: string
  assembly: string
  diff: DiffLine[]
  metrics: { code_size: number; estimated_cycles: number; dynamic_count: number }
  output: number[]
  output_correct: boolean
  explanation: string
}

export interface Stage {
  pass: string | null
  label: string
  ir_text: string
  diff: DiffLine[]
  code_size: number
  estimated_cycles: number
  removed: number
  added: number
}

export interface StepsResult {
  pass_order: string[]
  stages: Stage[]
  output_correct: boolean | null
}

export interface AssemblyResult {
  pass_order: string[]
  ir_lines: string[]
  asm_lines: string[]
  mapping: { ir_line: number; asm_start: number; asm_end: number }[]
}

export interface BenchmarkEntry {
  pass_order: string[]
  label: string
  code_size: number
  estimated_cycles: number
  dynamic_count: number
  output_correct: boolean
}

export interface BenchmarkResult {
  results: BenchmarkEntry[]
  baseline: BenchmarkEntry
}

export interface ExampleMeta {
  name: string
  description: string
  suite: string
}

export interface ExampleSource {
  name: string
  source: string
  doc: { title: string; points: string[] } | null
}

export function isApiError(x: unknown): x is ApiError {
  return typeof x === 'object' && x !== null && (x as ApiError).error === true
}

async function post<T>(url: string, body: unknown): Promise<T | ApiError> {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return resp.json()
}

export const api = {
  compile: (source: string) => post<CompileResult>('/api/compile', { source }),
  optimize: (source: string, pass_order: string[]) =>
    post<OptimizeResult>('/api/optimize', { source, pass_order }),
  optimizeSteps: (source: string, pass_order: string[]) =>
    post<StepsResult>('/api/optimize-steps', { source, pass_order }),
  assembly: (source: string, pass_order: string[]) =>
    post<AssemblyResult>('/api/assembly', { source, pass_order }),
  benchmark: (source: string) => post<BenchmarkResult>('/api/benchmark', { source }),
  examples: async (): Promise<ExampleMeta[]> => (await fetch('/api/examples')).json(),
  example: async (name: string): Promise<ExampleSource> =>
    (await fetch(`/api/examples/${name}`)).json(),
}

export const PASSES = ['CF', 'CP', 'CSE', 'DCE', 'SR', 'AS'] as const
export const PASS_NAMES: Record<string, string> = {
  CF: 'Constant Folding',
  CP: 'Copy Propagation',
  CSE: 'Common Subexpression Elimination',
  DCE: 'Dead Code Elimination',
  SR: 'Strength Reduction',
  AS: 'Algebraic Simplification',
}
