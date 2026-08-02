#!/usr/bin/env bash
#
# deploy-voicebox-lxc.sh — provision Voicebox as a Docker stack inside a
# dedicated unprivileged LXC on Proxmox VE.
#
#   Run this ON the Proxmox host (192.168.68.4), as root.
#
#   Preview the RAM maths without changing anything:
#       ./deploy-voicebox-lxc.sh --check
#
#   Deploy:
#       ./deploy-voicebox-lxc.sh
#
# Why an LXC and not a VM: Voicebox is a single Docker workload. An LXC shares
# the host kernel, so there is no second kernel + balloon driver overhead, and
# the memory cap is a hard cgroup limit rather than a ballooned guess. That
# matters when the explicit requirement is "don't run the node out of RAM".
#
# The RAM safety model is three nested ceilings:
#
#     Proxmox node
#       └─ LXC            memory = CT_RAM        (hard cgroup limit)
#            └─ container mem_limit = CT_RAM-2GB (hard cgroup limit)
#
# The container OOMs before the LXC does, and the LXC OOMs before the node
# notices. The node itself always keeps HOST_RESERVE_MB plus whatever every
# other running guest has already been promised.

set -euo pipefail

# ─── Tunables (override via environment) ──────────────────────────────────────
CT_HOSTNAME="${CT_HOSTNAME:-voicebox}"
CT_RAM_WANTED_MB="${CT_RAM_WANTED_MB:-12288}"   # 12 GB target for the LXC
CT_RAM_FLOOR_MB="${CT_RAM_FLOOR_MB:-10240}"     # refuse to deploy below 10 GB
CT_SWAP_MB="${CT_SWAP_MB:-2048}"
CT_CORES="${CT_CORES:-4}"
CT_DISK_GB="${CT_DISK_GB:-48}"                  # ~11 GB image + ~10 GB models + room
HOST_RESERVE_MB="${HOST_RESERVE_MB:-2048}"      # never hand this to a guest
CONTAINER_HEADROOM_MB="${CONTAINER_HEADROOM_MB:-2048}"  # LXC RAM minus container cap
VOICEBOX_TAG="${VOICEBOX_TAG:-latest}"
CT_BRIDGE="${CT_BRIDGE:-vmbr0}"
CT_IP="${CT_IP:-dhcp}"                          # or e.g. 192.168.68.60/24
CT_GW="${CT_GW:-}"                              # required if CT_IP is static
TEMPLATE_PATTERN="${TEMPLATE_PATTERN:-debian-13-standard}"

DRY_RUN=0
[[ "${1:-}" == "--check" || "${1:-}" == "--dry-run" ]] && DRY_RUN=1

# ─── Output helpers ───────────────────────────────────────────────────────────
c_red=$'\e[31m'; c_grn=$'\e[32m'; c_yel=$'\e[33m'; c_blu=$'\e[36m'; c_off=$'\e[0m'
info() { echo "${c_blu}==>${c_off} $*"; }
ok()   { echo "${c_grn} ok${c_off} $*"; }
warn() { echo "${c_yel}  !${c_off} $*"; }
die()  { echo "${c_red}FAIL${c_off} $*" >&2; exit 1; }

# ─── Preflight ────────────────────────────────────────────────────────────────
# --check changes nothing, so it does not require root. Being able to preview
# the RAM maths without sudo is genuinely useful, and it makes this script
# testable.
if (( ! DRY_RUN )); then
    [[ $EUID -eq 0 ]] || die "must run as root on the Proxmox host (or use --check to preview)"
fi
command -v pct >/dev/null 2>&1 || die "pct not found — this is not a Proxmox VE host"
command -v pvesh >/dev/null 2>&1 || die "pvesh not found — this is not a Proxmox VE host"

info "Proxmox $(pveversion | head -1)"
info "Node: $(hostname)"

