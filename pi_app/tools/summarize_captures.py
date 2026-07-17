"""Summarize Checkpoint 4 capture manifests for evidence recording."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--latest", type=int, default=20)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    paths = sorted(args.root.glob("*/manifest.json"), key=lambda path: path.stat().st_mtime)[-args.latest :]
    manifests = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if len(manifests) != args.latest:
        raise SystemExit(f"expected {args.latest} manifests, found {len(manifests)}")
    series: dict[str, list[float]] = {}
    for manifest in manifests:
        node = manifest["node"]
        durations = dict(manifest["metrics"]["durations_ms"])
        durations["node_trigger_to_frame"] = (node["frame_ready_us"] - node["trigger_accepted_us"]) / 1000
        durations["node_acquisition"] = (node["frame_ready_us"] - node["acquisition_started_us"]) / 1000
        durations["jpeg_bytes"] = manifest["files"][0]["bytes"]
        samples = manifest["metrics"].get("resource_samples", [])
        if len(samples) >= 2 and "process_cpu_user_seconds" in samples[0]:
            cpu_start = samples[0]["process_cpu_user_seconds"] + samples[0]["process_cpu_system_seconds"]
            cpu_end = samples[-1]["process_cpu_user_seconds"] + samples[-1]["process_cpu_system_seconds"]
            durations["process_cpu_capture_to_payload_ms"] = (cpu_end - cpu_start) * 1000
            durations["process_peak_rss_bytes"] = max(sample["process_rss_bytes"] for sample in samples)
            durations["minimum_available_memory_bytes"] = min(sample["available_memory_bytes"] for sample in samples)
            durations["maximum_system_load_1m"] = max(sample["system_load_average_1m"] for sample in samples)
        for name, value in durations.items():
            series.setdefault(name, []).append(float(value))
    summary = {
        "capture_count": len(manifests),
        "first_capture_id": manifests[0]["capture_id"],
        "last_capture_id": manifests[-1]["capture_id"],
        "complete_count": sum(item["status"] == "complete" for item in manifests),
        "checksum_failure_count": sum(not item["metrics"]["integrity"]["checksum_ok"] for item in manifests),
        "error_count": sum(len(item.get("errors", [])) for item in manifests),
        "trigger_sources": dict(sorted(Counter(
            item.get("metrics", {}).get("trigger_source", "unknown") for item in manifests
        ).items())),
        "metrics": {
            name: {
                "median": round(statistics.median(values), 3),
                "p95": round(percentile(values, 0.95), 3),
                "maximum": round(max(values), 3),
                "minimum": round(min(values), 3),
            }
            for name, values in sorted(series.items())
        },
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
