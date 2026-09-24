# WiFi Sense — Verification and Validation

---

## 1. Test environment

| Item         | Value                                             |
| ------------ | ------------------------------------------------- |
| Room         | 5.0 × 4.0 m, sensor on the x=0 wall at y = 2.0 m |
| Node         | ESP32 + HLK-LD2450 + HLK-LD2412 + AM312 PIR       |
| Firmware     | `firmware/sensor-node.yaml`                     |
| Server       | `uvicorn server:app`, Python 3.11+              |
| Client       | Chrome / Firefox on PC; phone browser for FR7     |
| Ground truth | tape measure, floor marked at 0.5 m intervals     |
| Date of run  | **TODO**                                    |

> **TODO** — fill the date and note the firmware commit hash for each run, so a result can be traced back to a version of the code.

---

## 2. Acceptance criteria

The requirements need numbers before they can be tested. These are the thresholds I hold the product to; where PROJECT-INTRO is vaguer than this, this table is the stricter reading.

| Req  | Measurable criterion                                                                                                    |
| ---- | ----------------------------------------------------------------------------------------------------------------------- |
| FR1  | A person entering the room is reported present within 3 s, in 10 of 10 entries                                          |
| FR2  | Reported position is within 0.5 m of the tape-measured position, at 8 marked points; frames arrive at ≥5 Hz            |
| FR3  | A seated, motionless person stays counted for ≥5 minutes                                                               |
| FR4  | The state text matches the number of dots on the map at all times                                                       |
| FR5  | Zero dots appear for a person walking in the corridor behind the wall over a 5-minute run                               |
| FR6  | No camera or microphone exists anywhere in the product (inspection, not a test)                                         |
| FR7  | Dashboard loads on a phone outside the home network within 10 s; notification arrives within 30 s of an armed detection |
| NFR1 | Empty room, 8 hours: zero false presence events                                                                         |
| NFR2 | Dashboard latency (real movement → dot moves) under 1 s                                                                |

---

## 3. Verification tests — does it work correctly?

| No  | Test                                            | Instructions                                                                         | Result                                                                                                                                                                                    |
| --- | ----------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| V1  | Server starts and serves the dashboard          | 1.`uvicorn server:app` 2. open `http://localhost:8000` 3. page renders room grid | <br /> Works                                                                                                                                                                              |
| V2  | WebSocket connects and streams                  | 1. open dashboard 2. read Status line 3. watch console frames                        | Works                                                                                                                                                                                     |
| V3  | Simulator produces moving dots                  | 1. start with radar offline 2. observe dots 3. check Source line                     | Work                                                                                                                                                                                      |
| V4  | Node connects to the server                     | 1. power node 2. start server 3. read Radar line                                     | **TODO** — expect "sees no one" / "sees someone moving"                                                                                                                            |
| V5  | Coordinate transform is correct                 | 1. stand at marked point (2.0, 2.0) 2. read Position line                            | **TODO** — expect 2.0 ± 0.5, 2.0 ± 0.5                                                                                                                                           |
| V6  | Out-of-room points are rejected                 | 1. hold a reflector beyond the wall 2. check no dot appears                          | **TODO**                                                                                                                                                                            |
| V7  | Hold timer in room centre                       | 1. person stands mid-room 2. cover/stop detection 3. watch dot                       | **TODO** — expect yellow dot with counter, removed at 300 s                                                                                                                        |
| V8  | Hold timer in door zone                         | 1. walk into door zone 2. leave room                                                 | **TODO** — expect immediate removal, no yellow dot                                                                                                                                 |
| V9  | Hold timer in window zone                       | 1. stand in window zone 2. stop being detected                                       | **TODO** — expect yellow dot, removed at ~15 s                                                                                                                                     |
| V10 | Radar disconnect recovery                       | 1. running live 2. unplug node 3. wait 30 s 4. replug                                | **TODO** — expect "offline", fallback to simulator, reconnect within ~5 s                                                                                                          |
| V11 | Three targets tracked at once                   | 1. three people walk the room 2. count dots                                          | **TODO**                                                                                                                                                                            |
| V12 | Secrets are not in the repository               | `git ls-files firmware/`                                                           | **PASS** — only `sensor-node.yaml` is tracked; `secrets.yaml` is ignored                                                                                                       |
| V13 | `/status` and `/api/state` return real data | 1.`curl localhost:8000/api/state`                                                  | **FAIL** — returns the hard-coded placeholder `{"occupied": false, "people": 0, "source": "placeholder"}`. Expected: live state. Logged as R5 in [REALISATION.md](REALISATION.md) |
| V14 | Live radar path runs end to end                 | 1. start server with node online 2. walk the room                                    | **FAIL** — blocked by R1–R4 (syntax and scope errors in `radar.py`, `server.py`, `dashboard.html`)                                                                          |

