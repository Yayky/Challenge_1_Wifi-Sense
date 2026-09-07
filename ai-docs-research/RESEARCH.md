# WiFi CSI Sensing — Hardware Capture Pipeline Research

Researched 2026-09-02 against primary sources (Espressif docs/repos, GitHub repos and issues, papers). All claims cited in [Sources](#sources).

## TL;DR — recommended setup

**Two-ESP32 pair running Espressif's own `esp-csi` get-started firmware, with the RX board plugged into the PC over USB serial.** No purchases required to start, no dependence on the apartment WiFi at all.

- **TX**: any ESP32 you own, flashed with `esp-csi/examples/get-started/csi_send` — broadcasts ESP-NOW packets at 100 Hz on a fixed channel (default ch. 11, HT40) [S1][S3]. Powered by any USB charger, placed anywhere in the room.
- **RX**: your best ESP32 variant, flashed with `csi_recv`. Espressif's own chip ranking for CSI quality is **ESP32-C5 > ESP32-C6 > ESP32-C3 ≈ ESP32-S3 > classic ESP32** [S5], and the get-started guide recommends C5/C6 [S2]. Use the best board in your drawer; a classic ESP32 still works, just worst RX quality.
- **Backhaul**: USB serial from RX to the PC (a ~100-line Python serial→UDP bridge feeds the existing FastAPI server; or add a serial ingest path to `server.py`). Serial is immune to client isolation, needs no network config, and at 921600–2,000,000 baud comfortably carries 100 Hz of HT40 CSI (the known bottleneck only appears at 256 subcarriers × 100 Hz with ASCII output on C6 [S7]).

**Recommended $40 upgrade**: a GL.iNet Opal (GL-SFT1200, $39.99 [S15]) travel router as your own controlled AP. PC + ESP32(s) all join it; UDP backhaul then works (no client isolation, you control the channel), the RX board becomes wireless and placeable anywhere, and the router doubles as a stable ping target for single-ESP32 CSI capture. This is the cleanest fix for every network problem in this project at once.

Why not the other routes: pinging the apartment AP works even with client isolation (the ping targets the gateway itself, isolation only blocks client↔client [S13][S14]) but leaves channel, band, and packet rate outside your control; passive ambient sniffing gives erratic packet rates; Nexmon on a Pi works but is a firmware-patching slog and monopolizes the Pi's only radio (and you have no Ethernet for backhaul).

---

## Findings by research question

### 1. ESP32 CSI capture, 2025/2026 state

**espressif/esp-csi** (last push 2026-04, 1.5k stars, actively maintained [S16]):
- Chip support: "All ESP32 series support CSI, including ESP32 / ESP32-S2 / ESP32-C3 / ESP32-S3 / ESP32-C5 / ESP32-C6 / ESP32-C61" [S1].
- Examples: `get-started` (csi_send/csi_recv ESP-NOW pair + `csi_recv_router` ping-based capture), `esp-radar` (activity detection, RainMaker cloud), `console_test` (interactive tuning + human-activity detection), `wifi_sensing_demo` (motion detection with on-site training and web diagnostics) [S1].
- Three documented capture methods: (a) router CSI via ping, (b) device-to-device exchange, (c) broadcast-packet capture — the last is called out as "the highest detection accuracy and reliability" but needs a dedicated sender device [S1].
- Chip ranking (Espressif ESP-Techpedia, verbatim): "ESP32-C5 > ESP32-C6 > ESP32-C3 ≈ ESP32-S3 > ESP32" [S5]. C5 is dual-band Wi-Fi 6 (2.4+5 GHz) [S18]; C6 is 2.4 GHz-only Wi-Fi 6 [S17].
- CSI internals (ESP-IDF docs): per-frame CSI covers up to three LTFs (LLTF, HT-LTF, STBC-HT-LTF); a non-HT 20 MHz frame yields 128 bytes, an HT40+STBC frame up to 612 bytes; 802.11n/40 MHz gives 114 subcarriers (108 usable). In STA mode CSI is only produced "from AP when it is connected"; enable promiscuous mode (`esp_wifi_set_promiscuous()`) to get CSI from arbitrary frames [S6].
- 802.11ax: C6/C5 can capture HE-LTF CSI (242 subcarriers per HE20 frame vs 52 for HT-LTF), but HE CSI requires an associated HE20 link, and the subcarrier layout differs from HT-LTF; there is an open bug where C6 omits L-LTF data and mis-orders HT-LTF subcarriers [S8]. Practical consequence: on C6, 11n HT40 capture is the well-trodden path; HE capture is bleeding-edge.
- Getting-started hygiene from Espressif: keep TX and RX > 1 m apart; PCB antennas have "poor directivity and are easily interfered with" — external-antenna boards preferred [S2].

**Steven M. Hernandez ESP32-CSI-Tool** [S9]: pinned to ESP-IDF **v4.3** (2021-era), classic ESP32 only in practice, serial/SD output, active-AP / active-STA / passive modes. Last push July 2024; effectively legacy. Historically important (basis of many papers) but **use esp-csi instead** — it is the vendor-maintained successor with newer-chip support.

### 2. TX–RX topology without a controlled router

Ranked for this project:

1. **(a) Two ESP32s, dedicated TX broadcasting + RX capturing** — best. This is esp-csi's "broadcast" method ("highest detection accuracy and reliability" [S1]). `csi_send` transmits ESP-NOW broadcasts to `ff:ff:ff:ff:ff:ff` at a configurable 100 Hz on a fixed channel with HT40 [S3] — exactly the stable 20–100 Hz a sensing pipeline needs, and no AP involved anywhere. Note the TX runs in STA mode without associating; the RX filters on the sender's MAC.
2. **(b) ESP32 pinging the apartment AP** (`csi_recv_router` [S4]) — works, including under client isolation: isolation is an L2 forwarding policy at the AP that blocks *client-to-client* frames [S13][S14]; the ping targets the gateway itself, which normally answers (some guest/captive networks do firewall ICMP to the gateway — test first). Every ping reply from the AP yields a CSI sample. Downsides: the AP picks the channel/band (may be 5 GHz, may hop on DFS events), reply rate can be throttled, and you're measuring the ESP32↔AP path, not a geometry you chose. Fallback if ICMP is blocked: in STA mode the AP's beacons still generate CSI, but only at ~10 Hz (102.4 ms beacon interval) — marginal for motion, too coarse for breathing spectra.
3. **(c) Passive sniffing of ambient traffic** (promiscuous mode [S6]) — worst for sensing: packet rate depends entirely on other people's traffic, so the CSI time series is irregularly sampled and gap-ridden. Fine for a demo, bad for the 20–100 Hz consistency requirement.

### 3. Getting CSI from ESP32 to the PC

Throughput needed is tiny: ≤612 bytes CSI + ~100 bytes metadata per frame × 100 Hz ≈ 70 KB/s ≈ 0.6 Mbit/s.

- **USB serial** (RX board plugged into PC): simplest, network-independent. Use ≥921600 baud (ESP32-CSI-Tool's own guidance: baud rate "extremely important" for high sample rates [S9]). Known ceiling: esp-csi issue #249 documents dropped frames on a C6 at 2,000,000 baud with 256 subcarriers × 100+ Hz because ASCII encoding inflates data ~4× [S7]. At 128 subcarriers it's fine; binary framing fixes it entirely.
- **UDP over apartment WiFi** (what `esp32/wifi_csi_sensor.ino` in this repo does today): blocked whenever the AP enables client isolation, which is a default-on companion of guest SSIDs and common on ISP/landlord-managed APs [S13][S14]. Untestable assumption — assume broken until proven otherwise.
- **UDP over your own travel router / ESP32 SoftAP**: works and keeps the RX placeable. An ESP32 RX can even run SoftAP for the PC while capturing, but the SoftAP's own beacons/traffic pollute the channel and the single radio time-shares; a travel router is cleaner.
- Verdict: serial for v1; UDP via travel router for v2. Never depend on the apartment WiFi for the CSI path.

### 4. Raspberry Pi Nexmon CSI

`seemoo-lab/nexmon_csi` is alive (pushed 2026-07 [S16]) and supports the **bcm43455c0** — the chip in **Pi 3B+, Pi 4B, and Pi 5** [S10]. Not supported: Pi 3B (non-plus), Pi Zero W, Pi Zero 2 W (bcm43430-family chips absent from the supported list [S10]). Historically pinned to kernels 4.19/5.4/5.10, but a new Makefile targets recent Raspberry Pi OS kernels without a patched brcmfmac, and Discussion #395 (active Dec 2025 → Jul 2026) confirms working setups on Pi 5 / Raspberry Pi OS Trixie / kernel 6.12 and unchanged operation on Pi 4B [S10][S11].

Pain level: real. Pi 5 needs a switch off the 16k-page kernel, the toolchain still wants Python 2.7 (archived-Debian workaround), 64-bit OS needs armhf libs, and netlink quirks recur [S11]. Structural problem for *this* apartment: nexmon_csi puts the Pi's **only** radio into monitor mode (CSI arrives as UDP on port 5500 locally [S10]), so with no Ethernet the Pi needs a second USB WiFi adapter just to backhaul data to the PC. Upside if you do it: 64/128/256-subcarrier CSI (up to 80 MHz) of *any* overheard traffic, far richer than ESP32. Verdict: worthwhile phase-2 experiment if you own a 3B+/4/5; wrong first move.

### 5. BFI sniffing (Wi-BFI / BeamSense)

Feasible without owning the router in principle: 802.11ac/ax compressed beamforming feedback travels in Action-No-Ack management frames sent **unencrypted**, so a monitor-mode capture (tshark) decodes them without association [S12][S12b]. `kfoysalhaque/Wi-BFI` (MobiCom'23 workshop tool, pushed 2026-05 [S16]) decodes SU/MU-MIMO feedback for ac/ax at 20/40/80/160 MHz [S12].

Reality check: you only get frames when a beamforming sounding exchange actually happens, i.e. the apartment AP must be ac/ax with beamforming enabled *and* have active MIMO clients; sample timing is dictated by the AP's sounding schedule, not you. Adapter: **MT7612U**-based USB (e.g. Comfast CF-912AC, ~$20–30) — in-kernel `mt76` driver since Linux 4.19, monitor mode + injection on 2.4/5 GHz, the standard recommendation for Kali-style capture [S19]. Verdict: cheap to try since the adapter is useful anyway (also solves Pi-backhaul and general 5 GHz capture), but treat as a side experiment, not the pipeline.

### 6. 802.11mc FTM

Supported on **ESP32-S2/S3/C2/C3/C6 — not classic ESP32** [S20][S21]. Caveats from the tracker: C3 advertises responder capability but doesn't answer requests (initiator-only in practice) [S22]; multiple reports of "FTM Initiator mode not supported!" on C6 hardware [S23]. Usefulness here: FTM measures RTT *between two radios* — it's device-based ranging (~1–2 m at best indoors), not device-free sensing, so it contributes nothing to presence/motion/breathing. Marginal future use: ranging between ESP32 anchors to auto-measure anchor spacing for the floorplan/PDR layer. Low priority.

### 7. Cheap dedicated TX / controlled AP: travel router

Yes — this is the single cheapest fix for the "no router of my own" problem. A GL.iNet Opal (GL-SFT1200, dual-band, $39.99 [S15]) or Mango (GL-MT300N-V2, 2.4 GHz-only, ~$25–30 [S15b]) gives you:
- a fixed channel and band you choose (kills the channel-hopping and DFS problems);
- a private L2 segment with no client isolation → ESP32→PC UDP just works;
- a stable ping target for single-ESP32 CSI capture at any rate you want;
- WISP/repeater mode: it can join the apartment WiFi upstream, so the PC keeps internet while sitting on your sensing LAN — no Ethernet needed anywhere.

The two-ESP32 ESP-NOW link still provides the *sensing* path (better than router-ping per Espressif [S1]); the travel router provides the *backhaul* and control plane. Buy the Opal over the Mango: dual-band means the backhaul can sit on 5 GHz while sensing runs on 2.4 GHz, avoiding self-interference (see Gotchas).

### 8. Hobbyist state of the art

- **esp-csi examples** — the vendor demos (`console_test` human-activity detection, `wifi_sensing_demo` motion detection with on-site training) all use the two-ESP32 or ESP32↔router topologies described above [S1]. This repo *is* the current hobbyist baseline.
- **Wi-ESP** (Atif et al. 2020, J. Comput. Design & Eng.) — ESP32 (WROOM-era) as a standalone 802.11n CSI collector, pitched as replacement for Intel 5300/Atheros CSI NICs; AP↔STA ESP32 pair topology [S24].
- **ESP32-CSI-Tool** — dozens of papers built on it in the same AP↔STA-pair or passive topologies [S9].
- **ESPARGOS** (Univ. Stuttgart, 2024–2026) — current high end of "cheap" WiFi sensing: 2×4 patch-antenna array, one ESP32-S2 per antenna, shared 40 MHz reference clock for phase coherence, real-time CSI streaming via `pyespargos`; does passive direction-finding, through-wall tracking, live WiFi "heatmaps" [S25][S26]. Beyond DIY-from-parts (custom PCB), but its papers/datasets are the best reference for what phase-coherent multi-antenna ESP32 CSI can do, and hardware manufacturing runs have been prepared [S26].
- Espressif also notes serious CSI work increasingly wants multi-antenna receivers; their answer is multi-chip boards with shared crystals (C3/S3 multi-antenna dev board) [S5].

---

## Option comparison

| # | Option | CSI source | Packet rate control | Needs apartment WiFi? | Survives client isolation? | Cost | Effort | Sensing quality | Verdict |
|---|--------|-----------|--------------------|--------------------|--------------------------|------|--------|----------------|---------|
| 1 | 2×ESP32 ESP-NOW pair, serial backhaul | Dedicated 100 Hz broadcast [S1][S3] | Full (100 Hz fixed) | No | N/A (no network used) | $0 | Low | High (Espressif's "highest accuracy" method) | **Do first** |
| 2 | 2×ESP32 pair + travel router backhaul | Same as #1 | Full | Only for internet uplink | Yes (own AP) | $40 | Low | High, RX freely placeable | **v2 upgrade** |
| 3 | 1×ESP32 pinging apartment AP | AP ping replies [S4] | Partial (rate yes, channel/band no) | Yes | Yes (pings gateway, not a client [S13]) | $0 | Low | Medium; path not chosen by you | Backup / quick demo |
| 4 | ESP32 passive sniffer | Ambient traffic [S6] | None | Needs nearby traffic | Yes | $0 | Low | Poor (irregular sampling) | Skip |
| 5 | Pi 3B+/4/5 + nexmon_csi | Ambient or your own TX, ≤80 MHz [S10] | None (passive) | No | Yes | $0–20 (USB WiFi for backhaul) | High [S11] | Highest per-frame richness | Phase 2 |
| 6 | Wi-BFI sniffing (MT7612U) | AP↔client beamforming reports [S12] | None (AP's sounding schedule) | Needs ac/ax MIMO traffic | Yes | ~$25 | Medium | Unpredictable; research-grade | Side quest |
| 7 | FTM ranging | RTT, not CSI [S20] | — | No | — | $0 | Medium | Not device-free sensing | Skip for sensing |

## Topology diagrams

**v1 — zero purchases (recommended start):**

```
                 sensing zone (person walks/breathes here)
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  [ESP32 TX]  ))))))  ESP-NOW broadcast, ch.11 HT40, 100 Hz  ))))))  [ESP32 RX (C6/S3/C3 best)]
  csi_send                                                            csi_recv
  (any USB charger)                                                      |
                                                                         |  USB serial, >=921600 baud
                                                                         |  (CSI frames -> bridge script -> UDP :5000)
                                                                    [PC, Arch Linux]
                                                                    server.py + dashboard

  [Apartment WiFi] ---- only used by the PC for internet; NOT part of the pipeline
```

**v2 — travel router backhaul (RX placeable anywhere):**

```
  [ESP32 TX] )))) ESP-NOW 100 Hz, 2.4 GHz ch.N )))) [ESP32 RX] 
                                                        |
                                                        | UDP CSI frames over 5 GHz (Opal LAN)
                                                        v
  [Apartment WiFi] <--WISP/repeater uplink-- [GL.iNet Opal, your AP] <--5 GHz--> [PC]
   (internet only)                            fixed channels, no isolation        server.py
```

Sensing link on 2.4 GHz, backhaul on 5 GHz — backhaul traffic never appears in the CSI channel.

## Shopping list

| Item | Status | Price | Role |
|------|--------|-------|------|
| 2× ESP32 dev boards (any variants) | **owned** | — | TX + RX for v1; use the newest variant (C6 > C3≈S3 > ESP32 [S5]) as RX |
| Raspberry Pi 3B+/4 (if that's what you have) | **owned** | — | optional nexmon_csi phase 2 [S10] |
| USB cables/chargers | **owned** | — | power + serial |
| GL.iNet GL-SFT1200 Opal | buy | $39.99 [S15] | controlled dual-band AP: backhaul, channel control, ping target |
| ESP32-C6-DevKitC-1 (or two) | buy (optional) | ~$8–12 | best cheap RX chip [S5]; get external-antenna version if possible [S2] |
| ESP32-C5 devkit | buy (optional, when easily available) | ~$15–25 | top-ranked CSI chip, dual-band Wi-Fi 6 [S5][S18] |
| MT7612U USB adapter (e.g. Comfast CF-912AC) | buy (optional) | ~$20–30 | 5 GHz monitor mode for Wi-BFI [S19]; doubles as Pi backhaul radio |

Total for the recommended path: **$0 now, ~$50 for v2** (Opal + one C6 board).

## Gotchas

- **Client isolation**: assume the apartment AP blocks client↔client L2 traffic [S13][S14] — so ESP32→PC UDP over that network (the current `.ino` approach) likely fails silently. Gateway-directed traffic (ping) usually still works. Serial or your own AP sidesteps it entirely.
- **Channel control**: CSI is only captured on the channel the radio is parked on. The apartment AP can sit on any channel (incl. 5 GHz DFS ones the ESP32 classic can't even hear) and can move. Fixed-channel ESP-NOW pair or your own router removes this variable.
- **2.4 vs 5 GHz**: everything you own except a hypothetical C5 is 2.4 GHz-only. 2.4 GHz is congested (neighbors, BT, microwaves → CSI noise) but penetrates walls better. Keep the sensing link on a channel distant from the apartment AP's, and put backhaul on the other band (Opal) or on a wire.
- **Self-interference**: if backhaul UDP shares the sensing channel, your own bursts add channel occupancy and occasionally delay the 100 Hz TX. Serial or cross-band backhaul avoids it.
- **IDF versions**: esp-csi tracks current ESP-IDF (5.x); ESP32-CSI-Tool is frozen at IDF v4.3 [S9] — don't mix guides. The repo's Arduino sketch needs arduino-esp32 ≥2.x; note Arduino cores lag IDF, and C5 support arrived in arduino-esp32 3.3.x (band-switching PR [S21b]).
- **Serial throughput**: ASCII CSI at 256 subcarriers × 100 Hz overruns even 2 Mbaud [S7]. Use ≥921600 baud, prefer binary framing, and keep to 128 subcarriers (HT40) unless you implement binary output.
- **C6/HE quirks**: HE-LTF CSI needs an associated HE20 link, has a different subcarrier layout, and C6 currently drops L-LTF and mis-orders HT-LTF subcarriers in some IDF versions [S8]. Capture 11n HT40 on C6 for now.
- **Antennas and placement**: PCB-antenna boards are directional and interference-prone — Espressif recommends external antennas; keep TX–RX separation >1 m [S2]. Mount boards rigidly (a swaying board *is* motion to CSI); keep them off metal surfaces and away from USB3 ports/hubs (2.4 GHz-band RFI).
- **Power supply noise**: cheap USB chargers modulate the RF front-end; amplitude wobble from a bad PSU looks like a breathing signal. Use a decent charger or a powerbank for the TX when validating.
- **Beacon-rate fallback**: AP beacons give only ~10 Hz CSI — enough for presence, too slow for reliable breathing extraction (this repo's buffer math assumes 20 Hz).
- **Nexmon monopolizes the Pi radio**: monitor-mode CSI means no normal WiFi on the same chip [S10]; with no Ethernet, budget a USB WiFi adapter for backhaul or log locally.

## Sources

- [S1] esp-csi README — chips, examples, three capture methods, broadcast "highest detection accuracy": https://github.com/espressif/esp-csi
- [S2] esp-csi get-started README — ESP-NOW pair, C5/C6 recommended, >1 m spacing, external antennas: https://github.com/espressif/esp-csi/blob/master/examples/get-started/README.md
- [S3] csi_send source — 100 Hz (`usleep(1000*1000/CONFIG_SEND_FREQUENCY)`), ch. 11, HT40, broadcast MAC: https://github.com/espressif/esp-csi/blob/master/examples/get-started/csi_send/main/app_main.c
- [S4] csi_recv_router README — ping-based router CSI, all-chip support: https://github.com/espressif/esp-csi/blob/master/examples/get-started/csi_recv_router/README.md
- [S5] ESP-Techpedia ESP-CSI solution — chip ranking "ESP32-C5 > ESP32-C6 > ESP32-C3 ≈ ESP32-S3 > ESP32", multi-antenna notes: https://docs.espressif.com/projects/esp-techpedia/en/latest/esp-friends/solution-introduction/esp-csi/esp-csi-solution.html
- [S6] ESP-IDF Wi-Fi vendor features — CSI LTF types, 128/612-byte buffers, subcarrier tables, STA-mode "from AP when connected", promiscuous mode, enable steps: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi-driver/wifi-vendor-features.html
- [S7] esp-csi issue #249 — C6 @2 Mbaud drops frames at 256 subcarriers/100 Hz, ASCII 4× inflation, binary-output request (open): https://github.com/espressif/esp-csi/issues/249
- [S8] esp-idf issue #14271 — C6 missing L-LTF, wrong HT-LTF subcarrier order; HE-LTF 242 subcarriers, needs associated HE20 link: https://github.com/espressif/esp-idf/issues/14271
- [S9] ESP32-CSI-Tool — IDF v4.3 pin, three modes, serial/SD output, baud-rate guidance; last push 2024-07: https://github.com/StevenMHernandez/ESP32-CSI-Tool
- [S10] nexmon_csi README — bcm43455c0 (Pi 3B+/4B/5), kernels 4.19/5.4/5.10 + new no-patched-brcmfmac Makefile, UDP :5500, 64/128/256 subcarriers: https://github.com/seemoo-lab/nexmon_csi
- [S11] nexmon_csi Discussion #395 — Pi 5 / RPi OS Trixie / kernel 6.12 working; Python 2.7 + armhf-lib pain points; active Dec 2025–Jul 2026: https://github.com/seemoo-lab/nexmon_csi/discussions/395
- [S12] Wi-BFI repo — monitor-mode tshark capture, ac/ax, 20–160 MHz, SU/MU-MIMO: https://github.com/kfoysalhaque/Wi-BFI
- [S12b] Wi-BFI paper (Haque et al., MobiCom'23 wksp) — BFA frames captured over the air, unencrypted feedback: https://arxiv.org/abs/2309.04408
- [S13] Cisco Meraki — wireless client isolation blocks client-to-client at L2: https://documentation.meraki.com/Wireless/Operate_and_Maintain/How_Tos/Firewall_and_Traffic_Shaping/Wireless_Client_Isolation
- [S14] TP-Link — AP isolation behavior and guest-network defaults: https://www.tp-link.com/us/blog/2586/what-is-ap-isolation-and-when-to-enable-it-/
- [S15] GL.iNet US store / product pages — Opal GL-SFT1200 $39.99, Beryl AX GL-MT3000 $98.99: https://store-us.gl-inet.com/collections/travel-routers ; https://www.gl-inet.com/en-us/products/gl-sft1200
- [S15b] GL.iNet Mango GL-MT300N-V2 product page: https://www.gl-inet.com/en-us/products/gl-mt300n-v2
- [S16] GitHub API repo metadata (checked 2026-09-02): esp-csi pushed 2026-04-22; nexmon_csi pushed 2026-07-09; Wi-BFI pushed 2026-05-16; ESP32-CSI-Tool pushed 2024-07-16.
- [S17] ESP32-C6 product page — 2.4 GHz Wi-Fi 6: https://www.espressif.com/en/products/socs/esp32-c6
- [S18] ESP32-C5 product page — dual-band Wi-Fi 6: https://www.espressif.com/en/products/socs/esp32-c5
- [S19] morrownr/USB-WiFi — MT7612U in-kernel since 4.19, monitor mode/injection, adapter recommendations: https://github.com/morrownr/USB-WiFi/blob/main/home/Recommended_Adapters_for_Kali_Linux.md
- [S20] ESP32 forum — FTM unsupported on classic ESP32: https://www.esp32.com/viewtopic.php?t=19642
- [S21] arduino-esp32 FTM example — supported chip list (C2/C3/C6/S2/S3): https://github.com/espressif/arduino-esp32/blob/master/libraries/WiFi/examples/FTM/FTM_Initiator/README.md
- [S21b] arduino-esp32 PR #11045 — 2.4/5 GHz band switching (C5 support): https://github.com/espressif/arduino-esp32/pull/11045
- [S22] esp-idf issue #7578 — ESP32-C3 advertises FTM responder but doesn't answer: https://github.com/espressif/esp-idf/issues/7578
- [S23] esp-idf issues #15216 / #17932 — ESP32-C6 "FTM Initiator mode not supported!": https://github.com/espressif/esp-idf/issues/15216 ; https://github.com/espressif/esp-idf/issues/17932
- [S24] Wi-ESP (Atif et al. 2020), J. Comput. Design & Eng. 7(5):644–656: https://academic.oup.com/jcde/article/7/5/644/5837600
- [S25] ESPARGOS datasets paper (Euchner et al., 2024): https://arxiv.org/abs/2408.16377 ; array/system paper: https://arxiv.org/abs/2502.09405
- [S26] pyespargos — real-time CSI streaming library for the ESP32-S2 array: https://github.com/ESPARGOS/pyespargos
