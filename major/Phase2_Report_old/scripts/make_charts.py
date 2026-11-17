import glob, os, statistics, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from compiler.main import run_benchmark
from compiler.benchmarks.visualizer import compute_geomean_summary
from compiler.optimizations.pass_manager import PassManager
from compiler.lexer import Lexer; from compiler.parser import Parser; from compiler.ir_generator import IRGenerator
from compiler.benchmarks.metric_collector import count_code_size

OUT="/home/manas/Desktop/major/Phase2_Report/figures/"
BLUE="#2a78d6"; BLUE_L="#86b6ef"; BLUE_D="#1c5cab"; ORANGE="#eb6834"; AQUA="#1baf7a"
INK="#0b0b0b"; INK2="#52514e"; GRID="#e6e5e1"
plt.rcParams.update({"font.size":9,"axes.edgecolor":GRID,"axes.labelcolor":INK2,"xtick.color":INK2,"ytick.color":INK2,
    "axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,"grid.linewidth":0.8,
    "axes.axisbelow":True,"text.color":INK,"figure.dpi":200,"savefig.dpi":200,"savefig.bbox":"tight","savefig.facecolor":"white"})

allr={}
for f in sorted(glob.glob('compiler/benchmarks/programs/*.c')):
    n=os.path.splitext(os.path.basename(f))[0]; allr[n]=run_benchmark(open(f).read())

rows=[]
for n,rs in allr.items():
    b=[r for r in rs if not r.pass_order][0]; opt=[r for r in rs if r.pass_order]
    rows.append(dict(name=n, base_size=b.code_size, best_size=min(r.code_size for r in opt),
        base_cyc=b.estimated_cycles, best_cyc=min(r.estimated_cycles for r in opt),
        base_dyn=b.dynamic_instruction_count, best_dyn=min(r.dynamic_instruction_count for r in opt),
        distinct=len(set((r.code_size,r.estimated_cycles,r.dynamic_instruction_count) for r in opt)),
        n_best=sum(1 for r in opt if r.code_size==min(x.code_size for x in opt)),
        worst_size=max(r.code_size for r in opt)))
for r in rows:
    r["red_size"]=(1-r["best_size"]/r["base_size"])*100; r["red_cyc"]=(1-r["best_cyc"]/r["base_cyc"])*100; r["red_dyn"]=(1-r["best_dyn"]/r["base_dyn"])*100
json.dump(rows, open("data/data_summary.json","w"), indent=1)

def hbar(ax, names, vals, color, title, fmt="{:.1f}%"):
    y=range(len(names))
    bars=ax.barh(y, vals, height=0.62, color=color, zorder=3)
    for b_,v in zip(bars, vals):
        ax.text(v+0.6, b_.get_y()+b_.get_height()/2, fmt.format(v), va="center", ha="left", fontsize=8, color=INK)
    ax.set_yticks(list(y)); ax.set_yticklabels(names); ax.invert_yaxis()
    ax.set_title(title, fontsize=9.5, loc="left", color=INK, pad=6)
    ax.grid(axis="y", visible=False); ax.set_xlim(0, max(vals)*1.22)
    ax.tick_params(axis="y", length=0)

# (a) reduction small multiples
rs_sorted=sorted(rows, key=lambda r:-r["red_size"])
names=[r["name"] for r in rs_sorted]
fig,axes=plt.subplots(1,3,figsize=(7.2,4.4),sharey=True)
hbar(axes[0],names,[r["red_size"] for r in rs_sorted],BLUE,"Static code size reduction")
hbar(axes[1],names,[r["red_cyc"] for r in rs_sorted],BLUE,"Estimated-cycle reduction")
hbar(axes[2],names,[r["red_dyn"] for r in rs_sorted],BLUE,"Dynamic instruction reduction")
for ax in axes: ax.set_xlabel("% below unoptimized baseline")
fig.tight_layout(w_pad=1.2); fig.savefig(OUT+"fig_reduction_by_program.png"); plt.close(fig)

# (b) position effect dumbbell
passes=["CF","CP","CSE","DCE","SR","AS"]; first={};last={}
for p in passes:
    fv=[];lv=[]
    for n,rs in allr.items():
        b=[r for r in rs if not r.pass_order][0]
        for r in rs:
            if not r.pass_order: continue
            if r.pass_order[0]==p: fv.append(r.code_size/b.code_size)
            if r.pass_order[-1]==p: lv.append(r.code_size/b.code_size)
    first[p]=statistics.mean(fv); last[p]=statistics.mean(lv)
order=sorted(passes,key=lambda p:first[p])
fig,ax=plt.subplots(figsize=(6.6,3.2))
for i,p in enumerate(order):
    ax.plot([first[p],last[p]],[i,i],color=GRID,lw=2.5,zorder=2)
    ax.scatter(first[p],i,s=70,color=BLUE_L,edgecolor="white",lw=1.5,zorder=3)
    ax.scatter(last[p],i,s=70,color=BLUE_D,edgecolor="white",lw=1.5,zorder=3)
    lo,hi=sorted([first[p],last[p]])
    ax.text(lo-0.012,i,f"{lo:.3f}",va="center",ha="right",fontsize=8)
    ax.text(hi+0.012,i,f"{hi:.3f}",va="center",ha="left",fontsize=8)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.invert_yaxis(); ax.tick_params(axis="y",length=0)
