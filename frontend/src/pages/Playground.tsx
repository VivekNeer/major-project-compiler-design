import { useCallback, useEffect, useState } from 'react'
import { api, isApiError, type ApiError, type CompileResult } from '../api'
import type { SharedProps } from '../App'
import Editor from '../components/Editor'
import ExamplePicker from '../components/ExamplePicker'
import AstTree from '../components/AstTree'

type Tab = 'tokens' | 'ast' | 'symbols' | 'ir'

export default function Playground({ source, setSource, examples }: SharedProps) {
  const [result, setResult] = useState<CompileResult | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [tab, setTab] = useState<Tab>('ir')
  const [busy, setBusy] = useState(false)

  const compile = useCallback(async () => {
    setBusy(true)
    const r = await api.compile(source)
    setBusy(false)
    if (isApiError(r)) {
      setError(r)
      setResult(null)
    } else {
      setError(null)
      setResult(r)
    }
  }, [source])

  // Compile once on mount so the page isn't empty
  useEffect(() => {
    compile()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div>
      <h1 className="page-title">Playground</h1>
      <p className="page-sub">
        Write C-subset code and inspect every front-end artifact: tokens, AST,
        symbol table, and three-address IR. Semantic errors are underlined in
        the editor.
      </p>

      <div className="row" style={{ marginBottom: 12 }}>
        <button className="btn primary" onClick={compile} disabled={busy}>
          {busy ? 'Compiling…' : 'Compile  (⌘/Ctrl+Enter)'}
        </button>
        <ExamplePicker examples={examples} onLoad={setSource} />
        {error && (
          <span className="badge bad">
            {error.phase} error{error.line ? ` · line ${error.line}` : ''}
          </span>
        )}
        {result && !error && <span className="badge ok">compiled</span>}
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') compile()
          }}
        >
          <Editor value={source} onChange={setSource} error={error} height="440px" />
          {error && <div className="error-box mt">{error.message}</div>}
        </div>

        <div className="panel" style={{ height: 480 }}>
          <div className="panel-head">
            <span>Pipeline Output</span>
            <div className="seg">
              {(['tokens', 'ast', 'symbols', 'ir'] as Tab[]).map((t) => (
                <button
                  key={t}
                  className={tab === t ? 'on' : ''}
                  onClick={() => setTab(t)}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div className={`panel-body ${tab === 'ir' ? 'code' : ''}`}>
            {!result && <span style={{ color: 'var(--text-3)' }}>Compile to see output</span>}

            {result && tab === 'tokens' && (
              <table className="data">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Type</th>
                    <th>Value</th>
                    <th>Loc</th>
                  </tr>
                </thead>
                <tbody>
                  {result.tokens.map((t, i) => (
                    <tr key={i}>
                      <td>{i}</td>
                      <td style={{ color: 'var(--mauve)' }}>{t.type}</td>
                      <td>{t.value}</td>
                      <td style={{ color: 'var(--text-3)' }}>
                        {t.line}:{t.col}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {result && tab === 'ast' && <AstTree root={result.ast} />}

            {result && tab === 'symbols' && (
              <table className="data">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Scope depth</th>
                    <th>IR name</th>
                  </tr>
                </thead>
                <tbody>
                  {result.symbols.map((s, i) => (
                    <tr key={i}>
                      <td>{s.name}</td>
                      <td style={{ color: 'var(--peach)' }}>
                        {s.type}
                        {s.array_size ? `[${s.array_size}]` : ''}
                      </td>
                      <td>{s.scope}</td>
                      <td style={{ color: 'var(--text-3)' }}>{s.ir_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {result && tab === 'ir' && result.ir_text}
          </div>
        </div>
      </div>
    </div>
  )
}
