# get_data.py
# Data Getter for Museum Consortium, Group A
# Searches the Art Institute of Chicago API for the class theme ("food"),
# collects artworks from several pages of results, and saves them to group_a.json.

import json
import urllib.parse
import urllib.request

# ---- Settings ----
THEME = "food"            # class theme = our search word
PER_PAGE = 50             # how many results to ask for per page (API max is 100)
PAGES_TO_GET = 3          # 3 pages x 50 = up to 150 artworks (we need at least 40)
FIELDS = "id,title,artist_title,date_display,medium_display,image_id,short_description"
BASE_URL = "https://api.artic.edu/api/v1/artworks/search"
OUTPUT_FILE = "group_a.json"


def build_url(page):
    """Make the search URL for one page of results."""
    params = {
        "q": THEME,
        "limit": PER_PAGE,
        "page": page,
        "fields": FIELDS,
    }
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def get_page(page):
    """Ask the API for one page and return the JSON as a Python dictionary."""
    url = build_url(page)
    print("Getting page", page, "->", url)
    # The museum asks callers to identify themselves with a user-agent header
    headers = {
        "User-Agent": "HCDE310-GroupA/1.0 (student project)",
        "AIC-User-Agent": "HCDE310-GroupA (your-uw-email@uw.edu)",
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        text = response.read().decode("utf-8")
    return json.loads(text)


def get_all_artworks():
    """Loop over pages and put every artwork (a dictionary) into one list."""
    all_artworks = []
    for page in range(1, PAGES_TO_GET + 1):
        result = get_page(page)
        artworks = result["data"]                  # list of artwork dictionaries
        total_pages = result["pagination"]["total_pages"]
        all_artworks.extend(artworks)
        print("  got", len(artworks), "artworks, running total:", len(all_artworks))

        # Stop early if the API has no more pages
        if page >= total_pages:
            print("  no more pages, stopping")
            break
    return all_artworks


def save_json(artworks, filename):
    """Save the list of artworks to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artworks, f, indent=2, ensure_ascii=False)
    print("Saved", len(artworks), "artworks to", filename)


if __name__ == "__main__":
    artworks = get_all_artworks()

    if len(artworks) < 40:
        print("Warning: only got", len(artworks), "artworks, assignment needs at least 40")

    # Quick check for the Cleaner: how many are missing an image or title?
    missing = [a for a in artworks if not a.get("image_id") or not a.get("title")]
    print(len(missing), "artworks have no image or no title (the Cleaner will remove these)")

    save_json(artworks, OUTPUT_FILE)
