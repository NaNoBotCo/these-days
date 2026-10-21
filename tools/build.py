#!/usr/bin/env python3
"""Writes docs/ (English) and docs/th/ from src/data.json.

Each tile shows its site's own share picture, read from the page's og:image at build
time; a site with none gets a one-line row. Counts are read live at build:
Mot Dang's record count from its API, NaNoBotCo's public GitHub Pages sites from gh.

  python3 tools/build.py            # build
  python3 tools/build.py --cards    # also redraw docs/card.png and docs/th/card.png
"""
import datetime, html, json, pathlib, re, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://nanobotco.github.io/these-days/"
CACHE = ROOT / "src" / "cache.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) these-days-build"}
e = html.escape


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(400_000).decode("utf-8", "replace")


def og_image(url):
    try:
        status, t = fetch(url)
    except Exception:
        return None
    m = (re.search(r'<meta[^>]+property=["\']og:image["\'][^>]*content=["\']([^"\']+)', t)
         or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', t))
    if not m:
        return None
    img = urllib.parse.urljoin(url, html.unescape(m.group(1)))
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(img, headers=UA, method=method)
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200 and r.headers.get("Content-Type", "").startswith("image"):
                    return img
        except Exception:
            pass
    return None


def counts(prev):
    out = dict(prev)
    try:
        _, t = fetch("https://motdang.net/api/v1/")
        out["records"] = json.loads(t)["count"]
    except Exception:
        pass
    try:
        r = subprocess.run(["gh", "api", "--paginate", "users/NaNoBotCo/repos?per_page=100&type=owner",
                            "-q", ".[] | select(.private==false and .has_pages==true) | .name"],
                           capture_output=True, text=True, timeout=120, check=True)
        out["sites"] = len([x for x in r.stdout.split() if x])
    except Exception:
        pass
    out["date"] = datetime.date.today().isoformat()
    return out


def tile(it, lang, img):
    name, line = it[lang]
    if img:
        return (f'<a class="tile" href="{e(it["url"])}"><img src="{e(img)}" alt="" loading="lazy" '
                f'width="1200" height="630"><span class="nm">{e(name)}</span><span class="ln">{e(line)}</span></a>')
    return f'<a class="row" href="{e(it["url"])}"><span class="nm">{e(name)}</span> <span class="ln">{e(line)}</span></a>'


def fmt_date(iso, lang):
    d = datetime.date.fromisoformat(iso)
    if lang == "th":
        mo = "ม.ค. ก.พ. มี.ค. เม.ย. พ.ค. มิ.ย. ก.ค. ส.ค. ก.ย. ต.ค. พ.ย. ธ.ค.".split()
        return f"{d.day} {mo[d.month-1]} {d.year + 543}"
    return d.strftime("%-d %b %Y")


def page(data, lang, imgs, n):
    m, f = data["meta"][lang], data["footer"]
    other = "en" if lang == "th" else "th"
    here = BASE + ("th/" if lang == "th" else "")
    card = here + "card.png"
    num = lambda x: f"{x:,}"
    secs = []
    for s in data["sections"]:
        h, line = s[lang]
        tiles = "".join(tile(it, lang, imgs.get(it["url"])) for it in s["items"])
        secs.append(f'<section id="{s["key"]}"><h2>{e(h)}</h2><p class="sub">{e(line)}</p><div class="grid">{tiles}</div></section>')
    css = (ROOT / "src" / "style.css").read_text()
    js = (ROOT / "src" / "lang.js").read_text() if lang == "en" else ""
    return f"""<!doctype html>
<html lang="{m['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(m['title'])}</title>
<meta name="description" content="{e(m['desc'])}">
<link rel="canonical" href="{here}">
<link rel="alternate" hreflang="en" href="{BASE}">
<link rel="alternate" hreflang="th" href="{BASE}th/">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(m['card_title'])}">
<meta property="og:description" content="{e(m['desc'])}">
<meta property="og:url" content="{here}">
<meta property="og:image" content="{card}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(m['card_title'])} {e(m['card_line'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(m['card_title'])}">
<meta name="twitter:description" content="{e(m['desc'])}">
<meta name="twitter:image" content="{card}">
<meta name="theme-color" content="#B3261E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Noto+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet">
<style>{css}</style>
{js}
</head>
<body>
<header class="top"><a class="me" href="{here}">NaN</a><a class="sw" href="{m['switch_href']}" hreflang="{other}" data-lang="{other}">{e(m['switch'])}</a></header>
<main>
<div class="hero"><h1>{e(m['q'])}</h1><p class="ans">{e(m['a'])}</p>
<p class="nums"><span><b>{num(n['records'])}</b> {e(m['records'])}</span><span><b>{num(n['sites'])}</b> {e(m['sites'])}</span><span class="dt">{e(m['counted'])} {fmt_date(n['date'], lang)}</span></p>
<nav class="toc">{''.join(f'<a href="#{s["key"]}">{e(s[lang][0])}</a>' for s in data['sections'])}</nav></div>
{''.join(secs)}
</main>
<footer><h2>{e(m['more'])}</h2><p class="links"><a href="{f['index']}">{e(m['index'])}</a><a href="{f['impossible']}">{e(m['impossible'])}</a><a href="{f['support']}">{e(m['support'])}</a><a href="mailto:{f['email']}">{e(m['hello'])} · {f['email']}</a></p>
<p class="by">NaN · NaNoBotCo</p></footer>
</body>
</html>
"""


def cards(data):
    import os, tempfile
    chrome = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    for lang in ("en", "th"):
        m = data["meta"][lang]
        path = "nanobotco.github.io/these-days/" + ("th/" if lang == "th" else "")
        font = "'Thonburi','Sukhumvit Set'" if lang == "th" else "Georgia,'Times New Roman',serif"
        doc = f"""<!doctype html><html lang="{lang}"><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:#FBF5EA;color:#1E1A17;font-family:{font}}}
.band{{position:absolute;left:0;top:0;bottom:0;width:28px;background:#B3261E}}
.t{{position:absolute;left:96px;top:88px;width:1000px}}
h1{{font-size:88px;line-height:1.12;font-weight:700;color:#B3261E;word-break:keep-all}}
p{{font-family:'Helvetica Neue',Arial,{font};font-size:40px;line-height:1.35;margin-top:30px;color:#4A3F37}}
.f{{position:absolute;left:96px;bottom:48px;font:30px 'Helvetica Neue',Arial,sans-serif;color:#7A6B5E}}
.n{{position:absolute;right:72px;bottom:40px;font:700 44px Georgia,serif;color:#1E1A17}}
</style><body><div class="band"></div><div class="t"><h1 id="h">{e(m['card_title'])}</h1><p>{e(m['card_line'])}</p></div>
<div class="f">{path}</div><div class="n">NaN</div>
<script>var h=document.getElementById('h'),t=document.querySelector('.t'),s=88;while(t.offsetHeight>420&&s>40){{s-=4;h.style.fontSize=s+'px';}}</script></body></html>"""
        with tempfile.TemporaryDirectory() as tmp:
            src = pathlib.Path(tmp) / "c.html"
            src.write_text(doc)
            out = ROOT / "docs" / ("th" if lang == "th" else "") / "card.png"
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            "--window-size=1200,630", f"--screenshot={out}", src.as_uri()], check=True, capture_output=True, timeout=60)


