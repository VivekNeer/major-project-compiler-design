#!/usr/bin/env bash
# Build the team report and the four individual reports.
#
#   ./build.sh            -> out/report_team.pdf + out/report_<Name>.pdf x4
#   ./build.sh team       -> team copy only
#   ./build.sh C          -> individual copy for student C only
#
# Requires pdflatex on PATH (TeX Live 2023 or later). On the reference
# machine TeX Live comes from nix; set TEXBIN to its bin directory if needed:
#   TEXBIN=/nix/store/<hash>-texlive-2025-...-env/bin ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
PDFLATEX="${TEXBIN:+$TEXBIN/}pdflatex"
mkdir -p out

# student letter -> file-name stem (keep in sync with \StudentA..D in report.tex)
declare -A NAME=( [A]=Aniket_De [B]=Kushal_S_M [C]=Manas_S [D]=Vivek_Neeralagi )

compile() {  # $1 = jobname, $2 = extra TeX preamble ("" for team)
  local job="$1" pre="$2"
  for _ in 1 2 3; do
    "$PDFLATEX" -interaction=nonstopmode -halt-on-error -jobname="$job" \
      "${pre}\input{report.tex}" > "out/$job.log" 2>&1 || { tail -30 "out/$job.log"; exit 1; }
  done
  mv -f "$job.pdf" "out/$job.pdf"
  rm -f "$job".{aux,lof,lot,out,toc,log}
  echo "built out/$job.pdf ($(pdfinfo "out/$job.pdf" 2>/dev/null | awk '/Pages/{print $2}') pages)"
}

what="${1:-all}"
if [[ "$what" == "all" || "$what" == "team" ]]; then
  compile report_team ""
fi
for L in A B C D; do
  if [[ "$what" == "all" || "$what" == "$L" ]]; then
    compile "report_${NAME[$L]}" "\\def\\Individual{$L}"
  fi
done