# ─── RAM budget ───────────────────────────────────────────────────────────────
# Count RAM already *promised* to running guests, not merely RAM currently
# touched. A guest that is idle today can balloon up tomorrow, so committed
# allocation is the honest number to plan against.
node_total_mb=$(free -m | awk '/^Mem:/{print $2}')
node_used_mb=$(free -m | awk '/^Mem:/{print $3}')

allocated_mb=0
guest_lines=""

while read -r id state; do
    [[ -z "$id" ]] && continue
    # `|| true` matters: if a guest vanishes between `qm list` and `qm config`,
    # or the config read hiccups, pipefail + set -e would otherwise abort the
    # whole deployment silently. A guest we can't read is skipped, not fatal.
    m=$(qm config "$id" 2>/dev/null | awk -F': ' '/^memory:/{print $2; exit}' || true)
    [[ "$m" =~ ^[0-9]+$ ]] || m=0
    allocated_mb=$((allocated_mb + m))
    guest_lines+=$(printf '\n    VM  %-6s %-9s %6s MB' "$id" "$state" "$m")
done < <(qm list 2>/dev/null | awk 'NR>1 && $3=="running"{print $1, $3}' || true)

while read -r id state; do
    [[ -z "$id" ]] && continue
    m=$(pct config "$id" 2>/dev/null | awk -F': ' '/^memory:/{print $2; exit}' || true)
    [[ "$m" =~ ^[0-9]+$ ]] || m=0
    allocated_mb=$((allocated_mb + m))
    guest_lines+=$(printf '\n    LXC %-6s %-9s %6s MB' "$id" "$state" "$m")
done < <(pct list 2>/dev/null | awk 'NR>1 && $2=="running"{print $1, $2}' || true)

budget_mb=$(( node_total_mb - allocated_mb - HOST_RESERVE_MB ))

echo
echo "  ── RAM budget on $(hostname) ──────────────────────────────"
printf '    node total                 %6s MB\n' "$node_total_mb"
printf '    node currently used        %6s MB\n' "$node_used_mb"
if [[ -n "$guest_lines" ]]; then
    echo "    committed to running guests:${guest_lines}"
else
    echo "    committed to running guests: (none)"
fi
printf '    -------------------------------------\n'
printf '    committed total            %6s MB\n' "$allocated_mb"
printf '    reserved for PVE host      %6s MB\n' "$HOST_RESERVE_MB"
printf '    AVAILABLE FOR VOICEBOX     %6s MB\n' "$budget_mb"
echo   "  ───────────────────────────────────────────────────────────"
echo

if (( budget_mb < CT_RAM_FLOOR_MB )); then
    die "only ${budget_mb} MB free but Voicebox needs at least ${CT_RAM_FLOOR_MB} MB.
      Options: use the other Proxmox node, shut down an idle guest, add RAM,
      or lower CT_RAM_FLOOR_MB if you accept a single-engine/slow config."
fi

CT_RAM_MB=$CT_RAM_WANTED_MB
if (( CT_RAM_MB > budget_mb )); then
    CT_RAM_MB=$budget_mb
    warn "trimming LXC RAM to ${CT_RAM_MB} MB to stay inside the node budget"
fi
CONTAINER_MEM_MB=$(( CT_RAM_MB - CONTAINER_HEADROOM_MB ))

if (( CT_RAM_MB < 16384 )); then
    warn "under 16 GB: Voicebox will run one TTS engine at a time comfortably."
    warn "Loading several engines concurrently may hit the cap. This is expected."
fi

ok "LXC will get ${CT_RAM_MB} MB; Voicebox container hard-capped at ${CONTAINER_MEM_MB} MB"
ok "node keeps $(( budget_mb - CT_RAM_MB + HOST_RESERVE_MB )) MB of headroom"

# ─── GPU detection ────────────────────────────────────────────────────────────
IMAGE_TAG="$VOICEBOX_TAG"
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
    warn "NVIDIA GPU detected: $(nvidia-smi -L | head -1)"
    warn "This script deploys the CPU image. For CUDA, pass GPU devices into the"
    warn "LXC and re-run with VOICEBOX_TAG=latest-cuda. See README."
