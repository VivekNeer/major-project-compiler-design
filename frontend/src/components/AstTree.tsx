import { useState } from 'react'
import type { AstNode } from '../api'

function NodeView({ node, depth }: { node: AstNode; depth: number }) {
  const [open, setOpen] = useState(depth < 3)
  const hasChildren = node.children.length > 0
  const fields = Object.entries(node.fields).filter(
    ([, v]) => v !== null && v !== '' && !(Array.isArray(v) && v.length === 0),
  )

  return (
    <div className="ast-node">
      <div
        className="node-row"
        onClick={() => hasChildren && setOpen(!open)}
        role={hasChildren ? 'button' : undefined}
      >
        <span className="ast-caret">{hasChildren ? (open ? '▾' : '▸') : '·'}</span>
        <span className="ast-type">{node.type}</span>
        {fields.map(([k, v]) => (
          <span key={k}>
            {' '}
            <span className="ast-field">{k}=</span>
            <span className="ast-value">{JSON.stringify(v)}</span>
          </span>
        ))}
        {node.line > 0 && <span className="ast-field"> :{node.line}</span>}
      </div>
      {open && hasChildren && (
        <div className="ast-children">
          {node.children.map((c, i) => (
            <NodeView key={i} node={c} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function AstTree({ root }: { root: AstNode }) {
  return <NodeView node={root} depth={0} />
}
