# WiFi Sense — Realisation

---

## 1. What has been realised

| Artifact                | File                          | State                                                   |
| ----------------------- | ----------------------------- | ------------------------------------------------------- |
| Sensor node firmware    | `firmware/sensor-node.yaml` | flashed and running on the ESP32                        |
| Radar client            | `radar.py`                  | written,**not yet running — see §5**            |
| Server + presence logic | `server.py`                 | simulator path working; radar path**in progress** |
| Movement simulator      | `simulator.py`              | working, one- and two-person modes                      |
| Dashboard               | `dashboard.html`            | working against the simulator                           |
| Dependency list         | `requirements.txt`          | current                                                 |
| Secrets template        | `firmware/secrets.yaml`     | git-ignored, local only                                 |

Demo evidence: `docs/first_real_life_demotest.mp4` — first run with the real LD2450 attached (23 September 2026).

> **TODO** — that video is not committed and not described anywhere. Add a caption here: what is on screen, what worked, what did not.

### 1.1 Hardware built

| Component       | Connection                               | Note                                    |
| --------------- | ---------------------------------------- | --------------------------------------- |
| ESP32 dev board | USB 5 V                                  | host for everything below               |
| HLK-LD2450      | UART, TX GPIO26 / RX GPIO25, 256000 baud | multi-target x/y positions              |
| HLK-LD2412      | UART, TX GPIO17 / RX GPIO16, 115200 baud | presence, moving/still, distance        |
| AM312 PIR       | GPIO27                                   | cross-check, not yet used by the server |

Wiring is documented in `docs/SensorNodeWiring.png`,`docs/BreadboardConnections.png` and the KiCad schematic under`docs/cads/wiring/`.

### 1.2 How to run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload          # then open http://localhost:8000
```

`firmware/secrets.yaml` must exist locally with `api_key`, `radar_address`, `wifi_ssid`, `wifi_password`, `ota_password` and `fallback_password`. The server reads it at import time, so it will not start without it.

Flashing the node:

```bash
esphome run firmware/sensor-node.yaml
```

---

## 2. How it was realised — the order of work

| When         | Step                                          | Outcome                          |
| ------------ | --------------------------------------------- | -------------------------------- |
| Week 1       | Research sensors, competitors, methods        | `ai-docs-research/`            |
| Week 2       | Simulator, WebSocket stream, canvas dashboard | commit "Simulated state working" |
| Week 2       | Hold logic: door / window / room zones        | in`server.py`                  |
| Week 3       | Node firmware, wiring, first real radar test  | `sensor-node.yaml`, demo video |
| now (Week 4) | Connecting`radar.py` into the live stream   | in progress                      |

The build order was deliberate: every piece of the product — server, protocol, dashboard, hold logic — was finished against the simulator before any hardware existed. That was the mitigation for "radar modules arrive late" in the risk analysis, and it paid off; when the LD2450 arrived there was a finished product waiting for it.

---

## 3. Tools used

| Tool                         | Used for                                                 |
| ---------------------------- | -------------------------------------------------------- |
| Python 3 + FastAPI + Uvicorn | server, WebSocket stream                                 |
| ESPHome                      | node firmware, UART drivers for both radars, OTA updates |
| `aioesphomeapi`            | Python client for the node's native API                  |
| Plain HTML + Canvas          | dashboard                                                |
| Git + GitHub                 | version control, backup                                  |
| draw.io                      | room layout and wiring diagrams                          |
| KiCad                        | wiring schematic                                         |
| Mermaid                      | flow, architecture and state diagrams in the docs        |
| Claude / ChatGPT             | see §4                                                  |
| Tailscale                    | planned remote access                                    |

Choosing ESPHome over writing my own C++ UART parser is the decision that saved the most time. Both radar protocols are already implemented, tested by a lot of people, and expose clean named entities — writing that myself would have been several days spent re-solving a solved problem, with batch-to-batch firmware quirks on top.

---

## 4. GenAI use — honestly

The workshop asks which prompts I used and what I did with the results. The useful answer here is a mistake and what it taught me.

### 4.1 How I use it

| Category                              | My use                                                                              |
| ------------------------------------- | ----------------------------------------------------------------------------------- |
| Concept explanation                   | how WebSockets differ from polling; what a noise PSK is; what CSI actually measures |
| Explanation of how code works         | reading`aioesphomeapi`'s callback model                                           |
| Error message explanation / debugging | ESPHome build errors, asyncio tracebacks                                            |
| Co-creation                           | drafting a function I then rewrite; reviewing my hold logic for holes               |
| **Not** used for                | generating the whole product, or anything I cannot explain in a review              |

> **TODO** — paste 3–5 real prompts with the answer and what I changed about the output. Concrete examples score better than this table. Candidates: the ESPHome LD2450 entity naming question, the asyncio lifespan/`create_task`question, and the hold-duration discussion.

---

## 5. Known problems in the current code

Stating these rather than hiding them, because the next commit fixes them and the validation results below depend on it.

| #  | File          | Problem                                                                                                                   |
| -- | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| R1 | `server.py` | `/status` and `/api/state` return hard-coded placeholders                                                             |
| R2 | `server.py` | hold logic tracks a single`last_x`/`last_y`, so it only holds one person                                              |
| R3 | `server.py` | `firmware/secrets.yaml` is read at import; the server cannot start without hardware credentials, even in simulator mode |


## 6. Does the realisation follow the design?

| Design element               | Realised? | Notes                                                       |
| ---------------------------- | --------- | ----------------------------------------------------------- |
| §2 three-layer architecture | yes       | firmware / server / dashboard split holds                   |
| §3 coordinate transform     | yes       | `sensor_to_room()` matches the documented formula         |
| §3 room bounds filter (FR5) | yes       | `in_room()`                                               |
| §4.1 ESPHome entity names   | yes       | firmware and`radar.py` agree                              |
| §4.2 WebSocket frame        | yes       | fields as documented, including`source`                   |
| §5 hold state machine       | partly    | zones and timers exist; single-person only (R6)             |
| §5 sensor fusion            | no        | PIR and LD2412 are published but unused — still undesigned |
| §6 dashboard                | yes       | room, grid, zones, red/yellow dots, status lines            |
| §6 phone layout             | no        | fixed 500 × 400 canvas                                     |
| §7 Tailscale remote access  | no        | not set up yet                                              |
| §7 secrets kept out of git  | yes       | `.gitignore` covers `firmware/secrets.yaml`             |
| §8 reconnect on node loss   | yes       | 5 s retry loop in`radar.py`                               |
| §8 browser reconnect        | no        | manual refresh                                              |
| notifications (FR7)          | no        | not started                                                 |

Two honest gaps: fusion and notifications. Both are "should/could have" in the MoSCoW list, and both are blocked on design decisions I have not made rather than on code I have not written.

---

## 7. Evidence checklist for the portfolio

- [X] Source code in the repository
- [X] Firmware configuration
- [X] Wiring diagrams and schematic
- [X] Git history showing how the work progressed
- [X] First real-hardware demo video
- [ ] Screenshots of the dashboard (simulator and live) — **TODO**
- [ ] Photos of the assembled node — **TODO**
- [ ] Concrete GenAI prompt examples — **TODO** (§4.2)
- [ ] Working live-radar run after fixing R1–R4 — **TODO**
