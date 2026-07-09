#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="$ROOT_DIR/test_papers"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl was not found in PATH." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

download() {
  arxiv_id="$1"
  filename="$2"
  target="$TARGET_DIR/$filename"

  if [ -s "$target" ] && head -c 5 "$target" | grep -q "%PDF-"; then
    echo "Already present: $filename"
    return
  fi

  echo "Downloading arXiv:$arxiv_id -> $filename"
  curl \
    --fail \
    --location \
    --retry 3 \
    --retry-delay 2 \
    --user-agent "Read2Reproduce test fixture downloader" \
    "https://arxiv.org/pdf/$arxiv_id" \
    --output "$target.tmp"

  if ! head -c 5 "$target.tmp" | grep -q "%PDF-"; then
    rm -f "$target.tmp"
    echo "Downloaded content is not a PDF: arXiv:$arxiv_id" >&2
    exit 1
  fi

  mv "$target.tmp" "$target"
}

download "1706.03762" "computer_science_1706.03762_attention_is_all_you_need.pdf"
download "1602.03837" "physics_1602.03837_gravitational_waves.pdf"
download "math/0211159" "mathematics_math0211159_ricci_flow.pdf"
download "1610.08935" "chemistry_1610.08935_ani_1.pdf"
download "2311.12143" "biology_2311.12143_gene_expression.pdf"
download "1908.06687" "medicine_1908.06687_clinical_trial_survival.pdf"
download "2406.01898" "economics_2406.01898_economic_dynamics.pdf"
download "2307.01918" "social_science_2307.01918_computational_reproducibility.pdf"
download "2103.13729" "engineering_2103.13729_digital_twinning.pdf"
download "2211.11861" "humanities_2211.11861_digital_historian.pdf"

echo "Test papers are ready in $TARGET_DIR"
