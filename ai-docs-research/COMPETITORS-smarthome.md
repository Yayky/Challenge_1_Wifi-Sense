# Commercial Smart-Home Presence/Occupancy Sensors — Competitive Landscape

Research date: 2026-09-08

Comparison target: WiFi Sense (DIY project) — see project description below.

## Project being compared against: WiFi Sense

**WiFi Sense** is a student-built, camera-free room presence system for a single 20 m² studio apartment. Hardware: an HLK-LD2450 24GHz mmWave radar module (tracks x/y position of up to 3 people simultaneously, ~10 Hz over UART) plus an AM312 PIR motion sensor, both read by an ESP32 running ESPHome. Sensor data streams to a self-hosted Python FastAPI server, which renders live person "blips" on a top-down room radar dashboard (a web page, also reachable on a phone over a Tailscale VPN — no port forwarding, no cloud relay). Total sensor cost is roughly €25. The project is fully open source. Planned next steps: away-mode notifications when presence is detected while the occupant is out, and migrating hosting to a Raspberry Pi for 24/7 uptime.

## Comparison Table

| Product | Price | Tech | Outputs | Hub/cloud? | Visual map? | Open? | Notes |
|---|---|---|---|---|---|---|---|
| **WiFi Sense** (this project) | ~€25 parts | LD2450 + AM312, ESP32/ESPHome | per-target x/y, speed, presence | No — self-hosted | **Yes, purpose-built** | Yes, fully | Must be built and tuned by hand |
| Everything Presence Lite | ~€33 | LD2450 + BH1750, ESP32/ESPHome | per-target x/y, 4 polygon zones, 2 exclusion zones | No cloud; HA assumed | Zone *editor* only, no live view | Yes (⭐300+) | **Same radar chip as WiFi Sense** |
| Everything Presence One | ~€55 | DFRobot SEN0609 + PIR + temp/humidity/light | fused presence booleans, environment | No cloud; HA assumed | No | Yes | No x/y — trades coordinates for PIR fusion + range |
| Aqara FP2 | €75-85 (often ~€55) | 60GHz mmWave | up to 5 targets, 30 zones/320 cells, falls, sleep | WiFi; local control after setup | **Yes — live person map in app** | No | Most capable consumer option |
| Aqara FP300 | ~€50 | 60GHz mmWave + PIR + temp/humidity/light | presence + environment | Thread/Zigbee, Matter | No | No | Battery-powered (2-3 yr) |
| Aqara FP1E | ~€30 | mmWave | presence boolean | **Requires Aqara hub** | No | No | Stripped-down, no zones |
| Apollo MSR-2 | €35-55 | LD2410B + light/UV/pressure/CO2 | presence, distance, environment | No cloud; HA assumed | No | Yes, ESPHome | LD2410B not LD2450 — no x/y |
| Sonoff SNZB-06P / 06P24 | €15-25 | 5.8GHz / 24GHz mmWave | presence boolean, 3 sensitivity levels, ~4 m | Requires Zigbee bridge | No | No | Cheap, basic |
| Generic Tuya/Zigbee mmWave | €15-25 | LD2410-family | presence boolean + distance | Zigbee2MQTT or Tuya cloud | No | No | Firmware varies by batch |
| IKEA VALLHORN | ~€10 | PIR | motion only | IKEA DIRIGERA | No | No | Blind to still people |

## Everything Presence Lite

**Price:** £28 GBP (~€33) direct from the manufacturer; also seen listed at $34–38 USD depending on region/sale (shop.everythingsmart.io).

**Sensor tech:** HiLink LD2450 24GHz mmWave module — the *same radar chip* WiFi Sense uses — plus a BH1750 ambient-light sensor. No PIR on the Lite (PIR fusion is reserved for the pricier "One"). Built on an ESP32, flashed with ESPHome firmware. The board also exposes spare GPIO for optional modules (e.g. CO2).

