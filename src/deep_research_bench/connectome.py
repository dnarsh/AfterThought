"""Read the public FlyWire FAFB v783 neuron metadata snapshot.

Downloads happen only when ``query_neurons`` is called. This is metadata,
not connectivity, a live CAVE query, or a neural simulation. Data retains
FlyWire's CC BY-NC 4.0 terms; no dataset is bundled with the application.
"""

from __future__ import annotations

import csv
import gzip
import io
import math
import os
import tempfile
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterator
from urllib.request import Request, urlopen


SOURCE_URL = "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/neurons.csv.gz"
LICENSE_URL = "https://join.flywire.ai/guidelines"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "flywire"
MAX_COMPRESSED_BYTES = 4 * 1024 * 1024
MAX_DECODED_BYTES = 40 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
_CACHE_LOCK = threading.Lock()


class ConnectomeError(RuntimeError):
    """A safe, user-visible failure loading the fixed public snapshot."""


def _fetch_bytes() -> bytes:
    request = Request(SOURCE_URL, headers={"User-Agent": "DeepResearchBench/0.1"})
    with urlopen(request, timeout=15) as response:
        if response.geturl() != SOURCE_URL:
            raise ConnectomeError("The FlyWire metadata source changed. Retry later.")
        data = response.read(MAX_COMPRESSED_BYTES + 1)
    if len(data) > MAX_COMPRESSED_BYTES:
        raise ConnectomeError("The FlyWire metadata archive exceeds the download limit.")
    return data


def _bounded_lines(archive: bytes) -> Iterator[str]:
    total = 0
    with gzip.GzipFile(fileobj=io.BytesIO(archive), mode="rb") as stream:
        while True:
            line = stream.readline(MAX_LINE_BYTES + 1)
            if not line:
                return
            total += len(line)
            if len(line) > MAX_LINE_BYTES or total > MAX_DECODED_BYTES:
                raise ConnectomeError("The FlyWire metadata exceeds the decoded data limit.")
            yield line.decode("utf-8-sig" if total == len(line) else "utf-8")


def _rows(archive: bytes) -> Iterator[Dict[str, str]]:
    reader = csv.DictReader(_bounded_lines(archive))
    required = {"root_id", "group", "nt_type", "nt_type_score"}
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise ConnectomeError("The FlyWire metadata format is not supported.")
    for row in reader:
        if None in row or not row.get("root_id", "").isdigit():
            raise ConnectomeError("The FlyWire metadata contains an invalid neuron record.")
        if any(row.get(key) is None for key in required):
            raise ConnectomeError("The FlyWire metadata contains an incomplete neuron record.")
        yield row


def _archive():
    # One fixed filename and a serialized atomic write keep simultaneous requests
    # from publishing a partial download. The ignored cache contains public data.
    cache_file = DEFAULT_CACHE_DIR / "neurons-v783.csv.gz"
    with _CACHE_LOCK:
        if cache_file.exists():
            if cache_file.stat().st_size > MAX_COMPRESSED_BYTES:
                raise ConnectomeError("The cached FlyWire metadata exceeds the data limit.")
            return cache_file.read_bytes(), cache_file.stat().st_mtime
        archive = _fetch_bytes()
        # Validate the complete archive before making it reusable by later calls.
        count = sum(1 for _ in _rows(archive))
        if not count:
            raise ConnectomeError("The FlyWire metadata contains no neuron records.")
        DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=str(DEFAULT_CACHE_DIR), prefix=".neurons-", delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(archive)
            os.replace(str(temporary), str(cache_file))
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        return archive, cache_file.stat().st_mtime


def query_neurons(q: str = "", transmitter: str = "", limit: int = 30) -> dict:
    """Filter actual metadata, returning IDs as strings to preserve 64-bit values.

    ``q`` searches root ID, group, and predicted neurotransmitter. Transmitter
    counts describe the entire snapshot; ``matching_neurons`` applies the filters.
    """
    if not isinstance(q, str) or len(q) > 128:
        raise ValueError("The neuron query must contain at most 128 characters.")
    if not isinstance(transmitter, str) or len(transmitter) > 32:
        raise ValueError("The neurotransmitter filter is invalid.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("The neuron result limit must be an integer from 1 to 100.")
    query = q.strip().casefold()
    selected_transmitter = transmitter.strip().upper()
    try:
        archive, retrieved = _archive()
        counts = Counter()
        neurons = []
        total = 0
        matching = 0
        for row in _rows(archive):
            total += 1
            nt = row["nt_type"].strip().upper() or "UNKNOWN"
            counts[nt] += 1
            group = row["group"].strip()
            if selected_transmitter and nt != selected_transmitter:
                continue
            if query and query not in " ".join((row["root_id"], group, nt)).casefold():
                continue
            matching += 1
            if len(neurons) >= limit:
                continue
            raw_score = row["nt_type_score"].strip()
            confidence = float(raw_score) if raw_score else None
            if confidence is not None and (not math.isfinite(confidence) or not 0 <= confidence <= 1):
                raise ConnectomeError("The FlyWire metadata contains an invalid prediction score.")
            neurons.append({
                "id": row["root_id"],
                "label": group or row["root_id"],
                "group": group,
                "neurotransmitter": nt,
                "confidence": confidence,
            })
        return {
            "dataset": "FlyWire FAFB v783",
            "source_url": SOURCE_URL,
            "license_url": LICENSE_URL,
            "license": "CC BY-NC 4.0",
            "snapshot": True,
            "total_neurons": total,
            "matching_neurons": matching,
            "neurotransmitters": [
                {"name": name, "count": count}
                for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            ],
            "neurons": neurons,
            "retrieved_at": datetime.fromtimestamp(retrieved, timezone.utc).isoformat(),
        }
    except ConnectomeError:
        raise
    except (OSError, EOFError, UnicodeError, csv.Error, ValueError):
        raise ConnectomeError("FlyWire metadata is unavailable. Check your connection and retry.") from None
