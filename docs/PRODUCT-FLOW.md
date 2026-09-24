# WiFi Sense product flow

Based on the working tree on 17 September 2026, including uncommitted changes. The first chart describes the intended product. The second describes the code that exists now. Dashed boxes in the product chart indicate planned work; plain boxes show behavior already present in the simulator path.

## Intended product

Monitoring repeats until stopped. Empty, occupied, and notified are outcomes of one cycle, not the end of monitoring.

```mermaid
flowchart TD
    Start([Start WiFi Sense]) --> Boot[Start Python server and sensor node]
    Boot --> Input[LD2450 radar reads target positions<br/>ESP32 sends readings to server]
    Input --> Link{Fresh sensor data available?}
    Link -->|No| Unknown[Presence unknown: sensor or connection unavailable<br/>Recovery behavior still needs design]
    Unknown --> Retry[Restore connection and resume sensing]
    Retry --> Input
    Link -->|Yes| Filter[Convert positions to room coordinates<br/>Ignore detections outside room]
    Filter --> Evidence[Evaluate presence<br/>Optional PIR cross-check and later LD2412<br/>Fusion rules still need design]
    Evidence --> Seen{Person detected inside room?}
    Seen -->|Yes| Present[Update person positions<br/>Reset missing-target timer]
    Seen -->|No| Previous{Previously tracked person missing?}
    Previous -->|No| Empty[Show empty room]
    Previous -->|Yes| Zone{Last known location?}
    Zone -->|Door zone| Remove[Remove missing person]
    Zone -->|Window zone| Window[Keep last position for about 15 seconds]
    Zone -->|Elsewhere| Room[Keep last position for about 5 minutes]
    Window --> Expired{Hold expired?}
    Room --> Expired
    Expired -->|No| Held[Show yellow held dot and timer<br/>Presence inferred, not confirmed]
    Expired -->|Yes| Remove
    Remove --> Remain{Any detected or held people remain?}
    Remain -->|No| Empty
    Remain -->|Yes| Occupied[Show occupied room and count]
    Present --> Occupied
    Held --> Occupied
    Empty --> Quiet[No presence notification]
    Occupied --> Armed{System armed?}
    Armed -->|No| Quiet
    Armed -->|Yes| AlertRule{Presence meets notification rule?}
    AlertRule -->|No| Quiet
    AlertRule -->|Yes| Notify[Send notification through ntfy<br/>User can open dashboard through Tailscale]
    Notify --> Delivery{Notification delivered?}
    Delivery -->|Yes| Notified[User notified]
    Delivery -->|No| Failure[Notification not delivered<br/>Retry and failure reporting still need design]
    Quiet --> Continue{Keep monitoring?}
    Notified --> Continue
    Failure --> Continue
    Continue -->|Yes| Input
    Continue -->|No| Stop([Stop monitoring])

    classDef planned stroke:#64748b,stroke-width:2px,stroke-dasharray:5 5;
    class Boot,Input,Link,Unknown,Retry,Filter,Evidence,Remain,Armed,AlertRule,Notify,Delivery,Notified,Failure planned;
```

The notification rule is not implemented or fully specified. Decisions still needed include whether held presence can trigger an alert, what happens when arming an already occupied room, repeat-alert cooldown, and delivery retries. The chart identifies these decisions without claiming they already work. The same applies to connection recovery and combining sensor readings.

The hold durations above come from current code. Applying them independently to multiple people is future work. Removing a target means the software stops counting it; it does not prove the person left. No detection likewise does not prove the room is physically empty.

## Current implementation

```mermaid
flowchart TD
    Start([Start FastAPI server]) --> Open[Open dashboard on server PC]
    Open --> Connect{WebSocket connects?}
    Connect -->|No| Offline[No live frames<br/>On close, show disconnected]
    Connect -->|Yes| Init[Show live status<br/>Create simulator for this connection]
    Init --> Frame[Get next simulated frame]
    Frame --> HasPeople{Frame contains people?}
    HasPeople -->|Yes| Save[Remember FIRST person's position<br/>Reset hold counter<br/>Send all simulated people]
    HasPeople -->|No| Last{Saved position exists?}
    Last -->|No| Empty[Send empty people list]
    Last -->|Yes| Zone{Saved position in which zone?}
    Zone -->|Door| Zero[Hold limit: 0 frames]
    Zone -->|Window| Short[Hold limit: 150 frames]
    Zone -->|Elsewhere| Long[Hold limit: 3000 frames]
    Zero --> Limit{Held frames below limit?}
    Short --> Limit
    Long --> Limit
    Limit -->|Yes| Hold[Increment hold counter<br/>Send ONE held person at saved position]
    Limit -->|No| Clear[Clear saved position]
    Clear --> Empty
    Save --> Send[Send JSON over WebSocket]
    Hold --> Send
    Empty --> Send
    Send --> Draw[Dashboard redraws room and count<br/>Red dots: detected<br/>Yellow dot and timer: held<br/>Zero people: empty]
    Draw --> Wait[Wait 0.1 seconds]
    Wait --> Frame
    Send -.->|WebSocketDisconnect| Closed[Server ends this stream<br/>Browser shows disconnected<br/>Last displayed room state remains]
    Closed --> Reload[Reopen or reload dashboard to reconnect]
    Offline --> Reload
    Reload --> Connect
```

- The simulator supplies two mirrored positions when visible, followed by empty frames to mimic a stationary person disappearing. It initially moves for 100 frames, disappears for 50, then repeats 10 visible frames and 50 empty frames.
- Hold timing is frame-based: approximately 15 seconds at the window and 5 minutes elsewhere at the intended 10 updates per second. Actual elapsed time can be longer. A new nonempty frame resets the hold.
- Only the first person's position is remembered. If some people disappear while another remains, no per-person hold runs. If everyone disappears, only one held dot remains.
- Each dashboard connection starts its own simulator and hold state. There is no shared room state yet.
- `/status` always returns zero people. `/api/state` always returns an unoccupied placeholder. Neither endpoint supplies the dashboard's live state.
- The dashboard connects to `ws://localhost:8000/ws`. Remote phone access needs changes. There is no automatic browser reconnection or stale-data timeout; after disconnect, old dots can remain visible.
- Firmware config exposes a PIR input on GPIO27 and configures WiFi, an encrypted ESPHome API, and a fallback hotspot. It does not configure either radar, and the Python server does not consume its readings.
- There are no notifications, arm/disarm controls, room-boundary filtering, or CSI processing in the current application.

## Research branch

Planned WiFi-CSI research is separate from the product's alert decisions:

```mermaid
flowchart LR
    TX[ESP32 transmits WiFi] --> RX[Second ESP32 captures CSI]
    RX --> USB[USB serial to Python server]
    USB --> Analysis[Analyze signal changes for motion]
    Analysis --> Compare[Compare with radar reference data]
    Radar[Radar presence and positions] --> Compare
    Compare --> Results[Research graphs and accuracy results]
```

No CSI code exists in the current application. Other roadmap items, such as automatic arming and Raspberry Pi hosting, do not yet add implemented outcomes. Speculative extensions in the introduction have no defined control flow.

## Sources

- [Server and hold decisions](../server.py)
- [Simulator](../simulator.py)
- [Dashboard rendering and connection handling](../dashboard.html)
- [Sensor firmware configuration](../firmware/sensor-node.yaml)
- [Product requirements](PROJECT-INTRO.md)
- [Product plan and notification choices](../ai-docs-research/PLAN.md)

Where documentation and code disagree, the current-implementation chart follows code. For example, the introduction refers to a `main.py` entry point that is not present, and older planning text describes a different hold-release rule.