**What it outputs:** This is the closest commercial cousin to WiFi Sense. The LD2450 firmware exposes native per-target x/y coordinates, distance, speed and approach angle for up to 3 simultaneously tracked people — genuine coordinates, not just a boolean, mirroring what WiFi Sense already does. On top of that it layers up to 4 configurable zones (including polygon zones) and up to 2 exclusion zones, so it can also emit simple in-zone/out-of-zone booleans for Home Assistant automations. A companion Home Assistant add-on ("zone creator") gives a drag-and-draw editor for defining those zone boundaries on a static floor plan — but this is a boundary-editing tool, not a live animated radar view of moving blips. There is no shipped equivalent of WiFi Sense's real-time top-down dashboard; the x/y data exists as HA entities/attributes for automations, not as a default visual "watch people move" screen (third parties have built HA dashboard cards for this, but it's not out of the box).

**Hub/cloud:** No cloud, no subscription. Runs fully local via ESPHome; the native API/MQTT could technically be read by other software, but in practice essentially all users consume it through Home Assistant.

**Ecosystem:** Home Assistant-first (native ESPHome integration), can double as a Bluetooth proxy for HA. No native Apple HomeKit/Alexa without going through HA's own bridge integrations.

**Open source:** Yes. Firmware/config live on GitHub (`EverythingSmartHome/everything-presence-lite`, 300+ stars), fully user-modifiable and reflashable — closer in spirit to WiFi Sense than most of the other products below.

**Reliability complaints:** A Home Assistant Community thread ("Trouble with Everything presence lite") describes occupancy sometimes reporting "clear" while a person stands right in front of the unit; other community reports describe frequent false triggers from tiny movements, requiring users to drop LD2450 sensitivity (e.g. to level 5) to calm it down. The manufacturer's own troubleshooting/tuning guide acknowledges this and dedicates a page to sensitivity calibration — i.e. the same per-room mmWave tuning burden WiFi Sense's builder would also face with a bare LD2450.

Sources: [shop.everythingsmart.io product page](https://shop.everythingsmart.io/products/everything-presence-lite) · [Hardware overview docs](https://everythingsmarthome.github.io/everything-presence-lite/hardware-overview.html) · [GitHub repo](https://github.com/EverythingSmartHome/everything-presence-lite) · [HA Community: "Trouble with Everything presence lite"](https://community.home-assistant.io/t/trouble-with-everything-presence-lite/760627) · [Troubleshooting/tuning guide](https://everythingsmarthome.github.io/everything-presence-lite/troubleshooting.html) · [CNX Software coverage](https://www.cnx-software.com/2025/05/08/everything-presence-lite-esp32-based-mmwave-presence-sensor-tracks-up-to-three-targets-simultaneously/)

## Everything Presence One

**Price:** £47 GBP (~€55) direct, sometimes listed around $65 USD (shop.everythingsmart.io).

**Sensor tech:** DFRobot SEN0609 24GHz mmWave module (25 m range, 100°×40° detection — wider and longer-range than the LD2450 used in the Lite and in WiFi Sense) fused with a Panasonic industrial-grade PIR (12 m range), plus an SHTC3 temperature/humidity sensor and a BH1750 ambient-light sensor. ESP32-based, ships preloaded with ESPHome.

**What it outputs:** Fused motion/presence booleans (mmWave + PIR agreement logic), temperature, humidity, light level, and Bluetooth-proxy scanning. Unlike the Lite, the One's documentation does not advertise per-target x/y coordinate tracking — the SEN0609 is oriented toward wide-area zone presence rather than the LD2450's individual multi-target position output. So the One trades away the Lite's (and WiFi Sense's) coordinate tracking in exchange for PIR fusion, longer range, and more environmental sensors.

**Hub/cloud:** No cloud/subscription; runs local ESPHome firmware exactly like the Lite. Home Assistant is the primary intended consumer; a beta Samsung SmartThings driver also exists.

**Ecosystem:** Home Assistant-first, beta SmartThings support, and being a bare ESP32 it can be reflashed with Tasmota/Arduino/other custom firmware.

**Visual map UI:** None. No zone-drawing or radar-style view comparable to the Lite's zone editor is offered — it surfaces as a set of discrete HA sensor/binary_sensor entities (motion, presence, temperature, humidity, illuminance), not a spatial view.

**Open source:** Yes — GitHub repo (`EverythingSmartHome/everything-presence-one`), ESPHome-based, user-reflashable.

**Reliability complaints:** GitHub issue "False positives · Issue #2" on the everything-presence-one repo documents users reporting spurious presence triggers, echoing the same sensitivity-tuning complaints seen on the Lite.

