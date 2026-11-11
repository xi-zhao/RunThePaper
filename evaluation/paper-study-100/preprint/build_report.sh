#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/pragent-preprint-tex.XXXXXX")"
trap 'status=$?; if [ "$status" -ne 0 ]; then tail -60 "$build_dir/build.log" 2>/dev/null || true; fi; rm -rf "$build_dir"' EXIT
pandoc report.md --from markdown+tex_math_dollars+tex_math_single_backslash+raw_tex --to latex \
  --standalone --number-sections --template template.tex --output main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$build_dir" main.tex > "$build_dir/build.log"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$build_dir" main.tex >> "$build_dir/build.log"
cp "$build_dir/main.pdf" PRAgent_Technical_Report.pdf
if rg 'Overfull|Missing character|Warning:.*undefined' "$build_dir/main.log"; then
  printf '\nReview the layout warnings above.\n'
fi
printf 'Created PRAgent_Technical_Report.pdf\n'
