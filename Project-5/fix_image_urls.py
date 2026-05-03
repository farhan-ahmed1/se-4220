"""Repair seed image URLs by rewriting LoremFlickr cache URLs into stable
direct Flickr CDN URLs.

Background: update_seed_images.py originally stored URLs like
    https://loremflickr.com/cache/resized/<server>_<photo_id>_<secret>_<size>_<W>_<H>_<filter>.jpg
which are temporary -- LoremFlickr evicts those cached resizes after a
while, returning 404. The underlying Flickr photos are still hosted at
Flickr's permanent CDN, so we can rewrite each URL to:
    https://live.staticflickr.com/<server>/<photo_id>_<secret>_<size>.jpg
which Flickr keeps stable indefinitely.

Run after the cache URLs start 404-ing:
    python fix_image_urls.py

Idempotent: only rewrites rows whose image_url currently points at
loremflickr.com/cache/resized/.
"""

from __future__ import annotations

import os
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

import db

load_dotenv()


# LoremFlickr cache filenames come in two shapes:
#   <server>_<photo_id>_<secret>_<size>_<W>_<H>_<filter>.jpg     (most common)
#   <server>_<photo_id>_<secret>_<W>_<H>_<filter>.jpg            (no size letter)
LOREMFLICKR_CACHE_RE = re.compile(
    r"loremflickr\.com/cache/resized/"
    r"(?P<server>\d+)_(?P<photo>\d+)_(?P<secret>[a-f0-9]+)"
    r"(?:_(?P<size>[a-z]))?_"
    r"\d+_\d+_[a-z]+\.jpg",
    re.IGNORECASE,
)

# When LoremFlickr can't match the keyword set, it returns a placeholder
# image at /cache/resized/defaultImage.small_*. Those rows need a re-fetch
# with broader keywords, not a URL rewrite.
DEFAULT_IMAGE_RE = re.compile(r"loremflickr\.com/cache/resized/defaultImage", re.IGNORECASE)


# Fallback keywords keyed by category slug, used to re-fetch any row that
# previously hit LoremFlickr's defaultImage placeholder. Picked to maximise
# the chance LoremFlickr finds a tagged photo on Flickr.
FALLBACK_KEYWORDS = {
    "computer-tech":    "computer",
    "customer-service": "office",
    "tutoring":         "books",
}


def to_flickr_cdn(url: str) -> str | None:
    m = LOREMFLICKR_CACHE_RE.search(url)
    if not m:
        return None
    size = m.group("size")
    suffix = f"_{size}" if size else ""
    return (
        f"https://live.staticflickr.com/"
        f"{m.group('server')}/{m.group('photo')}_{m.group('secret')}{suffix}.jpg"
    )


def refetch_via_loremflickr(keyword: str, seed: int) -> str | None:
    """Hit LoremFlickr, follow the 302, then return a stable Flickr CDN URL
    parsed out of the cached filename. Returns None on failure or if the
    response is another defaultImage."""
    url = f"https://loremflickr.com/600/400/{keyword}?random={seed}"
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=15) as resp:
            cached = resp.url
    except URLError:
        return None
    if "defaultImage" in cached:
        return None
    return to_flickr_cdn(cached)


def main():
    rows = db.query_all(
        """
        SELECT l.id, l.image_url, c.slug AS category_slug
        FROM listings l
        JOIN categories c ON c.id = l.category_id
        WHERE l.image_url LIKE 'https://loremflickr.com/%%'
        ORDER BY l.id
        """
    )
    print(f"Found {len(rows)} listings with LoremFlickr URLs to repair.")

    updated = 0
    refetched = 0
    failed = 0

    for row in rows:
        url = row["image_url"]

        if DEFAULT_IMAGE_RE.search(url):
            keyword = FALLBACK_KEYWORDS.get(row["category_slug"], row["category_slug"])
            print(f"  listing {row['id']} ({row['category_slug']}): defaultImage placeholder -> refetching with '{keyword}' ...", end=" ", flush=True)
            new_url = refetch_via_loremflickr(keyword, seed=row["id"])
            if not new_url:
                print("FAILED")
                failed += 1
                continue
            db.execute("UPDATE listings SET image_url = %s WHERE id = %s",
                       (new_url, row["id"]))
            print("ok")
            refetched += 1
            continue

        new_url = to_flickr_cdn(url)
        if not new_url:
            print(f"  listing {row['id']}: regex did not match, skipping ({url})")
            failed += 1
            continue
        db.execute("UPDATE listings SET image_url = %s WHERE id = %s",
                   (new_url, row["id"]))
        updated += 1

    print(f"\nDone. {updated} rewritten, {refetched} re-fetched, {failed} failed.")


if __name__ == "__main__":
    main()
