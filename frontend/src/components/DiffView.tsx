import type { DiffLine } from '../api'

export default function DiffView({ diff }: { diff: DiffLine[] }) {
  return (
    <>
      {diff.map((d, i) => (
        <div key={i} className={`ir-line ${d.type === 'kept' ? '' : d.type}`}>
          {d.text || ' '}
        </div>
      ))}
    </>
  )
}
