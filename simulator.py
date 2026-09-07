"""Realistic CSI simulation — no hardware required for testing."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List

import numpy as np

_ACTIVITY_PARAMS = {
    "walking":    {"freq": 1.5,  "amp": 0.22},
    "breathing":  {"freq": 0.28, "amp": 0.07},
    "sleeping":   {"freq": 0.22, "amp": 0.04},   # slow deep breathing
    "stationary": {"freq": 0.04, "amp": 0.008},
}

_SCENARIOS: dict[str, list[dict]] = {
    "empty":              [],
    "one_person_sitting": [{"x": 0.5, "y": 0.5, "act": "breathing"}],
    "one_person_walking": [{"x": 0.5, "y": 0.5, "act": "walking"}],
    "two_people":         [{"x": 0.3, "y": 0.4, "act": "breathing"},
                           {"x": 0.7, "y": 0.6, "act": "walking"}],
    "sleeping":           [{"x": 0.5, "y": 0.5, "act": "sleeping"}],
}


@dataclass
class _Person:
    x: float
    y: float
    activity: str
    phase: float = field(default_factory=lambda: random.uniform(0, 2 * np.pi))
    vx: float = 0.0
    vy: float = 0.0

    def _new_heading(self) -> None:
        ang = random.uniform(0, 2 * np.pi)
        self.vx, self.vy = float(np.cos(ang)), float(np.sin(ang))

    def tick(self, dt: float) -> None:
        if self.activity == "walking":
            if self.vx == 0.0 and self.vy == 0.0:
                self._new_heading()
            if random.random() < 0.015:          # occasional turn
                self._new_heading()
            speed = 0.28                           # room-units / second
            self.x += self.vx * speed * dt
            self.y += self.vy * speed * dt
            # bounce off the room walls so the blip stays inside the house
            if self.x < 0.06 or self.x > 0.94:
                self.vx *= -1
                self.x = float(np.clip(self.x, 0.06, 0.94))
            if self.y < 0.06 or self.y > 0.94:
                self.vy *= -1
                self.y = float(np.clip(self.y, 0.06, 0.94))
            if random.random() < 0.0008:
                self.activity = random.choice(["stationary", "breathing"])
        elif self.activity in ("breathing", "sleeping"):
            # tiny sway so a "stationary" blip still feels alive
            self.x = float(np.clip(self.x + random.gauss(0, 0.0015), 0.05, 0.95))
            self.y = float(np.clip(self.y + random.gauss(0, 0.0015), 0.05, 0.95))
            if random.random() < 0.0008:
                self.activity = "walking"
                self._new_heading()
        else:  # stationary
            if random.random() < 0.001:
                self.activity = random.choice(["walking", "breathing"])
                if self.activity == "walking":
                    self._new_heading()


class CSISimulator:
    def __init__(self, n_subcarriers: int = 30, sample_rate: float = 20.0) -> None:
        self.n_sub = n_subcarriers
        self.sr = sample_rate
        self.dt = 1.0 / sample_rate
        self.t = 0.0
        self.noise = 0.007

        rng = np.random.default_rng(42)
        self._sub_phase = rng.uniform(0, 2 * np.pi, n_subcarriers)
        self._sub_sens = rng.uniform(0.6, 1.4, n_subcarriers)
        self._freq_spread = np.linspace(0.5, 3.5, n_subcarriers)

        self.persons: List[_Person] = [_Person(0.4, 0.5, "breathing")]

    def next_frame(self) -> np.ndarray:
        self.t += self.dt
        csi = np.full(self.n_sub, 0.48)

        for p in self.persons:
            p.tick(self.dt)
            params = _ACTIVITY_PARAMS[p.activity]
            path = np.sqrt(p.x ** 2 + p.y ** 2) * 2 * np.pi
            phase = self._sub_phase + path * self._freq_spread
            csi += params["amp"] * self._sub_sens * np.sin(
                2 * np.pi * params["freq"] * self.t + phase + p.phase
            )

        csi += np.random.normal(0, self.noise, self.n_sub)
        csi = np.clip(csi, 0, None)
        mx = csi.max()
        if mx > 0:
            csi /= mx
        return csi.astype(np.float32)

    def set_scenario(self, name: str) -> None:
        defs = _SCENARIOS.get(name, _SCENARIOS["one_person_sitting"])
        self.persons = [_Person(d["x"], d["y"], d["act"]) for d in defs]

    def targets(self) -> List[dict]:
        """Ground-truth person positions for the radar (simulate mode only)."""
        return [
            {
                "x": round(p.x, 4),
                "y": round(p.y, 4),
                "activity": p.activity,
                "moving": p.activity == "walking",
            }
            for p in self.persons
        ]
