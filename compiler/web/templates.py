"""HTML/CSS/JS frontend for the interactive compiler learning tool.

The entire frontend is a single HTML string served by FastAPI.
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Compiler Explorer</title>
<style>
:root {
  --bg: #1e1e2e; --surface: #282840; --surface2: #313150;
  --text: #cdd6f4; --subtext: #a6adc8; --blue: #89b4fa;
  --green: #a6e3a1; --red: #f38ba8; --yellow: #f9e2af;
  --peach: #fab387; --mauve: #cba6f7; --teal: #94e2d5;
  --overlay: #45475a; --radius: 8px; --font-mono: 'Consolas','Fira Code',monospace;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:'Segoe UI',system-ui,sans-serif; font-size:14px; }
header { background:var(--surface); border-bottom:1px solid var(--overlay); padding:12px 24px; display:flex; align-items:center; justify-content:space-between; }
header h1 { font-size:18px; font-weight:600; }
header h1 span { color:var(--blue); }
.header-controls { display:flex; gap:12px; align-items:center; }
button { background:var(--surface2); color:var(--text); border:1px solid var(--overlay); padding:6px 16px; border-radius:var(--radius); cursor:pointer; font-size:13px; transition:background .15s; }
button:hover { background:var(--overlay); }
button.primary { background:var(--blue); color:var(--bg); border-color:var(--blue); font-weight:600; }
button.primary:hover { opacity:0.9; }
select { background:var(--surface2); color:var(--text); border:1px solid var(--overlay); padding:6px 10px; border-radius:var(--radius); font-size:13px; }
.mode-toggle { display:flex; gap:2px; background:var(--surface2); border-radius:var(--radius); padding:2px; }
.mode-toggle button { border:none; border-radius:6px; padding:6px 16px; font-size:12px; font-weight:500; }
.mode-toggle button.active { background:var(--blue); color:var(--bg); }
.hidden { display:none !important; }

/* === LEARN MODE === */
#learn-mode { padding:16px 24px; }
.step-bar { display:flex; gap:4px; margin-bottom:16px; }
.step-tab { padding:8px 14px; background:var(--surface); border:1px solid var(--overlay); border-radius:var(--radius); font-size:12px; cursor:pointer; color:var(--subtext); }
.step-tab.active { background:var(--blue); color:var(--bg); border-color:var(--blue); font-weight:600; }
.step-tab.done { border-color:var(--green); color:var(--green); }
.learn-layout { display:grid; grid-template-columns:1fr 1fr; gap:16px; min-height:calc(100vh - 160px); }
.panel { background:var(--surface); border:1px solid var(--overlay); border-radius:var(--radius); overflow:hidden; }
.panel-header { background:var(--surface2); padding:8px 14px; font-size:12px; font-weight:600; color:var(--subtext); text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid var(--overlay); display:flex; justify-content:space-between; align-items:center; }
.panel-body { padding:14px; overflow:auto; max-height:calc(100vh - 220px); }
.nav-bar { display:flex; justify-content:space-between; align-items:center; margin-top:12px; padding:8px 0; }

/* Code editor */
.editor textarea { width:100%; min-height:200px; background:var(--bg); color:var(--text); border:1px solid var(--overlay); border-radius:var(--radius); padding:12px; font-family:var(--font-mono); font-size:13px; resize:vertical; line-height:1.6; }
.editor textarea:focus { outline:none; border-color:var(--blue); }

/* Tokens */
.token-list { display:flex; flex-wrap:wrap; gap:6px; }
.token-chip { padding:4px 10px; border-radius:20px; font-family:var(--font-mono); font-size:12px; cursor:pointer; transition:transform .1s; }
.token-chip:hover { transform:scale(1.05); }
.token-chip.keyword { background:#313169; color:var(--blue); }
.token-chip.identifier { background:#1e3a2e; color:var(--green); }
.token-chip.number { background:#3a2e1e; color:var(--peach); }
.token-chip.operator { background:#2e2e2e; color:var(--subtext); }
.token-chip.delimiter { background:#2e2e2e; color:var(--subtext); }

/* AST tree */
.ast-tree { font-family:var(--font-mono); font-size:12px; }
.ast-node { margin-left:20px; border-left:1px solid var(--overlay); padding-left:10px; margin-top:4px; }
.ast-node-header { cursor:pointer; padding:3px 6px; border-radius:4px; display:inline-block; }
.ast-node-header:hover { background:var(--surface2); }
.ast-type { color:var(--mauve); font-weight:600; }
.ast-field { color:var(--subtext); font-size:11px; }
.ast-loc { color:var(--overlay); font-size:10px; }

/* Symbol table */
.sym-table { width:100%; border-collapse:collapse; font-size:13px; }
.sym-table th { background:var(--surface2); padding:8px 12px; text-align:left; font-weight:600; color:var(--subtext); }
.sym-table td { padding:6px 12px; border-top:1px solid var(--overlay); }

/* IR view */
.ir-view { font-family:var(--font-mono); font-size:12px; line-height:1.7; white-space:pre; }
.ir-line { padding:1px 8px; }
.ir-line.removed { background:rgba(243,139,168,0.15); color:var(--red); text-decoration:line-through; }
.ir-line.added { background:rgba(166,227,161,0.15); color:var(--green); }
.ir-line.kept { color:var(--subtext); }

/* Metrics */
.metrics-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:16px; }
.metric-card { background:var(--bg); border:1px solid var(--overlay); border-radius:var(--radius); padding:12px; text-align:center; }
.metric-value { font-size:28px; font-weight:700; color:var(--blue); font-family:var(--font-mono); }
.metric-label { font-size:11px; color:var(--subtext); margin-top:4px; }
.metric-bar { height:6px; background:var(--overlay); border-radius:3px; margin-top:8px; overflow:hidden; }
.metric-bar-fill { height:100%; border-radius:3px; transition:width .3s; }

/* Explanation box */
.explanation { background:var(--bg); border:1px solid var(--overlay); border-radius:var(--radius); padding:12px; margin-top:12px; font-size:13px; line-height:1.6; }
.explanation h4 { color:var(--blue); margin-bottom:6px; font-size:13px; }
.explanation p { color:var(--subtext); }

/* Output */
.output-box { background:var(--bg); border:1px solid var(--overlay); border-radius:var(--radius); padding:12px; font-family:var(--font-mono); font-size:13px; }
.output-value { color:var(--green); }
.output-correct { color:var(--green); }
.output-incorrect { color:var(--red); }

/* Error display */
.error-box { background:rgba(243,139,168,0.1); border:1px solid var(--red); border-radius:var(--radius); padding:12px; margin:12px 0; }
.error-box h4 { color:var(--red); font-size:13px; margin-bottom:4px; }
.error-box p { color:var(--text); font-size:13px; }

/* === EXPLORE MODE === */
#explore-mode { display:grid; grid-template-columns:1fr 1.2fr 0.8fr; grid-template-rows:1fr auto; gap:12px; padding:16px 24px; height:calc(100vh - 60px); }
#explore-mode .panel-body { max-height:calc(100vh - 200px); }
.pass-toolbar { grid-column:1/4; background:var(--surface); border:1px solid var(--overlay); border-radius:var(--radius); padding:12px 16px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.pass-chip { display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:20px; font-family:var(--font-mono); font-size:12px; font-weight:600; cursor:grab; user-select:none; border:2px solid transparent; transition:transform .1s, border-color .15s; }
.pass-chip:active { cursor:grabbing; transform:scale(1.05); }
.pass-chip.cf { background:#313169; color:var(--blue); }
.pass-chip.dce { background:#1e3a2e; color:var(--green); }
.pass-chip.cse { background:#3a2e1e; color:var(--peach); }
.pass-chip.cp { background:#3a1e3a; color:var(--mauve); }
.pass-chip.sr { background:#1e3a3a; color:var(--teal); }
.pass-chip.as { background:#3a3a1e; color:var(--yellow); }
.pass-chip.drag-over { border-color:var(--blue); }
.toolbar-label { font-size:12px; color:var(--subtext); font-weight:600; }

/* Compare mode */
.compare-layout { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.compare-header { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.compare-label { font-weight:700; font-size:14px; }
.compare-a { color:var(--blue); }
.compare-b { color:var(--peach); }

/* Spinner */
.spinner { display:inline-block; width:18px; height:18px; border:2px solid var(--overlay); border-top-color:var(--blue); border-radius:50%; animation:spin .6s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
</head>
<body>

<header>
  <h1><span>&#9881;</span> Compiler Explorer</h1>
  <div class="header-controls">
    <select id="example-select" onchange="loadExample(this.value)">
      <option value="">Load Example...</option>
    </select>
    <div class="mode-toggle">
      <button id="btn-learn" class="active" onclick="setMode('learn')">Learn</button>
      <button id="btn-explore" onclick="setMode('explore')">Explore</button>
    </div>
  </div>
</header>

<!-- ==================== LEARN MODE ==================== -->
<div id="learn-mode">
  <div class="step-bar" id="step-bar"></div>
  <div class="learn-layout">
    <div class="panel">
      <div class="panel-header">Source Code</div>
      <div class="panel-body editor">
        <textarea id="source-editor" spellcheck="false" placeholder="Enter your C code here...">int main() {
    int a = 2 + 3;
    int b = a * 4;
    int unused = 99;
    print(b);
    return 0;
}</textarea>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header">
        <span id="step-title">Click Compile to start</span>
        <button id="btn-info" onclick="toggleExplanation()" style="font-size:11px;padding:3px 10px;">? How it works</button>
      </div>
      <div class="panel-body" id="step-content">
        <p style="color:var(--subtext)">Write or load a program, then click <b>Compile</b> to see each phase.</p>
      </div>
      <div class="explanation hidden" id="explanation-box">
        <h4 id="explanation-title"></h4>
        <p id="explanation-text"></p>
      </div>
    </div>
  </div>
  <div class="nav-bar">
    <button id="btn-prev" onclick="prevStep()" disabled>&larr; Previous</button>
    <button id="btn-compile" class="primary" onclick="compile()">Compile</button>
    <button id="btn-next" onclick="nextStep()" disabled>Next &rarr;</button>
  </div>
</div>

<!-- ==================== EXPLORE MODE ==================== -->
<div id="explore-mode" class="hidden">
  <div class="panel">
    <div class="panel-header">Source Code</div>
    <div class="panel-body editor">
      <textarea id="explore-editor" spellcheck="false" placeholder="Enter your C code here..."></textarea>
    </div>
  </div>
  <div class="panel">
    <div class="panel-header">
      <span>IR View</span>
      <div style="display:flex;gap:4px;">
        <button class="active" id="btn-ir-base" onclick="setIRView('base')" style="font-size:11px;padding:3px 10px;">Base</button>
        <button id="btn-ir-opt" onclick="setIRView('opt')" style="font-size:11px;padding:3px 10px;">Optimized</button>
        <button id="btn-ir-diff" onclick="setIRView('diff')" style="font-size:11px;padding:3px 10px;">Diff</button>
      </div>
    </div>
    <div class="panel-body ir-view" id="explore-ir">
      <span style="color:var(--subtext)">Compile a program to see IR</span>
    </div>
  </div>
  <div class="panel">
    <div class="panel-header">
      <span>Metrics</span>
      <button id="btn-compare" onclick="toggleCompare()" style="font-size:11px;padding:3px 10px;">Compare</button>
    </div>
    <div class="panel-body" id="explore-metrics">
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-value" id="m-size">-</div>
          <div class="metric-label">Code Size</div>
          <div class="metric-bar"><div class="metric-bar-fill" id="m-size-bar" style="width:0%;background:var(--blue)"></div></div>
        </div>
        <div class="metric-card">
          <div class="metric-value" id="m-cycles">-</div>
          <div class="metric-label">Est. Cycles</div>
          <div class="metric-bar"><div class="metric-bar-fill" id="m-cycles-bar" style="width:0%;background:var(--peach)"></div></div>
        </div>
        <div class="metric-card">
          <div class="metric-value" id="m-dynamic">-</div>
          <div class="metric-label">Dynamic Insts</div>
          <div class="metric-bar"><div class="metric-bar-fill" id="m-dynamic-bar" style="width:0%;background:var(--green)"></div></div>
        </div>
      </div>
      <div class="output-box" id="explore-output" style="margin-top:8px;">
        <span style="color:var(--subtext)">Output will appear here</span>
      </div>
      <div id="explore-explanation" class="explanation hidden"></div>
    </div>
  </div>
  <div class="pass-toolbar">
    <span class="toolbar-label">Pass Order:</span>
    <div id="pass-chips" style="display:flex;gap:6px;flex:1;flex-wrap:wrap;"></div>
    <button class="primary" onclick="applyPasses()">Apply</button>
  </div>
</div>

<script>
// === STATE ===
let compileData = null;
let currentStep = 0;
let currentMode = 'learn';
let passOrder = ['CF','CP','SR','AS','DCE','CSE'];
let baselineMetrics = null;
let exploreBaseIR = '';
let exploreOptData = null;
let irViewMode = 'base';
let comparing = false;

const STEPS = ['source','tokens','ast','symbols','ir','optimize','execute'];
const STEP_LABELS = ['Source','Tokens','AST','Symbols','IR','Optimize','Execute'];
const TOKEN_CLASSES = {INT:'keyword',IF:'keyword',ELSE:'keyword',WHILE:'keyword',RETURN:'keyword',PRINT:'keyword',NUMBER:'number',IDENTIFIER:'identifier',PLUS:'operator',MINUS:'operator',STAR:'operator',SLASH:'operator',PERCENT:'operator',EQ:'operator',NEQ:'operator',LT:'operator',GT:'operator',LTE:'operator',GTE:'operator',AND:'operator',OR:'operator',NOT:'operator',ASSIGN:'operator',LPAREN:'delimiter',RPAREN:'delimiter',LBRACE:'delimiter',RBRACE:'delimiter',SEMICOLON:'delimiter',COMMA:'delimiter'};
const PASS_COLORS = {CF:'cf',DCE:'dce',CSE:'cse',CP:'cp',SR:'sr',AS:'as'};
const PASS_FULL = {CF:'Constant Folding',DCE:'Dead Code Elimination',CSE:'Common Subexpression Elimination',CP:'Copy Propagation',SR:'Strength Reduction',AS:'Algebraic Simplification'};
const EXPLANATIONS = {
  source: {title:'Source Code',text:'This is the raw input to the compiler. Our language is a small subset of C supporting integers, if/else, while loops, functions, and print statements.'},
  tokens: {title:'Lexical Analysis (Tokenization)',text:'The lexer reads source code character by character and groups them into tokens - the smallest meaningful units like keywords, identifiers, numbers, and operators. Comments and whitespace are discarded.'},
  ast: {title:'Parsing (Syntax Analysis)',text:'The parser checks that the token sequence follows grammar rules and builds an Abstract Syntax Tree (AST) - a hierarchical representation of the program structure. Each node represents a language construct.'},
  symbols: {title:'Symbol Table',text:'The symbol table tracks every variable declaration: its name, type, scope level, and the internal name used in the IR. It handles nested scopes and variable shadowing.'},
  ir: {title:'IR Generation (Three-Address Code)',text:'The IR generator walks the AST and produces flat three-address code instructions. Each instruction has at most one operator and two operands. Complex expressions are broken into simple steps using temporary variables.'},
  optimize: {title:'Optimization Passes',text:'Each optimization pass transforms the IR to produce smaller or faster code. The order of passes matters - this is the phase ordering problem. Different orderings can produce different results.'},
  execute: {title:'Execution & Metrics',text:'The IR interpreter executes the optimized code and counts the actual instructions executed (dynamic count), which accounts for loop iterations. We compare static code size, estimated cycles, and dynamic count.'},
  CF: {title:'Constant Folding',text:'Evaluates expressions with compile-time constant operands. For example, 2+3 becomes 5. Also propagates known constant values through subsequent uses.'},
  DCE: {title:'Dead Code Elimination',text:'Removes instructions that compute values never used by any subsequent instruction. Also removes unreachable code that follows unconditional jumps.'},
  CSE: {title:'Common Subexpression Elimination',text:'Identifies expressions computed previously with the same operands and reuses the earlier result instead of recomputing.'},
  CP: {title:'Copy Propagation',text:'When a variable is assigned as a copy of another (x = y), subsequent uses of x are replaced with y. This often enables further dead code elimination.'},
  SR: {title:'Strength Reduction',text:'Replaces expensive operations with cheaper equivalents. For example, x*2 becomes x+x, x*0 becomes 0, x+0 becomes x.'},
  AS: {title:'Algebraic Simplification',text:'Applies mathematical identities to simplify expressions. For example, x==x becomes 1, x-x becomes 0, x&&0 becomes 0.'},
};

// === INIT ===
document.addEventListener('DOMContentLoaded', () => {
  renderStepBar();
  renderPassChips();
  loadExampleList();
});

async function loadExampleList() {
  try {
    const resp = await fetch('/api/examples');
    const examples = await resp.json();
    const sel = document.getElementById('example-select');
    examples.forEach(e => {
      const opt = document.createElement('option');
      opt.value = e.name;
      opt.textContent = e.name;
      sel.appendChild(opt);
    });
  } catch(e) { console.error(e); }
}

async function loadExample(name) {
  if (!name) return;
  try {
    const resp = await fetch('/api/examples/' + name);
    const data = await resp.json();
    document.getElementById('source-editor').value = data.source;
    document.getElementById('explore-editor').value = data.source;
  } catch(e) { console.error(e); }
}

// === MODE TOGGLE ===
function setMode(mode) {
  currentMode = mode;
  document.getElementById('learn-mode').classList.toggle('hidden', mode !== 'learn');
  document.getElementById('explore-mode').classList.toggle('hidden', mode !== 'explore');
  document.getElementById('btn-learn').classList.toggle('active', mode === 'learn');
  document.getElementById('btn-explore').classList.toggle('active', mode === 'explore');
  // Sync editors
  if (mode === 'explore') {
    document.getElementById('explore-editor').value = document.getElementById('source-editor').value;
  } else {
    document.getElementById('source-editor').value = document.getElementById('explore-editor').value;
  }
}

// === LEARN MODE ===
function renderStepBar() {
  const bar = document.getElementById('step-bar');
  bar.innerHTML = STEP_LABELS.map((label, i) =>
    `<div class="step-tab${i===0?' active':''}" id="stab-${i}" onclick="goToStep(${i})">${label}</div>`
  ).join('');
}

async function compile() {
  const source = currentMode==='learn' ? document.getElementById('source-editor').value : document.getElementById('explore-editor').value;
  document.getElementById('btn-compile').innerHTML = '<span class="spinner"></span>';
  try {
    const resp = await fetch('/api/compile', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source})});
    compileData = await resp.json();
    if (compileData.error) {
      showError(compileData);
      return;
    }
    currentStep = 0;
    goToStep(1); // jump to tokens
    document.getElementById('btn-next').disabled = false;
    // Also store base IR text for explore mode
    exploreBaseIR = compileData.ir_text;
    baselineMetrics = {code_size: compileData.ir.length, estimated_cycles: 0, dynamic_count: 0};
    if (currentMode === 'explore') {
      document.getElementById('explore-ir').innerHTML = renderIRLines(compileData.ir_text, 'kept');
      applyPasses();
    }
  } catch(e) { showError({phase:'network',message:e.message}); }
  finally { document.getElementById('btn-compile').textContent = 'Compile'; }
}

function showError(err) {
  const content = document.getElementById(currentMode==='learn'?'step-content':'explore-ir');
  content.innerHTML = `<div class="error-box"><h4>${err.phase} error${err.line?' at line '+err.line:''}</h4><p>${err.message}</p></div>`;
}

function goToStep(i) {
  if (!compileData && i > 0) return;
  currentStep = i;
  // Update tabs
  document.querySelectorAll('.step-tab').forEach((t,idx) => {
    t.classList.toggle('active', idx === i);
    t.classList.toggle('done', idx < i);
  });
  document.getElementById('btn-prev').disabled = i === 0;
  document.getElementById('btn-next').disabled = !compileData || i >= STEPS.length - 1;
  renderStep(i);
  // Update explanation
  const key = STEPS[i];
  if (EXPLANATIONS[key]) {
    document.getElementById('explanation-title').textContent = EXPLANATIONS[key].title;
    document.getElementById('explanation-text').textContent = EXPLANATIONS[key].text;
  }
}

function nextStep() { if (currentStep < STEPS.length-1) goToStep(currentStep+1); }
function prevStep() { if (currentStep > 0) goToStep(currentStep-1); }

function toggleExplanation() {
  document.getElementById('explanation-box').classList.toggle('hidden');
}

function renderStep(i) {
  const el = document.getElementById('step-content');
  const title = document.getElementById('step-title');
  title.textContent = STEP_LABELS[i];
  switch(STEPS[i]) {
    case 'source': el.innerHTML = '<p style="color:var(--subtext)">Your source code is in the editor on the left. Click Next to see the token stream.</p>'; break;
    case 'tokens': el.innerHTML = renderTokens(compileData.tokens); break;
    case 'ast': el.innerHTML = renderAST(compileData.ast, 0); break;
    case 'symbols': el.innerHTML = renderSymbols(compileData.symbols); break;
    case 'ir': el.innerHTML = '<div class="ir-view">' + renderIRLines(compileData.ir_text, 'kept') + '</div>'; break;
    case 'optimize': renderOptimizeStep(el); break;
    case 'execute': renderExecuteStep(el); break;
  }
}

function renderTokens(tokens) {
  return '<div class="token-list">' + tokens.map(t => {
    const cls = TOKEN_CLASSES[t.type] || 'operator';
    return `<span class="token-chip ${cls}" title="${t.type} at L${t.line}:${t.col}">${t.value}</span>`;
  }).join('') + '</div>';
}

function renderAST(node, depth) {
  if (!node) return '';
  const fields = node.fields ? Object.entries(node.fields).filter(([k,v])=>v!==null&&v!==undefined&&!(Array.isArray(v)&&v.length===0)).map(([k,v])=>`<span class="ast-field">${k}=${JSON.stringify(v)}</span>`).join(' ') : '';
  const loc = `<span class="ast-loc">L${node.line}:${node.col}</span>`;
  const children = (node.children||[]).map(c => renderAST(c, depth+1)).join('');
  const id = 'ast-' + Math.random().toString(36).substr(2,6);
  return `<div class="ast-node">
    <div class="ast-node-header" onclick="this.parentElement.querySelector('.ast-children')?.classList.toggle('hidden')">
      <span class="ast-type">${node.type}</span> ${fields} ${loc}
    </div>
    ${children ? `<div class="ast-children">${children}</div>` : ''}
  </div>`;
}

function renderSymbols(symbols) {
  if (!symbols.length) return '<p style="color:var(--subtext)">No symbols declared.</p>';
  return `<table class="sym-table"><thead><tr><th>Name</th><th>Type</th><th>Scope</th><th>IR Name</th></tr></thead><tbody>` +
    symbols.map(s => `<tr><td>${s.name}</td><td>${s.type}</td><td>${s.scope}</td><td style="font-family:var(--font-mono)">${s.ir_name}</td></tr>`).join('') +
    '</tbody></table>';
}

function renderIRLines(text, defaultType) {
  return text.split('\\n').map(line =>
    `<div class="ir-line ${defaultType}">${escapeHtml(line)}</div>`
  ).join('');
}

function renderDiffLines(diff) {
  return diff.map(d =>
    `<div class="ir-line ${d.type}">${d.type==='removed'?'- ':''}${d.type==='added'?'+ ':''}${escapeHtml(d.text)}</div>`
  ).join('');
}

async function renderOptimizeStep(el) {
  const source = document.getElementById('source-editor').value;
  el.innerHTML = '<p><span class="spinner"></span> Optimizing with all 6 passes...</p>';
  try {
    const resp = await fetch('/api/optimize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source, pass_order:['CF','CP','SR','AS','DCE','CSE']})});
    const data = await resp.json();
    if (data.error) { el.innerHTML = `<div class="error-box"><h4>${data.phase} error</h4><p>${data.message}</p></div>`; return; }
    el.innerHTML = `
      <div style="margin-bottom:8px;font-weight:600;color:var(--blue)">Pass Order: ${data.pass_order.join(' -> ')}</div>
      <div class="ir-view" style="max-height:300px;overflow:auto;">${renderDiffLines(data.diff)}</div>
      <div class="explanation" style="margin-top:12px"><h4>What changed</h4><p>${data.explanation}</p></div>
    `;
  } catch(e) { el.innerHTML = `<p style="color:var(--red)">Error: ${e.message}</p>`; }
}

async function renderExecuteStep(el) {
  const source = document.getElementById('source-editor').value;
  el.innerHTML = '<p><span class="spinner"></span> Running interpreter...</p>';
  try {
    const resp = await fetch('/api/optimize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source, pass_order:['CF','CP','SR','AS','DCE','CSE']})});
    const data = await resp.json();
    if (data.error) { el.innerHTML = `<div class="error-box"><h4>Error</h4><p>${data.message}</p></div>`; return; }
    const baseResp = await fetch('/api/optimize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source, pass_order:[]})});
    const baseData = await baseResp.json();
    el.innerHTML = `
      <div class="metrics-grid">
        <div class="metric-card"><div class="metric-value">${baseData.metrics.code_size} -> ${data.metrics.code_size}</div><div class="metric-label">Code Size</div></div>
        <div class="metric-card"><div class="metric-value">${Math.round(baseData.metrics.estimated_cycles)} -> ${Math.round(data.metrics.estimated_cycles)}</div><div class="metric-label">Est. Cycles</div></div>
        <div class="metric-card"><div class="metric-value">${baseData.metrics.dynamic_count} -> ${data.metrics.dynamic_count}</div><div class="metric-label">Dynamic Insts</div></div>
      </div>
      <div class="output-box">
        <strong>Output:</strong> <span class="output-value">[${data.output.join(', ')}]</span>
        <span class="${data.output_correct?'output-correct':'output-incorrect'}">${data.output_correct?' Correct':' MISMATCH'}</span>
      </div>
    `;
  } catch(e) { el.innerHTML = `<p style="color:var(--red)">Error: ${e.message}</p>`; }
}

// === EXPLORE MODE ===
function renderPassChips() {
  const container = document.getElementById('pass-chips');
  container.innerHTML = passOrder.map((p, i) =>
    `<div class="pass-chip ${PASS_COLORS[p]}" draggable="true" data-idx="${i}"
      ondragstart="dragStart(event)" ondragover="dragOver(event)" ondrop="drop(event)" ondragend="dragEnd(event)"
      title="${PASS_FULL[p]}">${p}</div>`
  ).join('');
}

let dragIdx = null;
function dragStart(e) { dragIdx = +e.target.dataset.idx; e.target.style.opacity='0.4'; }
function dragOver(e) { e.preventDefault(); e.target.classList.add('drag-over'); }
function dragEnd(e) { e.target.style.opacity='1'; document.querySelectorAll('.pass-chip').forEach(c=>c.classList.remove('drag-over')); }
function drop(e) {
  e.preventDefault();
  const toIdx = +e.target.dataset.idx;
  if (dragIdx === null || isNaN(toIdx)) return;
  const item = passOrder.splice(dragIdx, 1)[0];
  passOrder.splice(toIdx, 0, item);
  renderPassChips();
  dragIdx = null;
}

async function applyPasses() {
  const source = document.getElementById('explore-editor').value;
  if (!source.trim()) return;
  // First compile to get baseline if needed
  if (!exploreBaseIR) {
    await compile();
    if (!compileData || compileData.error) return;
  }
  try {
    const resp = await fetch('/api/optimize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source, pass_order: passOrder})});
    exploreOptData = await resp.json();
    if (exploreOptData.error) { showError(exploreOptData); return; }
    // Also get baseline metrics
    const baseResp = await fetch('/api/optimize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source, pass_order:[]})});
    const baseData = await baseResp.json();
    baselineMetrics = baseData.metrics;
    updateExploreView();
  } catch(e) { console.error(e); }
}

function updateExploreView() {
  if (!exploreOptData) return;
  setIRView(irViewMode);
  // Update metrics
  const m = exploreOptData.metrics;
  const b = baselineMetrics || m;
  document.getElementById('m-size').textContent = m.code_size;
  document.getElementById('m-cycles').textContent = Math.round(m.estimated_cycles);
  document.getElementById('m-dynamic').textContent = m.dynamic_count;
  document.getElementById('m-size-bar').style.width = (b.code_size?Math.min(100,m.code_size/b.code_size*100):100)+'%';
  document.getElementById('m-cycles-bar').style.width = (b.estimated_cycles?Math.min(100,m.estimated_cycles/b.estimated_cycles*100):100)+'%';
  document.getElementById('m-dynamic-bar').style.width = (b.dynamic_count?Math.min(100,m.dynamic_count/b.dynamic_count*100):100)+'%';
  // Output
  document.getElementById('explore-output').innerHTML = `<strong>Output:</strong> <span class="output-value">[${exploreOptData.output.join(', ')}]</span> <span class="${exploreOptData.output_correct?'output-correct':'output-incorrect'}">${exploreOptData.output_correct?'Correct':'MISMATCH'}</span>`;
  // Explanation
  const expEl = document.getElementById('explore-explanation');
  expEl.classList.remove('hidden');
  expEl.innerHTML = `<h4>Pass Order: ${exploreOptData.pass_order.join(' -> ')}</h4><p>${exploreOptData.explanation}</p>`;
}

function setIRView(mode) {
  irViewMode = mode;
  ['base','opt','diff'].forEach(m => {
    const btn = document.getElementById('btn-ir-'+m);
    if(btn) btn.classList.toggle('active', m===mode);
  });
  const el = document.getElementById('explore-ir');
  if (!compileData && !exploreOptData) return;
  if (mode === 'base' && compileData) {
    el.innerHTML = renderIRLines(compileData.ir_text, 'kept');
  } else if (mode === 'opt' && exploreOptData) {
    el.innerHTML = renderIRLines(exploreOptData.optimized_ir_text, 'kept');
  } else if (mode === 'diff' && exploreOptData) {
    el.innerHTML = renderDiffLines(exploreOptData.diff);
  }
}

function toggleCompare() {
  comparing = !comparing;
  document.getElementById('btn-compare').textContent = comparing ? 'Exit Compare' : 'Compare';
  // Simple compare: show a prompt for second ordering
  if (comparing && exploreOptData) {
    const second = prompt('Enter second pass order (comma-separated):', 'DCE,CF,CSE,CP,SR,AS');
    if (!second) { comparing=false; return; }
    const source = document.getElementById('explore-editor').value;
    fetch('/api/optimize', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source, pass_order:second.split(',')})})
    .then(r=>r.json()).then(data2 => {
      const el = document.getElementById('explore-ir');
      el.innerHTML = `
        <div class="compare-layout">
          <div><div class="compare-header"><span class="compare-label compare-a">A: ${exploreOptData.pass_order.join('->')}</span> (size:${exploreOptData.metrics.code_size})</div>
            ${renderIRLines(exploreOptData.optimized_ir_text,'kept')}</div>
          <div><div class="compare-header"><span class="compare-label compare-b">B: ${data2.pass_order.join('->')}</span> (size:${data2.metrics.code_size})</div>
            ${renderIRLines(data2.optimized_ir_text,'kept')}</div>
        </div>`;
    });
  }
}

function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
</script>
</body>
</html>"""
