import CodeMirror from '@uiw/react-codemirror'
import { cpp } from '@codemirror/lang-cpp'
import { linter, type Diagnostic } from '@codemirror/lint'
import { createTheme } from '@uiw/codemirror-themes'
import { tags as t } from '@lezer/highlight'
import { useMemo } from 'react'
import type { ApiError } from '../api'

// Catppuccin-Mocha editor theme, matching the app tokens in index.css.
const mocha = createTheme({
  theme: 'dark',
  settings: {
    background: '#181825',
    foreground: '#cdd6f4',
    caret: '#89b4fa',
    selection: '#31324499',
    selectionMatch: '#45475a66',
    lineHighlight: '#26263766',
    gutterBackground: '#181825',
    gutterForeground: '#585b70',
    gutterActiveForeground: '#a6adc8',
    gutterBorder: 'transparent',
    fontFamily:
      "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace",
  },
  styles: [
    { tag: [t.keyword, t.controlKeyword, t.moduleKeyword], color: '#cba6f7' },
    { tag: [t.typeName, t.standard(t.typeName)], color: '#f9e2af' },
    { tag: t.number, color: '#fab387' },
    { tag: [t.string, t.special(t.string)], color: '#a6e3a1' },
    { tag: [t.comment, t.blockComment, t.lineComment], color: '#6c7086', fontStyle: 'italic' },
    { tag: [t.function(t.variableName), t.function(t.propertyName)], color: '#89b4fa' },
    { tag: t.variableName, color: '#cdd6f4' },
    { tag: [t.operator, t.punctuation], color: '#94e2d5' },
    { tag: t.bracket, color: '#9399b2' },
    { tag: t.bool, color: '#fab387' },
  ],
})

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
        theme={mocha}
        onChange={onChange}
        extensions={[cpp(), lintExt]}
        basicSetup={{ foldGutter: false, autocompletion: false }}
      />
    </div>
  )
}
