"""Preserve the bounded verification results created in the research browser."""

import argparse
import csv
import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path

LOGGER = logging.getLogger(__name__)
EXPRESSION = "JSON.stringify({initial:forumCheck,extra:forumExtra,images:forumImages,photos:forumPhotos,sansha:sanshaVerify,spatial:specialVerification})"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target")
    parser.add_argument("output", type=Path)
    parser.add_argument("--proxy", required=True)
    arguments = parser.parse_args()
    if not arguments.output.parent.is_dir():
        raise ValueError("Output parent must exist")
    url = arguments.proxy.rstrip("/") + "/eval?" + urllib.parse.urlencode({"target": arguments.target})
    request = urllib.request.Request(url, EXPRESSION.encode(), {"Content-Type": "text/plain; charset=utf-8"})
    with urllib.request.urlopen(request, timeout=30) as response:
        envelope = json.loads(response.read())
    results = json.loads(envelope["value"])
    arguments.output.with_suffix(".json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = {record["id"]: record for section in ("initial", "extra", "sansha") for record in results[section]["rows"]}
    with arguments.output.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "errno", "name", "scenic", "source", "type", "error"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows.values())
    LOGGER.info("distinct_checked=%s valid=%s", len(rows), sum(record.get("errno") == 0 for record in rows.values()))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
