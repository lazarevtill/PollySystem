#!/usr/bin/env bash

TARGET="${1:-full-code}"

case "$TARGET" in
  frontend)
    ROOT_DIR="./frontend"
    ;;
  backend)
    ROOT_DIR="./backend"
    ;;
  full-code)
    ROOT_DIR="."
    ;;
  *)
    echo "Invalid target: $TARGET. Use frontend, backend, or full-code."
    exit 1
    ;;
esac

OUTPUT_FILE="${TARGET}.txt"
> "$OUTPUT_FILE"

# File extensions to include
extensions=(
  "*.tsx" "*.ts" "*.js" "*.json" "*.css" "*.env"
  "*.html" "*.config.js" "*.py" "*.ini" "*.sh"
  "*.yaml" "*.yml" "*.md"
)

#########################################
# Define paths to exclude
#########################################
# Directories to prune:
prune_patterns=(
  "$ROOT_DIR/.venv"
  "$ROOT_DIR/venv"
  "$ROOT_DIR/node_modules"
  "$ROOT_DIR/frontend/node_modules"
  "$ROOT_DIR/frontend/.next"
  "$ROOT_DIR/.next"
  # For __pycache__, match any in the tree:
  # Use a pattern that matches anywhere:
  "*/__pycache__"
)

# Individual files to exclude:
exclude_files=(
  "$ROOT_DIR/docker-compose.yml"
  "$ROOT_DIR/create.sh"
  "$ROOT_DIR/frontend.txt"
  "$ROOT_DIR/backend.txt"
  "$ROOT_DIR/full-code.txt"
  "$ROOT_DIR/project_files.txt"
  "$ROOT_DIR/README.md"
  "$ROOT_DIR/package-lock.json"
  "$ROOT_DIR/frontend/package-lock.json"
  "$ROOT_DIR/postcss.config.js"
  "$ROOT_DIR/frontend/postcss.config.js"
  "$ROOT_DIR/frontend/styles/output.css"
)

echo "Collecting files for target: $TARGET"
echo "Output file: $OUTPUT_FILE"

# Build prune conditions
prune_args=()
# For directories, we prune the directory itself
for p in "${prune_patterns[@]}"; do
  prune_args+=(-path "$p" -prune -o)
done

# For single files, we also use -path ... -prune
for f in "${exclude_files[@]}"; do
  prune_args+=(-path "$f" -prune -o)
done

# Build file pattern conditions
file_patterns=()
for ext in "${extensions[@]}"; do
  file_patterns+=( -name "$ext" -o )
done
# Remove the last -o
unset 'file_patterns[-1]'

# Construct final find command:
# Explanation of logic:
# - Start at $ROOT_DIR
# - Apply each -path ... -prune -o condition in sequence
# - Finally, select files with -type f and the name patterns
#
# The logic:
# find $ROOT_DIR [prune conditions] -type f (ext patterns) -print
find "$ROOT_DIR" \
  "${prune_args[@]}" \
  -type f \( "${file_patterns[@]}" \) -print | while IFS= read -r FILE; do
    echo "File: $FILE" >> "$OUTPUT_FILE"
    echo "----------------------------------------" >> "$OUTPUT_FILE"
    cat "$FILE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"
done

echo "Collection complete. Check $OUTPUT_FILE for the combined source."
