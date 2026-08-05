import { useCallback, useMemo, useState } from 'react'
import {
  Chart as ChartJS, LinearScale, PointElement, BarElement,
  CategoryScale, Tooltip, Legend,
} from 'chart.js'
import { Scatter, Bar } from 'react-chartjs-2'
import {
  api, isApiError,
  type ApiError, type BenchmarkEntry, type BenchmarkResult,
} from '../api'
import type { SharedProps } from '../App'
import ExamplePicker from '../components/ExamplePicker'
import Editor from '../components/Editor'

ChartJS.register(LinearScale, CategoryScale, PointElement, BarElement, Tooltip, Legend)

const SERIES_1 = '#3987e5' // validated dark-mode blue
const SERIES_2 = '#d95926' // validated dark-mode orange
const TEXT_2 = '#a6adc8'
const GRID = 'rgba(54, 58, 79, 0.55)'

function paretoFrontier(entries: BenchmarkEntry[]): Set<string> {
  // Minimise both code_size and estimated_cycles
  const front = new Set<string>()
  for (const e of entries) {
    const dominated = entries.some(
      (o) =>
        (o.code_size < e.code_size && o.estimated_cycles <= e.estimated_cycles) ||
        (o.code_size <= e.code_size && o.estimated_cycles < e.estimated_cycles),
    )
    if (!dominated) front.add(e.label)
  }
  return front
}

