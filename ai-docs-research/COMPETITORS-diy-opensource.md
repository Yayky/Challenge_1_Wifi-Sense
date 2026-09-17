# DIY / Open-Source Landscape — Competitive Positioning vs. WiFi Sense

Research date: 2026-09-09

Scope: comparing existing **DIY / open-source** projects and platforms — not
commercial products (see `COMPETITORS-smarthome.md` and
`COMPETITORS-security-eldercare.md` for those) — against the "WiFi Sense"
student project.

## Project being compared against: WiFi Sense
HLK-LD2450 24GHz mmWave radar + AM312 PIR on an ESP32 running ESPHome firmware,
feeding a **self-written Python FastAPI server** that broadcasts person
positions over WebSocket to a **self-written HTML canvas dashboard** showing
live blips on a top-down room map. Deliberately NOT using Home Assistant.
Plus a planned WiFi-CSI research layer using two ESP32s, with the radar used
as ground truth for the CSI-based detections.

## Comparison table

| Project | What it does | Needs HA? | Live position map? | Maintained | Closeness to WiFi Sense |
|---|---|---|---|---|---|
| ESPHome `ld2450` (official) | Firmware driver: exposes per-target x/y, angle, speed, distance, zones as entities | No (but assumed) | No — data only | Yes, in ESPHome core | **This is a component of WiFi Sense**, not a rival |
| [TillFleisch/ESPHome-HLK-LD2450](https://github.com/TillFleisch/ESPHome-HLK-LD2450) | External ESPHome component, adds convex-polygon zones | No | No | ⭐166, pushed 2025-12 | Firmware layer only |
| [Chreece/LD2450-ESPHome](https://github.com/Chreece/LD2450-ESPHome) | Custom component + sample HA dashboard config | Yes | Via Plotly card | ⭐35, pushed 2023-11 (stale) | Dashboard is HA-bound |
| Plotly Graph Card (HACS) | Generic HA chart card; community uses it to scatter-plot LD2450 targets + zones | Yes | Yes-ish (scatter plot) | Active | The HA answer to "show me blips" |
| [joshuabarraza/mmwave-radar](https://github.com/joshuabarraza/mmwave-radar) | LD2450 → Pi → Python asyncio → WebSocket → HTML canvas radar with fading blip trails | **No** | **Yes** | ⭐0, MIT, pushed 2026-03 | **Nearly identical architecture** |
| [PeterkoCZ91/HLK-LD2450-security](https://github.com/PeterkoCZ91/HLK-LD2450-security) | ESP32+LD2450 intrusion detection, Kalman filtering, polygon zones, dark-mode web dashboard with live radar map | Optional | **Yes** | ⭐7, MIT, pushed 2026-07 | Same idea + security framing |
| [nick28s/IoTProject-ZonePresenceDetection-LD2450](https://github.com/nick28s/IoTProject-ZonePresenceDetection-LD2450) | Student IoT zone-presence project, LD2450 + web interface | No | Zones via web UI | ⭐14, GPL-3.0, pushed 2025-01 | Comparable student project |
| [csRon/HLK-LD2450](https://github.com/csRon/HLK-LD2450) | Python serial protocol implementation + `plot_targets.py` demo | No | Matplotlib plot | ⭐33, MIT, pushed 2024-07 | Reference for frame parsing |
| [ESPresense](https://github.com/ESPresense/ESPresense) | BLE room-level presence via ESP32 nodes → MQTT | No (MQTT) | Room-level, not x/y | ⭐1474, pushed 2026-09 | Different modality (device-based) |
| [room-assistant](https://github.com/mKeRix/room-assistant) | Room-level presence platform, multiple sensor types | No | Room-level | ⭐1347, pushed 2026-09 | Different granularity |
| esp-csi / ESP32-CSI-Tool / nexmon_csi / Wi-BFI / ESPARGOS | WiFi CSI capture toolkits — see `RESEARCH.md` for full detail | No | Mostly raw plots | Mixed | The CSI layer's toolchain |

## Findings by item

### 1. ESPHome `ld2450` + Home Assistant — the default path

The official ESPHome `ld2450` component exposes, per tracked target (up to 3):
x coordinate, y coordinate, distance, angle and speed, plus configurable zones
[[docs](https://esphome.io/components/sensor/ld2450/)]. So the *data* WiFi Sense
wants is available out of the box to anyone using ESPHome — WiFi Sense's own
firmware layer is exactly this component. This is not a competitor so much as a
dependency.

What Home Assistant does **not** give you out of the box is a live top-down
radar view. The community's answer is the **Plotly Graph Card** from HACS:
users scatter-plot the target x/y entities and draw configured zones as
semi-transparent rectangles. Apex Charts was tried first and rejected because it
only accepts time on the X axis
[[HA Community thread](https://community.home-assistant.io/t/hlk-ld2450-initial-experiments-to-connect-to-homeassistant/578878/174)].
Chreece's repo ships a copy-paste HA dashboard config that pulls all LD2450
targets into cards, relying on the HACS frontend add-ons auto-entities,
layout-card and Plotly Graph Card
[[repo](https://github.com/Chreece/LD2450-ESPHome)].

So: a live blip view **is** achievable in HA, but it is a generic charting card
bent into the role, assembled from three HACS dependencies — not a purpose-built
radar display.

### 2. Custom LD2450 visualisers on GitHub — the closest prior art

**[joshuabarraza/mmwave-radar](https://github.com/joshuabarraza/mmwave-radar)**
(MIT, pushed March 2026) is architecturally almost identical to WiFi Sense:
LD2450 over UART into a Raspberry Pi 4B, a Python asyncio service that decodes
frames, applies motion stabilisation and broadcasts JSON over a WebSocket, and a
browser page rendering a sweep animation with fading blip trails on an HTML
canvas. The author frames it as a "Call of Duty-style movement radar". It has 0
stars — obscure, but it exists and predates this project.

**[PeterkoCZ91/HLK-LD2450-security](https://github.com/PeterkoCZ91/HLK-LD2450-security)**
(MIT, ⭐7, pushed July 2026) is ESP32 + LD2450 with real-time 2D target tracking,
Kalman filtering, polygon detection zones and a dark-mode bilingual web dashboard
with a live radar map, plus optional Home Assistant integration. Its intrusion-
detection framing matches WiFi Sense's "is someone in my room" use case, and it
is *ahead* of WiFi Sense on tracking sophistication (Kalman filtering).

**[csRon/HLK-LD2450](https://github.com/csRon/HLK-LD2450)** (MIT, ⭐33) is a clean
Python implementation of the LD2450 serial protocol with a `plot_targets.py`
demo. Useful as a reference for frame parsing if the ESPHome route is ever
abandoned.

**[nick28s/IoTProject-ZonePresenceDetection-LD2450](https://github.com/nick28s/IoTProject-ZonePresenceDetection-LD2450)**
(GPL-3.0, ⭐14) is another student IoT project: LD2450 zone presence detection
with a web interface. Direct evidence that this is a well-trodden student
project shape.

### 3. HA floor-plan / presence visualisation

Beyond the Plotly approach, Home Assistant has a mature ecosystem of floor-plan
Lovelace cards for showing room state, and **Bermuda BLE Trilateration** for
device-based room location from ESPHome Bluetooth proxies. These solve
"which room is this *device* in", a different question from "where in this room
is this *person*". They are complementary rather than competing.

### 4. Open-source WiFi CSI projects

Covered in depth in `RESEARCH.md`. Summary for positioning: espressif/esp-csi
is the vendor-maintained capture toolchain (and is what WiFi Sense will use),
StevenMHernandez/ESP32-CSI-Tool is the legacy academic standard, nexmon_csi
gives far richer CSI on a Raspberry Pi at high setup cost, and ESPARGOS is the
research high-end (phase-coherent ESP32 antenna array). None of these ship a
person-tracking dashboard — they produce raw CSI for you to analyse. The gap
between "captured CSI" and "a person on a map" is exactly the hard part, and it
is unsolved in the hobbyist open-source space.

### 5. Room-occupancy platforms

**ESPresense** (⭐1474, AGPL-3.0, actively maintained) and **room-assistant**
(⭐1347, MIT, actively maintained) are the mature open-source presence platforms.
Both are *device-based*: they locate phones/watches/beacons by BLE signal
strength, at room-level granularity. They answer "who is home and roughly where",
not "there is an unidentified person standing at (1.2, 2.8) in this room".
Different modality, complementary, not competing.

## Is WiFi Sense novel?

**No — and it doesn't need to be.**

Concretely, the answer to each part:

- **LD2450 + ESP32 + ESPHome**: the standard approach, and the basis of a
  commercial product (Everything Presence Lite).
- **Live top-down blip dashboard fed by WebSocket from a Python service**:
  already built by joshuabarraza/mmwave-radar, and by PeterkoCZ91's security
  project — the latter with Kalman filtering WiFi Sense does not have.
- **A student building LD2450 zone presence with a web UI**: nick28s did it as
  an IoT course project.
- **Radar as ground truth for evaluating WiFi CSI sensing**: this is standard
  methodology in the academic WiFi-sensing literature, not an original research
  design. Papers routinely use a better sensor to label data for a worse one.

What is *genuinely* different is narrow and worth stating precisely rather than
overselling:

1. **No Home Assistant dependency.** The overwhelming majority of LD2450 work
   assumes HA. WiFi Sense consumes the ESPHome native API directly from its own
   Python server, so the whole stack is a standalone application. That is a real
   architectural difference, though joshuabarraza's project shares it.
2. **Both layers in one system.** No existing project combines commodity radar
   tracking *and* a WiFi-CSI experiment in a single codebase with a shared
   dashboard and a shared coordinate frame. The individual halves exist; the
   combination is uncommon.
3. **It is built rather than assembled.** Everything Presence Lite costs €33 and
   would give better tracking out of the box. Choosing to build the equivalent —
   and understanding every layer from UART framing to canvas rendering — is the
   point of the exercise.

For a first-semester learning project, "not novel" is the correct and expected
outcome. The value being demonstrated is not invention but engineering process:
researching what exists, choosing an approach with reasons, building it,
testing it, and being able to explain and defend every decision. A project that
honestly maps its own prior art is doing better analysis than one that claims
originality it does not have.

## Sources

- ESPHome LD2450 component docs — https://esphome.io/components/sensor/ld2450/
- HA Community, "HLK-LD2450 Initial experiments" (Plotly card approach) — https://community.home-assistant.io/t/hlk-ld2450-initial-experiments-to-connect-to-homeassistant/578878/174
- TillFleisch/ESPHome-HLK-LD2450 — https://github.com/TillFleisch/ESPHome-HLK-LD2450
- Chreece/LD2450-ESPHome — https://github.com/Chreece/LD2450-ESPHome
- joshuabarraza/mmwave-radar — https://github.com/joshuabarraza/mmwave-radar
- PeterkoCZ91/HLK-LD2450-security — https://github.com/PeterkoCZ91/HLK-LD2450-security
- csRon/HLK-LD2450 — https://github.com/csRon/HLK-LD2450
- nick28s/IoTProject-ZonePresenceDetection-LD2450 — https://github.com/nick28s/IoTProject-ZonePresenceDetection-LD2450
- ESPresense — https://github.com/ESPresense/ESPresense
- room-assistant — https://github.com/mKeRix/room-assistant
- Repo metadata (stars, licence, last push) retrieved via GitHub API, 2026-09-09
- WiFi CSI toolchain detail — see `RESEARCH.md` in this folder
