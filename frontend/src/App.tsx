import { useEffect, useState } from 'react'
import { api, type ExampleMeta } from './api'
import Playground from './pages/Playground'
import OptLab from './pages/OptLab'
import AssemblyView from './pages/AssemblyView'
import Explorer from './pages/Explorer'
import Reference from './pages/Reference'

const DEFAULT_SOURCE = `int main() {
    int sum = 0;
    for (int i = 1; i <= 10; i = i + 1) {
        sum = sum + i * i;
    }
    print(sum);
    return 0;
}
`

const SECTIONS = [
  { id: 'playground', label: 'Playground', icon: '▶' },
  { id: 'optlab', label: 'Optimization Lab', icon: '⚙' },
  { id: 'assembly', label: 'Assembly', icon: '≣' },
  { id: 'explorer', label: 'Phase Explorer', icon: '◉' },
  { id: 'reference', label: 'Reference', icon: '≡' },
] as const

type SectionId = (typeof SECTIONS)[number]['id']

export default function App() {
  const [section, setSection] = useState<SectionId>('playground')
  const [source, setSource] = useState(DEFAULT_SOURCE)
  const [examples, setExamples] = useState<ExampleMeta[]>([])

  useEffect(() => {
    api.examples().then(setExamples).catch(() => setExamples([]))
  }, [])

  const shared = { source, setSource, examples }

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="brand">
          <span className="brand-chain" aria-hidden="true">
            <i /><i /><i />
          </span>
          Compiler Explorer
          <small>Phase-Ordering Research Tool</small>
        </div>
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            className={`nav-item ${section === s.id ? 'active' : ''}`}
            onClick={() => setSection(s.id)}
          >
            <span className="icon">{s.icon}</span>
            {s.label}
          </button>
        ))}
        <div className="foot">
          C-subset compiler · 6 passes · 721 orderings · RISC-V RV32IM
          <br />
          <a href="/legacy">legacy UI</a>
        </div>
      </nav>
      <main className="main">
        {section === 'playground' && <Playground {...shared} />}
        {section === 'optlab' && <OptLab {...shared} />}
        {section === 'assembly' && <AssemblyView {...shared} />}
        {section === 'explorer' && <Explorer {...shared} />}
        {section === 'reference' && <Reference />}
      </main>
    </div>
  )
}

export interface SharedProps {
  source: string
  setSource: (s: string) => void
  examples: ExampleMeta[]
}
