#!/usr/bin/env python3
"""Build the Design Feed dataset.

Pulls every source listed in ../sources.json, normalises each entry into one
shape, works out what is trending across the web right now, and writes
../data/feed.json for the static gallery to read.

Standard library only -- no pip install, so the GitHub Action needs no setup
step. Run it from anywhere:

    python3 design-feed/scripts/scrape.py [--limit N] [--no-enrich] [--out PATH]
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import gzip
import hashlib
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCES_PATH = os.path.join(ROOT, "sources.json")
OUT_PATH = os.path.join(ROOT, "data", "feed.json")

UA = "Mozilla/5.0 (compatible; DesignFeedBot/1.0; +https://github.com/Aditya-Kabra/Claude_Test)"
FEED_TIMEOUT = 25
PAGE_TIMEOUT = 15
MAX_PAGE_BYTES = 200_000     # og:image lives in <head>, so the first chunk is plenty
ENRICH_BUDGET = 220          # cap on article pages fetched for a missing image
HOST_GAP = 3.5               # seconds between two feeds on the same host
MAX_AGE_DAYS = 45            # anything older is dropped; galleries recycle old posts
TARGET_ITEMS = 900


# --------------------------------------------------------------------------
# Topic taxonomy. Each topic is matched against title + summary + feed tags.
# Order matters only for the "primary" topic shown on a card.
# --------------------------------------------------------------------------
TOPICS = {
    "ui-ux":        ["ui", "ux", "user interface", "user experience", "usability", "interaction design",
                     "design system", "wireframe", "prototype", "onboarding", "dashboard", "app design",
                     "mobile app", "ios", "android", "figma", "microinteraction", "navigation", "form design"],
    "web-design":   ["website", "web design", "landing page", "homepage", "site of the day", "sotd",
                     "portfolio site", "webflow", "one page", "scroll", "hero section", "web experience",
                     "responsive", "awwwards"],
    "branding":     ["brand", "branding", "logo", "identity", "rebrand", "visual identity", "wordmark",
                     "packaging", "brand new", "monogram", "brand system", "naming"],
    "typography":   ["typography", "typeface", "font", "lettering", "type design", "serif", "sans",
                     "variable font", "kerning", "calligraphy", "glyph"],
    "illustration": ["illustration", "illustrator", "drawing", "character design", "comic", "sketch",
                     "hand drawn", "collage"],
    "motion":       ["motion", "animation", "animated", "after effects", "kinetic", "transition",
                     "gsap", "lottie", "video", "reel", "loop"],
    "3d":           ["3d", "blender", "cinema 4d", "render", "webgl", "three.js", "spline", "voxel",
                     "raytrac", "shader"],
    "product":      ["product design", "startup", "saas", "launch", "product hunt", "feature", "pricing page",
                     "roadmap", "product team"],
    "industrial":   ["industrial design", "furniture", "chair", "lamp", "appliance", "concept car",
                     "wearable", "hardware", "gadget", "materials", "ceramic", "prototype model"],
    "architecture": ["architecture", "architect", "pavilion", "facade", "building", "housing",
                     "museum", "studio designs", "renovation", "urban"],
    "interior":     ["interior", "apartment", "kitchen", "living room", "workspace", "hotel", "restaurant design",
                     "showroom", "loft"],
    "graphic":      ["poster", "editorial design", "print", "layout", "graphic design", "book cover",
                     "magazine", "zine", "album art", "signage"],
    "photography":  ["photograph", "photo series", "portrait", "photographer", "camera", "film photography"],
    "art":          ["artist", "sculpture", "installation", "gallery show", "exhibition", "painting", "mural"],
    "ai":           ["ai ", "artificial intelligence", "machine learning", "genai", "generative", "midjourney",
                     "chatgpt", "claude", "llm", "diffusion", "copilot", "prompt"],
    "accessibility":["accessib", "a11y", "wcag", "screen reader", "contrast ratio", "inclusive design",
                     "keyboard navigation"],
    "css-code":     ["css", "html", "javascript", "front-end", "frontend", "tailwind", "react", "svg",
                     "grid layout", "flexbox", "container quer", "browser", "web component", "code"],
    "color":        ["color", "colour", "palette", "gradient", "contrast", "pantone", "hue"],
    "tools":        ["tool", "plugin", "app for", "release", "version", "open source", "library",
                     "template", "resource", "freebie", "toolkit"],
    "portfolio":    ["portfolio", "case study", "cv", "resume", "personal site", "showcase"],
    "inspiration":  ["inspiration", "roundup", "best of", "collection", "curated", "showcase", "trends",
                     "moodboard", "gallery"],
    "research":     ["research", "study", "usability test", "data", "survey", "report", "analytics",
                     "user testing", "metrics"],
}

TOPIC_LABELS = {
    "ui-ux": "UI / UX", "web-design": "Web Design", "branding": "Branding", "typography": "Typography",
    "illustration": "Illustration", "motion": "Motion", "3d": "3D", "product": "Product",
    "industrial": "Industrial", "architecture": "Architecture", "interior": "Interiors",
    "graphic": "Graphic", "photography": "Photography", "art": "Art", "ai": "AI",
    "accessibility": "Accessibility", "css-code": "Code & CSS", "color": "Color", "tools": "Tools",
    "portfolio": "Portfolios", "inspiration": "Inspiration", "research": "Research",
}

STOPWORDS = set("""
a an the and or but if then than that this these those with without within from into onto of for to in on at
by as is are was were be been being it its you your yours we our us they them their he she his her i me my
mine how what why when where who which whom whose can could should would will shall may might must do does
did done doing have has had having not no nor so such very more most much many few own same just also about
after before again further once here there all any both each other some now because while during since until
against between over under above below out off down up back inside outside around across through
get got gets make makes made making take takes taken give gives given go goes going come comes came
need needs needed want wants like likes look looks looking see seen show shows shown know knows knew
think thinks say says said work works working try tries trying find finds found keep keeps still even ever
every only really let lets start starts stop stops begin begins end ends turn turns put puts
new news best top great good better worse worst nice cool awesome amazing beautiful stunning perfect
big small long short high low old young full free real true false right left wrong easy hard simple
first last next part one two three four five six seven eight nine ten 2023 2024 2025 2026 2027
way ways thing things year years day days week weeks month months time times today tomorrow
people person team teams world global everything something anything nothing someone everyone
guide guides tip tips trick tricks tutorial list lists roundup weekly daily monthly issue issues
post posts article articles blog blogs read reads reading watch watching help helps helping
use uses used using via vs versus into onto plus including includes include based
love loves hate hates want wanted plus minus more less
project projects studio studios client clients company companies collection collections
design designs designer designers designed designing built build builds building
system systems concept concepts idea ideas thought thoughts question questions answer answers
""".split())


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
def http_get(url: str, timeout: int, max_bytes: int | None = None, retries: int = 2) -> bytes:
    """GET a URL, following redirects, with a couple of retries and gzip support."""
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read(max_bytes) if max_bytes else resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    try:
                        raw = gzip.decompress(raw)
                    except OSError:
                        # A truncated gzip stream still decodes far enough for <head>.
                        raw = gzip.GzipFile(fileobj=__import__("io").BytesIO(raw)).read(max_bytes or -1)
                return raw
        except Exception as exc:                                  # noqa: BLE001 - report, don't crash the run
            last = exc
            if attempt < retries:
                throttled = isinstance(exc, urllib.error.HTTPError) and exc.code in (429, 503)
                time.sleep((9.0 if throttled else 1.5) * (attempt + 1))
    raise last if last else RuntimeError("unreachable")


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</p>", " ", text)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return WS_RE.sub(" ", text).strip()


def clamp(text: str, length: int) -> str:
    text = text.strip()
    if len(text) <= length:
        return text
    cut = text[:length].rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:-") + "…"


def local(tag: str) -> str:
    """Strip the XML namespace from an element tag."""
    return tag.rsplit("}", 1)[-1].lower()


DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M %z",
    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d %b %Y %H:%M:%S %z",
]


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    normalised = re.sub(r"\s+", " ", value).replace("GMT", "+0000").replace("UTC", "+0000")
    normalised = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", normalised)
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(normalised, fmt)
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Image extraction
# --------------------------------------------------------------------------
BAD_IMAGE_BITS = (
    "gravatar", "feedburner", "pixel.", "/pixel", "spacer.gif", "blank.gif", "1x1", "doubleclick",
    "googleadservices", "twitter.com/i/", "badge", "rss.png", "icon-", "favicon", "avatar",
    "emoji", "/ads/", "sharethis", "addtoany", "gif;base64", "stat?", "count.gif",
    "external-preview.redd.it",   # reddit's proxy for off-site images; 403s on hotlink
)
IMG_EXT_RE = re.compile(r"\.(jpe?g|png|webp|avif|gif)(?:[?#]|$)", re.I)


def usable_image(url: str) -> bool:
    if not url or len(url) < 12:
        return False
    low = url.lower()
    if not low.startswith("http"):
        return False
    if any(bit in low for bit in BAD_IMAGE_BITS):
        return False
    return True


def upgrade_image(url: str) -> str:
    """Trade a thumbnail URL up for the largest version the CDN will serve."""
    url = html.unescape(url).strip()
    url = url.replace("http://", "https://", 1) if url.startswith("http://") else url
    # Medium (Muzli, UX Collective, UX Planet, Prototypr)
    url = re.sub(r"(cdn-images-\d+\.medium\.com/max/)\d+", r"\g<1>1400", url)
    url = re.sub(r"(miro\.medium\.com/(?:v2/)?(?:resize:fit:)?)\d+", r"\g<1>1400", url)
    # WordPress resized copies -> original
    url = re.sub(r"-\d{3,4}x\d{3,4}(\.(?:jpe?g|png|webp))", r"\1", url, flags=re.I)
    # Common ?w= / &width= query thumbnails
    url = re.sub(r"([?&](?:w|width))=\d{1,3}\b", r"\1=1200", url, flags=re.I)
    # preview.redd.it needs a signed query and 403s when hotlinked; the same
    # asset is served unsigned from i.redd.it. external-preview has no such
    # twin, so it is rejected outright by usable_image() below.
    url = re.sub(r"^https://preview\.redd\.it/([^?]+).*$", r"https://i.redd.it/\1", url)
    return url


def first_image_in_html(blob: str) -> str:
    if not blob:
        return ""
    for match in re.finditer(r"<img[^>]+>", blob, re.I):
        tag = match.group(0)
        src = ""
        for attr in ("data-src", "data-lazy-src", "src"):
            found = re.search(rf'{attr}=["\']([^"\']+)["\']', tag, re.I)
            if found:
                src = found.group(1)
                break
        if not src:
            srcset = re.search(r'srcset=["\']([^"\']+)["\']', tag, re.I)
            if srcset:
                src = srcset.group(1).split(",")[-1].strip().split(" ")[0]
        src = html.unescape(src or "")
        if usable_image(src):
            return src
    return ""


META_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image(?::secure_url)?|twitter:image(?::src)?)["\'][^>]*>', re.I)


def image_from_page(page_html: str) -> str:
    for tag in META_IMAGE_RE.findall(page_html):
        found = re.search(r'content=["\']([^"\']+)["\']', tag, re.I)
        if found and usable_image(html.unescape(found.group(1))):
            return html.unescape(found.group(1))
    found = re.search(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)["\']', page_html, re.I)
    if found and usable_image(found.group(1)):
        return html.unescape(found.group(1))
    return ""


# --------------------------------------------------------------------------
# Feed parsing
# --------------------------------------------------------------------------
def element_text(el: ET.Element) -> str:
    return "".join(el.itertext())


def parse_entry(entry: ET.Element, source: dict) -> dict | None:
    """Normalise one <item> (RSS) or <entry> (Atom) into the feed shape."""
    title = link = summary = author = ""
    published = None
    image = ""
    width = height = 0
    tags: list[str] = []
    content_blobs: list[str] = []

    for child in entry:
        name = local(child.tag)
        text = (child.text or "").strip()

        if name == "title" and not title:
            title = strip_html(element_text(child))
        elif name == "link":
            href = child.get("href") or text
            rel = (child.get("rel") or "alternate").lower()
            typ = (child.get("type") or "").lower()
            if rel == "enclosure" or "image" in typ:
                candidate = upgrade_image(href)
                if usable_image(candidate) and not image:
                    image = candidate
            elif rel in ("alternate", "") and href and not link:
                link = href
        elif name in ("guid", "id") and not link and text.startswith("http"):
            link = text
        elif name in ("description", "summary", "subtitle"):
            content_blobs.append(text or element_text(child))
            if not summary:
                summary = strip_html(text or element_text(child))
        elif name in ("encoded", "content"):
            content_blobs.append(text or element_text(child))
            if not summary:
                summary = strip_html(text or element_text(child))
        elif name in ("pubdate", "published", "updated", "date", "created"):
            published = published or parse_date(text)
        elif name in ("creator", "author", "name"):
            author = author or strip_html(element_text(child))
        elif name == "category":
            label = (child.get("term") or text).strip()
            if label:
                tags.append(label)
        elif name in ("content", "thumbnail") and child.get("url"):
            typ = (child.get("type") or child.get("medium") or "").lower()
            candidate = upgrade_image(child.get("url"))
            if usable_image(candidate) and ("image" in typ or not typ or IMG_EXT_RE.search(candidate)):
                if not image or (child.get("width") or "0").isdigit() and int(child.get("width") or 0) > width:
                    image = candidate
                    width = int(child.get("width") or 0)
                    height = int(child.get("height") or 0)
        elif name == "group":
            for grand in child:
                if grand.get("url") and usable_image(upgrade_image(grand.get("url"))):
                    candidate = upgrade_image(grand.get("url"))
                    w = int(grand.get("width") or 0)
                    if not image or w > width:
                        image, width, height = candidate, w, int(grand.get("height") or 0)
        elif name == "enclosure" and child.get("url"):
            candidate = upgrade_image(child.get("url"))
            if usable_image(candidate) and "image" in (child.get("type") or "image"):
                image = image or candidate

    if not title or not link:
        return None

    if not image:
        for blob in content_blobs:
            found = first_image_in_html(blob)
            if found:
                image = upgrade_image(found)
                break

    # dc:creator often arrives as "someone@example.com (Real Name)" -- keep the
    # name, drop the address; nobody needs a byline that doubles as an email.
    named = re.match(r"^\s*\S+@\S+\s*\((.+)\)\s*$", author)
    if named:
        author = named.group(1)
    author = re.sub(r"\S+@\S+\.\S+", "", author)
    author = re.sub(r"^/?u/", "", author).strip(" -–—()")
    if author.lower() in ("", "admin", "editor", "staff", "team"):
        author = ""

    return {
        "title": clamp(title, 160),
        "url": link.strip(),
        "summary": clamp(summary, 320),
        "author": clamp(author, 60),
        "image": image,
        "w": width,
        "h": height,
        "published": published,
        "feedTags": tags[:8],
    }


FIELD_PATTERNS = {
    "title": r"<title[^>]*>(.*?)</title>",
    "link": r"<link[^>]*>(.*?)</link>",
    "summary": r"<description[^>]*>(.*?)</description>",
    "date": r"<(?:pubDate|published|updated|dc:date)[^>]*>(.*?)</(?:pubDate|published|updated|dc:date)>",
    "author": r"<(?:dc:creator|author)[^>]*>(.*?)</(?:dc:creator|author)>",
}


def unwrap_cdata(text: str) -> str:
    return re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text or "", flags=re.S)


def parse_feed_loose(text: str, source: dict) -> list[dict]:
    """Last-resort parser for feeds that are not valid XML."""
    out = []
    blocks = re.findall(r"<(item|entry)\b.*?</\1>", text, re.S | re.I)
    for block in blocks[: source.get("limit", 20)]:
        field = {}
        for key, pattern in FIELD_PATTERNS.items():
            found = re.search(pattern, block, re.S | re.I)
            field[key] = unwrap_cdata(found.group(1)).strip() if found else ""
        if not field["link"]:
            href = re.search(r'<link[^>]+href=["\']([^"\']+)', block, re.I)
            guid = re.search(r"<guid[^>]*>(https?://[^<]+)</guid>", block, re.I)
            field["link"] = (href.group(1) if href else guid.group(1) if guid else "")
        title = strip_html(field["title"])
        link = html.unescape(field["link"]).strip()
        if not title or not link.startswith("http"):
            continue
        image = first_image_in_html(block)
        if not image:
            media = re.search(r'<(?:media:content|media:thumbnail|enclosure)[^>]+url=["\']([^"\']+)', block, re.I)
            image = media.group(1) if media else ""
        image = upgrade_image(html.unescape(image)) if image else ""
        out.append({
            "title": clamp(title, 160), "url": link,
            "summary": clamp(strip_html(field["summary"]), 320),
            "author": clamp(strip_html(field["author"]), 60),
            "image": image if usable_image(image) else "",
            "w": 0, "h": 0, "published": parse_date(field["date"]), "feedTags": [],
        })
    return out


def parse_feed(raw: bytes, source: dict) -> list[dict]:
    text = raw.decode("utf-8", "replace")
    text = text.lstrip("﻿ \r\n\t")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        # A stray raw ampersand or control char breaks strict XML; patch and retry once.
        patched = re.sub(r"&(?!#?\w{1,8};)", "&amp;", text)
        patched = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", patched)
        try:
            root = ET.fromstring(patched)
        except ET.ParseError:
            # Some feeds ship raw unescaped HTML in <description>. Fall back to
            # pulling the fields out with regex rather than losing the source.
            entries = parse_feed_loose(patched, source)
            if entries:
                return entries
            raise ValueError("unparseable XML and no items found by fallback") from None

    entries: list[ET.Element] = []
    for el in root.iter():
        if local(el.tag) in ("item", "entry"):
            entries.append(el)

    out = []
    for el in entries[: source.get("limit", 20)]:
        try:
            parsed = parse_entry(el, source)
        except Exception:                                          # noqa: BLE001
            parsed = None
        if parsed:
            out.append(parsed)
    return out


# --------------------------------------------------------------------------
# Enrichment, classification, scoring
# --------------------------------------------------------------------------
# Whole-word matching matters here: a plain substring test makes "ui" fire on
# "building" and "3d" on "h3ading", which drags half the feed into UI / UX.
TOPIC_RE = {
    topic: re.compile(r"\b(?:" + "|".join(re.escape(k.strip()) for k in sorted(kws, key=len, reverse=True)) + r")\b", re.I)
    for topic, kws in TOPICS.items()
}


def infer_topics(item: dict, source: dict) -> list[str]:
    title = item["title"]
    body = " ".join([item["summary"], " ".join(item.get("feedTags", []))])
    scores: Counter = Counter()
    for topic, pattern in TOPIC_RE.items():
        in_title = len(pattern.findall(title))
        in_body = len(pattern.findall(body))
        if in_title or in_body:
            scores[topic] += min(in_title, 2) * 2.5 + min(in_body, 3) * 1.0
    # The source itself is a prior, not a verdict: strong enough to stand alone
    # when nothing matched, weak enough to be outranked by the item's own words.
    for topic in source.get("topics", []):
        scores[topic] += 1.6
    ranked = [t for t, score in scores.most_common(6) if score >= 1.5][:4]
    return ranked or ["inspiration"]


def enrich_images(items: list[dict], budget: int) -> int:
    """Fetch og:image for items whose feed carried no picture. Bounded and parallel."""
    targets = [i for i in items if not i["image"]][:budget]
    if not targets:
        return 0

    def work(item):
        try:
            page = http_get(item["url"], PAGE_TIMEOUT, MAX_PAGE_BYTES, retries=0)
            found = image_from_page(page.decode("utf-8", "replace"))
            if found:
                item["image"] = upgrade_image(urllib.parse.urljoin(item["url"], found))
                return 1
        except Exception:                                          # noqa: BLE001
            pass
        return 0

    with futures.ThreadPoolExecutor(max_workers=16) as pool:
        return sum(pool.map(work, targets))


def canonical(url: str) -> str:
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return url.lower()
    query = urllib.parse.parse_qsl(parts.query)
    query = [(k, v) for k, v in query if not k.lower().startswith(("utm_", "ref", "source", "fbclid", "mc_"))]
    netloc = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit(("https", netloc, path, urllib.parse.urlencode(query), ""))


def title_key(title: str) -> str:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return " ".join(w for w in words if w not in STOPWORDS)[:80]


def phrases_of(item: dict) -> set[str]:
    """Unigrams and bigrams worth counting as a trend signal.

    Bigrams carry most of the meaning here -- "brand identity" and "design
    system" say something, "brand" and "system" on their own barely do -- so
    both are counted and bigrams win the ranking later.
    """
    tokens = re.findall(r"[a-z][a-z0-9'+.-]{1,}", item["title"].lower())
    tokens = [t.strip("'.-") for t in tokens]
    out: set[str] = set()
    for word in tokens:
        if len(word) >= 5 and word not in STOPWORDS:
            out.add(word)
    for a, b in zip(tokens, tokens[1:]):
        if len(a) >= 3 and len(b) >= 3 and a not in STOPWORDS and b not in STOPWORDS:
            out.add(f"{a} {b}")
    return out


def deterministic_ratio(item: dict) -> float:
    """A stable aspect ratio so the masonry has no layout shift before images load.

    Real dimensions win when the feed supplied them; otherwise a per-family
    default is jittered by a hash of the id so the grid keeps a varied rhythm.
    """
    if item.get("w") and item.get("h"):
        return max(0.55, min(2.2, round(item["w"] / item["h"], 3)))
    base = {"gallery": 1.34, "editorial": 1.5, "craft": 1.6, "brand": 1.25,
            "link": 1.6, "social": 1.0}.get(item["family"], 1.4)
    seed = int(hashlib.md5(item["id"].encode()).hexdigest()[:8], 16)
    jitter = [-0.32, -0.16, 0.0, 0.0, 0.18, 0.36][seed % 6]
    return round(max(0.62, min(2.0, base + jitter)), 3)


def build(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Scrape design sources into feed.json")
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--limit", type=int, default=TARGET_ITEMS, help="max items to keep")
    ap.add_argument("--no-enrich", action="store_true", help="skip og:image lookups")
    ap.add_argument("--only", default="", help="comma-separated source ids, for debugging")
    args = ap.parse_args(argv)
    if args.only and args.out == OUT_PATH:
        args.out = os.path.join(ROOT, "data", "_debug-feed.json")
        print(f"--only is set, writing to {args.out} instead of the real dataset", file=sys.stderr)

    registry = json.load(open(SOURCES_PATH, encoding="utf-8"))["sources"]
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        registry = [s for s in registry if s["id"] in wanted]

    now = datetime.now(timezone.utc)
    oldest = now - timedelta(days=MAX_AGE_DAYS)
    report: list[dict] = []
    collected: list[dict] = []

    def pull(source):
        started = time.time()
        try:
            raw = http_get(source["feed"], FEED_TIMEOUT)
            entries = parse_feed(raw, source)
            return source, entries, None, time.time() - started
        except Exception as exc:                                   # noqa: BLE001
            return source, [], f"{type(exc).__name__}: {exc}"[:140], time.time() - started

    # Reddit answers 429 when nine subreddit feeds arrive at once. Grouping by
    # host and walking each group sequentially keeps one polite connection per
    # site while different sites still run in parallel.
    by_host: dict[str, list[dict]] = defaultdict(list)
    for source in registry:
        by_host[urllib.parse.urlsplit(source["feed"]).netloc.lower()].append(source)

    def pull_host(group):
        out = []
        for index, source in enumerate(group):
            if index:
                time.sleep(HOST_GAP)
            out.append(pull(source))
        return out

    print(f"Pulling {len(registry)} sources across {len(by_host)} hosts...", file=sys.stderr)
    with futures.ThreadPoolExecutor(max_workers=14) as pool:
        results = [r for group in pool.map(pull_host, by_host.values()) for r in group]

    for source, entries, error, elapsed in results:
        report.append({
            "id": source["id"], "name": source["name"], "site": source["site"],
            "family": source["family"], "items": len(entries),
            "ok": error is None, "error": error, "ms": int(elapsed * 1000),
        })
        status = "ok  " if error is None else "FAIL"
        print(f"  {status} {source['id']:<20} {len(entries):>3} items  {int(elapsed*1000):>5}ms"
              + (f"  {error}" if error else ""), file=sys.stderr)

        for entry in entries:
            published = entry["published"]
            if published and published > now + timedelta(hours=12):
                published = now                                    # a few feeds post-date entries
            if published and published < oldest:
                continue
            entry.update({
                "source": source["id"], "sourceName": source["name"], "sourceSite": source["site"],
                "family": source["family"], "weight": source.get("weight", 0.7),
                "published": published or now - timedelta(days=3),
                "dated": published is not None,
            })
            collected.append(entry)

    # ---- dedupe: same canonical URL, or the same title from a different aggregator
    by_url: dict[str, dict] = {}
    seen_titles: dict[str, str] = {}
    for entry in sorted(collected, key=lambda e: -e["weight"]):
        key = canonical(entry["url"])
        tkey = title_key(entry["title"])
        if key in by_url:
            by_url[key]["alsoOn"].append(entry["sourceName"])
            continue
        if len(tkey) > 25 and tkey in seen_titles:
            by_url[seen_titles[tkey]]["alsoOn"].append(entry["sourceName"])
            continue
        entry["alsoOn"] = []
        entry["id"] = hashlib.sha1(key.encode()).hexdigest()[:12]
        by_url[key] = entry
        seen_titles[tkey] = key

    items = list(by_url.values())
    print(f"{len(collected)} raw -> {len(items)} unique", file=sys.stderr)

    # ---- classify
    source_by_id = {s["id"]: s for s in registry}
    for item in items:
        item["topics"] = infer_topics(item, source_by_id[item["source"]])

    # ---- fill in missing images from the article page itself
    missing = sum(1 for i in items if not i["image"])
    if not args.no_enrich and missing:
        print(f"Fetching og:image for up to {min(missing, ENRICH_BUDGET)} of {missing} imageless items...",
              file=sys.stderr)
        found = enrich_images(items, ENRICH_BUDGET)
        print(f"  recovered {found} images", file=sys.stderr)

    # ---- trending signals: what many independent sources are talking about
    topic_sources = defaultdict(set)
    keyword_sources = defaultdict(set)
    keyword_count = Counter()
    recent_cutoff = now - timedelta(days=7)
    for item in items:
        if item["published"] < recent_cutoff:
            continue
        for topic in item["topics"]:
            topic_sources[topic].add(item["source"])
        for phrase in phrases_of(item):
            keyword_sources[phrase].add(item["source"])
            keyword_count[phrase] += 1

    max_topic_spread = max((len(v) for v in topic_sources.values()), default=1)

    def trend_score(phrase: str) -> float:
        spread = len(keyword_sources[phrase])
        volume = keyword_count[phrase]
        bigram_bonus = 1.35 if " " in phrase else 1.0
        return (spread * 2.5 + math.log1p(volume) * 3.0) * bigram_bonus

    candidates = [p for p, srcs in keyword_sources.items()
                  if len(srcs) >= (2 if " " in p else 3) and keyword_count[p] >= (3 if " " in p else 5)]
    candidates.sort(key=lambda p: (-trend_score(p), p))

    # Drop a unigram once a stronger bigram already contains it -- "identity"
    # under "brand identity" is noise, not a second trend.
    chosen: list[str] = []
    for phrase in candidates:
        if " " not in phrase and any(phrase in c.split() for c in chosen if " " in c):
            continue
        chosen.append(phrase)
        if len(chosen) >= 20:
            break
    trending_terms = [(p, keyword_count[p], len(keyword_sources[p])) for p in chosen]

    # ---- score
    for item in items:
        age_hours = max(0.0, (now - item["published"]).total_seconds() / 3600)
        recency = math.exp(-age_hours / 84.0)                      # ~3.5 day half-life
        spread = max(len(topic_sources[t]) for t in item["topics"]) / max_topic_spread
        cross = min(len(item["alsoOn"]), 3) / 3.0
        richness = min(len(item["summary"]) / 240.0, 1.0)
        heat = (0.40 * recency + 0.22 * item["weight"] + 0.16 * spread
                + 0.10 * cross + 0.07 * (1.0 if item["image"] else 0.0) + 0.05 * richness)
        item["heat"] = round(heat, 4)
        item["ratio"] = deterministic_ratio(item)

    items.sort(key=lambda i: -i["heat"])
    items = items[: args.limit]

    payload = {
        "generated": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "count": len(items),
        "withImages": sum(1 for i in items if i["image"]),
        "topics": [{"id": t, "label": TOPIC_LABELS[t],
                    "count": sum(1 for i in items if t in i["topics"]),
                    "sources": len(topic_sources.get(t, ()))}
                   for t in TOPICS
                   if sum(1 for i in items if t in i["topics"]) > 0],
        "trending": [{"term": w, "count": c, "sources": s} for w, c, s in trending_terms],
        "sources": sorted(report, key=lambda r: (not r["ok"], r["name"].lower())),
        "items": [{
            "id": i["id"], "t": i["title"], "u": i["url"], "s": i["summary"], "a": i["author"],
            "img": i["image"], "src": i["source"], "srcName": i["sourceName"], "site": i["sourceSite"],
            "fam": i["family"], "tp": i["topics"], "ts": i["published"].replace(microsecond=0)
                .isoformat().replace("+00:00", "Z"),
            "heat": i["heat"], "r": i["ratio"],
            "also": sorted(set(i["alsoOn"]))[:3],
        } for i in items],
    }
    payload["topics"].sort(key=lambda t: -t["count"])

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write("\n")

    ok_sources = sum(1 for r in report if r["ok"])
    size_kb = os.path.getsize(args.out) / 1024
    print(f"\nWrote {args.out}: {len(items)} items, {payload['withImages']} with images, "
          f"{ok_sources}/{len(report)} sources ok, {size_kb:.0f} KB", file=sys.stderr)
    if ok_sources < max(3, len(report) // 3):
        print("Too few sources responded -- refusing to call this a good run.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
