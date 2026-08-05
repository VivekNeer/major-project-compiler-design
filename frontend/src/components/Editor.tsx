import CodeMirror from '@uiw/react-codemirror'
import { cpp } from '@codemirror/lang-cpp'
import { linter, type Diagnostic } from '@codemirror/lint'
import { EditorView } from '@codemirror/view'
import { useMemo } from 'react'
import type { ApiError } from '../api'

const darkTheme = EditorView.theme(
  {
    '&': { backgroundColor: '#181825', color: '#cdd6f4' },
    '.cm-content': { caretColor: '#89b4fa', fontFamily: 'inherit' },
    '.cm-gutters': {
      backgroundColor: '#181825',
      color: '#585b70',
      border: 'none',
    },
    '.cm-activeLine': { backgroundColor: '#26263780' },
    '.cm-activeLineGutter': { backgroundColor: '#262637' },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground': {
      backgroundColor: '#31324488',
    },
    '.cm-lintRange-error': {
      textDecoration: 'underline wavy #f38ba8',
    },
  },
  { dark: true },
)

interface Props {
  value: string
  onChange: (v: string) => void
  error?: ApiError | null
  height?: string
}

export default function Editor({ value, onChange, error, height = '380px' }: Props) {
  const lintExt = useMemo(
    () =>
      linter((view) => {
        const diagnostics: Diagnostic[] = []
        if (error && error.line != null && error.line > 0) {
          const doc = view.state.doc
          if (error.line <= doc.lines) {
            const line = doc.line(error.line)
            const from = Math.min(line.from + Math.max((error.col ?? 1) - 1, 0), line.to)
            diagnostics.push({
              from,
              to: line.to,
              severity: 'error',
              message: `[${error.phase}] ${error.message}`,
            })
          }
        }
        return diagnostics
      }),
    [error],
  )

  return (
    <div className="cm-wrap">
      <CodeMirror
        value={value}
        height={height}
        onChange={onChange}
        extensions={[cpp(), darkTheme, lintExt]}
        basicSetup={{ foldGutter: false, autocompletion: false }}
      />
    </div>
  )
}
