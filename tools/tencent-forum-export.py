"""Save only archived forum post text and outgoing links from a research tab."""

import argparse
import csv
import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path

LOGGER = logging.getLogger(__name__)
FIELDS = ["id", "label", "href", "post", "archive"]
EXPRESSION = """JSON.stringify({archive:location.href,title:document.title,
posts:Array.from(document.querySelectorAll('[id^=postmessage_]')).map(post=>({
post:post.id,text:post.innerText,
links:Array.from(post.querySelectorAll('a')).map(anchor=>({
label:anchor.textContent.trim(),href:anchor.getAttribute('href'),
id:(anchor.getAttribute('href')||'').match(/[?&#]pano=([0-9A-Za-z]+)/)?.[1]||''}))}))})"""


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
    archive = json.loads(envelope["value"])
    arguments.output.with_suffix(".json").write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding="utf-8")
    with arguments.output.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for post in archive["posts"]:
            writer.writerows(dict(link, post=post["post"], archive=archive["archive"]) for link in post["links"] if link["id"])
    identifiers = [link["id"] for post in archive["posts"] for link in post["links"] if link["id"]]
    LOGGER.info("posts=%s pano_links=%s distinct_ids=%s archive=%s", len(archive["posts"]), len(identifiers), len(set(identifiers)), archive["archive"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
