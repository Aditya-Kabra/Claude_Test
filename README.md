> This repository holds five independent pages:
>
> - **[Smart Fabrics & E-Textiles](https://aditya-kabra.github.io/Claude_Test/)** — this page
> - **[Roleplay & Conversational Simulation](https://aditya-kabra.github.io/Claude_Test/roleplay/)** — see [`roleplay/`](roleplay/)
> - **[Design Feed](https://aditya-kabra.github.io/Claude_Test/design-feed/)** — a self-updating,
>   personalised gallery of trending design, scraped twice a day from ~50 sources.
>   See [`design-feed/`](design-feed/)
> - **[Daily Start](https://aditya-kabra.github.io/Claude_Test/daily/)** — short inspiration,
>   gratitude and reminder cards to start the day. See [`daily/`](daily/)
> - **[Pune AI Events](https://aditya-kabra.github.io/Claude_Test/pune-ai-events/)** — see [`pune-ai-events/`](pune-ai-events/)

# Global Smart Fabrics & E-Textiles Ecosystem Map

A directory of the organizations building electronic textiles worldwide: conductive fibers and
yarns, sensing garments, textile energy and actuation, interconnect and packaging, and the
research institutes and standards bodies behind them.

Everything lives in a single file, `index.html`. There is no build step, nothing to install,
and no external requests at all — the icons are an inline SVG sprite, so the page works
offline and from a local file. Icons are from [Tabler Icons](https://tabler.io/icons) (MIT).

## Viewing it

**Live:** https://aditya-kabra.github.io/Claude_Test/

Deployed by `.github/workflows/pages.yml`, which runs on pushes to `main` and to
`claude/smart-fabrics-use-cases-map-9armod` but only deploys from whichever of them is the
repository's **default branch** — GitHub's `github-pages` environment refuses deployments from
any other branch. The run on the non-default branch skips rather than failing, and the guard
re-targets itself if the default is changed.

Setup was a one-time manual step: **Settings → Pages → Source: GitHub Actions**. A workflow's
`GITHUB_TOKEN` can deploy to Pages but is not permitted to create the Pages site, so that first
switch has to be flipped by a repository admin.

Locally, open `index.html` in any browser, or serve it:

```
python3 -m http.server 8000
```

Then go to `http://localhost:8000`.

## What you can do with it

- **Search** across organization name, description, country, use cases, technology layers and
  standards. Typing `graphene`, `ECG`, `Japan` or `energy harvesting` all work.
- **Filter** on four independent axes at once. Within one axis the chips are an OR (pick two
  sectors and you see both); across axes they are an AND (pick a sector and a stage and you
  see only the overlap). Chip counts update as you filter, so a chip never promises results it
  cannot deliver.
- **Clear all filters** with the button that appears once anything is active.

The page follows your system light or dark theme.

## Adding or editing an entry

All content is the `data` array near the top of the `<script>` block. Each organization is one
object:

| Field   | Type       | Notes |
| ------- | ---------- | ----- |
| `n`     | string     | Organization name, shown in the card header and linked to `url`. |
| `cat`   | string     | Sector. Exactly one id from the `sectors` table. Drives the colored badge. |
| `url`   | string     | Homepage, opened in a new tab. |
| `hq`    | string     | Flag emoji plus country name, e.g. `"🇯🇵 Japan"`. Also feeds the Countries stat. |
| `f`     | string     | Year founded, or `"—"` if unknown. Hidden when `"—"`. |
| `fund`  | string     | Funding or funding type, or `"—"` if unknown. Hidden when `"—"`. |
| `stage` | string     | Maturity. Exactly one id from the `stages` table. |
| `layer` | string[]   | One or more ids from the `layers` table. |
| `cert`  | string[]   | Zero or more ids from the `certs` table. |
| `uc`    | string[]   | Free-text use cases. These are the tags in the Use Cases block. |
| `note`  | string     | Optional status line, e.g. an acquisition or a wind-down. `""` to omit. |
| `d`     | string     | One-paragraph description. |

The four lookup tables sit directly above `data` and define every valid id:

- **`sectors`** — `health`, `sports`, `defense`, `industrial`, `fashion`, `mobility`,
  `materials`, `energy`, `electronics`, `software`, `research`, `standards`
- **`stages`** — `research`, `pilot`, `commercial`
- **`layers`** — `fiber`, `sensing`, `energy`, `actuation`, `integration`, `software`
- **`certs`** — `oekotex`, `ce`, `fda`, `iso13485`, `milspec`, `ul`

Adding a new sector means adding an entry to `sectors` **and** a matching `.cat-<id>` rule in
the CSS palette block; the same applies to a new stage (`.stage-<id>`) or standard
(`.cert-<id>`). A new tech layer also needs an `icon` value pointing at a `<symbol>` in the
SVG sprite at the top of `<body>` — add the symbol there first. Nothing else needs to change —
the stats, filter chips and counts all derive from the data.

## A note on the data

Funding and founding figures were checked against public sources where possible, and left as
`"—"` rather than guessed where they could not be confirmed. Several well-known ventures in
this field have been wound down or absorbed; those are kept in the map with a `note` explaining
their status, because the history is part of what the map is for.
