#!/usr/bin/env python3
"""
Cognitive Voice Editor – One-Click Full Pipeline
=================================================
Raw mumbled / retake-heavy recording  →  clean natural voice track

Usage (simplest):
    python run_full_pipeline.py --input your_raw_audio.wav

Optional:
    python run_full_pipeline.py -i raw.wav -o clean.wav --language ur --api_key YOUR_GEMINI_KEY
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("full_pipeline")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cognitive Voice Editor – Full automatic clean-up pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", "-i", required=True, type=Path, help="Your raw recording")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Final clean WAV path")
    parser.add_argument("--work_dir", type=Path, default=None, help="Intermediate JSON folder")
    parser.add_argument("--language", "-l", default=None, help="Language code: en, ur, hi, ar")
    parser.add_argument("--model_size", default="base", choices=["tiny", "base", "small", "medium"])
    parser.add_argument("--api_key", "-k", default=None, help="Gemini API key")
    parser.add_argument("--dry_run_prune", action="store_true", help="Skip Gemini")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.is_file():
        log.error("Input file not found: %s", input_path)
        sys.exit(1)

    output_path = args.output.resolve() if args.output else input_path.with_name(input_path.stem + "_clean.wav")
    work = args.work_dir or Path("pipeline_work")
    work.mkdir(parents=True, exist_ok=True)

    m01_json = work / "01_manifest.json"
    m02_json = work / "02_pruned.json"
    m03_json = work / "03_paced.json"
    m04_json = work / "04_welded.json"

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    dry_run = args.dry_run_prune or (api_key is None)

    if dry_run:
        log.warning("No Gemini API key → DRY-RUN prune mode (all sentences kept).")

    t_start = time.perf_counter()
    print("\n" + "=" * 64)
    print("  COGNITIVE VOICE EDITOR – FULL PIPELINE")
    print("=" * 64)
    print(f"  Input  : {input_path.name}")
    print(f"  Output : {output_path.name}")
    print(f"  Mode   : {'DRY-RUN' if dry_run else 'FULL'}")
    print("=" * 64 + "\n")

    log.info("MODULE 01  Ingestion + VAD + Word alignment …")
    from src.config import AudioConfig
    from src.pipeline import SessionOnePipeline
    cfg = AudioConfig(whisper_model_size=args.model_size, device=args.device, compute_type="int8", language=args.language)
    SessionOnePipeline(cfg).run(input_path, m01_json)

    log.info("MODULE 02  Cognitive pruning + Gravity …")
    from src.prune_pipeline import CognitivePruningPipeline
    CognitivePruningPipeline(api_key=api_key, dry_run=dry_run, model_name="gemini-2.5-flash").run(m01_json, m02_json)

    log.info("MODULE 03  Dynamic pacing …")
    from src.pacing_pipeline import PacingPipeline
    PacingPipeline().run(m02_json, m03_json)

    log.info("MODULE 04  Acoustic welding …")
    from src.welding_pipeline import WeldingPipeline
    WeldingPipeline().run(raw_audio_path=input_path, paced_manifest_path=m03_json, output_wav=output_path, output_manifest=m04_json)

    elapsed = time.perf_counter() - t_start
    print("\n" + "=" * 64)
    print("  DONE")
    print("=" * 64)
    print(f"  Clean audio  : {output_path}")
    print(f"  Total time   : {elapsed:.1f} s")
    if dry_run:
        print("  NOTE: No Gemini key → retakes NOT removed.")
        print("  Get key: https://aistudio.google.com/apikey")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
