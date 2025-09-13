#!/usr/bin/env bash
set -euo pipefail

# Unified NetBox + Nautobot cleanup utility
# Default: fast cleanup (containers, orphans, redis/cache, nautobot media/static) — keep DBs
# Flags:
#   --nautobot-only     Clean only Nautobot bits (containers, redis, media/static; DB kept unless --db)
#   --netbox-only       Clean only NetBox bits (containers, redis; DB kept unless --db)
#   --db                Also wipe BOTH Postgres databases (NetBox volume + Nautobot bind folder)
#   --all               Clean both stacks (default scope, DB kept unless --db)
#   --images            Prune dangling images
#   --hard              Also remove project networks and named volumes beyond the basics
#   -y/--yes            Non-interactive (auto-confirm DB wipes)
#
# Examples:
#   ./cleanup.sh                 # fast clean (keep DBs)
#   ./cleanup.sh --db            # fast clean + wipe both DBs
#   ./cleanup.sh --nautobot-only # only Nautobot fast clean (keep Nautobot DB)
#   ./cleanup.sh --netbox-only --db  # NetBox clean + wipe NetBox DB
#   ./cleanup.sh --all --images  # both stacks + prune dangling images

# ---------- config you likely won't need to change ----------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_CMD="docker compose"

# Compose service names (from unified-docker/docker-compose.yml)
NB_STACK=( netbox netbox-worker netbox-postgres netbox-redis netbox-redis-cache )
NB_VOLS=( unified-docker_netbox-postgres-data unified-docker_netbox-redis-data unified-docker_netbox-redis-cache-data )
NB_CONTAINER_LEGACY_NAMES=( netbox netbox-worker netbox-housekeeping nb-postgres nb-redis )

NB_NET="unified-docker_netbox-net"

NB_POSTGRES_VOL="unified-docker_netbox-postgres-data"  # named volume
# NetBox stores redis data in named volumes (above)

NB_PORT="8080"

# Nautobot
NBOT_STACK=( nautobot nautobot-worker nautobot-beat nautobot-postgres nautobot-redis )
NBOT_VOLS=( unified-docker_nautobot-static unified-docker_nautobot-media )
NBOT_CONTAINER_LEGACY_NAMES=( nautobot nautobot-worker nautobot-beat )

NBOT_NET="unified-docker_nautobot-net"

# Nautobot DB/Redis are bind-mounts to local folders
NBOT_DB_DIR="${PROJECT_DIR}/postgres"
NBOT_REDIS_DIR="${PROJECT_DIR}/redis"
NBOT_PORT="8081"

# ---------- parse args ----------
SCOPE="all"          # all | nautobot | netbox
WIPE_DB="no"
PRUNE_IMAGES="no"
HARD="no"
ASSUME_YES="no"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --nautobot-only) SCOPE="nautobot"; shift ;;
    --netbox-only)   SCOPE="netbox"; shift ;;
    --db)            WIPE_DB="yes"; shift ;;
    --images)        PRUNE_IMAGES="yes"; shift ;;
    --all)           SCOPE="all"; shift ;;
    --hard)          HARD="yes"; shift ;;
    -y|--yes)        ASSUME_YES="yes"; shift ;;
    -h|--help)
      sed -n '1,80p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

confirm() {
  local prompt="${1:-Are you sure?}"
  if [[ "$ASSUME_YES" == "yes" ]]; then return 0; fi
  read -r -p "$prompt [y/N] " ans
  [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]]
}

have() { command -v "$1" >/dev/null 2>&1; }

if ! have docker; then
  echo "❌ docker not found in PATH"; exit 1
fi
if ! $COMPOSE_CMD version >/dev/null 2>&1; then
  if have docker-compose; then
    COMPOSE_CMD="docker-compose"
  else
    echo "❌ Neither 'docker compose' nor 'docker-compose' is available"; exit 1
  fi
fi

cd "$PROJECT_DIR"

