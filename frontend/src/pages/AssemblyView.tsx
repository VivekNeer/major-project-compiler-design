import { useCallback, useMemo, useState } from 'react'
import {
  api, isApiError, PASSES,
  type ApiError, type AssemblyResult,
} from '../api'
import type { SharedProps } from '../App'
import Editor from '../components/Editor'
import ExamplePicker from '../components/ExamplePicker'

export default function AssemblyView({ source, setSource, examples }: SharedProps) {
  const [result, setResult] = useState<AssemblyResult | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [optimized, setOptimized] = useState(true)
  const [busy, setBusy] = useState(false)
  const [hovered, setHovered] = useState<number | null>(null) // ir line index

  const run = useCallback(async () => {
    setBusy(true)
    const r = await api.assembly(source, optimized ? [...PASSES] : [])
    setBusy(false)
    if (isApiError(r)) {
      setError(r)
      setResult(null)
    } else {
      setError(null)
      setResult(r)
    }
  }, [source, optimized])

  // asm line -> ir line, and ir line -> asm range
  const { asmToIr, irToRange } = useMemo(() => {
    const a2i = new Map<number, number>()
    const i2r = new Map<number, [number, number]>()
    result?.mapping.forEach((m) => {
      i2r.set(m.ir_line, [m.asm_start, m.asm_end])
      for (let l = m.asm_start; l < m.asm_end; l++) a2i.set(l, m.ir_line)
    })
    return { asmToIr: a2i, irToRange: i2r }
  }, [result])

  const hoveredRange = hovered != null ? irToRange.get(hovered) : undefined

  return (
    <div>
      <h1 className="page-title">Assembly</h1>
      <p className="page-sub">
        RISC-V RV32IM lowering of the IR. Hover either column to see which
        assembly a given IR instruction became — and vice versa.
      </p>

      <div className="row" style={{ marginBottom: 12 }}>
        <button className="btn primary" onClick={run} disabled={busy}>
          {busy ? 'Generating…' : 'Generate Assembly'}
        </button>
        <label className="row" style={{ gap: 6, fontSize: 13 }}>
          <input
            type="checkbox"
            checked={optimized}
            onChange={(e) => setOptimized(e.target.checked)}
          />
          optimize first (CF→CP→CSE→DCE→SR→AS)
        </label>
        <ExamplePicker examples={examples} onLoad={setSource} />
      </div>

      {error && <div className="error-box" style={{ marginBottom: 12 }}>{error.message}</div>}

      {!result && (
        <Editor value={source} onChange={setSource} error={error} height="300px" />
      )}

      {result && (
        <div className="asm-cols">
          <div className="panel" style={{ maxHeight: 560 }}>
            <div className="panel-head">Three-Address IR ({result.ir_lines.length} lines)</div>
            <div className="panel-body" style={{ padding: '8px 6px' }}>
              {result.ir_lines.map((line, i) => (
                <div
                  key={i}
                  className={`map-line ${irToRange.has(i) ? 'linked' : ''} ${hovered === i ? 'hl' : ''}`}
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                >
                  {line || ' '}
                </div>
              ))}
            </div>
          </div>

          <div className="panel" style={{ maxHeight: 560 }}>
            <div className="panel-head">RV32IM Assembly ({result.asm_lines.length} lines)</div>
            <div className="panel-body" style={{ padding: '8px 6px' }}>
              {result.asm_lines.map((line, i) => {
                const inRange =
                  hoveredRange && i >= hoveredRange[0] && i < hoveredRange[1]
                const irLine = asmToIr.get(i)
                return (
                  <div
                    key={i}
                    className={`map-line ${irLine != null ? 'linked' : ''} ${inRange ? 'hl' : ''}`}
                    onMouseEnter={() => irLine != null && setHovered(irLine)}
                    onMouseLeave={() => setHovered(null)}
                  >
                    {line || ' '}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="mt">
          <button className="btn small" onClick={() => setResult(null)}>
            ← Back to editor
          </button>
        </div>
      )}
    </div>
  )
}
