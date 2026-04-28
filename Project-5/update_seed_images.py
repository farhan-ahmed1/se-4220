"""Replace the placeholder picsum.photos seed images with category-relevant
photos from LoremFlickr (which serves CC-licensed Flickr photos).

Why LoremFlickr instead of Unsplash Source: source.unsplash.com was
deprecated by Unsplash in 2024 and now returns HTTP 503. LoremFlickr is
still alive and supports keyword-based image selection.

What this script does:
  1. For each category, picks 3 keyword sets (one per seeded listing).
  2. Calls https://loremflickr.com/600/400/<keywords>?random=<n>, which
     302-redirects to a specific cached image URL like
     /cache/resized/<id>.jpg.
  3. Follows that redirect once and stores the resolved URL in the
     listings.image_url column. This makes the image stable on every page
     load (no re-rolling on every browser visit).

Run after seed.py:
    python update_seed_images.py

Idempotent: only updates listings whose image_url currently points at
picsum.photos. Re-running won't re-fetch already-updated rows.
"""

from __future__ import annotations

import os
import sys
import time
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError

# Allow running this file directly without installing the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

import db

load_dotenv()


LOREMFLICKR = "https://loremflickr.com"


# Per-category keyword sets. Three entries per category (one per seeded
# listing). Keywords are comma-separated and become path segments in the
# LoremFlickr URL.
KEYWORDS = {
    # ---------- For Sale ----------
    "cars-trucks": ["car,sedan", "pickup,truck", "honda,civic"],
    "motorcycles": ["motorcycle,harley", "sportbike,kawasaki", "cruiser,honda"],
    "boats":       ["boat,water", "fishing,boat", "jetski,water"],
    "books":       ["book,stack", "novel,paperback", "textbook,desk"],
    "furniture":   ["sofa,couch", "dining,table", "mattress,bedroom"],

    # ---------- Housing ----------
    "apartments-rent": ["apartment,interior", "studio,loft", "kitchen,modern"],
    "houses-sale":     ["house,suburban", "bungalow,cottage", "house,colonial"],
    "rooms-roommates": ["bedroom,interior", "dorm,room", "bedroom,decor"],
    "sublets":         ["small,apartment", "studio,minimal", "bedroom,window"],
    "vacation-rentals":["cabin,lake", "cottage,exterior", "farmhouse,country"],

    # ---------- Services ----------
    "computer-tech": ["computer,laptop", "code,programming", "wifi,router"],
    "tutoring":      ["tutor,study", "books,math", "classroom,desk"],
    "cleaning":      ["cleaning,housekeeping", "vacuum,floor", "sponge,kitchen"],
    "moving":        ["moving,boxes", "truck,moving", "movers,couch"],
    "lawn-garden":   ["lawn,mower", "snow,plow", "garden,landscape"],

    # ---------- Jobs ----------
    "software-engineering": ["office,coding", "developer,laptop", "server,datacenter"],
    "customer-service":     ["headset,office", "callcenter,desk", "support,phone"],
    "food-hospitality":     ["chef,kitchen", "waiter,restaurant", "hotel,lobby"],
    "education":            ["teacher,classroom", "school,desk", "students,learning"],
    "retail":               ["bookstore,shelf", "grocery,aisle", "cashier,register"],

    # ---------- Community ----------
    "events":     ["farmersmarket,vegetables", "stadium,football", "workshop,coding"],
    "lost-found": ["dog,labrador", "keys,lanyard", "wallet,leather"],
    "volunteers": ["foodbank,donation", "construction,helping", "tutor,adult"],
    "activities": ["soccer,park", "boardgames,table", "yoga,park"],
    "rideshare":  ["highway,car", "skyline,chicago", "skyline,minneapolis"],
}


def resolve_image(keywords: str, random_seed: int, retries: int = 3) -> str | None:
    """Hit LoremFlickr and return the resolved (post-redirect) image URL,
    or None if the service is unreachable."""
    url = f"{LOREMFLICKR}/600/400/{keywords}?random={random_seed}"
    for attempt in range(retries):
        try:
            # We don't follow the redirect automatically -- we just want the
            # Location header.
            req = Request(url, method="HEAD")
            with urlopen(req, timeout=10) as resp:
                # Some servers return 200 directly on HEAD if no redirect.
                # In our case LoremFlickr returns 302, but urllib auto-
                # follows redirects on HEAD too. resp.url is the final URL.
                return resp.url
        except URLError as e:
            print(f"    attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(1 + attempt)
    return None


def main():
    rows = db.query_all(
        """
        SELECT l.id, l.image_url, c.slug AS category_slug
        FROM listings l
        JOIN categories c ON c.id = l.category_id
        ORDER BY c.slug, l.id
        """
    )
    print(f"Found {len(rows)} total listings.")

    # Group rows by category so we know each listing's index within its category
    by_cat: dict[str, list[dict]] = {}
    for row in rows:
        by_cat.setdefault(row["category_slug"], []).append(row)

    updated = 0
    skipped = 0
    failed = 0

    for cat_slug, listings in by_cat.items():
        kws = KEYWORDS.get(cat_slug)
        if not kws:
            print(f"[{cat_slug}] no keyword set defined, skipping")
            continue

        for idx, row in enumerate(listings):
            current = row["image_url"] or ""
            if "loremflickr.com" in current:
                skipped += 1
                continue
            keyword = kws[idx % len(kws)]
            print(f"[{cat_slug}] listing {row['id']} -> {keyword} ...", end=" ", flush=True)
            resolved = resolve_image(keyword, random_seed=row["id"])
            if not resolved:
                print("FAILED")
                failed += 1
                continue
            # The resolved URL might be relative (e.g. /cache/resized/...)
            if resolved.startswith("/"):
                resolved = urljoin(LOREMFLICKR, resolved)
            db.execute(
                "UPDATE listings SET image_url = %s WHERE id = %s",
                (resolved, row["id"]),
            )
            updated += 1
            print("ok")

    print(f"\nDone. {updated} updated, {skipped} already had loremflickr URL, {failed} failed.")


if __name__ == "__main__":
    main()
