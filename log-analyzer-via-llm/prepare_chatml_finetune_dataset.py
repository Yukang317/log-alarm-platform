#!/usr/bin/env python3
"""
Build ChatML-style SFT dataset (JSONL) from:
  - data/ffmpeg_results.json
  - data/ffmpeg_logs/*.log

Each JSONL line is a single training sample:
{
  "messages": [
    {"role": "user", "message": "<log file content>"},
    {"role": "assistant", "message": "<json string with 4 fields>"}
  ]
}

No special tokens (e.g. "im_start") are included.
"""
# prepare_chatml_finetune_dataset.py  - ChatML格式微调数据集整理
# 数据集和结果：chatml_finetune_dataset.report.json 和 ffmpeg_results.json
#   nice_dataset.jsonl为复制件
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class BuildReport:
    total_results: int
    total_logs_on_disk: int
    samples_written: int
    missing_log_files: int
    empty_log_files: int
    duplicate_result_log_files: int
    results_without_log_file: int
    logs_not_referenced_by_results: int


def _read_text(path: Path) -> str:
    # utf-8-sig strips BOM if present; errors=replace keeps pipeline robust.
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.strip()


def _load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig", errors="strict")
    if text.startswith("\ufeff"):
        text = text[1:]
    return json.loads(text)


def _safe_psnr_value(item: Dict[str, Any]) -> float:
    # Support both "psnr_value" and historical "psnr".
    v = item.get("psnr_value", None)
    if v is None:
        v = item.get("psnr", None)
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _target_output_json_string(item: Dict[str, Any]) -> str:
    output = {
        "successful": bool(item.get("successful", False)),
        "psnr_value": _safe_psnr_value(item),
        "error_message": item.get("error_message", "") or "",
        "resolution_steps": item.get("resolution_steps", "") or "",
    }
    # Must be a JSON string in assistant message.
    return json.dumps(output, ensure_ascii=False, separators=(",", ":"))


def _iter_log_files(log_dir: Path) -> Iterable[Path]:
    # non-recursive by default; current dataset uses data/ffmpeg_logs/*.log
    yield from sorted(log_dir.glob("*.log"))


def build_dataset(
    results_path: Path,
    log_dir: Path,
    output_jsonl_path: Path,
    report_path: Optional[Path] = None,
) -> BuildReport:
    results = _load_json(results_path)
    if not isinstance(results, list):
        raise ValueError(f"Expected a JSON array in {results_path}, got {type(results).__name__}")

    logs_on_disk = {p.name for p in _iter_log_files(log_dir)}
    referenced_logs: Set[str] = set()

    missing_log_files = 0
    empty_log_files = 0
    duplicate_result_log_files = 0
    results_without_log_file = 0
    samples_written = 0

    seen_result_log_files: Set[str] = set()

    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl_path.open("w", encoding="utf-8") as out_f:
        for idx, item in enumerate(results):
            if not isinstance(item, dict):
                # Skip malformed entry.
                continue

            log_file = item.get("log_file")
            if not log_file or not isinstance(log_file, str):
                results_without_log_file += 1
                continue

            if log_file in seen_result_log_files:
                duplicate_result_log_files += 1
                # Keep the first occurrence; skip duplicates to avoid label conflicts.
                continue
            seen_result_log_files.add(log_file)

            referenced_logs.add(log_file)

            log_path = log_dir / log_file
            if not log_path.exists():
                missing_log_files += 1
                continue

            log_content = _read_text(log_path)
            if not log_content:
                empty_log_files += 1
                continue

            assistant_message = _target_output_json_string(item)
            sample = {
                "messages": [
                    # 这里有错误，应该是content，后续有脚本辅助转换了，在data/convert_message_to_content.py
                    {"role": "user", "message": log_content},
                    {"role": "assistant", "message": assistant_message},
                ]
            }
            out_f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            samples_written += 1

            if (idx + 1) % 1000 == 0:
                # Lightweight progress output.
                print(f"Processed {idx+1}/{len(results)} results, wrote {samples_written} samples...")

    logs_not_referenced_by_results = len(logs_on_disk - referenced_logs)
    report = BuildReport(
        total_results=len(results),
        total_logs_on_disk=len(logs_on_disk),
        samples_written=samples_written,
        missing_log_files=missing_log_files,
        empty_log_files=empty_log_files,
        duplicate_result_log_files=duplicate_result_log_files,
        results_without_log_file=results_without_log_file,
        logs_not_referenced_by_results=logs_not_referenced_by_results,
    )

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ChatML SFT JSONL dataset from ffmpeg logs/results.")
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project directory containing data/.",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=None,
        help="Path to ffmpeg_results.json (default: <project>/data/ffmpeg_results.json).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Directory containing .log files (default: <project>/data/ffmpeg_logs).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSONL path (default: <project>/data/chatml_finetune_dataset.jsonl).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional report JSON path (default: <project>/data/chatml_finetune_dataset.report.json).",
    )
    args = parser.parse_args()

    project_dir: Path = args.project_dir
    results_path = args.results or (project_dir / "data" / "ffmpeg_results.json")
    log_dir = args.log_dir or (project_dir / "data" / "ffmpeg_logs")
    output_path = args.output or (project_dir / "data" / "chatml_finetune_dataset.jsonl")
    report_path = args.report or (project_dir / "data" / "chatml_finetune_dataset.report.json")

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    if not log_dir.exists():
        raise FileNotFoundError(f"Log directory not found: {log_dir}")

    report = build_dataset(
        results_path=results_path,
        log_dir=log_dir,
        output_jsonl_path=output_path,
        report_path=report_path,
    )
    print("Done.")
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

