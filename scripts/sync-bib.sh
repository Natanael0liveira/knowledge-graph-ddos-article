#!/usr/bin/env bash
#
# sync-bib.sh
#
# Copia shared/references.bib para os diretórios dos papers,
# substituindo o symlink anterior (que o Overleaf não suporta).
#
# Por que existe: o Overleaf rejeita repositórios com symlinks no import
# do GitHub. Mantemos shared/references.bib como master e os papers/<X>/references.bib
# como cópias reais, sincronizadas por este script.
#
# Uso: rode este script sempre que editar shared/references.bib,
# antes de commitar e empurrar para o GitHub.
#
#   ./scripts/sync-bib.sh
#
# Para verificar se há divergência sem copiar, use --check:
#
#   ./scripts/sync-bib.sh --check

set -euo pipefail

# Diretório raiz do repositório (este script roda de qualquer lugar)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MASTER="$REPO_ROOT/shared/references.bib"

TARGETS=(
    "$REPO_ROOT/papers/http-session/references.bib"
    "$REPO_ROOT/papers/cdn-crosssurface/references.bib"
)

if [[ ! -f "$MASTER" ]]; then
    echo "ERRO: $MASTER não encontrado." >&2
    exit 1
fi

MODE="${1:-sync}"

case "$MODE" in
    --check)
        FAIL=0
        for target in "${TARGETS[@]}"; do
            if [[ ! -f "$target" ]]; then
                echo "FALTA: $target"
                FAIL=1
            elif ! cmp -s "$MASTER" "$target"; then
                echo "DIVERGE: $target"
                FAIL=1
            else
                echo "OK: $target"
            fi
        done
        exit "$FAIL"
        ;;
    sync|"")
        for target in "${TARGETS[@]}"; do
            # Se existe e é symlink, remove para evitar substituir o master por engano
            if [[ -L "$target" ]]; then
                rm "$target"
            fi
            cp "$MASTER" "$target"
            echo "Sincronizado: $target"
        done
        ;;
    *)
        echo "Uso: $0 [--check]" >&2
        exit 2
        ;;
esac
