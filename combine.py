#!/usr/bin/env python3
"""
combine.py - merge every group's JSON file into one food-themed exhibit page.

Usage:
    python combine.py                         # uses all *.json in the current folder
    python combine.py a.json b.json group_d.json
    python combine.py data/ -o food.html --title "Food in Art"

Outputs:
    food_exhibit.html   self-contained page: Exhibit, Timeline, Artists, Tour
    food_combined.json  the merged, de-duplicated records (handy for debugging)

Accepted input shapes (mixed freely across files):
    - a list of artwork objects
    - an object holding a list under data / artworks / items / exhibit / results
    - raw Art Institute of Chicago API output (artist_display, date_display,
      medium_display, image_id, short_description ...)
"""
import argparse
import glob
import json
import os
import re
import sys

IIIF = "https://www.artic.edu/iiif/2/{}/full/843,/0/default.jpg"
LIST_KEYS = ("data", "artworks", "items", "exhibit", "results", "works")


# ----------------------------------------------------------------- loading
def first(d, *keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", []):
            return v
    return None


def find_records(obj):
    """Return the list of artwork dicts inside whatever JSON shape we got."""
    if isinstance(obj, list):
        out = []
        for x in obj:
            if isinstance(x, dict) and any(k in x for k in ("title", "label")):
                out.append(x)
            elif isinstance(x, (list, dict)):
                out.extend(find_records(x))
        return out
    if isinstance(obj, dict):
        for k in LIST_KEYS:
            if k in obj:
                return find_records(obj[k])
        if "title" in obj:
            return [obj]
        out = []
        for v in obj.values():
            if isinstance(v, (list, dict)):
                out.extend(find_records(v))
        return out
    return []


def clean(s):
    if s is None:
        return ""
    s = re.sub(r"<[^>]+>", "", str(s))
    return re.sub(r"\s+", " ", s).strip()


def normalize(raw, source):
    title = clean(first(raw, "title", "name"))
    if not title:
        return None
    artist = first(raw, "artist", "artist_title", "artist_display", "creator", "maker")
    artist = clean(str(artist).split("\n")[0]) if artist else ""
    if not artist or artist.lower() in ("unknown", "unknown artist", "anonymous"):
        artist = "Unknown artist"
    image = first(raw, "image_url", "image", "thumbnail_url")
    if not image and raw.get("image_id"):
        image = IIIF.format(raw["image_id"])
    medium = clean(first(raw, "medium", "medium_display"))
    date = clean(first(raw, "date", "date_display"))
    label = clean(first(raw, "label", "short_description", "description",
                        "thumbnail_alt_text"))
    return {
        "id": first(raw, "id"),
        "title": title,
        "artist": artist,
        "date": date,
        "year": parse_year(date or clean(raw.get("date_start"))),
        "medium": medium,
        "image": image or "",
        "label": label,
        "extra": extra_text(label),
        "sources": [source],
    }


# ----------------------------------------------------------------- helpers
def parse_year(s):
    """Best-effort sort year. Negative = BC. None if undated."""
    s = str(s or "")
    bc = bool(re.search(r"\bB\.?\s?C\.?(E\.?)?\b", s, re.I))
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)\s+century", s, re.I)
    if m:
        c = int(m.group(1))
        # midpoint of the century: 11th c. BC -> -1050, 19th c. AD -> 1850
        return -(c * 100 - 50) if bc else (c - 1) * 100 + 50
    m = re.search(r"-?\d{3,4}", s)
    if m:
        y = abs(int(m.group(0)))
        return -y if bc else y
    return None


def extra_text(label):
    """Strip the boilerplate 'X was made by Y (date) using Z.' sentence."""
    if not label:
        return ""
    i = label.find(" using ")
    if i == -1:
        return ""
    m = re.search(r"\.\s+(?=[A-Z\"'])", label[i:])
    return label[i + m.end():].strip() if m else ""


def year_label(y):
    if y is None:
        return "Undated"
    return f"{-y} BC" if y < 0 else str(y)


def merge(records):
    """De-duplicate by id (else title+artist); union sources, keep richest text."""
    seen, out = {}, []
    for r in records:
        key = ("id", r["id"]) if r["id"] is not None else ("t", r["title"].lower(), r["artist"].lower())
        if key in seen:
            k = seen[key]
            for f in ("image", "date", "medium"):
                if not k[f] and r[f]:
                    k[f] = r[f]
            if len(r["label"]) > len(k["label"]):
                k["label"], k["extra"] = r["label"], r["extra"]
            if k["year"] is None:
                k["year"] = r["year"]
            k["sources"] = sorted(set(k["sources"]) | set(r["sources"]))
        else:
            seen[key] = r
            out.append(r)
    return out