def main():
    import urllib.parse  # noqa: F401  (used by og_image)
    data = json.loads((ROOT / "src" / "data.json").read_text())
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {"images": {}, "counts": {"records": 0, "sites": 0}}
    urls = [it["url"] for s in data["sections"] for it in s["items"]]
    with ThreadPoolExecutor(8) as ex:
        found = dict(zip(urls, ex.map(og_image, urls)))
    imgs = {u: found[u] or cache["images"].get(u) for u in urls}
    n = counts(cache["counts"])
    CACHE.write_text(json.dumps({"images": imgs, "counts": n}, indent=1, ensure_ascii=False) + "\n")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "th").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(page(data, "en", imgs, n))
    (ROOT / "docs" / "th" / "index.html").write_text(page(data, "th", imgs, n))
    (ROOT / "docs" / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
    (ROOT / "docs" / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{BASE}</loc><lastmod>{n['date']}</lastmod></url><url><loc>{BASE}th/</loc><lastmod>{n['date']}</lastmod></url></urlset>\n")
    if "--cards" in sys.argv:
        cards(data)
    miss = [u for u in urls if not imgs[u]]
    print(f"built: {len(urls)} links, {len(urls) - len(miss)} with pictures; records {n['records']:,}, sites {n['sites']}")
    for u in miss:
        print("  no picture:", u)


if __name__ == "__main__":
    import urllib.parse
    main()
