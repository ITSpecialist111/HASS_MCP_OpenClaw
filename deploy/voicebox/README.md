# Voicebox on Proxmox

Deploys [Voicebox](https://docs.voicebox.sh) — a local, open-source AI voice
studio (TTS, voice cloning, transcription) — as a Docker stack inside a
dedicated unprivileged LXC on Proxmox VE, with a hard RAM ceiling so it cannot
starve the node.

Voicebox also exposes an MCP endpoint, so an agent (Hermes, Claude, etc.) can
drive it directly once it is running.

---

## Hardware audit — 2026-08-01 (measured, not assumed)

**Verdict: neither available machine can run Voicebox, and the Proxmox host
cannot be upgraded to fix it.** Details below. This section supersedes any
"just run it" reading of the rest of this README.

### There is one Proxmox host, not two

`192.168.68.4` and `192.168.68.105` are two bridges on the **same physical
machine** — `vmbr0 = 192.168.68.4/22`, `vmbr1 = 192.168.68.105/32`. Same node
name, same CPU, same PVE build, same guests.

### The Proxmox host is already oversubscribed

| Guest | Configured | Actually using |
|---|---|---|
| `FW-OpnSense` (VM 102) | **13000 MB**, ballooning disabled | 11406 MB |
| `hermesagent` (LXC 103) | 4096 MB | 794 MB |
| `pihole` (LXC 101) | 512 MB | 142 MB |
| **Committed to running guests** | **17608 MB** | |
| **Physical RAM** | **15897 MB** | |
| **`available`** | **2175 MB** | |
| **Swap in use** | **2183 MB** | |

The host has promised **1711 MB more RAM than it physically has**, while running
the firewall. CPU is fine (load 0.29 on 4 cores) — memory is the whole problem.

Applying this project's own budget rule:

```
15897 - 17608 (committed) - 2048 (host reserve) = -3758 MB available
```

`deploy-voicebox-lxc.sh` will **refuse to deploy** here, which is correct.

### The RAM cannot be expanded

```
Maximum Capacity: 16 GB
Number Of Devices: 2
  DIMM1: 8 GB DDR3 1600 MT/s
  DIMM2: 8 GB DDR3 1600 MT/s
```

Both slots populated, board maxes at 16 GB. **There is no upgrade path.**
(CPU is an i5-4590T — a 35 W T-series part, so this is a small-form-factor box.)

### Even aggressive reclaim does not fit

Voicebox's floor is 8192 MB. Right-sizing every guest to something defensible:

| Scenario | Committed | Available for Voicebox |
|---|---|---|
| Today | 17608 MB | **-3758 MB** |
| `hermesagent` → 1536 MB | 15048 MB | -1199 MB |
| … plus OPNsense → 6144 MB | 8192 MB | 5657 MB |
| … plus OPNsense → 4096 MB | 6144 MB | **7705 MB** — still short |

Cutting the firewall from 13 GB to 4 GB is a significant change to critical
infrastructure and it *still* lands below the 8 GB minimum. Voicebox does not
fit on this hardware under any reasonable configuration.

### Home Assistant host — also no

Separate bare-metal box (not a Proxmox guest): 15.9 GB total, **6.8 GB
available**, **3.1 GB of 4 GB swap already in use**, load **8.60 on 4 cores**,
19 add-ons totalling 7.76 GB with Frigate alone at 4673 MB / 53% CPU.

### What would actually work

1. **A separate machine with 32 GB RAM** — a used SFF/micro (Optiplex or
   ThinkCentre M720q class) or an N100/N150 mini PC. This is the only route that
   runs Voicebox properly *and* relieves the existing pressure on the Proxmox
   box. Everything in this repo then applies unchanged.
2. **Run it on-demand on a desktop** rather than always-on, if occasional voice
   generation is all that is wanted.
3. **Use the Piper add-on already running on Home Assistant** (557 MB) if the
   goal is simply for HA to speak. Loses voice cloning, costs nothing.

### Independent of Voicebox: worth fixing anyway

The Proxmox host is running **OPNsense**, and it is 2.1 GB into swap with 2.1 GB
available and 1.7 GB of overcommit. If anything spikes, the OOM killer is a
threat to the firewall and therefore to the whole network. `hermesagent` is
committed 4096 MB but uses 794 MB, and an LXC can be resized live:

```bash
pct set 103 -memory 1536
```

That single change removes 2560 MB of overcommit with no reboot and no downtime.
**Not applied — flagging it rather than changing your infrastructure uninvited.**

---

## TL;DR (once suitable hardware exists)

```bash
# on the Proxmox host, as root
./deploy-voicebox-lxc.sh --check     # preview the RAM maths, changes nothing
./deploy-voicebox-lxc.sh             # deploy
```

Then on Home Assistant: edit the IP in `voicebox.yaml.disabled`, drop it into
`/homeassistant/packages/voicebox.yaml`, and reload YAML.

---

## Why not a Home Assistant add-on?

This was the first thing checked, because it would have been the tidier answer.
It is not viable. Re-measured on the HA host (192.168.68.57), 2026-08-01:

| | |
|---|---|
| RAM | 15901 MB total, **6482 MB available**, 142 MB free |
| Swap | 4096 MB total, **3279 MB in use — only 817 MB left** |
| `vm.swappiness` | **1** — the kernel only swaps here to avoid OOM |
| Load average | 5.64 / 6.10 / 6.64 on a 4-core i5-6500 |
| PSI CPU stall | **`some avg10=52.07%`** — something is waiting on CPU half the time |
| Running add-ons | 19, totalling **8542 MB** (+ ~1 GB HA Core) |
| Largest consumer | Frigate — **5557 MB @ 56.1% CPU** |

### The arithmetic is decisive

```
Voicebox minimum          8192 MB   (vendor's own floor for a single engine)
Available without swap    6482 MB
                        ---------
Shortfall                 1710 MB
Free swap                  817 MB
                        ---------
Nowhere to put            ~893 MB   -> OOM killer fires
```

The shortfall is *larger than the remaining swap*, so the allocation cannot be
satisfied by any means. The OOM killer selects on RSS, so the victim would be
Frigate (5557 MB) or HA Core.

`swappiness=1` matters here: this kernel is configured to swap only as a last
resort, and it has still been forced to push 3.2 GB out. That is real, sustained
memory pressure, not lazy paging.

### It cannot be freed up either

The obvious idea is to reclaim RAM from the existing speech add-ons, since
Voicebox does both TTS (`/generate`) and STT (`/transcribe`). It does not work:

- **Whisper (812 MB)** is the `stt_engine` in **3 of 6** voice pipelines
  (`Local Assistant`, `OpenAI`, `GLaDOS`).
- **Piper (534 MB)** is the `tts_engine` in **2 of 6** (`Local Assistant`, `GLaDOS`).
- Both are wired in over **Wyoming**. Voicebox speaks plain REST, so it cannot
  drop into a pipeline's `stt_engine`/`tts_engine` slot as a replacement.
- Even if both were removed anyway: `6482 + 1346 = 7828 MB` — **still 364 MB
  short** of the floor, having broken the local voice pipelines to get there.

The only add-on large enough to make room is Frigate, which is the NVR.

### An add-on has no RAM ceiling

There is a further problem specific to the add-on format. The Supervisor add-on
schema has **no memory-limit option** — an add-on gets no cgroup cap and simply
consumes until the OOM killer intervenes. The `mem_limit` / `memswap_limit`
safety ceiling used in `docker-compose.yml` here **cannot be expressed as an
add-on at all**. So the add-on route is not just tighter on RAM, it removes the
one mechanism that would contain the damage.

An add-on is a Docker container on the same host. The wrapper changes packaging,
not physics.

The HA host is also **bare metal, not a Proxmox guest** (`virtualization: ""`),
so "put it in Proxmox" and "put it in HA" are genuinely different machines.

**Decision: dedicated LXC on Proxmox. Home Assistant gets a REST/MCP client
only, which costs it nothing.**

> **Update after the full hardware audit:** the Proxmox host cannot host it
> either — see the audit section above. This package is correct and ready, but
> it needs a machine with more RAM than either existing box has.

---

## The RAM safety model

The explicit requirement was *don't run the Proxmox server out of RAM*. That is
handled with three nested hard ceilings rather than hope:

```
Proxmox node
  └─ LXC              memory = 12288 MB      (hard cgroup limit)
       └─ container   mem_limit = 10240 MB   (hard cgroup limit, swap disabled)
```

The container hits its cap before the LXC hits its cap, and the LXC hits its cap
before the node notices anything. Concretely:

1. **The node's budget is computed from *committed* RAM, not used RAM.** The
   script sums the configured `memory` of every *running* VM and LXC via
   `qm config` / `pct config`. An idle guest showing 200 MB of touched RAM can
   balloon to its full allocation at any moment; planning against current usage
   would be planning against a number that is free to change.

2. **`HOST_RESERVE_MB` (2048) is never handed out.** PVE itself, ZFS ARC and
   the kernel need room.

3. **If the remainder is below `CT_RAM_FLOOR_MB` (10240), the script refuses to
   deploy** and prints the shortfall. It does not "try anyway".

4. **If the remainder is between the floor and the target, the LXC is trimmed**
   to what actually fits rather than failing.

5. **The container's swap is disabled** (`memswap_limit == mem_limit`). Without
   that, an over-budget model load spills silently into swap and thrashes the
   node — exactly the pathology already visible on the HA box — instead of
   failing fast and loudly.

You can see all of this before touching anything:

```bash
./deploy-voicebox-lxc.sh --check
```

`--check` deliberately does not require root, so previewing the arithmetic is
zero-risk.

### Tunables

Override via environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `CT_RAM_WANTED_MB` | 12288 | Target LXC memory |
| `CT_RAM_FLOOR_MB` | 10240 | Refuse to deploy below this |
| `HOST_RESERVE_MB` | 2048 | Always left to the PVE host |
| `CONTAINER_HEADROOM_MB` | 2048 | LXC RAM minus container cap |
| `CT_CORES` | 4 | LXC vCPUs (container gets cores-1) |
| `CT_DISK_GB` | 48 | Rootfs size |
| `CT_IP` | `dhcp` | Or `192.168.68.60/24` (then set `CT_GW`) |
| `VOICEBOX_TAG` | `latest` | Or `latest-cuda` |
| `TEMPLATE_PATTERN` | `debian-13-standard` | LXC template |

Example — smaller footprint on a busier node:

```bash
CT_RAM_WANTED_MB=10240 CT_RAM_FLOOR_MB=8192 ./deploy-voicebox-lxc.sh
```

---

## Storage impact

| Item | Size |
|---|---|
| `ghcr.io/jamiepine/voicebox:latest` | 4.38 GB compressed, **~11 GB on disk** |
| HuggingFace model cache | ~5–10 GB depending on engines used |
| Generated audio | grows over time, in `/opt/voicebox/output` |
| **LXC rootfs default** | **48 GB** |

The CUDA image (`latest-cuda`, 4.56 GB compressed) is larger still. If the node
is tight on disk, raise or lower `CT_DISK_GB` accordingly.

> The upstream docs say prebuilt images are "coming soon". **That is stale** —
> `latest`, `dev`, `latest-cuda` and `dev-cuda` all exist on GHCR today
> (verified against the registry API). This deploys the prebuilt image rather
> than building from source, which saves a long build inside the LXC.

---

## Security

**Voicebox has no built-in authentication.** Not on the web UI, not on the REST
API, not on `/mcp`. Anyone who can reach port 17493 can generate speech, read
your voice profiles, and clone voices.

This deployment therefore:

- Keeps it on the LAN only. No port forwarding, no Cloudflare tunnel, no public
  DNS.
- Runs the LXC **unprivileged**, so a container root break-out lands on an
  unprivileged uid on the node.
- Binds `0.0.0.0` *inside the LXC* — necessary, because HA and any MCP agent
  must reach it — and treats the LXC boundary as the control point.

If you want it locked down further, add a Proxmox firewall rule on the LXC
allowing 17493 only from the hosts that need it:

```bash
# on the PVE host
cat >> /etc/pve/firewall/<CTID>.fw <<'EOF'
[OPTIONS]
enable: 1

[RULES]
IN ACCEPT -source 192.168.68.57 -p tcp -dport 17493 -log nolog  # Home Assistant
IN DROP   -p tcp -dport 17493 -log nolog
EOF
```

For a hostname plus auth, put it behind your existing reverse proxy with basic
auth and point HA at the proxy instead. Voicebox will not do it for you.

---

## GPU

The script detects an NVIDIA GPU on the node and tells you, but deploys the CPU
image by default — passing a GPU into an unprivileged LXC needs device
passthrough decisions that should be made deliberately, not silently by a
deploy script.

To use CUDA: pass the `/dev/nvidia*` devices into the LXC, install the NVIDIA
container toolkit inside it, then re-run with `VOICEBOX_TAG=latest-cuda`. See
<https://docs.voicebox.sh/overview/gpu-acceleration>.

---

## Home Assistant integration

`voicebox.yaml.disabled` is an HA package. It ships disabled on purpose: if the
REST sensors load before Voicebox exists they fail every 60 seconds and fill the
log.

To enable:

1. Replace `192.168.68.60` (3 occurrences) with the address the deploy script
   printed.
2. Copy to `/homeassistant/packages/voicebox.yaml`.
3. Developer Tools → YAML → Reload all YAML configuration.

This instance already has `packages: !include_dir_named packages` configured.

### What you get

| Entity | Purpose |
|---|---|
| `binary_sensor.voicebox_online` | Reachability |
| `binary_sensor.voicebox_model_loaded` | Whether a model is currently held in RAM |
| `binary_sensor.voicebox_healthy` | Template mirror, matches the house style |
| `sensor.voicebox_status` | `/health` status + attributes |
| `sensor.voicebox_vram_used` | VRAM in MB (GPU installs) |
| `sensor.voicebox_profiles` | Number of voice profiles |
| `rest_command.voicebox_generate` | Generate speech |
| `rest_command.voicebox_unload_model` | Free the model from RAM |
| `rest_command.voicebox_load_model` | Preload the model |

Two automations ship with it:

- **`Voicebox: unload model when idle`** — releases the TTS model after 60
  minutes loaded. Voicebox has no idle-unload of its own, so left alone it holds
  several GB indefinitely after a single request. This is what keeps the LXC
  sitting near its floor instead of near its cap. The next request reloads
  automatically: slower first response, much lower steady-state memory.
- **`Voicebox: alert when offline`** — notifies after 15 minutes unreachable,
  respecting the existing `input_boolean.network_alerts_enabled` mute used by
  the other infrastructure alerts.

### Generating speech

```yaml
action: rest_command.voicebox_generate
data:
  profile_id: "<id from sensor.voicebox_profiles attributes>"
  text: "The washing machine has finished."
  language: en          # optional, defaults to en
```

The response contains an `id`; the audio is then at
`http://<lxc-ip>:17493/audio/<id>`.

---

## API reference

Endpoints below are from the project's own `docs/openapi.json`, not the prose
docs. **Note there is no `/api` prefix.**

| Method | Path | |
|---|---|---|
| GET | `/health` | status, model_loaded, gpu_available, vram_used_mb |
| GET / POST | `/profiles` | list (returns a JSON **array**) / create |
| GET/PUT/DELETE | `/profiles/{id}` | manage a profile |
| POST/GET | `/profiles/{id}/samples` | voice-cloning samples |
| POST | `/generate` | requires `profile_id`, `text`; optional `language`, `seed`, `model_size` |
| GET | `/audio/{generation_id}` | fetch generated audio |
| GET | `/history`, `/history/stats` | past generations |
| POST | `/transcribe` | speech to text |
| POST | `/models/load`, `/models/unload` | **RAM control** |
| GET | `/models/status`, `/models/progress/{name}` | model state |

---

## MCP (agent access)

Voicebox speaks Streamable HTTP MCP at `/mcp`:

```
http://<lxc-ip>:17493/mcp
```

Tools: `voicebox.speak`, `voicebox.transcribe`, `voicebox.list_captures`,
`voicebox.list_profiles`. Send an `X-Voicebox-Client-Id` header to bind a
particular voice to a particular agent.

Because there is no auth on `/mcp` either, only register it with agents on the
trusted LAN.

---

## Operating it

```bash
CTID=<id>                                        # printed by the deploy script

pct status  $CTID
pct exec    $CTID -- docker ps
pct exec    $CTID -- docker logs -f voicebox
pct exec    $CTID -- docker stats --no-stream voicebox

# update
pct exec $CTID -- bash -c 'cd /opt/voicebox && docker compose pull && docker compose up -d'

# free RAM right now without stopping the service
pct exec $CTID -- curl -fsS -X POST http://127.0.0.1:17493/models/unload
```

### Rollback

Fully reversible — everything lives in one container:

```bash
pct stop $CTID && pct destroy $CTID
```

That removes the LXC, the Docker volumes, the model cache and the generated
audio. Nothing was changed on the Proxmox host or on Home Assistant outside of
this LXC. On the HA side, delete `packages/voicebox.yaml` and reload YAML.

---

## Files

| File | |
|---|---|
| `deploy-voicebox-lxc.sh` | The deployment. Run on the PVE host as root. |
| `docker-compose.yml` | Standalone copy of the stack (the script embeds its own copy — **keep them in sync**). |
| `test-ram-budget.sh` | Mock-based test suite for the RAM logic. 12 assertions, no Proxmox needed. |
| `voicebox.yaml.disabled` | Home Assistant package. |

### Verification performed

- `docker compose config` → exit 0; `mem_limit` resolves to 10737418240 bytes.
- `bash -n` on both scripts → clean.
- `test-ram-budget.sh` → **12 passed, 0 failed**, covering normal allocation,
  refusal when short, trimming to fit, an empty node, and a regression test for
  a guest whose config cannot be read.
- HA package: YAML valid; all 8 Jinja expressions compile; the `/generate`
  payload round-trips correctly including quotes, backslashes, newlines and
  Unicode.

**Not yet verified against real hardware** — the script has never run against a
live node, because the audit above showed the only available node cannot host
Voicebox. Template download, `pct create`, the Docker install and the first
image pull remain untested in reality. Run `--check` first on whatever machine
eventually hosts it.
