"""CSI processing and detection algorithms."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
from scipy.signal import butter, filtfilt, welch


class CSIProcessor:
    def __init__(self, sample_rate: float = 20.0) -> None:
        self.sample_rate = sample_rate
        self.presence_threshold = 0.001
        self.motion_threshold = 0.004

    # ── signal conditioning ──────────────────────────────────
    @staticmethod
    def _to_amplitude(csi: np.ndarray) -> np.ndarray:
        return np.abs(csi) if np.iscomplexobj(csi) else csi

    def _smooth(self, data: np.ndarray, cutoff: float = 0.15) -> np.ndarray:
        if len(data) < 15:
            return data
        try:
            b, a = butter(2, cutoff, btype="low")
            return filtfilt(b, a, data, axis=0)
        except Exception:
            return data

    # ── detection ────────────────────────────────────────────
    def detect_presence(self, amp: np.ndarray) -> Tuple[bool, float]:
        score = float(np.mean(np.var(amp, axis=0)))
        return score > self.presence_threshold, score

    def detect_motion(self, amp: np.ndarray) -> Tuple[float, np.ndarray]:
        if len(amp) < 2:
            return 0.0, np.zeros(amp.shape[1])
        diff = np.diff(amp, axis=0)
        per_sub = np.mean(np.abs(diff), axis=0)
        return float(np.mean(per_sub)), per_sub

    def count_persons(self, amp: np.ndarray, presence_score: float) -> int:
        if presence_score < self.presence_threshold:
            return 0
        try:
            centered = amp - np.mean(amp, axis=0)
            _, s, _ = np.linalg.svd(centered, full_matrices=False)
            ev = np.sort(s ** 2)[::-1]
            total = ev.sum() + 1e-12
            # Count components that each carry >8 % of variance.
            # In typical multipath environments each person creates ~2–3 such
            # components; dividing and rounding gives a reasonable person count.
            n_sig = int(np.sum(ev / total > 0.08))
            return max(1, min(round(n_sig / 2.5), 5))
        except Exception:
            return 1 if presence_score > self.motion_threshold else 0

    def classify_activity(self, amp: np.ndarray, presence_score: float) -> str:
        if presence_score < self.presence_threshold:
            return "empty"
        try:
            # Use the first PCA component as the dominant motion time-series.
            # Averaging across subcarriers cancels due to multipath phase diversity;
            # SVD picks out the single strongest coherent motion pattern instead.
            centered = amp - amp.mean(axis=0)
            U, s, _ = np.linalg.svd(centered, full_matrices=False)
            sig = U[:, 0] * s[0]
            sig -= sig.mean()

            nperseg = min(len(sig), 64)
            freqs, psd = welch(sig, fs=self.sample_rate, nperseg=nperseg)
            total = np.sum(psd) + 1e-12
            walk   = np.sum(psd[(freqs >= 0.5) & (freqs <= 3.0)]) / total
            breath = np.sum(psd[(freqs >= 0.1) & (freqs < 0.5)]) / total

            if walk > 0.45:
                return "walking"
            if breath > 0.25:
                if presence_score < self.motion_threshold * 0.8:
                    return "sleeping"
                return "present/breathing"
            if presence_score > self.motion_threshold:
                return "moving"
            return "stationary"
        except Exception:
            return "stationary"

    def compute_zones(self, per_sub: np.ndarray, n_zones: int = 4) -> list:
        n = len(per_sub)
        size = max(1, n // n_zones)
        zones = []
        for i in range(n_zones):
            seg = per_sub[i * size : (i + 1) * size]
            m = float(np.mean(seg)) if len(seg) > 0 else 0.0
            zones.append({"id": i, "motion": m, "active": m > self.motion_threshold * 0.5})
        return zones

    # ── main entry ───────────────────────────────────────────
    def analyze(self, csi_buffer: np.ndarray) -> Dict[str, Any]:
        raw = self._to_amplitude(csi_buffer)
        # Smoothed: low noise, used for presence + motion (stable variance)
        amp = self._smooth(raw)
        # Unsmoothed: preserves walking harmonics above 1.5 Hz for classification
        presence, presence_score = self.detect_presence(amp)
        motion_score, per_sub = self.detect_motion(amp)
        person_count = self.count_persons(amp, presence_score)
        activity = self.classify_activity(raw, presence_score)
        zones = self.compute_zones(per_sub)

        return {
            "presence": bool(presence),
            "presence_score": presence_score,
            "person_count": person_count,
            "activity": activity,
            "motion_score": motion_score,
            "zones": zones,
        }
