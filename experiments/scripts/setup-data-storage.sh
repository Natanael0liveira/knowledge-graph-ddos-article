#!/usr/bin/env bash
#
# setup-data-storage.sh
#
# Configura a estrutura de diretórios no HD externo e cria o .env
# que aponta o repositório para essa raiz de dados.
#
# Uso:
#   ./scripts/setup-data-storage.sh /Volumes/SeuHD/kg-ddos-data
#
# Ou via variável de ambiente:
#   export DATA_ROOT=/Volumes/SeuHD/kg-ddos-data
#   ./scripts/setup-data-storage.sh
#

set -euo pipefail

# ---- argumento ----
DATA_ROOT="${1:-${DATA_ROOT:-}}"
if [[ -z "$DATA_ROOT" ]]; then
    echo "ERRO: forneça o caminho do diretório de dados."
    echo "Uso: $0 /Volumes/SeuHD/kg-ddos-data"
    exit 1
fi

# Resolver path absoluto e validar
DATA_ROOT="$(cd "$(dirname "$DATA_ROOT")" 2>/dev/null && pwd)/$(basename "$DATA_ROOT")" || {
    # se o pai não existe, criar
    DATA_ROOT="$1"
}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Setup de diretórios para experimentos ==="
echo "Repositório:    $REPO_ROOT"
echo "Raiz de dados:  $DATA_ROOT"
echo ""

# ---- criar estrutura no HD externo ----
echo "[1/4] Criando estrutura em $DATA_ROOT..."

mkdir -p "$DATA_ROOT"/{raw,processed,synth,kg,results,logs}
mkdir -p "$DATA_ROOT"/raw/{cic-ddos-2019,cic-ids-2017,cic-iot-2023,rt-iot-2022,bccc-cpacket}
mkdir -p "$DATA_ROOT"/processed/{ja4,flows,sessions,clusters}
mkdir -p "$DATA_ROOT"/synth/{distributions,scenarios}
mkdir -p "$DATA_ROOT"/synth/scenarios/{A,B,C}
mkdir -p "$DATA_ROOT"/kg/{fuseki-tdb2,exports}
mkdir -p "$DATA_ROOT"/results/{raw,aggregated,figures}

echo "    OK."

# ---- verificar espaço livre ----
echo ""
echo "[2/4] Verificando espaço livre..."
FREE_GB=$(df -g "$DATA_ROOT" | awk 'NR==2 {print $4}')
echo "    Espaço livre detectado: ${FREE_GB} GB"

if [[ "$FREE_GB" -lt 100 ]]; then
    echo ""
    echo "    AVISO: recomendamos pelo menos 100 GB livres para todos os sprints."
    echo "    Você tem $FREE_GB GB. Pode continuar, mas Sprint 5 pode ficar apertado."
fi

# ---- escrever .env ----
echo ""
echo "[3/4] Escrevendo $REPO_ROOT/experiments/.env..."

cat > "$REPO_ROOT/experiments/.env" <<EOF
# Auto-gerado por scripts/setup-data-storage.sh em $(date)
# NÃO versionar (já está em .gitignore).
DATA_ROOT=$DATA_ROOT
EOF

echo "    OK."

# ---- criar symlink ----
echo ""
echo "[4/4] Criando symlink experiments/data → $DATA_ROOT..."

# Remover symlink antigo se existir
if [[ -L "$REPO_ROOT/experiments/data" ]]; then
    rm "$REPO_ROOT/experiments/data"
fi

# Não cria symlink se houver um diretório real lá
if [[ -d "$REPO_ROOT/experiments/data" && ! -L "$REPO_ROOT/experiments/data" ]]; then
    echo "    AVISO: $REPO_ROOT/experiments/data existe como diretório regular."
    echo "    Pulando symlink. Acesse o HD diretamente via $DATA_ROOT."
else
    ln -s "$DATA_ROOT" "$REPO_ROOT/experiments/data"
    echo "    OK."
fi

echo ""
echo "=== Setup concluído ==="
echo ""
echo "Verifique:"
echo "  cat $REPO_ROOT/experiments/.env"
echo "  ls -la $REPO_ROOT/experiments/data/"
echo ""
echo "Próximo passo: setup do ambiente Python."
echo "  cd $REPO_ROOT/experiments"
echo "  python3 -m venv .venv"
echo "  source .venv/bin/activate"
echo "  pip install -r requirements.txt"
echo ""
echo "Depois disso: cd sprint-1 && make help"
