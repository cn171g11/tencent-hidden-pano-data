"""Summarize saved forum links without querying panorama services."""

import csv
import json
import logging
from collections import Counter
from pathlib import Path

LOGGER = logging.getLogger(__name__)
ARCHIVE_FILES = ("tencent-forum-4391-page1.json", "tencent-forum-4391-page2.json")
OUTPUT_PREFIX = "tencent-forum-4391-combined"
PREVIOUS_FILES = (
    "tencent-hidden-streetview-dufu-49.csv",
    "tencent-hidden-streetview-round2-additional.csv",
    "tencent-panoid-round3-samples.csv",
    "tencent-hidden-streetview-round4-samples.csv",
    "tencent-hidden-streetview-round5-albums.csv",
    "tencent-hidden-streetview-round5-uids.csv",
    "tencent-enumeration-results.csv",
)


def previous_identifiers():
    identifiers = set()
    for filename in PREVIOUS_FILES:
        with Path(filename).open(encoding="utf-8-sig", newline="") as stream:
            for record in csv.DictReader(stream):
                identifier = record.get("pano_id") or record.get("id") or record.get("returned_pano")
                if identifier:
                    identifiers.add(identifier)
    return identifiers


def collect_links():
    records = []
    for filename in ARCHIVE_FILES:
        archive = json.loads(Path(filename).read_text(encoding="utf-8"))
        for post in archive["posts"]:
            records.extend(dict(link, archive=archive["archive"], post=post["post"])
                           for link in post["links"] if link["id"])
    return records


def main():
    records = collect_links()
    unique = {record["id"]: record for record in records}
    previous = previous_identifiers()
    summary = {"link_count": len(records), "unique_ids": len(unique),
               "lengths": dict(Counter(len(identifier) for identifier in unique)),
               "seven_q_unique": sum("7Q" in identifier for identifier in unique),
               "scene_unique": sum("SCENE" in identifier for identifier in unique),
               "xty_unique": sum("XTY" in identifier for identifier in unique),
               "overlap_with_saved_results": len(set(unique) & previous),
               "absent_from_saved_results": len(set(unique) - previous),
               "regions": dict(sorted(Counter(identifier[:4] for identifier in unique).items()))}
    Path(OUTPUT_PREFIX + ".json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with Path(OUTPUT_PREFIX + ".csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "label", "href", "post", "archive"])
        writer.writeheader()
        writer.writerows(unique.values())
    LOGGER.info("summary=%s", summary)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
