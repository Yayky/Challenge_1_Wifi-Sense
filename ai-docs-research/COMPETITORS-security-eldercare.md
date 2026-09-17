# Competitive Landscape: Security/Intrusion & Elder-Care Monitoring vs. WiFi Sense

Research date: 2026-09-08

Scope: comparing commercial camera-based, PIR-based, radar-based, WiFi-CSI-based
security products, and elder-care fall-detection products against the "WiFi Sense"
DIY project (HLK-LD2450 24GHz mmWave radar + ESP32/ESPHome + self-hosted Python
dashboard over Tailscale, no camera).

## A. Home Security / Intrusion Detection

### A1. Cameras (Ring, Arlo, Eufy)

**Ring Indoor Cam**
- Hardware: ~$50 (Indoor Cam), Indoor Cam Plus ~$60 (seen discounted to $35).
- Subscription (required to view/save recordings): Ring Protect Basic $5.99/mo or $69.99/yr (1 camera; raised from $4.99/$59.99 Feb 2026); Plus (unlimited cameras) $12/mo or $119.99/yr; Protect Pro $19.99/mo adds professional monitoring + AI facial recognition.
- Cloud-only: no local storage option on base plan; footage lives on Amazon/Ring cloud. Camera is a literal camera in the room — the exact thing the student is avoiding.
- Detects: motion/video, person detection, works only in cameras' field of view; needs light or good IR night vision.
- Install: plug-in or battery, app pairing, trivial.
- Consumer-buyable: yes, mainstream retail.

**Arlo**
- Hardware: $39.99 (Essential Indoor 3rd gen) up to $249.99 (Wireless Floodlight 2K).
- Subscription: Secure Plus single-camera $7.99/mo; unlimited-camera plan $17.99/mo (60-day cloud storage, AI detection, facial recognition, activity zones). Total Security bundle adds 24/7 professional monitoring.
- Local storage alternative: pairing with an Arlo base station/SmartHub + USB drive avoids the monthly fee for recorded video (only on certain models; base station often a separate purchase).
- Same fundamental limits as Ring: it's a camera, needs line of sight/lighting, mostly cloud-oriented business model.

**Eufy**
- Hardware: cameras from ~$42.99 up to $179; HomeBase hub ~$149.
- Subscription: optional cloud plan ~$3.99/mo per camera; base local storage is free and default (footage stays on HomeBase, not vendor cloud) — most privacy-friendly of the three.
- Caveat: in 2022 security researchers found some Eufy streams accessible without authentication (reportedly patched since); still a device with a camera lens pointed at a room, which is the deployment the student explicitly rules out for his bedroom.
- 2026 note: previously-free cloud storage has been discontinued industry-wide; subscriptions now standard even for "budget" brands.

**Takeaway vs. WiFi Sense**: All three are optical cameras — reliable, well-supported, easy install, but (a) recurring cost, (b) cloud dependency for full features, (c) a lens in the room, which is precisely the privacy problem the student's radar-based project is designed to avoid.

Sources:
- https://www.safehome.org/home-security-cameras/ring/
- https://www.security.org/security-cameras/ring/
- https://goabode.com/blog/ring-alarm-subscription-required-2026-what-you-lose-without-paying-and-why-abode-costs-504-less-over-3-years/
- https://www.security.org/security-cameras/arlo/
- https://www.safewise.com/home-security-systems/arlo/plans/
- https://www.security.org/security-cameras/eufy/
- https://www.eufy.com/collections/local-storage-security-camera
- https://www.securitycompasshq.com/pricing/eufy

### A2. Alarm PIR sensors (Ring Alarm, SimpliSafe, Ajax, Verisure)

**Ring Alarm**: 5-piece DIY kit $199 (base station, 1 contact sensor, 1 PIR motion detector, keypad, range extender). PIR motion sensor range ~10 ft. Optional Protect Pro monitoring plan $19.99/mo for professional response.