else
    info "No NVIDIA GPU — using the CPU image (LuxTTS is the fast engine on CPU)"
fi

# ─── Storage ──────────────────────────────────────────────────────────────────
ROOT_STORAGE="${ROOT_STORAGE:-$(pvesm status --content rootdir 2>/dev/null | awk 'NR>1 && $3=="active"{print $1; exit}')}"
[[ -n "$ROOT_STORAGE" ]] || die "no active storage supporting 'rootdir' found"
TMPL_STORAGE="${TMPL_STORAGE:-$(pvesm status --content vztmpl 2>/dev/null | awk 'NR>1 && $3=="active"{print $1; exit}')}"
[[ -n "$TMPL_STORAGE" ]] || die "no active storage supporting 'vztmpl' found"
ok "rootfs storage: ${ROOT_STORAGE}   template storage: ${TMPL_STORAGE}"

CTID="${CTID:-$(pvesh get /cluster/nextid)}"
ok "next free container ID: ${CTID}"

if (( DRY_RUN )); then
    echo
    info "--check mode: nothing was changed."
    info "Would create LXC ${CTID} (${CT_HOSTNAME}): ${CT_RAM_MB} MB RAM, ${CT_CORES} cores, ${CT_DISK_GB} GB on ${ROOT_STORAGE}"
    info "Would run ghcr.io/jamiepine/voicebox:${IMAGE_TAG} capped at ${CONTAINER_MEM_MB} MB"
    exit 0
fi

# ─── Template ─────────────────────────────────────────────────────────────────
info "Resolving ${TEMPLATE_PATTERN} template..."
pveam update >/dev/null 2>&1 || warn "pveam update failed; using cached index"

TEMPLATE_FILE=$(pveam list "$TMPL_STORAGE" 2>/dev/null | awk -v p="$TEMPLATE_PATTERN" '$1 ~ p {print $1; exit}')
if [[ -z "$TEMPLATE_FILE" ]]; then
    AVAIL=$(pveam available --section system | awk -v p="$TEMPLATE_PATTERN" '$2 ~ p {print $2}' | sort -V | tail -1)
    [[ -n "$AVAIL" ]] || die "no template matching '${TEMPLATE_PATTERN}' is available"
    info "Downloading ${AVAIL}..."
    pveam download "$TMPL_STORAGE" "$AVAIL"
    TEMPLATE_FILE=$(pveam list "$TMPL_STORAGE" | awk -v p="$TEMPLATE_PATTERN" '$1 ~ p {print $1; exit}')
fi
ok "template: ${TEMPLATE_FILE}"

# ─── Create the LXC ───────────────────────────────────────────────────────────
NET="name=eth0,bridge=${CT_BRIDGE},ip=${CT_IP}"
[[ "$CT_IP" != "dhcp" && -n "$CT_GW" ]] && NET="${NET},gw=${CT_GW}"

info "Creating LXC ${CTID}..."
# nesting + keyctl are what make Docker work in an unprivileged container.
# Unprivileged is worth keeping: a root break-out inside the container maps to
# an unprivileged uid on the node.
pct create "$CTID" "${TEMPLATE_FILE}" \
    --hostname "$CT_HOSTNAME" \
    --cores "$CT_CORES" \
    --memory "$CT_RAM_MB" \
    --swap "$CT_SWAP_MB" \
    --rootfs "${ROOT_STORAGE}:${CT_DISK_GB}" \
    --net0 "$NET" \
    --features nesting=1,keyctl=1 \
    --unprivileged 1 \
    --onboot 1 \
    --description "Voicebox TTS / voice studio. Web UI + MCP on :17493. Managed by deploy-voicebox-lxc.sh" \
    --start 1

ok "LXC ${CTID} created and started"

info "Waiting for network in the container..."
for i in $(seq 1 30); do
    if pct exec "$CTID" -- getent hosts deb.debian.org >/dev/null 2>&1; then break; fi
    sleep 2
    (( i == 30 )) && die "container never got DNS/network"
done
ok "container has network"

