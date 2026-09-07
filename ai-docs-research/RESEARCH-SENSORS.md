# Commodity Sensor Modules for Indoor Human Sensing — Research

Researched 2026-09-02 against manufacturer datasheets/manuals, GitHub repos, ESPHome docs, and Home Assistant community reports. All claims cited in [Sources](#sources).

Companion to `RESEARCH.md` (WiFi CSI: esp-csi pair, Nexmon, backhaul, GL.iNet travel router). This file covers everything *except* CSI. Where the two overlap (topology, backhaul), this file assumes the travel-router recommendation from RESEARCH.md may be adopted.

---

## TL;DR — recommended loadout for this project

The dashboard's schema (`targets: [{x, y, activity, moving}]`, presence, count, activity incl. breathing, zones) is served **almost exactly** by cheap 24 GHz radar for position and 60 GHz radar for vitals. CSI becomes the experimental layer, not the load-bearing one.

**Per-room "tracking node" (~$20/room):**

| Part | Price | Role |
|---|---|---|
| HLK-LD2450 | ~$10–15 (AliExpress) | x/y/speed of up to 3 targets at 10 Hz over UART — literally the `targets` array [S1][S2] |
| HLK-LD2412 | ~$5–8 | static presence hold (the LD2450 drops stationary people — by design [S6]); official ESPHome component since 2025.8 [S12] |
| ESP32 (owned) | $0 | reads both UARTs, ships JSON over UDP/ESPHome API to the PC |
| AM312 PIR (optional) | ~$1–2 | instant motion trigger / corroborator (the EP One pattern [S24]) |

**Bedroom "vitals node" (~$25):** Seeed **MR60BHA2** kit ($24.90, includes XIAO ESP32-C6, official ESPHome `seeed_mr60bha2` component) aimed at the bed from ≤1.5 m — real breathing rate + heart rate numbers, which is exactly the thing CSI struggles to do robustly [S15][S16][S17]. Budget alternative: HLK-LD6002 (~$12–23) with community libraries, but a 1,382,400-baud UART gotcha [S19][S20].

**"Who is where" layer ($0):** Bermuda (HA) or ESPresense on the same ESP32s — BLE room-level identification of phones/watches. Device-based, so it names the blips the radar sees [S26][S27].

**Skip (for now):** TI IWR6843ISK ($283 — capability is real, price isn't justified vs. $12 modules [S21][S22]); Infineon BGT60TR13C kits (raw radar, you write the DSP); UWB device-free sensing (research-grade); thermal as a primary (range-limited); LD2460 (5-target tracker, sample-stage availability — watch it [S8][S9]); ultrasonic (wrong tool).

**Floorplan layer (optional, ~$75 one-time):** LDROBOT LD19/D500 360° lidar kit on a Pi — a single static scan per room yields the wall polygon directly; stitch rooms by doorway alignment. Honest verdict below ([§9](#9-floorplan-angle)) — it works, but a tape measure is competitive for a small apartment.

Whole-apartment cost, 3 rooms + bedroom vitals + PIRs: **~$85–100** (excluding the $40 travel router already recommended in RESEARCH.md).

---

## Big comparison table

Prices are typical AliExpress/vendor prices as of 2026-09; "static people?" = detects a motionless (breathing-only) person; verdicts are for *this* dashboard specifically.

| Modality | Module | Outputs | Range / FoV | Rate | Price | Static people? | Breathing? | Multi-person? | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 24 GHz radar | **HLK-LD2450** | x, y, speed per target (UART 256000) | ~6 m / 120° H [S1][S2] | 10 Hz | $10–15 | ✗ (drops them [S6]) | ✗ | 3 targets | **BUY — the `targets` feed** |
| 24 GHz radar | **HLK-LD2412** | presence bool, moving/static distance + energy, per-gate energies | ~9 m / ~±60° [S12][S13] | ~10 Hz | $5–8 | ✓ (its specialty) | detects micro-motion, no rate | ✗ (1 zone) | **BUY — presence hold + zone energy** |
| 24 GHz radar | HLK-LD2410/B/C | same as LD2412, ~6 m, 9 gates × 0.75 m | 6 m / ±60° [S3][S4] | ~10 Hz | $3–6 | ✓ | micro-motion only | ✗ | Fine substitute if you have one; LD2412 is the better buy [S5] |
| 24 GHz radar | HLK-LD2420 | presence bool, distance | ~8 m | ~10 Hz | $2–3 | ✓ (weaker) | ✗ | ✗ | Cheapest; notorious firmware-format lottery between batches [S5] — skip |
| 24 GHz radar | HLK-LD2410S | low-power presence | ~6 m | slow | $4–6 | ✓ | ✗ | ✗ | Only for battery builds — not this project |
| 24 GHz radar | HLK-LD2411/2411S | gesture/proximity distance | short | — | $4–6 | ✗ | ✗ | ✗ | Wrong tool (gesture sensor) [S5] |
| 24 GHz radar | HLK-LD1125H | presence + micro-motion, 3 sensitivity zones | ~9 m motion | — | $10–14 | ✓ (false negs ≥5 m [S10]) | micro-motion | ✗ | Superseded by LD2412 |
| 24 GHz radar | HLK-LD2402 | presence bool moving+static, distance | ~10 m | — | $5–10 | ✓ [S11] | micro-motion | ✗ | Works (community ESPHome), but LD2412 has official support |
| 24 GHz radar | **HLK-LD2460** (2T4R) | x/y trajectories, up to **5** targets, UART 115200 | 6 m / 90–120° H, 50° V [S8][S9] | ~10 Hz | ~$12–18 | claimed better than LD2450 [S9] | ✗ | 5 targets | **WATCH** — sample-stage availability, thin ecosystem; the LD2450 successor once ESPHome support lands |
| 60 GHz radar | **Seeed MR60BHA2** (kit) | presence, target count, distance, **breath rate, heart rate** | presence 6 m; vitals ≤1.5 m [S15][S16] | ~1 Hz vitals | $24.90 kit | ✓ | ✓ (numeric rpm/bpm) | counts targets; vitals = 1 person | **BUY for bedroom** — official ESPHome, incl. ESP32-C6 |
| 60 GHz radar | HLK-LD6002 | breath rate, heart rate, distance | ~1.5–2 m vitals [S14][S19] | real-time | $12–23 | ✓ (in beam) | ✓ | 1 person | Budget vitals option; 1.38 Mbaud UART, community libs only [S19][S20] |
| 60 GHz radar | Seeed MR60FDA2 | fall event, presence | 6 m | — | ~$25 | ✓ | ✗ | ✗ | Fall detection is its one trick and user reports say it's unreliable (missed falls, still-person dropouts) [S18] — skip |
| 60 GHz radar | DFRobot C1001 (SEN0623) | presence, posture (lying), fall, sleep metrics, breath+heart ≤1.5 m | 11 m / 100°×100° [S23] | — | ~$30–40 | ✓ | ✓ | ✗ | Good all-rounder for a bedside; pricier than MR60BHA2, Arduino lib not ESPHome-official. "LD3320" from the brief is actually a *speech recognition* chip — not radar |
| High-end radar | TI IWR6843ISK + people-counting demo | 3D point cloud, tracks up to 20 people | ±60° az [S21] | 10–20 Hz | **$283** [S22] | ✓ | ✓ (vital-signs lab) | ✓✓ (~10 @ 85% [S21]) | Overkill: 20× the price of an LD2450 for capability this apartment doesn't need |
| High-end radar | Infineon BGT60TR13C demo kit | **raw** FMCW frames (you write the DSP) | short-range | high | ~$50–80 distr. [S25] | possible | possible | possible | Research toy, not a component — skip |
| UWB (tag) | Makerfabs ESP32-UWB DW3000 / MaUWB | tag↔anchor distances → cm-level x/y via trilateration | 40–120 m LoS | 10+ Hz | $44–55/board [S28][S29] | ✓ (tag ≠ person motion) | ✗ | 1 blip per tag (8 anchors / 64 tags claimed [S29]) | Device-*based*: precise, but 3 anchors + 1 tag ≈ $175 and people must carry tags — skip unless the tag UX is acceptable |
| UWB (device-free) | DW1000 CIR passive sensing | research: passive tracking from CIR | room | — | boards as above | ✓ (papers) | ✓ (papers) | limited | Real papers (multistatic passive tracking on COTS DW1000 [S30][S31]) but zero turnkey firmware — research project, not a component |
| Thermal | **MLX90640** (32×24) | temperature image → blob detect on ESP32/Pi | person blobs reliable ≲3–4 m; motion visible to ~9 m (110° variant test) [S32][S33] | up to 8 Hz practical on ESP32 [S34] | $25–45 clone, $75 Adafruit | ✓✓ (heat — best static detector) | ✗ | ✓ (blobs, if separated) | **Optional 2nd wave** — count verification + true static presence in the living room; needs your own blob-tracking code |
| Thermal | AMG8833 (8×8) | 64-pixel temp map | person ≲2.5–3 m practical / 60° | 10 Hz | $10–15 clone | ✓ (close) | ✗ | barely | Too coarse for room-scale counting — desk/sofa occupancy only |
| Thermal | MLX90641 (16×12) | temp map | between the two | 16 Hz | ~$30 | ✓ (close) | ✗ | barely | Odd middle child — skip |
| BLE (device) | ESPresense / Bermuda + ESP32 | room-level location of phones/watches (identity!) | per-room | seconds | $0 (reuse nodes) | ✓ (device present) | ✗ | ✓ (per device) | **RUN — free identity layer**; Bermuda if HA exists, else ESPresense MQTT [S26][S27] |
| BLE (device-free) | BLE CSI sensing | research only | — | — | — | — | — | — | No commodity path — ignore |
| PIR | AM312 / HC-SR501 | motion bool | 3–7 m / ~100° | instant | $1–2 | ✗ (classic PIR failure [S24]) | ✗ | ✗ | **Add for $2** — instant triggers + cross-check against radar false positives |
| Ultrasonic | HC-SR04 etc. | distance in a narrow cone | 4 m beam | fast | $1 | ✗ | ✗ | ✗ | Irrelevant for room sensing — confirm skip |
| 2D LiDAR | LDROBOT LD19/D500 kit | 360° range scan (room outline!) | 12 m, ±45 mm [S35][S36] | 10 Hz scan | $70–90 [S37] | (sees bodies as blobs, but not its job) | ✗ | — | **Optional one-time floorplan tool** on a Pi |

---

## De-facto Home Assistant standards (question 1 answered directly)

- **Single-room presence**: LD2410B/C is the most-deployed DIY module; official ESPHome `ld2410` component [S3][S4][S7]. The LD2412 is its straight upgrade (9 m, better static floor-noise handling) and got an **official** ESPHome component in 2025.8 [S12][S13].
- **Position/tracking**: LD2450, official ESPHome `ld2450` component (3 targets, x/y/speed/angle/distance, 3 configurable zones, min firmware V2.02.23090617) [S2].
- **The canonical combo** — used by commercial DIY products: Everything Presence **One** = LD2410B **+ PIR** + SHTC3 + BH1750 ("PIR for instant movement, mmWave for continued occupancy") [S24]; Everything Presence **Lite** (£28) = **LD2450 + light sensor** on an ESP32 [S38][S39]. So the community already converged on exactly the pairing recommended here: LD2450 for blips, LD2410-family for static hold, PIR for latency.
- **LD2450 static dropout — verified**: HA community threads confirm still targets vanish and "presence"/"still" stay off; a maintainer-level answer states plainly "the focus of 2450 is multiple moving targets" and the fix is pairing with an LD2410/12, not tuning [S6]. Atomic14's decoder guide says the same: "weak on stationary targets… pair with LD2412 for stationary detection" [S5]. Design your fusion assuming LD2450 target loss within ~30–60 s of stillness.

---

## Per-room node architecture

```
            PER-ROOM NODE (~$20)
 ┌─────────────────────────────────────────────┐
 │                    ESP32                    │
 │                                             │
 │  UART1 256000 8N1        UART2 115200 8N1   │
 │  ┌───────────┐            ┌───────────┐     │
 │  │  LD2450   │            │  LD2412   │     │
 │  │ x,y,speed │            │ presence, │     │
 │  │ ×3 @10Hz  │            │ gate      │     │
 │  └───────────┘            │ energies  │     │
 │        │                  └───────────┘     │
 │  GPIO ┌───────┐                 │           │
 │  ─────│ PIR   │ (optional)      │           │
 │       └───────┘                 │           │
 │            parse → fuse → JSON              │
 └──────────────────┬──────────────────────────┘
                    │ WiFi: UDP JSON @10Hz  (or ESPHome native API)
                    ▼
      GL.iNet travel router (own SSID, no client isolation)
                    │
                    ▼
        Arch PC — FastAPI server (server.py)
        per-node pose config → room→apartment
        coordinate transform → targets[] / zones
```

Notes:
- Classic ESP32 has 3 hardware UARTs — both radars fit on one board with pins to spare. **Hardware UART is mandatory** for the LD2450's 256000 baud; software serial corrupts frames [S5].
- Mount the LD2450 at ~1.4–2 m height, tilted slightly down, with its boresight covering the room; corner mounting maximizes coverage of a rectangular room.
- Bedroom node variant: swap the PIR for the MR60BHA2 kit (it's its own XIAO ESP32-C6 node — just aim it at the bed within 1.5 m, mattress height or ceiling above bed).

### Whole-apartment topology (no controlled router constraint)

```
 Room A node ──┐                                  ┌── Bermuda/ESPresense
 Room B node ──┼── WiFi ── GL.iNet travel router ─┼── (BLE scans run on the
 Bedroom vitals┘   UDP        (from RESEARCH.md)  │    same ESP32 nodes)
 (MR60BHA2)                        │              │
                                   ▼              ▼
                          Arch PC: FastAPI server ── dashboard.html
                                   ▲
 CSI pair (RESEARCH.md) ── USB serial (independent of all of the above)
```

Fallback if the travel router is never bought: the nearest node can run USB-serial to the PC (like the CSI RX), and the PC's WiFi adapter can host a hotspot for the remaining nodes — clunkier but workable. Do **not** put sensor UDP on the apartment WiFi (client isolation, per RESEARCH.md).

---

## Modality deep dives

### 1. 24 GHz Hi-Link family

**LD2450** — 24 GHz, 1T2R FMCW, tracks up to 3 moving targets: x/y coordinates (mm), speed (cm/s), and a distance-resolution word per target, 10 Hz over UART at 256000 8N1 [S1][S2]. FoV ±60° horizontal, ~35° vertical, 6 m max [S1]. Bluetooth config via HLKRadarTool app.
- **Frame format** (verify against your unit — Hi-Link ships firmware variants): 30-byte periodic frame `AA FF 03 00 | target1(8B) | target2(8B) | target3(8B) | 55 CC`; each target = x int16 LE, y int16 LE, speed int16 LE, distance-resolution uint16 LE. Signed values use **sign-and-magnitude with an inverted sign bit**: MSB=1 → positive (value & 0x7FFF), MSB=0 → negative — *not* two's complement. Empty target slots are all zeros. [S1][S40]
- Late-2025 batches reportedly changed report formats — log raw hex on first boot and keep the parser tolerant [S5].
- **Static dropout is by design** — see the standards section above [S5][S6]. Fusion rule: LD2450 target lost + LD2412 still says "occupied" → freeze the blip at its last position with `activity: "breathing"` instead of deleting it.

**LD2410/B/C** — the presence workhorse: outputs target state (none/moving/static/both), moving & static distances + energies; engineering mode adds per-gate energy for 9 gates × 0.75 m [S3][S4]. B adds Bluetooth tuning; C is pin-header form factor; radar performance identical [S5]. Frame protocol: header `F4 F3 F2 F1` … tail `F8 F7 F6 F5`, default 256000 baud [S3].

**LD2412** — LD2410 successor: ~9 m, wider FoV, floor-noise ("bottom noise") self-calibration, adjustable distance gates; default **115200** baud; official ESPHome component since 2025.8 [S12][S13]. **Buy this over the LD2410 for new builds.**

**LD2420** ($2–3) — works, but the community's least favorite: report-format lottery between firmware batches [S5]. **LD2411/S** — gesture/proximity sensor, not room presence [S5]. **LD1125H** — older 24 GHz micro-motion sensor, 3 sensitivity zones; false negatives for static occupancy at ≥5 m where the LD2410 had none [S10]. **LD2402** — 10 m presence module, responsive moving+static detection in an ESPHome test [S11]; no official component. All three: superseded — no reason to buy.

**LD2460** — the interesting one: 2×(1T2R) chips (2T4R), FMCW, tracks/positions **3–5 humans**, 90° H × 50° V (one reseller claims 120° H), 6 m, UART **115200** 8N1, BLE config app (iOS only so far) [S8][S9][S41]. Screek (who make HA sensors from Hi-Link modules) call it "better at stationary hold" than LD2450/2461 but note it's **sample-stage, only a few units out** [S9]. Module ~$12 (Alibaba/AliExpress). No ESPHome component yet. Verdict: this is the natural LD2450 successor for this exact dashboard (5 targets ≈ a small dinner party) — buy one to experiment when it's freely available, but don't build the system around it today.

**Gotchas (24 GHz):**
- Radar penetrates drywall — units detect people in the next room / hallway; in an apartment this includes **neighbors** through shared walls. Fix: reduce max gate/range (e.g. clamp to 2.25–4.5 m), aim boresight away from shared walls, and for the LD2450 clip targets to the room polygon server-side [S42].
- Fans, curtains, HVAC vents, monitors cause false positives; per-gate sensitivity tuning (lower gates near the offender to ~20–30 still-sensitivity) is the standard fix; HLKRadarTool has a 60-s auto-calibration (leave the room, press "Auto") [S42].
- One documented failure mode: periodic phantom occupancy every ~2 min — usually interference or PSU noise; use a clean 5 V supply and keep the radar away from the ESP32 antenna [S42].
- 256000 baud ⇒ hardware UART only [S5].

### 2. 60 GHz vital-sign radar — the breathing answer

This is the direct answer to "breathing/sleeping, which CSI struggles with": commodity 60 GHz FMCW modules output **numeric respiration and heart rates**.

- **Seeed MR60BHA2** ($24.90 kit incl. XIAO ESP32-C6, USB-C) [S17]: presence to 6 m, target count, distance, breath rate (rpm), heart rate (bpm) — vitals require the subject within **~1.5 m** and reasonably still [S15][S16]. Official ESPHome `seeed_mr60bha2` component; Seeed publishes full YAML + HA walkthroughs [S15][S16]. Reviews: "far more reliable than PIR… impressive and consistent" for its designed purpose [S43]. Caveats: radar-module firmware is **locked** (customization only for business customers) [S18]; vitals are single-person — with two people in bed it reports one blended/nearest reading. For "sleeping" classification (presence + low motion + stable breathing rate) it's ideal.
- **HLK-LD6002** (~$12–23, 2T2R, 3.3 V @ 600 mA): breath rate, heart rate, distance; UART at **1,382,400 baud** — many USB-serial adapters and softserial can't do it (ESP32 hardware UART can) [S14][S19]. Libraries: `icewind1991/hlk_ld6002` (Rust, sync+async embedded-io) [S20] and an Arduino/PlatformIO library [S19]. No ESPHome component. Verdict: fine if you enjoy protocol work; the MR60BHA2 is $10 more and turnkey.
- **Seeed MR60FDA2** (fall detection, ~$25): official ESPHome component with install-height/threshold config [S44], but a Seeed-forum thread reports it *not reliably detecting falls* and marking a still person absent [S18]. Fall detection isn't a project goal — skip.
- **DFRobot C1001 / SEN0623** (~$30–40): 60 GHz, 11 m, 100°×100°, two firmware modes — falls/posture (lying detection via point-cloud) and **sleep mode** (bed occupancy, movement, respiration + heart rate through the night, ≤1.5 m for vitals) [S23][S45]. DFRobot's own long-form test and a forum user found sleep mode "quite accurate" (HR/respiration within a couple of points), though another reports slow reaction and unreliable distance [S45][S46]. Arduino library, UART. A legitimate MR60BHA2 alternative if posture/lying detection appeals; otherwise the Seeed kit wins on ESPHome support.

**Multi-person truth:** none of the commodity vital-sign modules do per-person vitals for multiple people. They vital-sign the dominant/nearest chest in the beam. Plan: one vitals sensor per bed, pointed at it, and treat its output as "the person in this bed".

**Gotchas (60 GHz):** vitals need quasi-static subjects — reading a phone is fine, tossing/turning blanks the rates for a few seconds; thick duvets attenuate; mount so the beam hits the torso (headboard/ceiling-over-bed both work per Seeed docs); 60 GHz does **not** meaningfully penetrate walls (a feature here — no neighbor ghosts).

### 3. Higher-end radar — verdict: overkill

- **TI IWR6843ISK**: $282.98 at DigiKey [S22]. TI's 3D people-counting demo tracks up to 20 people, ±60° FoV; real-world reports: ~10 people at ~85% accuracy ±1 [S21][S47]. There are open-source HA bridges for TI EVMs, but you're flashing TI demo firmware, tuning chirp configs, and parsing TLV point clouds. Capability is genuinely a tier above Hi-Link — but this apartment needs to count ~1–4 people, which an LD2450 (+LD2460 later) does at 1/20th the price. **Not worth it.**
- **Infineon BGT60TR13C** demo kit (DEMOBGT60TR13CTOBO1, roughly $50–80 at Farnell/RS [S25]): superb silicon (1T3R, 5 mW-class), but the kit gives you **raw FMCW frames plus a GUI/SDK** — presence/tracking algorithms run on a host, and there's no maintained hobby firmware that outputs "targets over UART". It's a radar-DSP learning project, not a component. **Skip** — and note the cheap sibling BGT60LTR11AIP Shield2Go is motion-only (Doppler), no positioning [S25].

### 4. UWB — precise but device-based

- **Hardware**: Makerfabs ESP32-UWB (DW1000, ~$36), ESP32-UWB DW3000 ($43.80), ESP32-UWB Pro (120 m), MaUWB_ESP32S3 with STM32 AT firmware ($54.80) — the AT-firmware boards claim up to **8 anchors + 64 tags**, and DW3000 boards interoperate with Apple U1/AirTag-class chips [S28][S29][S48]. CNX-Software's review measured ranging good to ~10–20 cm with calibration [S48].
- **Tag tracking**: 3 anchors + 1 wearable tag ⇒ cm-to-dm-level x/y — the most precise blip feed possible, and it carries identity. Reality check: ~$130–175 of boards for one room, tags must be **worn and charged** (an ESP32-UWB "tag" is a dev board with a LiPo — hours-to-days battery, not months), and visitors are invisible. This contradicts the device-free spirit of the project. **Verdict: skip**, unless "family members wear a tag/keychain" is acceptable — then it's the best positioning money can buy at this budget.
- **Device-free UWB radar**: academically real — multistatic passive human tracking with COTS DW1000 CIR [S30], device-free localization from CIR [S31], passive channel charting on UWB meshes [S49]. Nothing turnkey exists; the DW1000 reports only a truncated CIR window and you'd be implementing papers. **Research project, not a component.**
- **Floorplan tie-in**: UWB anchors can auto-range each other (inter-anchor distances → anchor coordinates via trilateration/MDS). That gives you sensor *positions* for free — but says nothing about walls. Useful only if UWB is bought anyway.

### 5. Thermal — the static-person truth-teller

Thermal is the only cheap modality where a *motionless* person is trivially detectable (they glow). No privacy-invasive optical imagery.

- **MLX90640** (32×24, I²C, 55°×35° or 110°×75° variants): at 1 m each pixel ≈ 1.7×1.5 cm — silhouettes visible; Adafruit says reliable detection at ~12 ft (3.7 m) is "very difficult" with the 110° variant [S32], while Waveshare's D110 test saw a waving adult to 9 m (detection ≠ counting) [S33]. Practical: **reliable person blobs ≲3–4 m** with the 55° lens. On ESP32, 8 Hz refresh is practical over I²C [S34]. Price: $25–45 AliExpress clones, $75 Adafruit. Community projects use it for doorway people-counting [S34].
- **AMG8833** (8×8, 10 fps, 60°): person ≈ 1–4 warm pixels beyond ~2.5 m — okay for "someone on the sofa", not for counting a room.
- **MLX90641** (16×12): halfway house, ~$30 — no compelling niche here.
- **Integration**: I²C to any ESP32/Pi; you write the blob detection (simple: background-subtract, threshold ~2 °C over ambient, connected components → centroids). Centroids + camera pose → coarse x/y, so it *can* feed `targets` for static people.
- **Gotchas**: range is the hard wall — one MLX90640 covers a small room from a corner, not a living room from afar; radiators/laptops/pets are warm blobs (pets are a feature or a bug); direct sunlight through windows saturates scenes; FoV/lens variant matters — buy the 55° for range, 110° for coverage.
- **Verdict**: not needed for v1 (LD2412 covers static presence more cheaply), but the best **second-wave** addition for count verification and ground truth — e.g. one MLX90640 over the main room to validate radar counts.

### 6. BLE device-based sensing — the free identity layer

- **ESPresense**: dedicated ESP32 firmware, MQTT out, fingerprinting + calibration tooling; the mature, most accurate option; wants a whole ESP32 per room [S26][S27].
- **Bermuda**: HA custom integration consuming standard ESPHome Bluetooth-proxy data — trivial to add if nodes run ESPHome anyway; room-level accuracy good, distance estimates jumpy (users report occasional teleporting) [S26][S27].
- Phones randomize MACs: track iPhones/Watches via their **IRK** (HA "Private BLE Device"), or have phones advertise a fixed beacon (Home Assistant companion app / an ESPresense-compatible beacon app).
- This is *device*-based: it tells you **who** is in which room, complementing radar's **where exactly**. Fusing "Bermuda says Josip's phone is in the living room" with "LD2450 sees one target at (1.2, 2.4)" labels the blip.
- **Device-free BLE sensing** (BLE-CSI): a handful of papers, no commodity hardware/firmware path — ignore.
- **Verdict**: run it on the same per-room ESP32s (ESPHome BT proxy costs nothing extra) if HA enters the picture; standalone ESPresense→MQTT→FastAPI otherwise. $0 either way.

### 7. Ultrasonic / acoustic / PIR — honest quick take

- **PIR (AM312 $1–2, HC-SR501 $2)**: instant motion, zero RF interference, but blind to static people — the exact failure mmWave fixes [S24]. Worth $2 per node as (a) sub-second light-trigger latency, (b) a sanity cross-check that votes down radar false positives. The Everything Presence One ships PIR+mmWave for precisely this reason [S24].
- **Ultrasonic (HC-SR04)**: narrow cone, distance-only, audible to pets, no static detection. Irrelevant for room-scale human sensing — confirmed skip.
- **Acoustic**: microphone-based presence is privacy-adverse and a large ML project — out of scope.

### 8. Fusion architectures — what serious builds do, and what this one should

**The proven pattern** (EP One/Lite, Apollo MSR-2, Screek): mmWave for occupancy hold + PIR for latency + env sensors, ESP32 + ESPHome, one node per room [S24][S38][S39]. The Lite proves LD2450-on-ESP32 is a solid commercial product (£28 [S39]) — you're building its superset for less.

**Firmware choice — ESPHome vs custom, opinionated:**
- **Custom Arduino/IDF firmware + UDP JSON** (matches the repo's existing `esp32/` + UDP ingest): full control of frame parsing and rate, no HA dependency, but you own the LD2450 protocol quirks, OTA, and reconnect logic.
- **ESPHome node + `aioesphomeapi` in server.py** — **recommended**: ESPHome's `ld2450`/`ld2412`/`seeed_mr60bha2` components already handle every protocol quirk, firmware-version drift, tuning entities, and OTA; the FastAPI server subscribes to entity state over the native API (Python `aioesphomeapi`, no Home Assistant required) and converts to the dashboard schema. You keep the custom server AND inherit thousands of users' worth of parser debugging. Caveat: ESPHome LD2450 target coordinates update via the API at entity-throttle rates — set `throttle` low (e.g. 100 ms) for smooth blips.
- Hybrid escape hatch: ESPHome supports lambdas/custom UART components if a needed field isn't exposed.

**Mapping onto the existing server schema** (`server.py` `_ingest`):
- `targets[]` ← LD2450 per-target x/y (mm → m), transformed per node pose; `moving` = |speed| > 0; `activity` = "walking" if |speed| > ~0.3 m/s else "breathing" if LD2412-static-confirmed else "moving".
- `presence` ← OR over rooms of LD2412 occupancy (radar-held, not LD2450-derived).
- `person_count` ← LD2450 target count, floored by LD2412 presence (≥1 if occupied), optionally verified by thermal blobs later.
- `zones` ← two options: geometric zones evaluated server-side from LD2450 x/y (preferred — reuses the dashboard's zone logic), or LD2412 engineering-mode per-gate energies as 0.75 m-ring "zone motion energy" (nice drop-in for the current esp32-mode `_zone_targets` estimator).
- `activity: "sleeping"` ← bedroom MR60BHA2: bed-presence + breath rate in 8–20 rpm + no LD2450 movement for N minutes.
- **Coordinate frames**: store per node `{room, x0, y0, yaw, mirror_x}`; sensor frame (x lateral, y boresight, mm) → apartment frame via rotate+translate. Beware the LD2450 sign convention (see §1) and that ESPHome already normalizes signs — calibrate by walking a known L-shaped path on first install. Where two nodes overlap, dedupe targets by gating distance (<0.7 m ⇒ same person) — same trick the simulator's targets make easy to test.
- **CSI's remaining role** (per RESEARCH.md): whole-apartment anomaly/motion layer and a research playground, with the radar stack as its labelled ground truth — that combination (commodity radar labels + CSI models) is exactly how academic CSI work gets its training data.

### 9. Floorplan angle

- **Cheap 2D lidar, honestly assessed**: an LDROBOT **LD19 / D500 kit** ($70–90, USB, 12 m range, ±45 mm, 360° @ 10 Hz, ROS1/2 + Python SDKs, works on a Pi) [S35][S36][S37] produces a full wall outline of a room from **one static placement in seconds** — no SLAM needed for a single convex-ish room: the scan *is* the polygon. For the whole apartment: scan each room from 1–2 spots, then manually align polygons at doorways (an evening of fiddling in a Python notebook), or do proper SLAM by carrying the Pi+lidar slowly (hobby-grade results without odometry are mediocre). Furniture occludes walls at knee height; glass and mirrors lie to lidar.
  **Verdict**: genuinely works and it's the only commodity "measure my walls" hardware in budget — but for a small apartment, 30 minutes with a tape measure or a phone AR floorplan app (e.g. magicplan-class) gets the same dashboard background for $0. Buy the lidar only if it also excites you as a toy; it does double duty later on a robot base.
- **UWB anchor self-ranging**: gives inter-sensor geometry (auto-placing sensor icons), not walls — only relevant if UWB is bought for tracking (§4).
- **Radar-derived mapping**: LD2450 walk-track heatmaps actually trace the *walkable* area over days — plot a 2D histogram of all target positions and the furniture/walls appear as negative space. Free, and surprisingly good for calibrating the dashboard's room polygon. Recommended before buying anything.

---

## Suggested rollout order

1. **Now (~$20)**: one ESP32 + LD2450 (+LD2412) node in the main room → real `targets[]` on the dashboard; walk-track heatmap doubles as room-shape calibration.
2. **Week 2 (~$25)**: MR60BHA2 kit at the bedside → real breathing/sleeping for the `activity` field.
3. **Then (~$25–40)**: replicate tracking nodes per room; add $2 PIRs; travel router (per RESEARCH.md) as the sensor backhaul.
4. **Optional wave**: MLX90640 for count ground truth; LD2460 when generally available + ESPHome-supported; lidar/AR-app floorplan; UWB only if wearing tags becomes acceptable.

---

## Sources

- [S1] Hi-Link HLK-LD2450 instruction manual (frame format, 256000 8N1, 3 targets, specs) — https://www.manualslib.com/manual/3439736/Hi-Link-Hlk-Ld2450.html and https://www.hlktech.net/index.php?id=1157
- [S2] ESPHome LD2450 component docs (entities, zones, UART requirements, min firmware) — https://esphome.io/components/sensor/ld2450/
- [S3] ESPHome LD2410 component docs — https://esphome.io/components/sensor/ld2410/
- [S4] SmartHomeScene, DIY presence sensor with LD2410 — https://smarthomescene.com/diy/diy-presence-sensor-with-hi-link-ld2410-and-esp32-for-home-assistant/
- [S5] atomic14, "Hi-Link radar decoder" LD2410/B/C/S vs LD2412 vs LD2420 vs LD2450 comparison (prices, firmware-batch variance, hardware-UART requirement, pairing advice) — https://www.atomic14.com/esp32/sensors/hlk-radar-decoder/
- [S6] HA Community, "HLK LD2450 only see moving targets, no presence" (static dropout confirmed; 'focus of 2450 is multiple moving targets') — https://community.home-assistant.io/t/having-issues-with-hlk-ld2450-only-see-moving-targets-no-presence/1004773
- [S7] SmartHomeScene, "Ultimate list of mmWave radar sensor modules" (ecosystem overview, ESPHome support matrix, LD2450 'mediocre static presence beyond 2 m') — https://smarthomescene.com/blog/the-ultimate-list-of-mmwave-radar-sensor-modules/
- [S8] Hi-Link HLK-LD2460 product page + manual (2T4R, 3–5 targets, 90°H/50°V, UART 115200) — https://www.hlktech.net/index.php?id=1335 and https://www.manualslib.com/manual/4054420/Hi-Link-Hlk-Ld2460.html
- [S9] Screek on LD2460 vs LD2461/LD2450 (5 targets, better stationary hold, ~$12, sample-stage, iOS-only app) — https://screek.io/4a/latest-radar-hlk-ld2460-improved-ld2461-supports-five-targets-uses-second-generation-chip-more-powerful-antenna-for-multiplayer-tracking-radar-more-powerful-detection-capability-compared-to-ld2450
- [S10] SmartHomeScene, DIY presence sensor with LD1125H (3 zones, static false negatives at 5 m vs LD2410) — https://smarthomescene.com/diy/diy-presence-sensor-with-hi-link-ld1125h-and-esp32-for-home-assistant/
- [S11] HomeAutomations, "Testing the HLK-LD2402 with ESPHome" — https://homeautomations.xyz/2025/04/testing-the-hlk-ld2402-mmwave-sensor-with-esphome/
- [S12] ESPHome LD2412 component docs (official; UART 115200) — https://esphome.io/components/sensor/ld2412/ ; added in ESPHome 2025.8 — https://new.esphome.io/changelog/2025.8.0/
- [S13] HA Community, HLK-LD2412 ESPHome support thread (range/noise-floor improvements over LD2410) — https://community.home-assistant.io/t/hlk-ld2412-sensor-esphome-support/737856
- [S14] Hi-Link HLK-LD6002 product page (60 GHz 2T2R respiratory/heartbeat, 3.3 V/600 mA) — https://www.hlktech.net/index.php?id=1180
- [S15] ESPHome seeed_mr60bha2 component docs — https://esphome.io/components/seeed_mr60bha2/
- [S16] Seeed wiki, MR60BHA2 with Home Assistant (entities: breath rate, heart rate, distance, num targets; ≤1.5 m vitals) — https://wiki.seeedstudio.com/ha_with_mr60bha2/
- [S17] Seeed product page MR60BHA2 ($24.90, XIAO ESP32-C6 kit) — https://www.seeedstudio.com/MR60BHA2-60GHz-mmWave-Sensor-Breathing-and-Heartbeat-Module-p-5945.html
- [S18] Seeed forum, MR60FDA2 unreliable fall detection + still-person dropouts; radar firmware locked to business customers — https://forum.seeedstudio.com/t/mr60fda2-two-issues-1-not-reliably-detecting-fall-and-2-device-says-that-a-still-person-is-not-present/283603 ; SmartHomeScene Seeed 60 GHz review — https://smarthomescene.com/reviews/seeed-studio-60ghz-mmwave-sensors-review/
- [S19] PlatformIO community, HLK-LD6002 Arduino library (1,382,400 baud warning) — https://community.platformio.org/t/hlk-ld6002-esp32-60ghz-radar-sensor-for-heart-breath-rate-monitoring/47929
- [S20] icewind1991/hlk_ld6002 library — https://github.com/icewind1991/hlk_ld6002
- [S21] TI TIDEP-01000 people counting reference design (250 objects, 20 tracks, ±60°) — https://www.ti.com/tool/TIDEP-01000 ; E2E field report ~10 people @ ~85 % — https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/799719/iwr6843isk-68xx---people-counting-demo
- [S22] DigiKey IWR6843ISK, $282.98 — https://www.digikey.com/en/products/detail/texas-instruments/IWR6843ISK/10434492
- [S23] DFRobot wiki SEN0623 C1001 (11 m, 100°×100°, fall + sleep modes, vitals ≤1.5 m) — https://wiki.dfrobot.com/SKU_SEN0623_C1001_mmWave_Human_Detection_Sensor
- [S24] Everything Presence One (LD2410B + PIR + SHTC3; "PIR for instant movement, mmWave for continued occupancy") — https://shop.everythingsmart.io/products/everything-presence-one-kit ; https://esp32.co.uk/esp32-ld2410-mmwave-presence-sensor-with-home-assistant/
- [S25] Infineon DEMO-BGT60TR13C eval board (raw radar + RDK/GUI; presence apps run on host) — https://www.infineon.com/evaluation-board/DEMO-BGT60TR13C ; distributor listings https://uk.farnell.com/infineon/demobgt60tr13ctobo1/demo-eval-board-radar-sensor-60ghz/dp/4035678 , https://uk.rs-online.com/web/p/sensor-development-tools/2500908 ; BGT60LTR11AIP Shield2Go (motion-only) — https://www.digikey.com/en/product-highlight/i/infineon/xensiv-bgt60ltr11aip-radar-shield2go
- [S26] Derek Seaman, ESPHome + Bermuda BLE room tracking (2025) — https://www.derekseaman.com/2025/12/home-assistant-track-whos-in-each-room-with-esphome-bermuda-ble.html ; Bermuda thread — https://community.home-assistant.io/t/bermuda-bluetooth-ble-room-presence-and-tracking-custom-integration/625780
- [S27] ESPresense room-level presence write-up — https://sumguy.com/espresense-room-level-bluetooth-presence/ ; Home Automation Guy on Bermuda — https://www.homeautomationguy.io/blog/room-location-detection-with-bermuda-and-home-assistant-8f94b
- [S28] Makerfabs ESP32 UWB DW3000 ($43.80, Apple-U1 interoperable) — https://www.makerfabs.com/esp32-uwb-dw3000.html / https://www.makerfabs.cc/product/esp32-uwb-dw3000.html
- [S29] Makerfabs MaUWB_ESP32S3 ($54.80; claimed 8 anchors / 64 tags) — https://www.makerfabs.com/mauwb-esp32s3-uwb-module.html
- [S30] "Multi-Static UWB Radar-based Passive Human Tracking Using COTS Devices" (DW1000) — https://arxiv.org/pdf/2109.12856
- [S31] "Exploiting UWB Channel Impulse Responses for Device-Free Localization" — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9416598/
- [S32] Adafruit forum on MLX90640 range ("reliable detection at 12 ft… very difficult" with wide-angle) — https://forums.adafruit.com/viewtopic.php?t=203088 ; Adafruit MLX90640 guide — https://learn.adafruit.com/adafruit-mlx90640-ir-thermal-camera/overview
- [S33] Waveshare MLX90640-D110 wiki (wave test detectable 1–9 m) — https://www.waveshare.com/wiki/MLX90640-D55_Thermal_Camera
- [S34] ESP32 MLX90640 projects (8 Hz practical; doorway people counting) — https://how2electronics.com/diy-esp32-mlx90640-ir-thermal-camera-with-live-web-display/ ; https://github.com/embedded-kiddie/MLX90640
- [S35] Hiwonder LD19/D500 lidar kit (12 m, ±45 mm, ROS1/2, Pi/USB) — https://www.hiwonder.com/products/ld19-d300-lidar ; RobotShop listing — https://www.robotshop.com/products/hiwonder-ld19-d500-lidar-developer-kit-360-dtof-laser-scanner-supports-ros1-2-raspberry-pi-jetson-nano
- [S36] youyeetoo FHL-LD19 (12 m, 30 klux, ROS/Pi tutorials) — https://www.amazon.com/youyeetoo-D300-Resistant-Raspberry-Tutorial/dp/B0B1QCV4XR
- [S37] Budget lidar pricing (~$70–90 for D500-class) — https://industrialmonitordirect.com/blogs/knowledgebase/affordable-lidar-options-for-student-robotics-projects
- [S38] Everything Presence Lite hardware overview (LD2450 + light sensor + ESP32) — https://everythingsmarthome.github.io/everything-presence-lite/hardware-overview.html ; CNX coverage — https://www.cnx-software.com/2025/05/08/everything-presence-lite-esp32-based-mmwave-presence-sensor-tracks-up-to-three-targets-simultaneously/
- [S39] Everything Presence Lite shop (£28) — https://shop.everythingsmart.io/products/everything-presence-lite
- [S40] ShillehTek LD2450 manual mirror (30-byte frame AA FF 03 00 … 55 CC; 10 fps) — https://shillehtek.com/blogs/shillehtek-product-manuals/hlk-ld2450-24ghz-mmwave-radar-human-body-tracking-sensor-module-manual
- [S41] Paradisetronic LD2460 listing (5 targets, 6 m, 120° claim, UART 5 V) — https://en.paradisetronic.com/products/ld2460-24ghz-radar-sensor-fur-multi-target-personen-bewegungsverfolgung-bis-zu-5-personen-bis-6m-reichweite-120-erfassungswinkel-5v-uart
- [S42] HA Community "LD2410 esphome tips" megathread (fans/curtains gate tuning, wall penetration, range clamping, auto-calibration, periodic phantom occupancy) — https://community.home-assistant.io/t/ld2410-esphome-tips/477058 ; https://community.home-assistant.io/t/hlk-ld2410-regular-false-positives/816276
- [S43] MESH review, XIAO MR60BHA2 — https://meshsmarthome.com/review-seeed-studio-xiao-mr60bha2-60ghz-mmwave-human-breathing-heartbeat-sensor/
- [S44] ESPHome seeed_mr60fda2 component docs — https://esphome.io/components/seeed_mr60fda2/
- [S45] DFRobot blog, C1001 comprehensive fall/sleep testing — https://www.dfrobot.com/blog-13919.html
- [S46] DFRobot forum, C1001 user reports (sleep mode accurate; reaction slow / distance unreliable per one user) — https://www.dfrobot.com/forum/topic/335849
- [S47] TI E2E, 3D people counting threads — https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/1254358/iwr6843isk-3d-people-counting
- [S48] CNX-Software MaUWB_DW3000 review (ranging precision testing) — https://www.cnx-software.com/2024/04/16/mauwb_dw3000-with-stm32-at-command-review-arduino-uwb-range-precision-indoor-positioning/
- [S49] "Passive Channel Charting: Locating Passive Targets using a UWB Mesh" — https://arxiv.org/html/2505.10194v1
