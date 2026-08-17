#!/bin/sh

# ----------------------------------------
# Run frontend Husky only if ANY file
# inside the frontend/ folder changed
# ----------------------------------------

# Handle first commit safely
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  against=HEAD
else
  against=$(git hash-object -t tree /dev/null)
fi

# Get all staged files
changed_files=$(git diff --cached --name-only "$against")

# Check if ANY file under frontend/ changed
echo "$changed_files" | grep -q '^frontend/'

if [ $? -ne 0 ]; then
  echo "No frontend files changed — skipping Husky."
  exit 0
fi

echo "Frontend files changed — running frontend Husky..."

# Run Husky from inside frontend
(
  cd frontend || exit 1
  ./.husky/pre-commit "$@"
)

exit $?
