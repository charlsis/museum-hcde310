# get_data.py
# Data Getter for Museum Consortium, Group A
# Searches the Art Institute of Chicago API for the class theme ("food"),
# collects artworks from several pages of results, and saves them to group_a.json.

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---- Settings ----
THEME = "food"             # class theme = our search word
PER_PAGE = 50              # results per page (API max is 100)
PAGES_TO_GET = 3           # 3 pages x 50 = up to 150 artworks
MIN_ARTWORKS = 40          # assignment minimum
FIELDS = [
    "id",
    "title",
    "artist_title",
    "date_display",
    "medium_display",
    "image_id",
    "short_description",
]
BASE_URL = "https://api.artic.edu/api/v1/artworks/search"
OUTPUT_FILE = "group_a.json"

# The museum asks callers to identify themselves
USER_AGENT = "HCDE310-GroupA (student project)"
TIMEOUT_SECONDS = 30       # give up on a request after this long
PAUSE_SECONDS = 1          # be polite: wait between page requests


# ---- Talking to the API ----
def build_url(page):
    """Make the search URL for one page of results."""
    params = {
        "q": THEME,
        "limit": PER_PAGE,
        "page": page,
        "fields": ",".join(FIELDS),
    }
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def get_page(page):
    """Ask the API for one page. Returns a dictionary, or None if something went wrong."""
    url = build_url(page)
    print("Getting page", page, "->", url)

    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "AIC-User-Agent": USER_AGENT},
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            text = response.read().decode("utf-8")
        return json.loads(text)
    except urllib.error.HTTPError as err:       # must come before URLError
        print("  HTTP error:", err.code, err.reason)
    except (urllib.error.URLError, TimeoutError) as err:
        print("  could not reach the API:", err)
    except json.JSONDecodeError:
        print("  the API sent back something that is not valid JSON")
    return None


def get_all_artworks():
    """Loop over pages and put every artwork (a dictionary) into one list."""
    all_artworks = []
    seen_ids = set()   # search results can repeat an artwork across pages

    for page in range(1, PAGES_TO_GET + 1):
        result = get_page(page)
        if result is None:
            print("  stopping early because page", page, "failed")
            break

        artworks = result.get("data", [])
        total_pages = result.get("pagination", {}).get("total_pages", page)

        new_count = 0
        for artwork in artworks:
            if artwork["id"] in seen_ids:
                continue
            seen_ids.add(artwork["id"])
            all_artworks.append(artwork)
            new_count += 1
        print("  got", new_count, "new artworks, running total:", len(all_artworks))

        # Stop early if the API has no more pages
        if page >= total_pages:
            print("  no more pages, stopping")
            break
        if page < PAGES_TO_GET:
            time.sleep(PAUSE_SECONDS)

    return all_artworks


# ---- Checking and saving ----
def count_incomplete(artworks):
    """Count artworks missing an image or a title (the Cleaner will remove these)."""
    return len([a for a in artworks if not a.get("image_id") or not a.get("title")])


def save_json(artworks, filename):
    """Save the list of artworks to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artworks, f, indent=2, ensure_ascii=False)
    print("Saved", len(artworks), "artworks to", filename)


# ---- Main program ----
def main():
    artworks = get_all_artworks()

    # Don't overwrite an existing good file with an empty one
    if not artworks:
        print("No artworks collected, so nothing was saved.")
        sys.exit(1)

    if len(artworks) < MIN_ARTWORKS:
        print("Warning: only got", len(artworks), "artworks, assignment needs at least", MIN_ARTWORKS)

    print(count_incomplete(artworks), "artworks have no image or no title (the Cleaner will remove these)")

    save_json(artworks, OUTPUT_FILE)


if __name__ == "__main__":
    main()