Sources: [shop.everythingsmart.io product page](https://shop.everythingsmart.io/products/everything-presence-one-kit) · [GitHub repo](https://github.com/EverythingSmartHome/everything-presence-one) · [GitHub Issue #2 "False positives"](https://github.com/EverythingSmartHome/everything-presence-one/issues/2)

## Aqara FP2

**Price:** ~$82.99 / £82.99 (roughly €75-85), frequently discounted to ~€55.

**Sensor tech:** 60GHz mmWave radar, mains/USB powered (wired — not battery).

**What it outputs:** The most capable consumer product in this comparison. Detects up to **5 targets** (Aqara notes 3 or fewer performs best), 120° field of view, ~19.5 ft wide × 26 ft deep, covering ~430 sq ft. The detection area can be subdivided into up to **30 zones / 320 cells**, and it also offers fall detection and sleep monitoring. Critically, the Aqara app shows a live **map view with person icons moving around** the configured floor plan — i.e. the commercial equivalent of WiFi Sense's radar dashboard already exists, polished, in a €75 product.

**Hub/cloud:** No Aqara hub required; connects over 2.4 GHz WiFi. Originally cloud-dependent, but a firmware update enabled local control, and it can run in Home Assistant without internet after initial setup. Setup still requires the Aqara app and a 2.4 GHz network.

**Ecosystem:** HomeKit, Alexa, Google Home, Home Assistant — the broadest support here.

**Open source:** No. Closed firmware, vendor app.

**Reliability:** Generally well reviewed for zone automation accuracy; the common complaints are setup fiddliness and that multi-person tracking degrades above ~3 people.

Sources: [Aqara product page](https://www.aqara.com/us/product/presence-sensor-fp2/) · [SmartHomeScene review](https://smarthomescene.com/reviews/aqara-fp2-human-presence-sensor-review/) · [MightyGadget review](https://mightygadget.com/aqara-presence-sensor-fp2-review/) · [Smart Home Field Guide 2026 comparison](https://smarthomefieldguide.com/blog/best-presence-sensor-2026/)

## Aqara FP300 / FP1E / FP1 (and other 2025-2026 Aqara presence sensors)

**FP300** (released Nov 2025): a 5-in-1 battery-powered sensor — 60GHz mmWave + PIR + temperature + humidity + light. Range 6 m, 120° FoV, Thread *and* Zigbee with Matter support, 2-3 year battery life. Notably it is **battery-powered**, which the FP2 and most mmWave sensors are not. It reports presence/occupancy, not per-person coordinates.

**FP1E**: the stripped-down model — no zoning, no light sensor, Zigbee 3.0 only, **requires an Aqara hub**, USB-powered, ~6 m coverage. Sale price seen at $29.99. Detects slight movements (static presence) but produces a simple occupancy boolean.

**Positioning note:** Aqara's line splits cleanly — FP2 for spatial/zone work, FP300 for convenient battery-powered whole-room presence, FP1E for cheap basic presence. Only the FP2 competes with WiFi Sense on position tracking.

Sources: [Aqara FP300 page](https://www.aqara.com/en/product/presence-multi-sensor-fp300/) · [HomeKit News FP300 launch](https://homekitnews.com/2025/11/12/aqaras-fp300-matter-over-thread-presence-sensor-available-now/) · [Trusted Reviews FP300](https://www.trustedreviews.com/reviews/aqara-presence-multi-sensor-fp300) · [Matter Alpha mmWave sensor guide](https://www.matteralpha.com/explainer/the-best-matter-compatible-mmwave-presence-sensors)

## SwitchBot, Sonoff and IKEA — the mainstream cheap tier

**Sonoff SNZB-06P** (~$15-18): 5.8GHz mmWave, Zigbee, requires a Zigbee bridge, 3 sensitivity levels, up to 4 m range. Detects moving *and* stationary people. **SNZB-06P24** (~$24.90) is the newer 24GHz revision. Output is a presence boolean — no coordinates, no zones.

**IKEA VALLHORN**: cheap PIR-based motion sensor, tightly bound to the IKEA/DIRIGERA ecosystem. Motion only, blind to static people — the classic PIR limitation WiFi Sense is designed around.

**SwitchBot** presence sensors: vendor-app-centric, occupancy boolean, cloud-linked by default.

Sources: [SmartHomeScene SNZB-06P teardown](https://smarthomescene.com/reviews/sonoff-presence-sensor-teardown-and-review-snzb-06p/) · [SmartHomeScene SNZB-06P24](https://smarthomescene.com/reviews/sonoff-senseguard-presence-sensor-snzb-06p24/) · [ITEAD product page](https://itead.cc/product/sonoff-zigbee-human-presence-sensor/)

## Generic Tuya/Zigbee mmWave sensors (AliExpress class, ~€15-25)

The cheapest route to local presence detection — cheaper than the Sonoff. Typically an LD2410-family module in a plastic case with Zigbee or WiFi. Output is an occupancy boolean plus a distance value; no multi-target coordinates. Quality and firmware vary wildly between batches (the same "firmware lottery" documented for bare Hi-Link modules in `RESEARCH-SENSORS.md`). Usable via Zigbee2MQTT or Tuya's cloud.

Source: [Best mmWave Presence Sensors for Home Assistant 2026](https://www.smarthomeexplorer.com/guides/best-mmwave-presence-sensors-home-assistant-2026)

## Screek and Apollo Automation — the ESPHome prosumer tier

**Apollo Automation MSR-2** ($37.99-57.99, ~€35-55): ESP32 + **HLK-LD2410B** 24GHz radar + LTR-390UV light/UV + DPS310 temp/pressure + optional SCD-40 CO2, plus Bluetooth proxy. Ships with ESPHome, fully open and reflashable, 30% smaller than the MSR-1. Note it uses the **LD2410B, not the LD2450** — so it does presence and distance, *not* multi-target x/y tracking. It competes with WiFi Sense on "is someone there", not on "where exactly".

**Screek** (screek.io): a small vendor building Home Assistant sensors from Hi-Link modules, and a useful source of commentary on new modules (their LD2460 write-up is cited in `RESEARCH-SENSORS.md`). Same ESPHome-first, open-firmware philosophy.

Sources: [Apollo MSR-2 product page](https://apolloautomation.com/products/msr-2) · [ESPHome Devices MSR-2 entry](https://devices.esphome.io/devices/apollo-automation-msr-2/) · [SmartHomeScene MSR-2 review](https://smarthomescene.com/reviews/apollo-msr-2-review-the-smallest-presence-sensor-ever-made/)

## What this means for WiFi Sense

**Where the commercial products are clearly better:**

1. **Aqara FP2 already does what WiFi Sense aims to do, better.** It tracks up to 5 people (vs 3), supports 30 zones, adds fall detection and sleep monitoring, and ships a polished app with a live person-on-a-map view. For €55-85 and twenty minutes of setup, a buyer gets a more capable product than this project will produce.
2. **Reliability and support.** These are tested products with firmware updates, warranties and support channels. A hand-built breadboard node has none of that.
3. **Everything Presence Lite (~€33) is the same LD2450 radar** in a designed enclosure with a zone editor, for less than the parts cost of building it badly.
4. **Ecosystem integration.** HomeKit/Alexa/Google/Matter support out of the box; WiFi Sense speaks only to itself.

**Where WiFi Sense genuinely differs:**

1. **No Home Assistant, no vendor app.** Every product above assumes either a vendor cloud/app or Home Assistant as the consumer. WiFi Sense is a standalone application that owns its own data end to end.
2. **The dashboard is the product, not an afterthought.** Even the Lite — same radar — has no live blip view; its x/y data exists as entities for automations. Building a purpose-made real-time radar display is the actual deliverable here.
3. **Full modifiability.** Closed products (FP2, Sonoff, SwitchBot, IKEA) cannot be changed. Even the open ones (Lite, MSR-2) are ESPHome configs feeding someone else's UI.
4. **The WiFi-CSI research layer.** No commercial presence sensor pairs a radar with a WiFi-sensing experiment using the radar as ground truth. That combination is outside every product in this category.

**Honest conclusion:** as a *product*, WiFi Sense is not competitive — the FP2 and Everything Presence Lite beat it on capability, reliability and price-per-effort. As a *learning project*, that is irrelevant. Understanding the full chain from UART frame parsing to canvas rendering is not something buying an FP2 provides, and the ability to explain and defend every layer is the actual deliverable.

