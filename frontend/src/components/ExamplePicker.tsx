import { api, type ExampleMeta } from '../api'

interface Props {
  examples: ExampleMeta[]
  onLoad: (source: string) => void
}

export default function ExamplePicker({ examples, onLoad }: Props) {
  const suites = ['MiBench', 'PolyBench', 'Other'].filter((s) =>
    examples.some((e) => e.suite === s),
  )

  return (
    <select
      defaultValue=""
      onChange={async (e) => {
        if (!e.target.value) return
        const ex = await api.example(e.target.value)
        onLoad(ex.source)
      }}
    >
      <option value="" disabled>
        Load example…
      </option>
      {suites.map((suite) => (
        <optgroup key={suite} label={suite}>
          {examples
            .filter((e) => e.suite === suite)
            .map((e) => (
              <option key={e.name} value={e.name} title={e.description}>
                {e.name}
              </option>
            ))}
        </optgroup>
      ))}
    </select>
  )
}
