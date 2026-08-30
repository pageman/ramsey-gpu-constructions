#!/usr/bin/env bash
# multi-format-paper-publisher: tex (embedded thebibliography) + pdf + docx + txt
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$ROOT/docs/paper/gpu-constructions-after-run001.tex}"
STEM="$(basename "$SRC" .tex)"
OUT="${2:-$ROOT/Downloads/Ramsey-GPU-Constructions/paper}"
mkdir -p "$OUT"
cp "$SRC" "$OUT/$STEM.tex"
cd "$OUT"
pdflatex -interaction=nonstopmode "$STEM.tex" >/tmp/pdflatex-1.log
pdflatex -interaction=nonstopmode "$STEM.tex" >/tmp/pdflatex-2.log
pandoc "$STEM.tex" -o "$STEM.docx"
pandoc "$STEM.tex" -t plain -o "$STEM.txt"
python3 "$ROOT/scripts/check-llm-cliches.py" "$STEM.txt"
ls -la "$STEM.tex" "$STEM.pdf" "$STEM.docx" "$STEM.txt"
