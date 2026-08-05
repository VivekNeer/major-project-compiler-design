// The app's signature element: the compiler pipeline as a connected rail.
// Each page highlights the span of the pipeline it lets you inspect, so the
// navigation device is also a truthful diagram of how the compiler works.

const STAGES = [
  'source',
  'lexer',
  'parser',
  'semantic',
  'IR',
  'passes',
  'RV32IM',
] as const

export type StageName = (typeof STAGES)[number]

interface Props {
  active: StageName[]
}

export default function PipelineRail({ active }: Props) {
  return (
    <div className="rail" role="img" aria-label={`Compiler pipeline, this page covers: ${active.join(', ')}`}>
      {STAGES.map((s, i) => (
        <span key={s} className="rail-seg">
          {i > 0 && <span className={`rail-link ${active.includes(s) && active.includes(STAGES[i - 1]) ? 'on' : ''}`} />}
          <span className={`rail-node ${active.includes(s) ? 'on' : ''}`}>
            <span className="rail-dot" />
            {s}
          </span>
        </span>
      ))}
    </div>
  )
}
