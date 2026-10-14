#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Generate figures first with build_figures.py when updating the source data.
# Requirements: pandoc, XeLaTeX, fonts Times New Roman, Arial and Courier New.
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/pragent-paper-tex.XXXXXX")"
trap 'status=$?; if [ "$status" -ne 0 ]; then tail -50 "$build_dir/build.log" 2>/dev/null || true; fi; rm -rf "$build_dir"' EXIT
pandoc paper.md --from markdown+tex_math_dollars+tex_math_single_backslash+raw_tex --to latex --standalone \
  --template template.tex --number-sections --output "$build_dir/paper.tex"
xelatex -interaction=nonstopmode -halt-on-error -output-directory "$build_dir" "$build_dir/paper.tex" > "$build_dir/build.log"
xelatex -interaction=nonstopmode -halt-on-error -output-directory "$build_dir" "$build_dir/paper.tex" >> "$build_dir/build.log"
cp "$build_dir/paper.pdf" PRAgent_100_Papers_Manuscript.pdf
cp "$build_dir/paper.tex" paper.tex
if rg 'Overfull|Missing character|Warning:.*undefined' "$build_dir/paper.log"; then
  printf '\nReview the layout warnings above.\n'
fi
printf 'Created %s/PRAgent_100_Papers_Manuscript.pdf\n' "$PWD"
