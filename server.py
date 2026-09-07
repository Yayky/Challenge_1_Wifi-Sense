"""FastAPI backend — WebSocket hub + CSI ingestion pipeline."""

from __future__ import annotations

import asyncio
import json
import socket
import struct
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from csi_engine import CSIProcessor
from simulator import CSISimulator

app = FastAPI(title="WiFi Sense", docs_url=None, redoc_url=None)

# ── shared state ─────────────────────────────────────────────
_clients: List[WebSocket] = []
_processor = CSIProcessor()
_simulator: Optional[CSISimulator] = None
_csi_buf: List[np.ndarray] = []
_BUF_MAX = 200  # 10 s at 20 Hz — needed for reliable low-frequency (breathing) detection
_mode = "simulate"

_DASHBOARD = Path(__file__).with_name("dashboard.html")


# ── HTTP routes ───────────────────────────────────────────────
@app.get("/")
async def root():
    return HTMLResponse(_DASHBOARD.read_text())


@app.get("/api/status")
async def api_status():
    return {"mode": _mode, "clients": len(_clients), "buffer": len(_csi_buf)}


# ── WebSocket ─────────────────────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    _clients.append(ws)
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "set_scenario" and _simulator is not None:
                _simulator.set_scenario(msg.get("scenario", "one_person_sitting"))
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        if ws in _clients:
            _clients.remove(ws)


# ── broadcast + ingest ────────────────────────────────────────
async def _broadcast(payload: dict) -> None:
    dead = []
    for ws in _clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _clients:
            _clients.remove(ws)


# Quadrant centres used to place estimated radar blips when we only have
# zone-level motion energy (esp32 mode — no true positions available).
_ZONE_CENTERS = [(0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)]


def _zone_targets(zones: list) -> list:
    out = []
    for z in zones:
        if z.get("active"):
            cx, cy = _ZONE_CENTERS[z["id"] % 4]
            out.append(
                {"x": cx, "y": cy, "activity": "moving", "moving": True, "estimated": True}
            )
    return out


async def _ingest(frame: np.ndarray, targets: Optional[list] = None) -> None:
    _csi_buf.append(frame)
    if len(_csi_buf) > _BUF_MAX:
        _csi_buf.pop(0)
    if len(_csi_buf) < 10:
        return

    result = _processor.analyze(np.array(_csi_buf))
    if targets is None:
        # No ground truth (esp32 mode) → estimate blips from active zones.
        targets = _zone_targets(result["zones"])
    await _broadcast(
        {
            "ts": time.time(),
            "amplitude": frame.tolist(),
            "presence": result["presence"],
            "person_count": result["person_count"],
            "activity": result["activity"],
            "motion_score": result["motion_score"],
            "zones": result["zones"],
            "targets": targets,
            "mode": _mode,
        }
    )


# ── data-source loops ─────────────────────────────────────────
async def _simulate_loop() -> None:
    global _simulator
    _simulator = CSISimulator()
    while True:
        frame = _simulator.next_frame()        # ticks persons, then read positions
        await _ingest(frame, _simulator.targets())
        await asyncio.sleep(0.05)


async def _esp32_loop(udp_host: str, udp_port: int) -> None:
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((udp_host, udp_port))
    sock.setblocking(False)
    print(f"  Listening for ESP32 data → UDP {udp_host}:{udp_port}")

    while True:
        try:
            data = await loop.sock_recv(sock, 65536)
            frame = _parse_esp32(data)
            if frame is not None:
                await _ingest(frame)
        except BlockingIOError:
            await asyncio.sleep(0.001)
        except Exception as exc:
            print(f"  UDP error: {exc}")
            await asyncio.sleep(0.01)


def _parse_esp32(data: bytes) -> Optional[np.ndarray]:
    # JSON format: {"csi": [0.1, 0.4, ...]}
    try:
        msg = json.loads(data)
        if "csi" in msg:
            return np.array(msg["csi"], dtype=np.float32)
    except Exception:
        pass
    # Binary format: packed float32 array
    try:
        n = len(data) // 4
        if n > 4:
            return np.array(struct.unpack(f"{n}f", data[: n * 4]), dtype=np.float32)
    except Exception:
        pass
    return None


# ── entry point ───────────────────────────────────────────────
def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def serve(
    mode: str = "simulate",
    host: str = "0.0.0.0",
    port: int = 8000,
    udp_host: str = "0.0.0.0",
    udp_port: int = 5000,
) -> None:
    global _mode
    _mode = mode

    @app.on_event("startup")
    async def _startup():
        if mode == "simulate":
            asyncio.create_task(_simulate_loop())
        else:
            asyncio.create_task(_esp32_loop(udp_host, udp_port))

    local_ip = _get_local_ip()
    print("\n  WiFi Sense")
    print(f"  Mode     : {mode.upper()}")
    print(f"  PC       : http://localhost:{port}")
    print(f"  Phone    : http://{local_ip}:{port}")
    if mode == "esp32":
        print(f"  UDP      : {udp_host}:{udp_port}  ← point ESP32 here")
    print()

    uvicorn.run(app, host=host, port=port, log_level="warning")
