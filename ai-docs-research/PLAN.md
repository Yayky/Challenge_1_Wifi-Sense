# WiFi Sense — Project Plan

Agreed 2026-09-02. Solo project by Josip for Fontys ICT Challenge 1 (Smart Home) + personal use.
Companion docs: `RESEARCH.md` (WiFi CSI), `RESEARCH-SENSORS.md` (radar & other sensors).

## Goal

Detect whether anyone is in my ~20 m² studio room, show them as live blips on a
room "radar" dashboard, and (later) check it remotely from my phone with alerts
while I'm away. Two sensing layers:

- **Radar layer (the product)**: HLK-LD2450 (x/y tracking of up to 3 people)
  on an ESP32 node; software presence-hold for still people (HLK-LD2412 radar
  as a later hardware upgrade).
- **CSI layer (the research)**: two ESP32s measuring WiFi channel distortion
  caused by human movement — demo level during the block, ground-truth
  experiment later.

## Decisions (settled)

| Decision | Choice |
|---|---|
| Scope | One room, one radar node |
| Firmware | ESPHome on nodes; server subscribes via `aioesphomeapi` (no Home Assistant) |
| Server | Existing FastAPI app; build on PC first, migrate to Raspberry Pi for 24/7 later |
| CSI backhaul | RX board → USB serial → server |
| Radar-node backhaul | WiFi UDP/API if apartment AP allows client↔client traffic (test pending); else USB cable |
| Mobile | PWA (dashboard installable on phone) + ntfy for notifications; reachable over Tailscale |
| Arm/disarm | Manual toggle v1 → automatic phone-presence later |
| Vitals sensor (MR60BHA2) | Not bought; documented in RESEARCH-SENSORS.md for later |
| Working mode | I build it; Claude writes specs/reviews, points at sources, completes only on request |
| Existing repo code | Inherited foundation — refactored piece by piece as I learn it |

## Block plan (4 weeks, Fontys phases → evidence)

### Week 1 — Analysis + Design
- Requirements doc: use case, functional requirements, quality criteria
  (detection latency, static-person hold time, false-positive rate, remote access).
- Architecture diagram: sensors → ESP32 node → server → dashboard/phone.
- Choice justification drawing on the research docs (why LD2450, why
  ESPHome, why not camera/PIR-only/UWB). **Evidence pieces 1–2.**

### Weeks 2–3 — Realisation
- Flash ESPHome on radar node; wire LD2450 (UART 256000) + AM312 PIR (GPIO).
- Server: `aioesphomeapi` ingest mode alongside the simulator; sensor-frame →
  room-coordinate transform; software presence-hold (target lost away from the
  door → freeze blip as "sitting still" until door-zone motion).
- Dashboard shows real blips.
- Stretch: CSI demo — esp-csi `csi_send`/`csi_recv` pair, serial bridge, live
  amplitude graph.

### Weeks 3–4 — Validation
- Test plan: scripted walks along known paths (does the blip track?), sit-still
  test (held ≥ N minutes?), empty-room soak (false positives overnight?),
  fan/curtain interference check.
- Classmates/teacher live test. Record results, tune (range gates, sensitivity),
  retest. **Evidence piece 3.**

## Personal roadmap (after the block, no deadline)

1. PWA install + ntfy alerts + Tailscale remote view; manual arm toggle.
2. Migrate server to Raspberry Pi (systemd service) for 24/7.
3. Auto arm/disarm from phone-on-network presence.
4. CSI research: radar positions as ground-truth labels, evaluate CSI
   presence/motion detection against them.
5. Maybe: MR60BHA2 sleep vitals, LD2460 when ESPHome supports it, Flutter app.

## Hardware

**Owned**: 5× ESP32 (3 own NodeMCU + 2 from school stockroom — exact variants
TBC, check silkscreen), Arduino UNO R4 WiFi (unused — its radio is a locked
coprocessor), Raspberry Pi Zero, breadboard, jumper wires (F-F, M-F).

Pi Zero note: fine as the future 24/7 server host for the radar layer (light
load), but it is the one Pi model that can never run the Nexmon CSI experiment,
and the original (non-W) has no WiFi at all — check which it is.

**To order** (Tinytronics/AliExpress):

| Item | Qty | ~Price | Role |
|---|---|---|---|
| HLK-LD2450 | 2 | €12 ea | position blips (3 targets, 10 Hz); 2nd unit = DOA spare, later coverage experiment |
| AM312 PIR | 2 | €2 ea | instant-motion cross-check (optional) |

**Ordered but not counted on for the block** (shipping may exceed 4 weeks):
HLK-LD2412 — static-presence hold. Until it arrives the server fakes it with a
software hold (target vanishing away from the door keeps its blip as "sitting
still"); if it lands early it becomes a stretch goal, wired to GPIO 32/33.
Still fully deferred: MR60BHA2 (sleep vitals).

**Still worth grabbing from school**: USB-UART adapter (3.3 V), micro-USB/USB-C
data cables incl. one long (2–3 m), 2 decent 5 V chargers (PSU ripple mimics
breathing in the data).

## Open facts

- [x] ESP32 count: 5 (variants TBC — if any school board is a C3/S3/C6, it
      becomes the CSI RX; classic-only means CSI runs on the worst-ranked RX
      or a C6 gets ordered later)
- [x] Raspberry Pi: Zero (W or non-W TBC)
- [ ] Room photos → sensor mounting positions (radar: 1.4–2 m high, corner,
      boresight away from shared walls)
- [ ] Client-isolation test: PC + phone on apartment WiFi, `ping <phone-ip>` —
      replies = node-over-WiFi OK, silence = USB-cable fallback
