# make_exhibit.py
# Exhibit Builder for Museum Consortium, Group A
# Reads the artworks saved by get_data.py, picks 8 for the exhibit,
# gives each one a short label, saves the exhibit to exhibit.json,
# and writes an HTML page (exhibit.html) that shows them.

import json
import html

# ---- Settings ----
INPUT_FILE = "group_a.json"       # made by get_data.py (or the Cleaner's cleaned file)
EXHIBIT_JSON = "exhibit.json"     # the 8 chosen artworks + labels
OUTPUT_HTML = "exhibit.html"      # the web page
EXHIBIT_SIZE = 12
EXHIBIT_TITLE = "Food in Art"

# If your group wants specific artworks, put their ids here (from group_a.json).
# Leave it empty to just use the first 8 artworks that have an image and a title.
CHOSEN_IDS = []

# If your group writes its own labels (or AI writes them and you check them),
# put them here as  id: "label text". Any artwork not listed gets an automatic label.
CUSTOM_LABELS = {
    # 12345: "A still life showing a table of fruit and bread, painted in soft light.",
}


def load_json(filename):
    """Read a JSON file and return the Python data inside it."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def is_usable(artwork):
    """An artwork is usable if it has both an image and a title."""
    return bool(artwork.get("image_id")) and bool(artwork.get("title"))


def pick_artworks(artworks):
    """Choose the 8 artworks for the exhibit."""
    usable = [a for a in artworks if is_usable(a)]

    if CHOSEN_IDS:
        chosen = [a for a in usable if a["id"] in CHOSEN_IDS]
    else:
        chosen = usable

    return chosen[:EXHIBIT_SIZE]


def first_sentence(text):
    """Return just the first sentence of a longer piece of text."""
    text = text.strip()
    end = text.find(". ")
    if end == -1:
        return text
    return text[: end + 1]


def make_label(artwork):
    """Make a 1-2 sentence label using only the museum's real information."""
    if artwork["id"] in CUSTOM_LABELS:
        return CUSTOM_LABELS[artwork["id"]]

    title = artwork.get("title") or "Untitled"
    artist = artwork.get("artist_title") or "an unknown artist"
    date = artwork.get("date_display")
    medium = artwork.get("medium_display")

    # Sentence 1: the facts
    label = title + " was made by " + artist
    if date:
        label += " (" + date + ")"
    if medium:
        label += " using " + medium.rstrip(".").lower()
    label += "."

    # Sentence 2: the museum's own short description, if it has one
    description = artwork.get("short_description")
    if description:
        label += " " + first_sentence(description)

    return label


def image_url(image_id):
    """Build the image link. The museum serves images through IIIF, using the image_id."""
    return "https://www.artic.edu/iiif/2/" + image_id + "/full/843,/0/default.jpg"


def build_exhibit(artworks):
    """Turn the chosen artworks into a list of small, clean exhibit entries."""
    exhibit = []
    for artwork in artworks:
        exhibit.append({
            "id": artwork["id"],
            "title": artwork.get("title"),
            "artist": artwork.get("artist_title") or "Unknown artist",
            "date": artwork.get("date_display") or "",
            "medium": artwork.get("medium_display") or "",
            "image_url": image_url(artwork["image_id"]),
            "label": make_label(artwork),
        })
    return exhibit


def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved", len(data), "artworks to", filename)


def make_card(entry):
    """Make the HTML for one artwork. html.escape keeps symbols like & and < from breaking the page."""
    title = html.escape(entry["title"])
    artist = html.escape(entry["artist"])
    date = html.escape(entry["date"])
    label = html.escape(entry["label"])
    url = html.escape(entry["image_url"])
    link = "https://www.artic.edu/artworks/" + str(entry["id"])

    return f"""
    <article class="card">
      <img src="{url}" alt="{title}" loading="lazy" referrerpolicy="no-referrer">
      <div class="text">
        <h2>{title}</h2>
        <p class="meta">{artist}{", " + date if date else ""}</p>
        <p class="label">{label}</p>
        <a href="{link}" target="_blank">View at the Art Institute of Chicago</a>
      </div>
    </article>"""


def write_html(exhibit, filename):
    """Write the whole web page to a .html file."""
    cards = "".join(make_card(entry) for entry in exhibit)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(EXHIBIT_TITLE)}</title>
  <style>
    body {{ font-family: Georgia, serif; background: #f7f3ec; color: #2b2622; margin: 0; }}
    header {{ text-align: center; padding: 40px 16px 20px; }}
    header h1 {{ margin: 0; font-size: 2.4rem; }}
    header p {{ color: #6b6158; }}
    main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
           gap: 24px; max-width: 1200px; margin: 0 auto; padding: 16px 16px 48px; }}
    .card {{ background: white; border-radius: 8px; overflow: hidden;
             box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; flex-direction: column; }}
    .card img {{ width: 100%; height: 260px; object-fit: cover; background: #e8e2d8; }}
    .text {{ padding: 16px; }}
    .text h2 {{ font-size: 1.15rem; margin: 0 0 4px; }}
    .meta {{ color: #6b6158; font-style: italic; margin: 0 0 10px; }}
    .label {{ line-height: 1.5; }}
    a {{ color: #8a3b12; font-size: 0.9rem; }}
    footer {{ text-align: center; color: #6b6158; padding-bottom: 32px; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(EXHIBIT_TITLE)}</h1>
    <p>{len(exhibit)} artworks from the Art Institute of Chicago &middot; Museum Consortium, Group A</p>
  </header>
  <main>{cards}
  </main>
  <footer>Images and data from the Art Institute of Chicago API.</footer>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(page)
    print("Wrote", filename)


if __name__ == "__main__":
    artworks = load_json(INPUT_FILE)
    chosen = pick_artworks(artworks)

    if len(chosen) < EXHIBIT_SIZE:
        print("Warning: only found", len(chosen), "usable artworks, need", EXHIBIT_SIZE)

    exhibit = build_exhibit(chosen)

    # Print each label so you can check it against the real artwork info
    for entry in exhibit:
        print("-", entry["id"], "|", entry["label"])

    save_json(exhibit, EXHIBIT_JSON)
    write_html(exhibit, OUTPUT_HTML)