echo "🧹 Cleanup scope: $SCOPE (DB wipe: $WIPE_DB, hard: $HARD, prune images: $PRUNE_IMAGES)"
echo "📁 Project: $PROJECT_DIR"

# ---------- helpers ----------
down_services() {
  echo "⏬ Bringing down compose stack (remove orphans)…"
  $COMPOSE_CMD down --remove-orphans || true
}

rm_named_containers_by_exact_name() {
  local names=("$@")
  for name in "${names[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -xq "$name"; then
      echo "🗑️  Removing leftover container: $name"
      docker rm -f "$name" || true
    fi
  done
}

rm_by_partial_name() {
  local pat="$1"
  docker ps -a --format '{{.ID}} {{.Names}}' | awk -v pat="$pat" '$2 ~ pat {print $1}' | while read -r cid; do
    echo "🗑️  Removing container $cid (matched $pat)…"
    docker rm -f "$cid" || true
  done
}

rm_named_volumes() {
  local vols=("$@")
  for v in "${vols[@]}"; do
    if docker volume ls --format '{{.Name}}' | grep -xq "$v"; then
      echo "🗑️  Removing volume: $v"
      docker volume rm "$v" || true
    fi
  done
}

rm_network() {
  local net="$1"
  if docker network ls --format '{{.Name}}' | grep -xq "$net"; then
    echo "🗑️  Removing network: $net"
    docker network rm "$net" || true
  fi
}

safe_rm_dir() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    echo "🗑️  Removing directory: $dir"
    rm -rf "$dir" 2>/dev/null || {
      echo "⚠️  Permission denied removing $dir. Try: sudo rm -rf \"$dir\""
    }
  fi
}

# ---------- perform cleanup ----------
down_services

case "$SCOPE" in
  nautobot|all)
    echo "🔧 Cleaning Nautobot (fast)…"
    # remove any legacy, conflicting, or stray containers
    rm_named_containers_by_exact_name "${NBOT_CONTAINER_LEGACY_NAMES[@]}"
    # remove any project-scoped containers that may be dangling
    rm_by_partial_name '^unified-docker-nautobot'
    # redis cache/state (safe to delete)
    safe_rm_dir "$NBOT_REDIS_DIR"
    # Nautobot media/static are mounted via named volumes; optional to wipe quickly
    if [[ "$HARD" == "yes" ]]; then
      rm_named_volumes "${NBOT_VOLS[@]}"
    fi
    # DB wipe if requested
    if [[ "$WIPE_DB" == "yes" ]]; then
      if confirm "❗ Wipe Nautobot DB at $NBOT_DB_DIR? This forces full migrations next start."; then
        safe_rm_dir "$NBOT_DB_DIR"
      else
        echo "➡️  Skipping Nautobot DB wipe."
      fi
    fi
    # network removal if requested
    if [[ "$HARD" == "yes" ]]; then
      rm_network "$NBOT_NET"
    fi
    ;;

  netbox|all)
    echo "🔧 Cleaning NetBox (fast)…"
    rm_named_containers_by_exact_name "${NB_CONTAINER_LEGACY_NAMES[@]}"
    rm_by_partial_name '^unified-docker-netbox'
    # redis/cache volumes are fine to remove for a clean restart
    rm_named_volumes unified-docker_netbox-redis-data unified-docker_netbox-redis-cache-data
    # DB wipe if requested (named volume)
    if [[ "$WIPE_DB" == "yes" ]]; then
      if confirm "❗ Wipe NetBox DB volume ($NB_POSTGRES_VOL)? This forces full migrations next start."; then
        rm_named_volumes "$NB_POSTGRES_VOL"
      else
        echo "➡️  Skipping NetBox DB wipe."
      fi
    fi
    if [[ "$HARD" == "yes" ]]; then
      rm_network "$NB_NET"
    fi
    ;;
esac

# prune dangling images if asked
if [[ "$PRUNE_IMAGES" == "yes" ]]; then
  echo "🧽 Pruning dangling images…"
  docker image prune -f || true
fi

echo "✅ Cleanup complete."
echo "➡️  Next: ./start.sh"
