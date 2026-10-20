#!/usr/bin/env bash
#
# sync-bib.sh
#
# Copies shared/references.bib into the paper directories that use it, replacing
# the symlink that existed before (Overleaf does not accept symlinks).
#
# Why it exists: Overleaf rejects GitHub imports that contain symlinks, so
# shared/references.bib is the master and papers/<X>/references.bib are real
# copies, kept in step by this script.
#
# Usage: run it after editing shared/references.bib, before committing.
#
#   ./scripts/sync-bib.sh            # copy the master into every target
#   ./scripts/sync-bib.sh --check    # report divergence without copying
#
# Only the superseded manuscript (papers/http-session/) uses the master. The NOMS
# paper keeps its own papers/http-session-noms/references.bib, with only the
# entries it or its Portuguese translation cites (the translation keeps an
# identical copy). Syncing it from the master would break the submission.

set -euo pipefail

# Repository root (the script runs from anywhere)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MASTER="$REPO_ROOT/shared/references.bib"

TARGETS=(
    "$REPO_ROOT/papers/http-session/references.bib"
)

if [[ ! -f "$MASTER" ]]; then
    echo "ERROR: $MASTER not found." >&2
    exit 1
fi

MODE="${1:-sync}"

case "$MODE" in
    --check)
        FAIL=0
        for target in "${TARGETS[@]}"; do
            if [[ ! -f "$target" ]]; then
                echo "MISSING: $target"
                FAIL=1
            elif ! cmp -s "$MASTER" "$target"; then
                echo "DIVERGES: $target"
                FAIL=1
            else
                echo "OK: $target"
            fi
        done
        exit "$FAIL"
        ;;
    sync|"")
        for target in "${TARGETS[@]}"; do
            # A symlink is removed first, so the copy never overwrites the master
            if [[ -L "$target" ]]; then
                rm "$target"
            fi
            cp "$MASTER" "$target"
            echo "Synced: $target"
        done
        ;;
    *)
        echo "Usage: $0 [--check]" >&2
        exit 2
        ;;
esac
