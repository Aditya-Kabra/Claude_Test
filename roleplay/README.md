# Roleplay & Conversational Simulation Landscape

**Live:** https://aditya-kabra.github.io/Claude_Test/roleplay/

A map of where conversational AI plays a *role* in order to elicit, assess or develop human
capability — as opposed to doing the job itself. 61 use cases, 113 organisations, two linked
views.

Everything is in one file, `index.html`. No build step, nothing to install, no external
requests. Icons are an inline SVG sprite from [Tabler Icons](https://tabler.io/icons) (MIT).

## The organising idea

The primary axis is **the role the AI plays**, not the industry. Role predicts the buyer, the
failure mode and the defensibility much better than sector does:

| Role | The AI is… |
| --- | --- |
| **Counterpart** | the person you practise against — a prospect, a patient, a hostile witness |
| **Assessor** | the one interviewing you and scoring what it hears |
| **Subject** | a stand-in for a population being studied |
| **Adversary** | attacking you to test your defences |
| **Companion** | an ongoing relationship rather than an exercise |
| **Character** | narrative or entertainment |
| **Operator** | actually doing the job. The crowded zone, included so the contrast is visible |

Secondary axes are **Domain** (15), **Modality** (text, voice, video, VR/XR, human-in-the-loop)
and **Saturation**.

## Fact and judgement are separated

This map is deliberately opinionated, so it marks which parts are which.

**Record** — role, domain, modality, buyer, what it replaces, the organisations, and everything
on an organisation card. Sourced, and left blank rather than guessed.

**Judgement** — `saturation`, `verdict`, `why`, `risk` and `moat`. These are one analyst's read.
They render inside the accented verdict block and the collapsible analysis section, and the
verdict block carries a "my judgement" tag. Disagree with them freely; the record underneath
should still stand.

The **Rated Open** and **No Vendor Found** counters in the header are the two numbers the map
exists to produce. "No vendor found" means no purpose-built organisation was identified for that
use case at all, which is the strongest whitespace signal here.

## Using it

- **Two views.** *Use Cases* is the strategy layer; *Organisations* is the evidence. The tabs
  carry their own counts.
- **Filters** work as OR within a group and AND across groups. Chip counts recompute against
  the other groups, so a chip never promises an empty result. The Saturation group appears only
  in the use-case view.
- **Cross-link.** The "N organisations" button on a use-case card switches to the organisation
  view filtered to exactly that use case, with a chip showing what is pinned.
- **Search** covers names, descriptions, buyers, countries and the verdicts themselves — so
  searching `Medicaid` or `assessment centre` finds the argument, not just the label.
- **Full analysis** starts collapsed on each card; the verdict is always visible.

## Data schema

Two record types, both in the `<script>` block.

### `useCases[]`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | kebab-case, referenced by `orgs[].uc` |
| `name` | string | card heading |
| `role` | string | one id from `roles` |
| `domain` | string[] | ids from `domains` |
| `modality` | string[] | ids from `modalities` |
| `saturation` | string | one id from `saturations` — **judgement** |
| `buyer` | string | who actually pays |
| `replaces` | string | the incumbent spend being displaced |
| `why` / `risk` / `moat` | string | **judgement**, in the collapsible analysis |
| `verdict` | string | **judgement**, always visible |
| `orgs` | string[] | organisation names, must match `orgs[].n` |

### `orgs[]`

| Field | Type | Notes |
| --- | --- | --- |
| `n` | string | name, referenced by `useCases[].orgs` |
| `url` | string | homepage, https |
| `hq` | string | flag emoji plus country, or `"—"` |
| `f` / `fund` | string | founded and funding, `"—"` when not confirmed |
| `role` | string | one id from `roles` |
| `domain` / `modality` | string[] | as above |
| `uc` | string[] | use-case ids this org serves |
| `note` | string | optional status line, `""` to omit |
| `d` | string | one-paragraph description |

**The two cross-references must agree.** If a use case names an organisation, that organisation's
`uc[]` must name the use case back — otherwise the "N organisations" button lies about the count.
`scratchpad/check-roleplay.js` enforces this in both directions.

Adding a role, domain, modality or saturation means adding it to the lookup table **and** a
matching CSS class (`.role-<id>`, `.sat-<id>`), plus a `<symbol>` in the sprite for any new icon.

## Rebuilding

The page is assembled from parts to keep the shared CSS identical to the sibling map:

```
scratchpad/rp/{base.css,extra.css,data.js,orgs.js,app.js}  →  build-roleplay.py  →  index.html
```

`base.css` is extracted from `../index.html`, so the two maps cannot drift apart visually.
Editing `index.html` directly is fine for small fixes; regenerate if you change the shared CSS.

## On the data

Organisations were checked against public sources. Founding years and funding are `"—"` where
they could not be confirmed, rather than estimated. Companies that have wound down or been
acquired are kept with a status note where the history is instructive — Woebot's consumer
wind-down and Inworld's pivot away from being an NPC studio both say more about their categories
than a list of survivors would.