# ─── Install Docker ───────────────────────────────────────────────────────────
info "Installing Docker in the container (this takes a couple of minutes)..."
pct exec "$CTID" -- bash -c '
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg >/dev/null
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null
systemctl enable --now docker
'
ok "Docker $(pct exec "$CTID" -- docker --version | awk '{print $3}' | tr -d ,) installed"

# ─── Write the stack ──────────────────────────────────────────────────────────
info "Writing the Voicebox stack..."
pct exec "$CTID" -- mkdir -p /opt/voicebox/output

# Build both files on the Proxmox host, then push them in. Writing them via
# `pct exec -- bash -c "cat > ... <<EOF"` means every quote inside the compose
# file has to survive two levels of shell quoting, which makes anything but the
# most trivial healthcheck impossible to express. pct push has no such problem.
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

cat > "$STAGE_DIR/.env" <<EOF
VOICEBOX_TAG=${IMAGE_TAG}
VOICEBOX_MEM_LIMIT=${CONTAINER_MEM_MB}m
VOICEBOX_CPUS=$(awk "BEGIN{printf \"%.1f\", ${CT_CORES} - 1}")
VOICEBOX_BIND=0.0.0.0
LOG_LEVEL=info
# The published image listens on 8000 despite the docs and Dockerfile saying
# 17493 (verified against the GHCR registry API 2026-08-01; :latest and :dev
# are the same 2026-02-03 build). Host-side stays 17493. If upstream ever
# republishes an image matching its Dockerfile, change this to 17493.
VOICEBOX_INTERNAL_PORT=8000
EOF

cat > "$STAGE_DIR/docker-compose.yml" <<'COMPOSE'
services:
  voicebox:
    image: ghcr.io/jamiepine/voicebox:${VOICEBOX_TAG:-latest}
    container_name: voicebox
    restart: unless-stopped
    ports:
      - "${VOICEBOX_BIND:-0.0.0.0}:17493:${VOICEBOX_INTERNAL_PORT:-8000}"
    environment:
      LOG_LEVEL: "${LOG_LEVEL:-info}"
      # The published image runs as root, so $HOME is /root and the documented
      # /home/voicebox/.cache/huggingface is never written to. Pin the cache
      # explicitly or several GB of models re-download on every recreate.
      HF_HOME: /cache/huggingface
      VOICEBOX_MODELS_DIR: /cache/huggingface
      NUMBA_CACHE_DIR: /tmp/numba_cache
    volumes:
      - ./output:/app/data/generations
      - voicebox-data:/app/data
      - huggingface-cache:/cache/huggingface
    mem_limit: ${VOICEBOX_MEM_LIMIT:-10g}
    memswap_limit: ${VOICEBOX_MEM_LIMIT:-10g}
    mem_reservation: 2g
    cpus: ${VOICEBOX_CPUS:-3.0}
    healthcheck:
      # curl is not guaranteed to exist inside the image. If it is missing the
      # check would exit 127, the container would be marked unhealthy, and a
      # perfectly working deployment would look like a failure. Try the three
      # tools any Python ML image is likely to have before giving up.
      test:
        - CMD-SHELL
        - >-
          P=${VOICEBOX_INTERNAL_PORT:-8000};
          curl -fsS http://127.0.0.1:$$P/health >/dev/null 2>&1
          || wget -qO- http://127.0.0.1:$$P/health >/dev/null 2>&1
          || python3 -c "import sys,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+sys.argv[1]+'/health',timeout=5)" $$P
          || exit 1
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 600s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    stop_grace_period: 30s

volumes:
  voicebox-data:
  huggingface-cache:
COMPOSE

pct push "$CTID" "$STAGE_DIR/.env"               /opt/voicebox/.env               --perms 0640
pct push "$CTID" "$STAGE_DIR/docker-compose.yml" /opt/voicebox/docker-compose.yml --perms 0644
ok "stack written to /opt/voicebox on the LXC"

