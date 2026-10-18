"""
Configuration dataclasses and tunable thresholds for Module 01.
All values are validated at runtime via Pydantic where possible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AudioConfig:
    """Immutable configuration for the entire ingestion → alignment pipeline."""

    target_sample_rate: int = 16_000
    target_channels: int = 1

    vad_threshold: float = 0.5
    min_silence_duration_ms: int = 400
    speech_pad_left_ms: int = 80
    speech_pad_right_ms: int = 120
    min_speech_duration_ms: int = 250

    max_chunk_duration_sec: float = 25.0
    min_chunk_duration_sec: float = 1.0

    whisper_model_size: str = "base"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 5
    temperature: float = 0.0
    condition_on_previous_text: bool = False
    language: Optional[str] = None

    target_lufs: float = -16.0
    true_peak_db: float = -1.5

    max_audio_duration_sec: float = 3600.0
    silence_merge_gap_ms: int = 100

    def resolve_device(self) -> str:
        if self.device != "auto":
            return self.device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"


DEFAULT_CONFIG = AudioConfig()
