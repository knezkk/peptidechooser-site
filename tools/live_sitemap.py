"""The live site's sitemap and page dates, for the deploy (owner task 23, 8 Nov 2026).

python3 tools/live_sitemap.py <dir> writes:
  <dir>/live-sitemap.xml  every live <url> in one urlset: sitemap.xml itself, or, since the sitemap index, each of its files
  <dir>/live-lastmod.json the live dist/lastmod.json (each page's visible-text fingerprint and the date it last changed)
  <dir>/live-seller-archive.json the live seller profiles, so a seller that leaves the data keeps its page
build.py reads them through LIVE_SITEMAP and LIVE_LASTMOD. A file it cannot read is left out; this never fails the deploy.
"""
import re
import sys
import urllib.request
from pathlib import Path

LIVE = "https://peptidechooser.com"


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "peptidechooser-deploy"}), timeout=30) as r:
            return r.read().decode("utf-8")
    except (OSError, ValueError):
        return None


def flat(xml):
    """Every <url> of a sitemap or of a sitemap index's files on our own host; None when a file cannot be read."""
    if "<sitemapindex" not in xml:
        return re.findall(r"<url>.*?</url>", xml, re.S)
    out = []
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        if not loc.startswith(LIVE + "/"):
            continue
        child = get(loc)
        if child is None:
            return None
        out += re.findall(r"<url>.*?</url>", child, re.S)
    return out


def main(folder):
    folder = Path(folder)
    xml = get(LIVE + "/sitemap.xml")
    urls = flat(xml) if xml else None
    if urls is not None:
        (folder / "live-sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(urls) + "</urlset>\n", encoding="utf-8")
        print(f"live_sitemap: {len(urls)} live pages")
    else:
        print("live_sitemap: the live sitemap could not be read")
    archive = get(LIVE + "/seller-archive.json")  # task 25: the profiles a departed seller's page is kept from
    if archive and archive.lstrip().startswith("{"):
        (folder / "live-seller-archive.json").write_text(archive, encoding="utf-8")
        print("live_sitemap: live seller profiles read")
    marks = get(LIVE + "/lastmod.json")
    if marks and marks.lstrip().startswith("{"):
        (folder / "live-lastmod.json").write_text(marks, encoding="utf-8")
        print("live_sitemap: live page dates read")
    else:
        print("live_sitemap: no live page dates yet, every page gets the data date")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
