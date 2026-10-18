"""Cognitive Voice Editor – Modules 01–04."""

from .pipeline import SessionOnePipeline, main as module01_main
from .prune_pipeline import CognitivePruningPipeline, main as module02_main
from .pacing_pipeline import PacingPipeline, main as module03_main
from .welding_pipeline import WeldingPipeline, main as module04_main
from .config import AudioConfig, DEFAULT_CONFIG
from .models import AudioManifest, SpeechSegment, WordTiming
from .pruning_models import PrunedTimelineManifest, PrunedSentence
from .pacing_models import PacedTimelineManifest, PacedSentenceNode
from .welding_models import WeldedTimelineManifest, AcousticSeam

__all__ = [
    "SessionOnePipeline",
    "CognitivePruningPipeline",
    "PacingPipeline",
    "WeldingPipeline",
    "module01_main",
    "module02_main",
    "module03_main",
    "module04_main",
    "AudioConfig",
    "DEFAULT_CONFIG",
    "AudioManifest",
    "PrunedTimelineManifest",
    "PacedTimelineManifest",
    "WeldedTimelineManifest",
]
__version__ = "4.0.0"