def collect_paths(args, out_names):
    paths = []
    for a in args or ["."]:
        if os.path.isdir(a):
            paths += glob.glob(os.path.join(a, "*.json"))
        else:
            paths += glob.glob(a) or [a]
    return [p for p in dict.fromkeys(paths) if os.path.basename(p) not in out_names]


# ----------------------------------------------------------------- page
PAGE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#faf6ef;--surface:#fff;--ink:#2a2118;--muted:#6f6254;--line:#e4d9c8;--accent:#b8421f;--accent-ink:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#1a1511;--surface:#251e18;--ink:#f1e8da;--muted:#a89a88;--line:#3a3027;--accent:#e2704a;--accent-ink:#1a1511}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Georgia,"Times New Roman",serif}
header{padding:2.2rem 1.2rem 1rem;max-width:1100px;margin:auto}
h1{margin:0;font-size:clamp(1.9rem,5vw,3rem);letter-spacing:-.02em}
.sub{color:var(--muted);margin:.3rem 0 0}
nav{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);display:flex;gap:.4rem;justify-content:center;padding:.6rem;flex-wrap:wrap}
nav button,.chip,.btn{font:inherit;font-family:system-ui,sans-serif;font-size:.9rem;border:1px solid var(--line);background:var(--surface);color:var(--ink);padding:.45rem .9rem;border-radius:99px;cursor:pointer}
nav button[aria-selected=true],.chip.on,.btn.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
main{max-width:1100px;margin:auto;padding:1.2rem}
section{display:none}section.on{display:block}
.chips{display:flex;gap:.4rem;flex-wrap:wrap;margin-bottom:1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1rem}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;display:flex;flex-direction:column}
.card:hover{border-color:var(--accent)}
.thumb{aspect-ratio:4/3;background:var(--line);display:flex;align-items:center;justify-content:center;color:var(--muted);font:.8rem system-ui}
.thumb img{width:100%;height:100%;object-fit:contain;background:#0001}
.cb{padding:.8rem}.cb h3{margin:0 0 .2rem;font-size:1.05rem}
.meta{color:var(--muted);font:.85rem system-ui}
.tl{position:relative;margin-left:1rem;padding-left:1.6rem;border-left:2px solid var(--line)}
.ti{position:relative;margin-bottom:1.2rem;display:flex;gap:1rem;align-items:flex-start;cursor:pointer}
.ti::before{content:"";position:absolute;left:-2.2rem;top:.5rem;width:.8rem;height:.8rem;border-radius:50%;background:var(--accent);border:2px solid var(--bg)}
.ti .yr{font:700 1.1rem system-ui;color:var(--accent);min-width:5.5rem}
.ti img{width:90px;height:70px;object-fit:cover;border-radius:6px;background:var(--line)}
.ti h3{margin:0;font-size:1.05rem}
.artist{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:1rem;margin-bottom:1rem}
.artist h3{margin:0}.strip{display:flex;gap:.5rem;overflow-x:auto;margin-top:.7rem}
.strip img{height:90px;border-radius:6px;cursor:pointer;background:var(--line)}
.tour{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:1rem}
.tour img{max-width:100%;max-height:60vh;display:block;margin:0 auto 1rem;border-radius:8px}
.tour h2{margin:.2rem 0}.ctl{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem;align-items:center}
.bar{height:6px;background:var(--line);border-radius:9px;overflow:hidden;margin-bottom:.8rem}
.bar i{display:block;height:100%;background:var(--accent);transition:width .3s}
dialog{border:1px solid var(--line);border-radius:14px;background:var(--surface);color:var(--ink);max-width:min(720px,94vw);padding:1.2rem}
dialog::backdrop{background:#0008}
dialog img{max-width:100%;max-height:55vh;display:block;margin:0 auto 1rem}
.badge{display:inline-block;font:.72rem system-ui;background:var(--line);color:var(--muted);padding:.1rem .5rem;border-radius:99px;margin:.1rem .2rem 0 0}
</style></head><body>
<header><h1>__TITLE__</h1>
<p class="sub" id="sub"></p></header>
<nav role="tablist">
 <button role="tab" data-t="exhibit" aria-selected="true">Exhibit</button>
 <button role="tab" data-t="timeline" aria-selected="false">Timeline</button>
 <button role="tab" data-t="artists" aria-selected="false">Artists</button>
 <button role="tab" data-t="tour" aria-selected="false">Tour</button>
</nav>
<main>
 <section id="exhibit" class="on"><div class="chips" id="chips"></div><div class="grid" id="grid"></div></section>
 <section id="timeline"><div class="tl" id="tl"></div></section>
 <section id="artists"></section>
 <section id="tour"></section>
</main>
<dialog id="dlg"></dialog>
<script>
const WORKS = __DATA__;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const yl = y => y == null ? "Undated" : (y < 0 ? (-y) + " BC" : String(y));
const byTime = [...WORKS].sort((a,b) => (a.year ?? 1e9) - (b.year ?? 1e9));
const img = (w, cls="") => w.image
  ? `<img ${cls} loading="lazy" src="${esc(w.image)}" alt="${esc(w.title)}" onerror="this.replaceWith(Object.assign(document.createElement('span'),{textContent:'Image unavailable'}))">`
  : `<span>No image</span>`;
const artists = [...new Set(WORKS.map(w => w.artist))];
$("#sub").textContent = `${WORKS.length} works · ${artists.length} artists · ${yl(byTime[0]?.year)} to ${yl([...byTime].reverse().find(w=>w.year!=null)?.year)}`;

// tabs
document.querySelectorAll("nav button").forEach(b => b.onclick = () => {
  document.querySelectorAll("nav button").forEach(x => x.setAttribute("aria-selected", x === b));
  document.querySelectorAll("section").forEach(s => s.classList.toggle("on", s.id === b.dataset.t));
});
const go = t => document.querySelector(`nav [data-t=${t}]`).click();

// detail dialog
function open_(i) {
  const w = WORKS[i];
  $("#dlg").innerHTML = `${w.image ? img(w) : ""}<h2>${esc(w.title)}</h2>
   <p class="meta">${esc(w.artist)} · ${esc(w.date)}<br>${esc(w.medium)}</p>
   <p>${esc(w.extra || w.label)}</p>
   <p>${w.sources.map(s => `<span class="badge">${esc(s)}</span>`).join("")}</p>
   <form method="dialog"><button class="btn primary">Close</button></form>`;
  $("#dlg").showModal();
}
const idx = w => WORKS.indexOf(w);

// exhibit
const sources = [...new Set(WORKS.flatMap(w => w.sources))];
let filt = "All";
function drawExhibit() {
  $("#chips").innerHTML = ["All", ...sources].map(s => `<button class="chip ${s===filt?"on":""}" data-s="${esc(s)}">${esc(s)}</button>`).join("");
  $("#chips").querySelectorAll("button").forEach(b => b.onclick = () => { filt = b.dataset.s; drawExhibit(); });
  $("#grid").innerHTML = byTime.filter(w => filt === "All" || w.sources.includes(filt)).map(w =>
    `<div class="card" onclick="open_(${idx(w)})"><div class="thumb">${img(w)}</div>
     <div class="cb"><h3>${esc(w.title)}</h3><div class="meta">${esc(w.artist)}<br>${esc(w.date)}</div></div></div>`).join("");
}
drawExhibit();

// timeline
$("#tl").innerHTML = byTime.map(w =>
  `<div class="ti" onclick="open_(${idx(w)})"><div class="yr">${yl(w.year)}</div>${w.image ? img(w) : ""}
   <div><h3>${esc(w.title)}</h3><div class="meta">${esc(w.artist)} · ${esc(w.medium)}<br>${esc(w.date)}</div></div></div>`).join("");

// artists
const groups = artists.map(a => {
  const ws = byTime.filter(w => w.artist === a);
  const ys = ws.map(w => w.year).filter(y => y != null);
  return {a, ws, span: ys.length ? (Math.min(...ys) === Math.max(...ys) ? yl(ys[0]) : `${yl(Math.min(...ys))} – ${yl(Math.max(...ys))}`) : "Undated",
          media: [...new Set(ws.map(w => w.medium).filter(Boolean))]};
}).sort((x, y) => y.ws.length - x.ws.length || x.a.localeCompare(y.a));
$("#artists").innerHTML = groups.map(g => `<div class="artist"><h3>${esc(g.a)}</h3>
  <div class="meta">${g.ws.length} work${g.ws.length>1?"s":""} in this exhibit · ${esc(g.span)}</div>
  <div>${g.media.map(m => `<span class="badge">${esc(m)}</span>`).join("")}</div>
  <div class="strip">${g.ws.map(w => `<span onclick="open_(${idx(w)})" title="${esc(w.title)}">${img(w)}</span>`).join("")}</div></div>`).join("");

// tour
let stop = 0, speaking = false;
function blurb(w) {
  const n = byTime.indexOf(w), prev = byTime[n-1];
  let t = `${w.title}, by ${w.artist === "Unknown artist" ? "an unknown artist" : w.artist}, dates to ${w.date || "an unrecorded date"}. It is made of ${w.medium ? w.medium.toLowerCase() : "materials not recorded"}.`;
  if (w.extra) t += " " + w.extra;
  const others = WORKS.filter(x => x.artist === w.artist && x !== w && w.artist !== "Unknown artist");
  if (others.length) t += ` Look for ${others.length} more work${others.length>1?"s":""} by ${w.artist} in this exhibit.`;
  if (prev && prev.year != null && w.year != null && w.year !== prev.year) t += ` That is ${Math.abs(w.year - prev.year)} years ${w.year>prev.year?"after":"before"} the previous stop.`;
  return t;
}
function drawTour() {
  const w = byTime[stop];
  $("#tour").innerHTML = `<div class="tour"><div class="bar"><i style="width:${(stop+1)/byTime.length*100}%"></i></div>
   <div class="meta">Stop ${stop+1} of ${byTime.length}</div>${w.image ? img(w) : ""}
   <h2>${esc(w.title)}</h2><p class="meta">${esc(w.artist)} · ${esc(w.date)}</p><p>${esc(blurb(w))}</p>
   <div class="ctl"><button class="btn" id="pv">← Back</button><button class="btn primary" id="nx">${stop===byTime.length-1?"Restart":"Next →"}</button>
   <button class="btn" id="rd">${speaking?"■ Stop":"▶ Read aloud"}</button>
   <button class="btn" id="ta">Timeline</button></div></div>`;
  $("#pv").onclick = () => { stop = Math.max(0, stop-1); speechSynthesis?.cancel(); speaking=false; drawTour(); };
  $("#nx").onclick = () => { stop = (stop+1) % byTime.length; speechSynthesis?.cancel(); speaking=false; drawTour(); };
  $("#ta").onclick = () => go("timeline");
  $("#rd").onclick = () => {
    if (!window.speechSynthesis) return;
    if (speaking) { speechSynthesis.cancel(); speaking = false; return drawTour(); }
    const u = new SpeechSynthesisUtterance(blurb(w)); u.onend = () => { speaking = false; drawTour(); };
    speaking = true; speechSynthesis.speak(u); drawTour();
  };
}
drawTour();
document.addEventListener("keydown", e => {
  if (!$("#tour").classList.contains("on")) return;
  if (e.key === "ArrowRight") $("#nx").click(); if (e.key === "ArrowLeft") $("#pv").click();
});
</script></body></html>
"""


def build_page(records, title):
    blob = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
    return PAGE.replace("__TITLE__", title).replace("__DATA__", blob)


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Combine group JSON files into a food-themed exhibit page.")
    ap.add_argument("inputs", nargs="*", help="JSON files, globs, or folders (default: *.json here)")
    ap.add_argument("-o", "--out", default="food_exhibit.html")
    ap.add_argument("--title", default="Food in Art: A Combined Exhibit")
    args = ap.parse_args()

    combined_json = os.path.splitext(args.out)[0].replace("exhibit", "combined") + ".json"
    if combined_json == os.path.splitext(args.out)[0] + ".json":
        combined_json = "food_combined.json"
    skip = {os.path.basename(args.out), os.path.basename(combined_json)}

    paths = collect_paths(args.inputs, skip)
    if not paths:
        sys.exit("No JSON files found. Pass file paths or run inside the folder holding them.")

    records = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"  skipped {p}: {e}", file=sys.stderr)
            continue
        group = os.path.splitext(os.path.basename(p))[0]
        found = [r for r in (normalize(x, group) for x in find_records(raw)) if r]
        print(f"  {p}: {len(found)} works")
        records += found

    merged = merge(records)
    if not merged:
        sys.exit("No artworks recognised in the input files.")

    with open(combined_json, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_page(merged, args.title))

    n_art = len({r["artist"] for r in merged})
    print(f"\n{len(records)} records -> {len(merged)} unique works, {n_art} artists")
    print(f"Wrote {args.out} and {combined_json}")


if __name__ == "__main__":
    main()
