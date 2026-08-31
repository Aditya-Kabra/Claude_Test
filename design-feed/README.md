# Design Feed

A personalised, self-updating gallery of what design is making right now — pulled from the
galleries, magazines, studio blogs and communities where the work actually lands, then ranked
around what *you* keep coming back to.

**Live:** https://aditya-kabra.github.io/Claude_Test/design-feed/

```
design-feed/
├── index.html          the gallery — one file, no build step, no external requests
├── sources.json        the feed registry; edit this to add or drop a source
├── scripts/scrape.py   the scraper; standard library only
└── data/feed.json      generated — the only thing the page fetches
```

## How it works

A scheduled GitHub Action (`.github/workflows/design-feed.yml`) runs `scrape.py` twice a day.
The scraper pulls every source in `sources.json` in parallel, normalises RSS and Atom into one
shape, and writes a single `data/feed.json`. The page fetches that file and does everything
else — filtering, ranking, personalisation — in the browser.

### What the scraper does

- **Pulls ~50 sources** grouped into six families: galleries and showcases, magazines, brand
  and type, craft and practice blogs, communities (Reddit), and link feeds.
- **Groups requests by host.** Nine subreddit feeds hitting Reddit at once earns a 429, so
  feeds on the same host are walked one at a time with a gap while different hosts run in
  parallel.
- **Finds a picture for every item it can.** In order: `media:content` / `media:thumbnail`,
  `<enclosure>`, the first real `<img>` in the content body, and — for the text-only link
  feeds — the article's own `og:image`, fetched from the page. Thumbnails are traded up to
  the largest version the CDN will serve, and `preview.redd.it` URLs are rewritten to
  `i.redd.it`, which does not 403 when hotlinked.
- **Classifies each item** against a 22-topic taxonomy using whole-word matching, weighted so
  a hit in the title counts for more than one in the summary. The source contributes a prior
  strong enough to stand alone but weak enough to be outranked by the item's own words.
- **Dedupes** on canonical URL (tracking parameters stripped) and on title, so the same piece
  arriving via three aggregators becomes one card that says who else picked it up.
- **Works out what is actually trending** by counting title phrases — bigrams included — that
  appear across *independent* sources in the last week. Something several unconnected
  publications covered is a trend; something one site posted four times is not.
- **Scores each item** for heat: recency (about a 3.5-day half-life), source authority, how
  many sources are covering that topic, cross-posting, and whether it has an image.

The scraper degrades rather than fails. A source that times out, 429s or returns malformed XML
is reported in `feed.json` and shown struck through in the page footer; the run still
succeeds. It only returns a non-zero exit code if fewer than a third of sources responded.

### What the page does

**For You** is ranked in your browser:

```
score = 0.32·heat + 0.40·topic-fit + 0.14·source-fit + 0.14·recency − seen-penalty
```

Topic and source affinities start from the interests you pick on first visit and then move
every time you like, save, open or hide something — hiding moves them hardest, and in the
other direction. Everything is kept in `localStorage` under `designfeed.profile.v1` and never
leaves the browser; there is no analytics, no cookie, no request to anything but the source
sites' own image CDNs.

The other tabs are unpersonalised on purpose: **Trending** is the raw heat ranking, **Latest**
is reverse-chronological, **Saved** is your bookmarks.

Also in the page: search (`/` to focus), topic and source filters, a lightbox with arrow-key
navigation, light and dark themes, and shareable URLs — the view, query and filters all live
in the hash.

## Running it locally

```
python3 design-feed/scripts/scrape.py     # refresh data/feed.json (takes ~2 minutes)
python3 -m http.server 8000               # from the repository root
```

Then open http://localhost:8000/design-feed/. Opening `index.html` straight off disk will not
work — `fetch()` refuses `file://` URLs — and the page says so if you try.

Useful flags while working on the scraper:

| Flag | Effect |
| ---- | ------ |
| `--only behance,dezeen` | Pull just those sources. Writes to `data/_debug-feed.json` so it cannot clobber the real dataset. |
| `--no-enrich` | Skip the `og:image` lookups. Much faster; text-only sources end up without pictures. |
| `--limit 200` | Keep fewer items. |
| `--out PATH` | Write somewhere else. |

## Adding a source

Add an object to `sources.json`. Nothing else needs to change — the topic chips, source
filter, stats and footer all derive from the data.

| Field | Notes |
| ----- | ----- |
| `id` | Short slug, unique. Used in URLs and the source filter. |
| `name` | Display name. |
| `site` | Homepage, linked from cards and the footer. |
| `feed` | The RSS or Atom URL. |
| `kind` | `rss`, `atom` or `reddit`. Informational — the parser handles all of them the same way. |
| `family` | One of `gallery`, `editorial`, `brand`, `craft`, `social`, `link`. Drives the "Every kind" filter and the default card aspect ratio. |
| `weight` | Editorial authority, 0–1. Feeds the heat score. |
| `limit` | Most items to take from one pull. |
| `topics` | Default topic hints applied to every item, on top of what the scraper infers. |

Check it works before committing:

```
python3 design-feed/scripts/scrape.py --only your-new-id
```

If a site has no feed at all, leave it out. Godly and The Brand Identity were both dropped for
this reason — their grids are client-rendered, so the server HTML has images but no titles or
links, and a card with neither is not worth showing.

## Deploying

`.github/workflows/pages.yml` publishes the whole repository to GitHub Pages, so this folder
goes live at `/design-feed/` on every push to the default branch. The refresh workflow commits
`data/feed.json`, which triggers that deploy — so the site keeps updating on its own with
nothing to run by hand.

## A note on the images

Cards hotlink each source's own image, with `referrerpolicy="no-referrer"`, which is what most
of these CDNs are happiest with. Nothing is copied or rehosted, and every card links back to
the original. A few hosts block hotlinking anyway; when an image fails the card falls back to a
generated gradient tile carrying the title, keyed off the item id so it looks the same on every
visit rather than flickering between colours.
