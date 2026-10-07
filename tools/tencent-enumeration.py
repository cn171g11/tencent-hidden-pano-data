"""Run bounded, resumable public panorama identifier experiments."""

import argparse
import csv
import itertools
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)
ID_PATTERN = re.compile(r"^[0-9A-Z]{23}$")
CSV_FIELDS = ["id", "name", "scenic", "source", "type", "mode", "lng", "lat", "url"]


class RequestGate:
    def __init__(self, interval):
        self.interval = interval
        self.lock = threading.Lock()
        self.next_start = 0.0

    def wait(self):
        with self.lock:
            time.sleep(max(0, self.next_start - time.monotonic()))
            self.next_start = time.monotonic() + self.interval


def generate_candidates(plan):
    candidates = {}
    for batch in plan["batches"]:
        combinations = itertools.product(batch["regions"], batch["codes"], batch["dates"], batch["scenes"])
        for region, code, capture_date, scene in combinations:
            datetime.strptime(capture_date, "%y%m%d")
            identifier = f"{region}3{code}W0{capture_date}0SCENE{scene:03d}"
            if not ID_PATTERN.fullmatch(identifier):
                raise ValueError(f"Invalid generated identifier: {identifier}")
            candidates.setdefault(identifier, []).append(batch["label"])
    return candidates


def load_cache(journal):
    if not journal.exists():
        return {}
    with journal.open(encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    return {record["id"]: record for record in records}


def interpret_response(identifier, payload, url):
    detail = payload.get("detail") or {}
    basic = detail.get("basic") or {}
    address = detail.get("addr") or {}
    is_valid = payload.get("info", {}).get("errno") == 0 and basic.get("svid") == identifier
    status = "valid" if is_valid else "invalid"
    if not is_valid and payload.get("info", {}).get("errno") != -1:
        status = "unexpected"
    return {"id": identifier, "status": status, "name": basic.get("append_addr", ""),
            "scenic": basic.get("scenic_id", ""), "source": basic.get("source", ""),
            "type": basic.get("type", ""), "mode": basic.get("mode", ""),
            "lng": address.get("x_lng"), "lat": address.get("y_lat"), "url": url,
            "quit": basic.get("quit_svid", ""), "scene_ids": [entry["svid"] for entry in detail.get("all_scenes", [])],
            "payload": payload if is_valid or status == "unexpected" else payload.get("info")}


def fetch_candidate(identifier, settings, gate):
    query = urllib.parse.urlencode({"svid": identifier, "output": "json"})
    url = settings["endpoint"] + "?" + query
    gate.wait()
    try:
        with urllib.request.urlopen(url, timeout=settings["timeout_seconds"]) as response:
            payload = json.loads(response.read().decode("gb18030"))
        return interpret_response(identifier, payload, url)
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeError, ValueError) as error:
        return {"id": identifier, "status": "error", "url": url, "error": str(error)}


def export_summary(candidates, cache, output_prefix):
    records = [cache[identifier] for identifier in candidates if identifier in cache]
    valid = [record for record in records if record["status"] == "valid"]
    with output_prefix.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(valid)
    counts = {status: sum(record["status"] == status for record in records)
              for status in ("valid", "invalid", "error", "unexpected")}
    summary = {"planned": len(candidates), "observed": len(records), "counts": counts,
               "scenic_count": len({record["scenic"] for record in valid if record["scenic"]}),
               "by_batch": summarize_batches(candidates, cache),
               "hits": [{key: record.get(key) for key in CSV_FIELDS} for record in valid]}
    output_prefix.with_suffix(".json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    LOGGER.info("planned=%s observed=%s counts=%s", len(candidates), len(records), counts)


def summarize_batches(candidates, cache):
    counts = {}
    for identifier, labels in candidates.items():
        for label in labels:
            batch = counts.setdefault(label, {"planned": 0, "valid": 0, "invalid": 0, "error": 0, "unexpected": 0, "pending": 0})
            batch["planned"] += 1
            batch[cache.get(identifier, {}).get("status", "pending")] += 1
    return counts


def audit_records(candidates, cache):
    records = [cache[identifier] for identifier in candidates if identifier in cache]
    valid = [record for record in records if record["status"] == "valid"]
    for prefix in sorted({record["id"][:4] for record in valid}):
        region = [record for record in valid if record["id"].startswith(prefix)]
        LOGGER.info("region=%s ids=%s codes=%s", prefix, len(region), "".join(sorted({record["id"][5] for record in region})))
    LOGGER.info("sources=%s", sorted({record["source"] for record in valid}))
    for record in valid:
        if not record["scenic"]:
            LOGGER.warning("missing_scenic_id=%s name=%s type=%s coordinates=%s,%s", record["id"], record["name"], record["type"], record["lng"], record["lat"])


def execute_plan(plan, candidates, journal, limit, should_retry_errors):
    cache = load_cache(journal)
    pending = [identifier for identifier in candidates if identifier not in cache or
               (should_retry_errors and cache[identifier]["status"] in ("error", "unexpected"))][:limit]
    gate = RequestGate(plan["settings"]["interval_seconds"])
    with journal.open("a", encoding="utf-8") as stream, ThreadPoolExecutor(max_workers=plan["settings"]["workers"]) as executor:
        requests = executor.map(lambda identifier: fetch_candidate(identifier, plan["settings"], gate), pending)
        for record in requests:
            record["batches"] = candidates[record["id"]]
            record["checked_at"] = datetime.now().astimezone().isoformat()
            cache[record["id"]] = record
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            if record["status"] == "valid":
                LOGGER.info("hit=%s scenic=%s", record["id"], record["scenic"])
    return cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audit", action="store_true")
    arguments = parser.parse_args()
    plan = json.loads(arguments.plan.read_text(encoding="utf-8"))
    settings = plan["settings"]
    if arguments.limit < 1 or settings["workers"] < 1 or settings["interval_seconds"] <= 0:
        raise ValueError("Limit, workers, and interval must be positive")
    candidates = generate_candidates(plan)
    journal = arguments.plan.parent / settings["journal"]
    output_prefix = arguments.plan.parent / settings["output_prefix"]
    if not journal.parent.is_dir() or not output_prefix.parent.is_dir():
        raise ValueError("Output directories must already exist")
    if arguments.dry_run:
        LOGGER.info("candidate_count=%s batches=%s", len(candidates), summarize_batches(candidates, {}))
        return
    if arguments.audit:
        cache = load_cache(journal)
        audit_records(candidates, cache)
        export_summary(candidates, cache, output_prefix)
        return
    cache = execute_plan(plan, candidates, journal, arguments.limit, arguments.retry_errors)
    export_summary(candidates, cache, output_prefix)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