ax.set_xlim(0.6,1.05); ax.grid(axis="y",visible=False); ax.set_xlabel("Mean code size ratio vs. baseline over all 15 programs (lower is better)")
ax.scatter([],[],s=70,color=BLUE_L,label="pass runs first"); ax.scatter([],[],s=70,color=BLUE_D,label="pass runs last")
ax.legend(loc="upper right",frameon=False,fontsize=8,ncol=1)
fig.tight_layout(); fig.savefig(OUT+"fig_position_effect.png"); plt.close(fig)
json.dump({"first":first,"last":last},open("data/data_position.json","w"),indent=1)

# (c) distinct outcomes + orderings achieving best
rs2=sorted(rows,key=lambda r:-r["distinct"]); names2=[r["name"] for r in rs2]
fig,axes=plt.subplots(1,2,figsize=(7.2,4.2),sharey=True)
hbar(axes[0],names2,[r["distinct"] for r in rs2],BLUE,"Distinct outcomes among 720 full orderings",fmt="{:.0f}")
hbar(axes[1],names2,[r["n_best"] for r in rs2],BLUE,"Orderings that reach the best code size",fmt="{:.0f}")
axes[0].set_xlabel("count of distinct (size, cycles, dynamic) triples"); axes[1].set_xlabel("count out of 720")
fig.tight_layout(w_pad=1.2); fig.savefig(OUT+"fig_distinct_outcomes.png"); plt.close(fig)

# (d) geomean classes
s=compute_geomean_summary(allr)
classes={}
for label,v in s.items():
    if label=="Baseline (none)": continue
    key=round(v["geomean_size"],4); classes.setdefault(key,{"cyc":[], "dyn":[], "labels":[]})
    classes[key]["cyc"].append(v["geomean_cycles"]); classes[key]["dyn"].append(v["geomean_dynamic"]); classes[key]["labels"].append(label)
items=sorted(classes.items())
labels=[f"{c['labels'][0].replace(' -> ','→')}  (×{len(c['labels'])})" for k,c in items]
vals=[k for k,c in items]
fig,ax=plt.subplots(figsize=(7.0,3.9))
y=range(len(vals)); bars=ax.barh(y,vals,height=0.62,color=BLUE,zorder=3)
for b_,v in zip(bars,vals): ax.text(v+0.008,b_.get_y()+b_.get_height()/2,f"{v:.4f}",va="center",fontsize=8)
ax.set_yticks(list(y)); ax.set_yticklabels(labels,fontsize=7.5); ax.invert_yaxis(); ax.tick_params(axis="y",length=0)
ax.axvline(1.0,color=INK2,lw=1,ls="-",zorder=4); ax.text(1.0,-0.7,"baseline = 1.0",fontsize=7.5,ha="center",color=INK2)
ax.set_xlim(0.5,1.08); ax.grid(axis="y",visible=False)
ax.set_xlabel("Geometric mean of normalized code size across 15 programs")
fig.tight_layout(); fig.savefig(OUT+"fig_geomean_classes.png"); plt.close(fig)
json.dump([{"size":k,"cyc":min(c["cyc"]),"cyc_max":max(c["cyc"]),"dyn":min(c["dyn"]),"n":len(c["labels"]),"rep":c["labels"][0]} for k,c in items],open("data/data_geomean_classes.json","w"),indent=1)

# (e) stage trace for factorial
src=open("compiler/benchmarks/programs/factorial.c").read()
ir=IRGenerator().generate(Parser(Lexer(src).tokenize()).parse())
orders=[["CF","CSE","CP","DCE","SR","AS"],["CF","DCE","CSE","CP","SR","AS"],["DCE","CF","CSE","CP","SR","AS"]]
cols=[BLUE,ORANGE,AQUA]
fig,ax=plt.subplots(figsize=(6.8,3.4))
for o,c in zip(orders,cols):
    cur=ir; ys=[count_code_size(cur)]
    for p in o: cur=PassManager([p]).run(cur); ys.append(count_code_size(cur))
    xs=range(len(ys)); ax.plot(xs,ys,color=c,lw=2,marker="o",ms=6,mec="white",mew=1.5,zorder=3,label="→".join(o))
    ax.text(xs[-1]+0.12,ys[-1],f"{ys[-1]}",va="center",fontsize=8.5)
ax.set_xticks(range(7)); ax.set_xticklabels(["base"]+[f"after\npass {i}" for i in range(1,7)],fontsize=8)
ax.set_ylabel("static code size (instructions)"); ax.set_ylim(0,44); ax.set_xlim(-0.3,6.6)
ax.legend(frameon=False,fontsize=8,loc="upper right"); ax.grid(axis="x",visible=False)
fig.tight_layout(); fig.savefig(OUT+"fig_stage_trace_factorial.png"); plt.close(fig)
print("charts done"); print(json.dumps(rows[:2],indent=0)[:300])
