#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  make_contact_sheets.sh <base_dir> <output_dir> <cols> <rows> <cell_width> <cell_height> [candidate_list]

Examples:
  make_contact_sheets.sh "/path/to/photos" "/tmp/contact_sheets_16" 4 4 480 360
  make_contact_sheets.sh "/path/to/photos" "/tmp/round2" 3 3 640 480 "/tmp/candidate_list.txt"

Backends:
  - macOS: uses osascript + JXA by default
  - Linux / Windows bash environments: uses Python + Pillow
  - Override with PHOTO_SELECTOR_BACKEND=macos-jxa or PHOTO_SELECTOR_BACKEND=python-pillow

Notes:
  - base_dir: directory containing source JPG/JPEG files
  - output_dir: directory where sheet_XX.jpg and index.txt will be written
  - candidate_list: optional text file, one filename per line; filenames are resolved relative to base_dir unless already absolute
EOF
}

if [ "$#" -lt 6 ] || [ "$#" -gt 7 ]; then
  usage >&2
  exit 1
fi

base_dir=$1
output_dir=$2
cols=$3
rows=$4
cell_width=$5
cell_height=$6
candidate_list=${7:-}

if [ ! -d "$base_dir" ]; then
  echo "Base directory not found: $base_dir" >&2
  exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
skill_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
jxa_script="$script_dir/contact_sheet.jxa"
python_script="$script_dir/contact_sheet_pillow.py"

python_cmd=()
backend=""

resolve_python_cmd() {
  if [ "${#python_cmd[@]}" -gt 0 ]; then
    return 0
  fi

  if [ -n "${PHOTO_SELECTOR_PYTHON:-}" ]; then
    python_cmd=("$PHOTO_SELECTOR_PYTHON")
    return 0
  fi

  if [ -x "$skill_dir/.venv/bin/python" ]; then
    python_cmd=("$skill_dir/.venv/bin/python")
    return 0
  fi

  if [ -x "$skill_dir/.venv/Scripts/python.exe" ]; then
    python_cmd=("$skill_dir/.venv/Scripts/python.exe")
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    python_cmd=(python3)
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    python_cmd=(python)
    return 0
  fi

  if command -v py >/dev/null 2>&1; then
    python_cmd=(py -3)
    return 0
  fi

  return 1
}

python_backend_ready() {
  resolve_python_cmd || return 1
  [ -f "$python_script" ] || return 1
  "${python_cmd[@]}" "$python_script" --check-deps >/dev/null 2>&1
}

select_backend() {
  if [ -n "${PHOTO_SELECTOR_BACKEND:-}" ]; then
    case "$PHOTO_SELECTOR_BACKEND" in
      macos-jxa)
        if ! command -v osascript >/dev/null 2>&1; then
          echo "PHOTO_SELECTOR_BACKEND=macos-jxa was requested, but osascript is not available." >&2
          exit 1
        fi
        if [ ! -f "$jxa_script" ]; then
          echo "Missing JXA script: $jxa_script" >&2
          exit 1
        fi
        backend="macos-jxa"
        return 0
        ;;
      python-pillow)
        if ! python_backend_ready; then
          echo "PHOTO_SELECTOR_BACKEND=python-pillow was requested, but Python 3 + Pillow is not ready." >&2
          echo "Install Pillow with: python -m pip install pillow" >&2
          exit 1
        fi
        backend="python-pillow"
        return 0
        ;;
      *)
        echo "Unsupported PHOTO_SELECTOR_BACKEND: $PHOTO_SELECTOR_BACKEND" >&2
        exit 1
        ;;
    esac
  fi

  case "$(uname -s)" in
    Darwin)
      if command -v osascript >/dev/null 2>&1 && [ -f "$jxa_script" ]; then
        backend="macos-jxa"
        return 0
      fi
      ;;
  esac

  if python_backend_ready; then
    backend="python-pillow"
    return 0
  fi

  echo "No compatible contact-sheet backend was found." >&2
  echo "- macOS can use osascript + JXA automatically." >&2
  echo "- Linux / Windows need Python 3 + Pillow (python -m pip install pillow)." >&2
  exit 1
}

basename_any_path() {
  local path=$1
  path=${path//\\//}
  basename "$path"
}

render_page() {
  local output_file=$1
  shift

  case "$backend" in
    macos-jxa)
      osascript -l JavaScript "$jxa_script" \
        "$output_file" \
        "$cols" \
        "$rows" \
        "$cell_width" \
        "$cell_height" \
        "$@" >/dev/null
      ;;
    python-pillow)
      "${python_cmd[@]}" "$python_script" \
        "$output_file" \
        "$cols" \
        "$rows" \
        "$cell_width" \
        "$cell_height" \
        "$@" >/dev/null
      ;;
    *)
      echo "Internal error: backend was not selected." >&2
      exit 1
      ;;
  esac
}

select_backend

mkdir -p "$output_dir"
index_file="$output_dir/index.txt"
: > "$index_file"

files=()

if [ -n "$candidate_list" ]; then
  if [ ! -f "$candidate_list" ]; then
    echo "Candidate list not found: $candidate_list" >&2
    exit 1
  fi

  while IFS= read -r line || [ -n "$line" ]; do
    line=${line%$'\r'}
    [ -n "$line" ] || continue
    case "$line" in
      /*|[A-Za-z]:\\*|[A-Za-z]:/*) files+=("$line") ;;
      *) files+=("$base_dir/$line") ;;
    esac
  done < "$candidate_list"
else
  while IFS= read -r file; do
    files+=("$file")
  done < <(find "$base_dir" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) | LC_ALL=C sort)
fi

count=${#files[@]}
if [ "$count" -eq 0 ]; then
  echo "No JPG files found." >&2
  exit 1
fi

for file in "${files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "Image not found: $file" >&2
    exit 1
  fi
done

page_size=$((cols * rows))
page=1

for ((i = 0; i < count; i += page_size)); do
  page_files=("${files[@]:i:page_size}")
  output_file=$(printf '%s/sheet_%02d.jpg' "$output_dir" "$page")

  render_page "$output_file" "${page_files[@]}"

  first_name=$(basename_any_path "${page_files[0]}")
  last_name=$(basename_any_path "${page_files[${#page_files[@]} - 1]}")
  printf 'sheet_%02d: %s - %s\n' "$page" "$first_name" "$last_name" >> "$index_file"

  page=$((page + 1))
done

printf 'Generated %d sheet(s) for %d image(s) in %s\n' "$((page - 1))" "$count" "$output_dir"
