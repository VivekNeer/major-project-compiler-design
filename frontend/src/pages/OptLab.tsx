import { useCallback, useState } from 'react'
import {
  api, isApiError, PASSES, PASS_NAMES,
  type ApiError, type StepsResult,
} from '../api'
import type { SharedProps } from '../App'
import Editor from '../components/Editor'
import ExamplePicker from '../components/ExamplePicker'
import PipelineRail from '../components/PipelineRail'
import DiffView from '../components/DiffView'

export default function OptLab({ source, setSource, examples }: SharedProps) {
  const [order, setOrder] = useState<string[]>([...PASSES])
  const [steps, setSteps] = useState<StepsResult | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [active, setActive] = useState(0)
  const [busy, setBusy] = useState(false)
  const [dragIdx, setDragIdx] = useState<number | null>(null)

  const run = useCallback(async () => {
    setBusy(true)
    const r = await api.optimizeSteps(source, order)
    setBusy(false)
    if (isApiError(r)) {
      setError(r)
      setSteps(null)
    } else {
      setError(null)
      setSteps(r)
      setActive(r.stages.length - 1)
    }
  }, [source, order])

  const move = (from: number, to: number) => {
    if (to < 0 || to >= order.length) return
    const next = [...order]
    const [x] = next.splice(from, 1)
    next.splice(to, 0, x)
    setOrder(next)
  }

  const stage = steps?.stages[active]
  const baseline = steps?.stages[0]

  return (
    <div>
      <h1 className="page-title">Optimization Lab</h1>
      <p className="page-sub">
        Arrange the six passes (drag, or focus a chip and use arrow keys), then
        step through the pipeline stage by stage — this is the phase-ordering
        problem made visible.
      </p>
      <PipelineRail active={['IR', 'passes']} />

      <div className="row" style={{ marginBottom: 12 }}>
        <div className="chips">
          {order.map((p, i) => (
            <span
              key={p}
              className={`chip ${dragIdx === i ? 'dragging' : ''}`}
              title={PASS_NAMES[p]}
              draggable
              tabIndex={0}
              onDragStart={() => setDragIdx(i)}
              onDragEnd={() => setDragIdx(null)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => {
                if (dragIdx !== null && dragIdx !== i) move(dragIdx, i)
                setDragIdx(null)
              }}
              onKeyDown={(e) => {
                if (e.key === 'ArrowLeft') move(i, i - 1)
                if (e.key === 'ArrowRight') move(i, i + 1)
              }}
            >
              {i + 1}. {p}
            </span>
          ))}
        </div>
        <button className="btn primary" onClick={run} disabled={busy}>
          {busy ? 'Running…' : 'Run Pipeline'}
        </button>
        <ExamplePicker examples={examples} onLoad={setSource} />
        {steps?.output_correct === true && <span className="badge ok">output correct</span>}
        {steps?.output_correct === false && <span className="badge bad">OUTPUT MISMATCH</span>}
      </div>

      {error && <div className="error-box" style={{ marginBottom: 12 }}>{error.message}</div>}

      <div className="grid-2" style={{ alignItems: 'start', marginBottom: 14 }}>
        <Editor value={source} onChange={setSource} error={error} height="300px" />

        <div>
          {steps && (
            <>
              <div className="timeline" style={{ marginBottom: 12 }}>
                {steps.stages.map((s, i) => {
                  const prev = i > 0 ? steps.stages[i - 1] : null
                  const delta = prev ? s.code_size - prev.code_size : 0
                  return (
                    <button
                      key={i}
                      className={`step-pill ${active === i ? 'active' : ''}`}
                      onClick={() => setActive(i)}
                    >
                      <span className="n">{s.label}</span>
                      <span className="d">
                        {s.code_size} insts{' '}
                        {prev && (
                          <span className={delta < 0 ? 'delta-down' : 'delta-same'}>
                            {delta < 0 ? delta : delta === 0 ? '±0' : `+${delta}`}
                          </span>
                        )}
                      </span>
                    </button>
                  )
                })}
              </div>

              {stage && baseline && (
                <div className="tiles">
                  <div className="tile">
                    <div className="k">Code size</div>
                    <div className="v">{stage.code_size}</div>
                    <div className={`s ${stage.code_size < baseline.code_size ? 'down' : 'neutral'}`}>
                      {baseline.code_size > 0
                        ? `${((1 - stage.code_size / baseline.code_size) * 100).toFixed(1)}% vs baseline`
                        : '—'}
                    </div>
                  </div>
                  <div className="tile">
                    <div className="k">Est. cycles</div>
                    <div className="v">{stage.estimated_cycles.toFixed(0)}</div>
                    <div className={`s ${stage.estimated_cycles < baseline.estimated_cycles ? 'down' : 'neutral'}`}>
                      {baseline.estimated_cycles > 0
                        ? `${((1 - stage.estimated_cycles / baseline.estimated_cycles) * 100).toFixed(1)}% vs baseline`
                        : '—'}
                    </div>
                  </div>
                  {active > 0 && (
                    <div className="tile">
                      <div className="k">This pass</div>
                      <div className="v">
                        −{stage.removed}
                        {stage.added > 0 ? ` +${stage.added}` : ''}
                      </div>
                      <div className="s neutral">{PASS_NAMES[stage.pass ?? ''] ?? 'no change'}</div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
          {!steps && !error && (
            <div className="panel">
              <div className="panel-body" style={{ color: 'var(--text-3)' }}>
                Run the pipeline to see per-pass stages.
              </div>
            </div>
          )}
        </div>
      </div>

      {stage && (
        <div className="panel" style={{ maxHeight: 420 }}>
          <div className="panel-head">
            <span>
              {active === 0
                ? 'Baseline IR'
                : `IR after ${stage.label} (stage ${active}/${steps!.stages.length - 1})`}
            </span>
            <span style={{ textTransform: 'none', color: 'var(--text-3)' }}>
              {active > 0 ? 'diff vs previous stage' : ''}
            </span>
          </div>
          <div className="panel-body code">
            {active === 0 ? stage.ir_text : <DiffView diff={stage.diff} />}
          </div>
        </div>
      )}
    </div>
  )
}
