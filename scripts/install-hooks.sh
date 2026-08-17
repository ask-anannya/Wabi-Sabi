#!/bin/sh

set -e

echo "Installing shared Git hooks..."

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT" || exit 1

mkdir -p .git/hooks

if [ ! -f scripts/pre-commit.sh ]; then
  echo "ERROR: scripts/pre-commit.sh not found!"
  echo "Please make sure your shared hook exists."
  exit 1
fi

cp scripts/setup-hooks.sh .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit

echo "Git pre-commit hook installed successfully!"
echo "From now on, commits will automatically run pre-commit.sh"