**SimpliSafe**: Foundation kit $299 (base station, 3 contact sensors, 1 motion sensor, keypad). Individual PIR sensors ~$15 (vs. $25 for contact sensors). Motion sensor range ~30 ft (longer than Ring's).

**Ajax Systems** (prosumer/EU): MotionProtect (PIR, pet-immune), MotionProtect Plus (dual PIR + microwave to cut false alarms), MotionProtect Curtain, MotionProtect Outdoor, MotionCam (PIR + photo verification on alarm). Positioned above Ring/SimpliSafe — professional installer channel, per-device pricing not publicly listed in most markets (sold through integrators).

**Verisure** (UK/EU, professionally monitored): ~£32/month monitoring fee (varies by property/sensor count), 12-month minimum contract (often 3-year), hardware/install cost £199–£1200 depending on complexity. Includes 24/7 SSAIB-certified monitoring, 4G backup, real-time camera streaming, equipment warranty. Premium, fully-managed, non-DIY.

**The core PIR weakness (directly relevant to WiFi Sense's design rationale)**: PIR sensors detect *change* in infrared radiation, not the presence of heat itself. A person sitting or lying still emits a steady IR signature with nothing to trigger detection — so PIR-based systems produce false negatives for stationary occupants. This is a well-documented security vulnerability (a motionless intruder, or in the elder-care context, a person collapsed on the floor, can go undetected). Researchers have built "motion-induced PIR" (mounting the PIR on a slowly rotating platform) specifically to work around this. mmWave radar (as used by WiFi Sense) does not share this weakness — it detects micro-motion like breathing/chest movement even from a stationary body, which is a genuine and correctly-identified technical advantage of the student's sensor choice.

### A3. Radar-based consumer/prosumer intrusion products

mmWave presence sensors have become a mainstream smart-home category, largely overlapping the LD2450/LD2412-class radar module WiFi Sense uses:

- **Aqara Presence Sensor FP2** — closest commercial analog to the DIY project. 24GHz mmWave, wired (mains-powered), $57.99–£99.99 RRP. Zone positioning (up to 30 zones, monitors rooms up to 40 m² — close to the student's 20 m² studio), multi-person tracking, **fall detection (>98% claimed accuracy)**, sleep monitoring. Runs automations locally without cloud round-trip; works with HomeKit/Alexa/Google Home/Home Assistant. No camera. This is essentially a polished, productized version of what the LD2450 + ESPHome setup does by hand.
- **Linptech ES1** — budget Zigbee mmWave presence sensor, $33.99, Zigbee2MQTT-compatible, less capable (no zone/fall detection).
- **Raw radar modules** (LD2412, LD2450, HLK-series, waveshare HMMD) — the same component tier the student is building on; sold as bare modules for makers/OEMs, not as a finished consumer security product.
- No major mainstream security brand (Ring/SimpliSafe/ADT/Verisure) currently ships a standalone mmWave *intrusion* product marketed for perimeter/room security the way they ship PIR — mmWave in the security-brand catalogs is still niche/emerging. The mmWave presence-sensor category is dominated by smart-home/DIY-adjacent brands (Aqara, Linptech, Everything Presence) rather than classic alarm companies.

Sources:
- https://www.safehome.org/security-systems/ring-alarm/
- https://www.security.org/home-security-systems/ring-alarm-vs-simplisafe/
- https://ajax.systems/groups/motion-detectors/
- https://ajax.systems/products/motionprotectplus/
- https://www.verisure.co.uk/advice-and-help/frequently-asked-questions/how-much-does-a-verisure-alarm-cost
- https://www.home-security-solutions.com/verisure-alarm-cost
- https://nami.ai/blog/pir-sensors-passive-infrared-sensors/
- https://www.butlr.com/blog/common-problems-pir-sensors
- https://www.researchgate.net/publication/338375555_A_Motion_Induced_Passive_Infrared_PIR_Sensor_for_Stationary_Human_Occupancy_Detection
- https://us.aqara.com/products/presence-sensor-fp2
- https://mightygadget.com/aqara-presence-sensor-fp2-review/
- https://www.linknlink.com/blogs/guides/best-mmwave-presence-sensors-home-assistant-2026

### A4. WiFi sensing productised (Origin Wireless/WiFi Motion, Cognitive Systems,
### Amazon eero, Xfinity WiFi Motion)

**This is the key finding of the research**: the WiFi-CSI sensing layer the student is experimenting with as a "research layer" is *not* a novel idea — it is already a mature, commercially deployed, multi-million-home product category, sold by ISPs as a router feature, not a gadget you buy separately.

**Origin Wireless (Origin AI)**
- Provides the underlying WiFi-sensing software stack licensed to carriers. Works by having the router ping selected *stationary* WiFi devices already in the home (smart plugs, TVs, thermostats — not phones/wearables) and extracting Channel State Information (CSI) from the response to build "sensing links" that act as invisible motion detectors throughout the home.
- **Verizon Fios** ships this as "Home Awareness" on newer Fios routers — the first Tier-1 US ISP to ship WiFi sensing as a built-in feature, with Origin as the technology provider.
- Business model: B2B — Origin licenses the tech to ISPs/router vendors; consumers don't buy an "Origin Wireless" product directly, they get it bundled into ISP routers/plans.

**Cognitive Systems Corp (WiFi Motion / Aura)**
- Founded 2014. Its "WiFi Motion" product is licensed to and installed by **120+ ISPs**, deployed in roughly **1 million homes** since Jan 2020.
- **Elder-care angle is explicit and productised**: partnered with **Electronic Caregiver, Inc.** in 2024 to offer AI-based ambient-assisted-living sensing via WiFi Motion to the 50M+ older adults in the US — i.e., a commercial company already sells exactly the "notify family if grandma hasn't moved" use case the student's own project could extend to, using the same underlying CSI technique.
- Also markets a general "Aura Home Security" positioning: detect movement/occupancy without a camera, no additional device purchase (uses existing mesh WiFi devices).

**Amazon eero**
- No strong evidence found that eero ships a shipped, marketed "built-in motion detection" consumer feature as of Sept 2026 (search turned up only third-party WiFi/mmWave presence sensors sold on Amazon, and Ring Alarm Pro's base station which *contains* an eero router but relies on separate PIR/contact sensors, not router-CSI sensing). Amazon/eero has filed patents and discussed WiFi-sensing R&D, but it doesn't appear to be a shipped headline feature the way Xfinity's is. Treat as "watch this space" rather than a shipped competitor.

**Xfinity WiFi Motion (Comcast)**
- Turns the radio link between the Xfinity Gateway and *stationary* WiFi devices (thermostats, smart speakers — explicitly not phones/wearables) into virtual motion sensors; movement through the home perturbs the RF signal.
- As of August 18, 2026, folded into a new bundle called **"Xfinity Shield"** — free for Xfinity Internet customers with a compatible gateway (XB7+), no extra device purchase, no subscription fee beyond internet service.
- Underlying enabling hardware/standard: chips like Infineon's AIROC ACW741x (WiFi 7 IoT, announced Jan 2026) and Qualcomm Dragonwing advertise native 802.11bf sensing-via-CSI support — i.e., CSI sensing is becoming a checkbox feature baked into commodity WiFi chipsets, not a research curiosity.
- **Privacy controversy (highly relevant to why the student avoids cloud/camera)**: reporting from Aug 2026 (Cybernews, TechTimes, Tom's Guide) flagged that Comcast's terms let it disclose the timestamped household-movement log to law enforcement or in litigation **without notifying the subscriber**, and that turning the feature off does not delete previously collected motion logs. Comcast was also the subject of a 2023 breach affecting 35.8M customers, compounding trust concerns. This is a concrete, current real-world illustration of the exact cloud/subscription/data-ownership risk the student's fully self-hosted, Tailscale-only architecture is structurally immune to.

**The underlying standard: IEEE 802.11bf ("Wi-Fi Sensing")**
- Approved 2024. Standardizes CSI acquisition at the MAC layer (both passive, using ambient traffic, and active, using dedicated sensing packets), replacing the proprietary CSI-extraction hacks (research code, monitor-mode capture) that hobbyists have used until now.
- Large-scale field data (a 10M+ router deployment) reports ~92.6% motion-detection accuracy with false-alarm rate reduced from 63.1% to 8.4%, and <0.3% network overhead from CSI transmission — evidence this is a solved-enough problem for entire-ISP-fleet deployment.
- **Known limitation directly relevant to the project**: CSI/WiFi-sensing models are highly room-specific — multipath propagation depends on wall materials, furniture, and geometry, so a model trained in one room generally cannot be reused in another without retraining. This matches the "research layer" framing: WiFi-CSI is a per-room calibration problem, not a plug-and-play universal sensor, which is exactly why productised versions (Xfinity, Cognitive Systems) restrict themselves to coarse motion/occupancy signals rather than precise x/y tracking, and why the student is using dedicated mmWave radar (LD2450) for the reliable, precise tracking rather than trying to make WiFi-CSI carry that load.

**Summary for A4**: WiFi-CSI "sense people through walls with just WiFi" is already shipping at ISP-fleet scale (Verizon, Comcast, 120+ ISPs via Cognitive Systems) including a real elder-care commercial partnership (Cognitive Systems x Electronic Caregiver). It ships bundled free with internet service rather than sold as a standalone product, detects only coarse motion/occupancy (not precise position), needs per-room-ish calibration, and comes with genuine privacy/data-retention/law-enforcement-disclosure baggage that a self-hosted DIY system does not have.

Sources:
- https://www.originwirelessai.com/wifi-sensing/
- https://wifinowglobal.com/news-and-blog/verizon-fios-launches-wi-fi-sensing-service-powered-by-origin/
- https://www.cognitivesystems.com/wifi-motion-by-cognitive-systems/
- https://www.prnewswire.com/news-releases/electronic-caregiver-inc-partners-with-cognitive-systems-corp-to-offer-ai-based-ambient-assisted-living-sensing-via-wifi-motion-to-the-50-million-older-adults-across-the-united-states-302137011.html
- https://www.pcworld.com/article/3215845/xfinity-routers-can-now-sense-movement-in-your-home-without-cameras.html
- https://www.theregister.com/security/2026/08/19/comcast-gives-its-wi-fi-motion-detector-a-security-makeover/5289572
- https://cybernews.com/privacy/comcast-xfinity-shield-routers-motion-sensors/
- https://www.techtimes.com/articles/324930/20260819/xfinity-shields-free-wi-fi-motion-logs-movements-police-can-subpoena-without-telling-you.htm
- https://arxiv.org/html/2507.22591v1
- https://secnora.com/blog/wi-fi-sensing-and-the-ieee-802-11bf-privacy-gap/

## B. Elderly Care / Fall Detection

### B1. Vayyar Care / Vayyar Home

- Technology: 4D imaging mmWave radar, whole-room field of view, works in all lighting and even through steam (marketed for bathrooms, where ~80% of falls occur), no camera, no wearable.
- Claims 4x more accurate fall detection than other automatic alert systems; also produces breathing/health analytics and location/activity data, not just binary fall alerts.
- **Consumer pricing**: ~$240 hardware (Amazon), required **Alexa Together subscription $19.99/month** to function (fall detection exclusively via Alexa Together per Vayyar's own docs), +$20/month more for emergency-services dispatch. So real all-in cost is roughly $240 upfront + ~$20–40/month forever.
- **B2B/senior-living model**: "Vayyar Home" sold to senior-living operators/care communities (partnership with K4Connect) as a passive, low-cost resident-safety tool to reduce staff burden — install-once, monitor-many business model, different economics than the consumer SKU.
- Consumer-buyable: yes, on Amazon, US customers only as of this research.

### B2. Tellus / Cherish Serenity / other radar wellness monitors

- No product literally named "Tellus" was found; closest matches are **TELUS Health** (Canadian telco) medical alert systems (from $35/month, non-radar wearable-pendant style) and radar fall-sensor vendors like **Milesight VS373** (60GHz mmWave, LoRaWAN, claims 99% fall-detection accuracy, industrial/IoT B2B sensor rather than consumer product) and **Essence MDsense** (radar-based indoor fall detector, sold through security dealer channels).
- **Cherish Serenity** (Cherish Health, launched CES Jan 2024, partnered with **AT&T**): whole-home radar coverage using AI to build a live 13-point skeleton model of each person to distinguish an intentional lie-down from an actual fall (including slow falls that accelerometer-based pendants miss); also monitors resting heart rate and respiration remotely, no camera, no wearable. Price ~$250–300 hardware + **$39/month subscription**. Distributed via **Alarm.com**'s dealer network, including **ADT** — i.e., sold through the same channel as traditional home-security systems, not as a standalone gadget.
- **Zoe Care** (adjacent, WiFi-CSI rather than radar, worth noting as it directly parallels the student's WiFi-CSI research layer): a smart-plug-form-factor device that analyzes ambient WiFi signal *shape* (not content) to detect falls across ~800 sq ft in care homes, no hardware cost, $20–25/month subscription, explicitly all local processing / nothing sent to the cloud except the alert itself. This is essentially a commercial, subscription-wrapped version of exactly the WiFi-CSI fall/motion detection the student is prototyping — further confirming WiFi-CSI-for-elder-care is already a funded, shipping product category, not just an ISP motion-sensing gimmick.

### B3. Wearables: Apple Watch fall detection & Lifeline pendants

- **Apple Watch** (SE and later, Series 4+, Ultra): built-in fall detection using accelerometer (impact spike) + gyroscope (wrist orientation/motion type); free, bundled into the watch. If immobile ~60 seconds after a detected hard fall, it auto-dials emergency services and shares GPS location.
- **Core weakness (must be worn/charged)**: battery life is only 18–24 hours, requiring nightly charging — exactly the window (sleeping, showering, changing) when the watch is most likely to be off the wrist or on the charger, and the times falls are common for elderly users. It also mainly catches *hard/high-impact* falls, missing gradual slips or falls from seated/kneeling positions, and can false-trigger on vigorous activity. A loose band also degrades detection accuracy.
- **Philips Lifeline** (pendant/wearable alert button): HomeSafe (in-home base unit) from $34.95/month; On-the-Go (cellular mobile pendant) $44.95–$49.95/month; **automatic fall detection add-on is a further $15/month**; $99.95 one-time activation fee (waived promos vary); plus shipping. All-in first-year cost easily exceeds $500–700. Same wearable weakness as Apple Watch: must be worn and charged/maintained (many elderly users forget to wear the pendant, especially in the bathroom/shower — the highest-fall-risk room — precisely where Vayyar/Cherish/radar-based systems target as their selling point).
- **Structural takeaway**: the wearable category is the most mature/certified (direct 911 dispatch, dedicated cellular hardware) but has the well-known adherence problem — it only helps if the person remembers to wear/charge it, which is a known failure mode driving the entire ambient-sensing (radar/WiFi-CSI/camera) product category discussed above.

Sources:
- https://www.amazon.com/Vayyar-Care-Touchless-Detection-Subscription/dp/B09JXV82Z6
- https://vayyar.com/care-docs/b2c/
- https://www.k4connect.com/k4connect-and-vayyar-care-partner-to-bring-next-level-radar-fall-detection-technology-to-the-senior-living-industry/
- https://www.milesight.com/iot/product/lorawan-sensor/vs373
- https://finance.yahoo.com/news/serenity-takes-full-home-radar-164255051.html
- https://medcitynews.com/2024/01/fall-detection-ai-home/
- https://techcrunch.com/2024/01/10/zoe-care-zoe-fall/
- https://support.apple.com/en-vn/HT208944
- https://www.ageinplaceguide.com/blog/apple-watch-fall-detection-seniors
- https://www.safehome.org/medical-alert-systems/philips-lifeline/
- https://www.caring.com/senior-products/best-medical-alert-systems/philips-lifeline

## Comparison Table

| Product / category | Upfront | Subscription | Tech | Detects | Privacy posture | Consumer-buyable |
|---|---|---|---|---|---|---|
| **WiFi Sense** (this project) | ~€25 parts | none | 24GHz radar (LD2450) + PIR | per-person x/y position, presence | No camera, no cloud, self-hosted, VPN-only access | Must be built |
| Ring Indoor Cam | ~$50 | $5.99–19.99/mo | camera | video, person detection | Camera in room; cloud-only storage on base plan | Yes |
| Arlo | $40–250 | $7.99–17.99/mo | camera | video, AI detection, zones | Camera; cloud-oriented, local via extra base station | Yes |
| Eufy | $43–179 (+$149 hub) | optional ~$3.99/mo | camera | video | Camera, but free local storage default — most private of the three | Yes |
| Alarm PIR sensors (Ring/SimpliSafe/Ajax/Verisure) | varies | varies | PIR | motion only | No camera | Yes |
| Xfinity WiFi Motion / "Shield" | €0 (bundled) | free w/ internet | **WiFi CSI** | coarse whole-home motion | Movement logs retained; disclosable to law enforcement without notice | ISP customers only |
| Verizon "Home Awareness" (Origin) | €0 (bundled) | bundled | **WiFi CSI** | coarse motion | ISP-held data | ISP customers only |
| Cognitive Systems WiFi Motion | €0 (bundled) | via ISP | **WiFi CSI** | motion, eldercare monitoring | ISP/vendor-held | Via 120+ ISPs |
| Vayyar Care | ~$240 | $19.99–39.99/mo | 4D mmWave radar | falls, breathing, location | No camera, no wearable; vendor cloud | Yes (US) |
| Cherish Serenity | ~$250–300 | $39/mo | mmWave radar + AI skeleton model | falls incl. slow falls, heart rate, respiration | No camera; vendor cloud | Via ADT/Alarm.com dealers |
| Zoe Care | €0 hardware | $20–25/mo | **WiFi CSI** | falls across ~800 sq ft | Local processing, only alerts leave | Care-home channel |
| Apple Watch | watch price | none | accelerometer + gyro | hard falls | On-device | Yes |
| Philips Lifeline | $99.95 activation | $34.95–64.95/mo | pendant + base | button press, optional auto-fall | On-device | Yes |

## Where WiFi Sense Sits

**Honest positioning, three points:**

**1. The commercial products are more reliable, supported and certified.** Vayyar and Cherish have tuned radar algorithms, warranties, and in some cases direct emergency dispatch. Ring and Arlo have mature apps and firmware pipelines. A student-built breadboard node on an ESP32 has none of that, and should not be presented as an alternative to a medical-alert system.

**2. WiFi-CSI sensing is already commercially deployed — the research layer is a reimplementation, not an invention.** This is the most important finding in this document and it should be stated plainly in the project report. Cognitive Systems' WiFi Motion runs in ~1 million homes via 120+ ISPs. Verizon Fios ships "Home Awareness" powered by Origin Wireless. Comcast bundles WiFi Motion into "Xfinity Shield" free for compatible-gateway customers. Zoe Care sells WiFi-CSI fall detection to care homes on subscription. IEEE 802.11bf was approved in 2024, and chipsets like Infineon's AIROC ACW741x and Qualcomm Dragonwing now advertise native CSI-sensing support — WiFi sensing is becoming a commodity chipset checkbox, not a research frontier.

  That is *fine*, and worth saying explicitly: the student is reimplementing a productised technique on €10 of hardware in order to understand it. Reproducing known results is a legitimate and normal way to learn, and being able to name the commercial state of the art is itself evidence of good research.

  It also validates a design decision already made: the productised versions restrict themselves to **coarse motion/occupancy**, not precise position, because CSI models are room-specific and multipath-dependent. That is exactly why this project uses mmWave radar for reliable tracking and treats CSI as the experimental layer rather than the load-bearing one.

**3. What a DIY system genuinely offers.** No subscription — the commercial ambient-sensing products cost $20–40/month indefinitely, which over three years exceeds €700–1400 against this project's ~€25. No cloud dependency and no vendor that can change terms, discontinue a service or be breached. Full data ownership: the Comcast case is a concrete, current illustration — reporting in August 2026 flagged that household movement logs could be disclosed to law enforcement without notifying the subscriber, and that disabling the feature does not delete logs already collected. A self-hosted system reachable only over a private VPN is structurally immune to that class of problem, not because of a privacy policy but because the data never leaves the owner's machine. And it is completely modifiable, which no closed product is.

**Where it does not compete:** as a security product (no professional monitoring, no certified dispatch, no tamper resistance) or as a medical-alert product (no fall detection, no emergency response). Those should be explicitly out of scope in the report.