---

## 4. Validation tests — is it the right product?

| No  | Requirement                                               | Validate                                                                                                  | Result                                                                                                                        |
| --- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| T1  | FR1 — detect that at least one person is present         | 1. start with empty room 2. walk in 3. read state text                                                    | **TODO** — expect "1 person" within 3 s                                                                                |
| T2  | FR2 — show each person's position on the map, ≥5×/s    | 1. stand on each of 8 floor marks 2. compare dot to tape measure 3. record error per point                | **TODO** — expect ≤0.5 m error at every point                                                                         |
| T3  | FR3 — a motionless person stays counted                  | 1. sit still in a chair 2. do not move for 6 minutes 3. watch dot and counter                             | **TODO** — expect the person never disappears                                                                          |
| T4  | FR4 — current state shown in text                        | 1. vary 0, 1, 2, 3 people 2. compare text against dots each time                                          | **TODO**                                                                                                                |
| T5  | FR5 — ignore movement outside the room                   | 1. have someone walk the corridor behind the wall for 5 min 2. count dots                                 | **TODO** — expect zero                                                                                                 |
| T6  | FR6 — no camera or microphone                            | 1. inspect the hardware 2. inspect the code for any image/audio handling                                  | **PASS** — the product contains a radar, a PIR and a microcontroller; no camera or microphone exists to be compromised |
| T7  | FR7 — viewable from the phone off-network + notification | 1. leave the house 2. open the dashboard over Tailscale 3. have someone enter the armed room              | **NOT RUN** — Tailscale not configured and notifications not implemented                                               |
| T8  | NFR1 — no false presence in an empty room                | 1. leave the house for 8 h with the server logging 2. review for any presence event                       | **TODO** — the fan and curtains are the suspects here                                                                  |
| T9  | NFR2 — the map keeps up with reality                     | 1. walk while a second person watches the screen 2. estimate lag                                          | **TODO** — expect under 1 s                                                                                            |
| T10 | Usable by someone who did not build it                    | 1. hand a housemate the dashboard 2. ask "is anyone in my room, and where?" 3. observe without explaining | **NOT RUN**                                                                                                             |

---

## 5. Test log

Each run gets a row. Keep failures, do not overwrite them — a fixed failure is better evidence than a test that was always green.

| Date       | Test | Result | What I changed                |
| ---------- | ---- | ------ | ----------------------------- |
| 2026-09-23 | V12  | PASS   | —                            |
| 2026-09-23 | V13  | FAIL   | logged as R5, not fixed yet   |
| 2026-09-23 | V14  | FAIL   | logged as R1–R4, fixing next |
|            |      |        |                               |

---

## 6. Evidence

| Evidence                             | File                                  | Covers              |
| ------------------------------------ | ------------------------------------- | ------------------- |
| First live-hardware demo recording   | `docs/first_real_life_demotest.mp4` | V4, V5 (informally) |
| Dashboard screenshots, simulator     | **TODO**                        | V3                  |
| Dashboard screenshots, live radar    | **TODO**                        | T1, T2              |
| Accuracy measurement photos or table | **TODO**                        | T2                  |
| Overnight empty-room log             | **TODO**                        | T8                  |
| Stakeholder / peer feedback notes    | **TODO**                        | T10                 |

---

## 7. Conclusion

> **TODO — write after the tests have actually run.** State per requirement whether it is met, which ones failed and what changed as a result, and what the product cannot yet do. An honest "FR7 is not met, here is why" is worth more here than a conclusion that quietly skips it.

What can already be said: the simulator path is a complete product end to end, and the live radar path is one debugging session away from testable. The requirements that are certainly not met yet are FR7 (remote access and notifications) and the multi-person half of FR3.
