Data Getter


Cleaner


Page Maker
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
    request = urllib.request.Request(url, headers={"AIC-User-Agent": "HCDE310-GroupA (student project)"})
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
Give each artwork a short label (1 to 2 sentences). If AI writes the labels, check that they match the real artwork information.
Save the exhibit to a JSON file, then make an HTML page that shows the 8 artworks with images and labels. Your Python writes the .html file; you don't need Flask.
Im supposed to write the html file from the json file. can you do that for me and make the html page

why is my git pushing with my other account when gh auth shows my school account is active

Untangling git commit identity from push authentication setup.
Untangling git commit identity from push authentication setup.
gh auth and git keep separate records of who you are, so switching accounts in gh doesn’t change what git uses. There are two separate things to check, depending on what “pushing with my other account” looks like.

1. The commits show your other name or email on GitHub
The commit author comes from your git config, not from your login. Check it from inside the repo folder:

bash
git config user.name
git config user.email
If those show your personal account, set your school info for this repo only:

bash
git config user.name "Your Name"
git config user.email "your-uw-email@uw.edu"
Leaving out --global means this applies only to this repo, so your other projects stay unchanged. The email must also be added to your school GitHub account (Settings → Emails), or GitHub won’t link the commits to that account.

This only fixes new commits. Commits you’ve already made keep the old author.

2. The push itself goes through as your other account
The login git uses for pushing depends on your remote URL:

bash
git remote -v
If it starts with https://: git is using a password or token saved in your Mac’s Keychain from your other account. You can make git ask gh for credentials instead:

bash
gh auth setup-git
After that, git uses whichever account gh auth status shows as active. If it still uses the old account, delete the saved login. Open the Keychain Access app, search for github.com, and delete the “internet password” entries. The next push will then use gh’s login.

If it starts with git@github.com:: you’re using SSH, and git authenticates with an SSH key. That key is registered to your other account, and gh has no effect here. Check which account the key belongs to:

bash
ssh -T git@github.com
It replies “Hi <username>!”. The simplest fix is to switch this repo to HTTPS and run gh auth setup-git as described above:

bash
git remote set-url origin https://github.com/OWNER/REPO.git
Replace OWNER/REPO with the part of your current remote URL after git@github.com:, without the .git ending.

If you send me the output of git remote -v and git config user.email, I can tell you which of these applies.

the html page needs to show 12 photos

Edited a file, shared a file
I updated make_exhibit.py to show 12 artworks. If you’ve already edited your own copy, the only line you need to change is near the top:

python
EXHIBIT_SIZE = 12
Then:

Run python make_exhibit.py again. It rewrites both exhibit.json and exhibit.html.
Refresh the page in Live Server.
Two other things to check:

If you’re using CHOSEN_IDS, list 12 ids. Otherwise you’ll only get as many artworks as you listed.
If any artwork has a label in CUSTOM_LABELS, check the 4 new labels too. The terminal prints all 12, so you can compare them with the real artwork info.
Make exhibit
PY


Explainer
No AI used.