export default function Explorer({ source, setSource, examples }: SharedProps) {
  const [data, setData] = useState<BenchmarkResult | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [busy, setBusy] = useState(false)
  const [selected, setSelected] = useState<BenchmarkEntry | null>(null)

  const run = useCallback(async () => {
    setBusy(true)
    setSelected(null)
    const r = await api.benchmark(source)
    setBusy(false)
    if (isApiError(r)) {
      setError(r)
      setData(null)
    } else {
      setError(null)
      setData(r)
    }
  }, [source])

  const frontier = useMemo(
    () => (data ? paretoFrontier(data.results) : new Set<string>()),
    [data],
  )

  const scatterData = useMemo(() => {
    if (!data) return null
    const onFront = data.results.filter((r) => frontier.has(r.label))
    const rest = data.results.filter((r) => !frontier.has(r.label))
    const toPoint = (r: BenchmarkEntry) => ({
      x: r.code_size,
      y: r.estimated_cycles,
      entry: r,
    })
    return {
      datasets: [
        {
          label: 'Orderings',
          data: rest.map(toPoint),
          backgroundColor: SERIES_1 + '55',
          borderColor: SERIES_1,
          borderWidth: 1,
          pointRadius: 4,
          pointHoverRadius: 7,
        },
        {
          label: 'Pareto frontier',
          data: onFront.map(toPoint),
          backgroundColor: SERIES_2,
          borderColor: '#1e1e2e',
          borderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 9,
        },
      ],
    }
  }, [data, frontier])

  const topData = useMemo(() => {
    if (!data) return null
    const top = [...data.results]
      .sort((a, b) => a.code_size - b.code_size)
      .slice(0, 10)
    return {
      labels: top.map((r) => r.label.replaceAll(' -> ', '→')),
      datasets: [
        {
          label: 'Code size (instructions)',
          data: top.map((r) => r.code_size),
          backgroundColor: SERIES_1,
          borderRadius: 4,
          maxBarThickness: 22,
        },
      ],
      entries: top,
    }
  }, [data])

  const axisOpts = {
    ticks: { color: TEXT_2, font: { size: 11 } },
    grid: { color: GRID },
    border: { color: GRID },
  }

  return (
    <div>
      <h1 className="page-title">Phase-Ordering Explorer</h1>
      <p className="page-sub">
        Runs all 721 pass orderings (6! permutations + baseline) on the current
        program. Each point is one ordering; the highlighted points are the
        Pareto frontier — orderings no other ordering beats on both size and
        cycles. Click a point for details.
      </p>

      <div className="row" style={{ marginBottom: 12 }}>
        <button className="btn primary" onClick={run} disabled={busy}>
          {busy ? 'Running 721 orderings…' : 'Run All 721 Orderings'}
        </button>
        <ExamplePicker examples={examples} onLoad={setSource} />
        {data && (
          <span className="badge info">
            {frontier.size} Pareto-optimal ordering{frontier.size === 1 ? '' : 's'}
          </span>
        )}
        {data && data.results.some((r) => !r.output_correct) ? (
          <span className="badge bad">some orderings incorrect!</span>
        ) : data ? (
          <span className="badge ok">all outputs verified</span>
        ) : null}
      </div>

      {error && <div className="error-box" style={{ marginBottom: 12 }}>{error.message}</div>}

      {!data && <Editor value={source} onChange={setSource} error={error} height="300px" />}

      {data && scatterData && (
        <>
          <div className="grid-2" style={{ alignItems: 'start' }}>
            <div className="panel">
              <div className="panel-head">Size vs Cycles — all orderings</div>
              <div className="panel-body" style={{ height: 380 }}>
                <Scatter
                  data={scatterData}
                  options={{
                    maintainAspectRatio: false,
                    animation: false,
                    onClick: (_evt, elements, chart) => {
                      if (!elements.length) return
                      const el = elements[0]
                      const ds = chart.data.datasets[el.datasetIndex]
                      // @ts-expect-error custom point payload
                      setSelected(ds.data[el.index].entry as BenchmarkEntry)
                    },
                    plugins: {
                      legend: { labels: { color: TEXT_2, usePointStyle: true } },
                      tooltip: {
                        callbacks: {
                          label: (ctx) => {
                            // @ts-expect-error custom point payload
                            const e = ctx.raw.entry as BenchmarkEntry
                            return `${e.label}: ${e.code_size} insts, ${e.estimated_cycles.toFixed(0)} cycles`
                          },
                        },
                      },
                    },
                    scales: {
                      x: {
                        ...axisOpts,
                        title: { display: true, text: 'Static code size (instructions)', color: TEXT_2 },
                      },
                      y: {
                        ...axisOpts,
                        title: { display: true, text: 'Estimated cycles', color: TEXT_2 },
                      },
                    },
                  }}
                />
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">Top 10 orderings by code size</div>
              <div className="panel-body" style={{ height: 380 }}>
                {topData && (
                  <Bar
                    data={topData}
                    options={{
                      indexAxis: 'y',
                      maintainAspectRatio: false,
                      animation: false,
                      onClick: (_evt, elements) => {
                        if (!elements.length) return
                        setSelected(topData.entries[elements[0].index])
                      },
                      plugins: { legend: { display: false } },
                      scales: {
                        x: {
                          ...axisOpts,
                          title: { display: true, text: 'Instructions', color: TEXT_2 },
                        },
                        y: { ...axisOpts, ticks: { ...axisOpts.ticks, font: { size: 10 } } },
                      },
                    }}
                  />
                )}
              </div>
            </div>
          </div>

          {selected && (
            <div className="tiles mt">
              <div className="tile" style={{ minWidth: 320 }}>
                <div className="k">Selected ordering</div>
                <div className="v" style={{ fontSize: 15 }}>
                  {selected.label}
                </div>
                <div className="s neutral">
                  {frontier.has(selected.label) ? 'On the Pareto frontier' : 'Dominated ordering'}
                </div>
              </div>
              <div className="tile">
                <div className="k">Code size</div>
                <div className="v">{selected.code_size}</div>
                <div className="s down">
                  {((1 - selected.code_size / data.baseline.code_size) * 100).toFixed(1)}% vs baseline
                </div>
              </div>
              <div className="tile">
                <div className="k">Est. cycles</div>
                <div className="v">{selected.estimated_cycles.toFixed(0)}</div>
                <div className="s down">
                  {((1 - selected.estimated_cycles / data.baseline.estimated_cycles) * 100).toFixed(1)}% vs baseline
                </div>
              </div>
              <div className="tile">
                <div className="k">Dynamic insts</div>
                <div className="v">{selected.dynamic_count}</div>
                <div className="s neutral">
                  baseline {data.baseline.dynamic_count}
                </div>
              </div>
            </div>
          )}

          <div className="mt">
            <button className="btn small" onClick={() => setData(null)}>
              ← Back to editor
            </button>
          </div>
        </>
      )}
    </div>
  )
}