pct exec "$CTID" -- docker compose -f /opt/voicebox/docker-compose.yml config >/dev/null \
    || die "generated compose file failed validation"
ok "compose file validated inside the container"

# ─── Pull and start ───────────────────────────────────────────────────────────
info "Pulling ghcr.io/jamiepine/voicebox:${IMAGE_TAG} (~4.4 GB compressed)..."
pct exec "$CTID" -- bash -c 'cd /opt/voicebox && docker compose pull'

info "Starting Voicebox..."
pct exec "$CTID" -- bash -c 'cd /opt/voicebox && docker compose up -d'

# ─── Verify ───────────────────────────────────────────────────────────────────
CT_ADDR=$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || true)

info "Waiting for Voicebox to answer on /health (first boot downloads models,"
info "so allow up to 20 minutes on a cold HuggingFace cache)..."

# The authoritative signal is the app answering a real request from inside the
# LXC, where we installed curl ourselves. Docker's own health status is only
# advisory here: if the image happens to ship without curl/wget/python3 the
# container can read "unhealthy" while the service is perfectly fine.
healthy=0
for i in $(seq 1 120); do
    if pct exec "$CTID" -- curl -fsS --max-time 5 http://127.0.0.1:17493/health >/dev/null 2>&1; then
        healthy=1
        ok "Voicebox responded on /health"
        break
    fi

    # If the container is no longer running, waiting is pointless.
    state=$(pct exec "$CTID" -- docker inspect -f '{{.State.Status}}' voicebox 2>/dev/null || echo missing)
    if [[ "$state" == "exited" || "$state" == "dead" ]]; then
        echo
        pct exec "$CTID" -- docker logs --tail 60 voicebox 2>&1 || true
        die "the voicebox container stopped (state=${state}) — see the logs above"
    fi

    sleep 10
    if (( i % 6 == 0 )); then
        st=$(pct exec "$CTID" -- docker inspect -f '{{.State.Health.Status}}' voicebox 2>/dev/null || echo unknown)
        info "  still waiting (docker health=${st}, $(( i / 6 )) min elapsed)"
    fi
done

if (( healthy == 0 )); then
    echo
    pct exec "$CTID" -- docker logs --tail 60 voicebox 2>&1 || true
    echo
    warn "Voicebox did not answer /health within 20 minutes."
    warn "The container is still running and may simply be downloading a large model."
    warn "Watch it with:  pct exec ${CTID} -- docker logs -f voicebox"
    die "gave up waiting for a healthy response"
fi

# Report docker's view too, purely informational.
dh=$(pct exec "$CTID" -- docker inspect -f '{{.State.Health.Status}}' voicebox 2>/dev/null || echo unknown)
if [[ "$dh" != "healthy" ]]; then
    warn "Docker reports health=${dh} even though the API responded."
    warn "That usually just means the image has no curl/wget/python3 for its own check."
fi

echo
echo "  ── Voicebox is up ─────────────────────────────────────────"
printf '    LXC              %s (%s) on %s\n' "$CTID" "$CT_HOSTNAME" "$(hostname)"
printf '    Address          %s\n' "${CT_ADDR:-unknown}"
printf '    Web UI           http://%s:17493\n' "${CT_ADDR:-<ip>}"
printf '    REST API         http://%s:17493\n' "${CT_ADDR:-<ip>}"
printf '    MCP (agents)     http://%s:17493/mcp\n' "${CT_ADDR:-<ip>}"
printf '    LXC RAM          %s MB\n' "$CT_RAM_MB"
printf '    Container cap    %s MB (hard, swap disabled)\n' "$CONTAINER_MEM_MB"
printf '    Stack            /opt/voicebox on the LXC\n'
echo   "  ───────────────────────────────────────────────────────────"
echo
warn "The API has NO authentication. Keep it on the LAN. See README for the"
warn "firewall rule and reverse-proxy options."
echo
info "Live memory:"
pct exec "$CTID" -- docker stats --no-stream --format '    {{.Name}}: {{.MemUsage}} ({{.MemPerc}})' voicebox || true
