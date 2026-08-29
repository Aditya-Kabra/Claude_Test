# Daily Start — Inspiration, Gratitude & Reminders

**Live:** https://aditya-kabra.github.io/Claude_Test/daily/

Short things to read before the day takes over, sorted into the areas you might actually need on
a given morning. 62 cards, 10 areas, 27 voices.

Everything is in one file, `index.html`. No build step, nothing to install, no external requests.
Icons are an inline SVG sprite from [Tabler Icons](https://tabler.io/icons) (MIT).

## The organising idea

The other two pages in this repository are directories of *organisations*. This one is a
directory of *small things to read*, filed the same way — because on a given morning you
usually know which **area** you need before you know which line you want:

| Area | For when you want… |
| --- | --- |
| **Inspiration** | a reason to aim higher than the day requires |
| **Gratitude** | to notice what is already here |
| **Motivation** | to start the thing you have been circling |
| **Joy & Delight** | more pleasure in the ordinary parts |
| **Reminders** | the thing you already know and keep forgetting |
| **Calm** | to come down before you act |
| **Focus** | to protect the hours that matter |
| **Resilience** | something for a day that has gone wrong |
| **Connection** | to be better company today |
| **Reflection** | to look at the day, before or after it |

Three secondary axes: **Moment** (morning, midday, evening, hard day, anytime), **Form** (read,
reframe, micro-practice, journal prompt, question, ritual) and **Voice** — the 27 writers,
researchers, athletes and teachers the lines come from.

## Quotation and paraphrase are separated

This is the part worth knowing before you quote anything from the page onward.

**`kind: "quote"`** — the line is **verbatim**, and `src` names where it is from. These render in
quotation marks with a solid rule and a blue **Quotation** tag. Where a line is a popular
rendering rather than a settled translation (the Marcus Aurelius and Rumi cards), `src` says so.

**`kind: "idea"`** — the line was **written for this page**, summarising an idea from that
person's work. These render in italics with a dashed rule and a grey **In our words** tag, and
the attribution reads "Written for this page, from …". They are never presented as something the
person said.

Nothing on the page invents a quotation and attributes it to a real person. If you want the
person's own wording for an `idea` card, the `src` line tells you where to go and the footer
links to them.

## What you can do with it

- **Your three for today** — three cards from three different areas, seeded on the date, so they
  are the same all day and the same on every device you open the page on. "Draw three more"
  reshuffles for this visit only; tomorrow starts from the date again. "The full card" clears any
  active filters, scrolls to that card and highlights it.
- **Search** across the lines, the context, the practices, the tags and the voices. `breathe`,
  `systems`, `hard day`, `Kobe` and `journal` all work.
- **Filter** on four independent axes at once. Within one axis the chips are an OR (pick two
  areas and you see both); across axes they are an AND (pick an area and a moment and you see
  only the overlap). Chip counts update as you filter, so a chip never promises results it cannot
  deliver.
- **Clear all filters** with the button that appears once anything is active.

The page follows your system light or dark theme.

## Adding or editing a card

All content is the `data` array in the `<script>` block. Each card is one object:

| Field    | Type     | Notes |
| -------- | -------- | ----- |
| `t`      | string   | Card title. Short — it is the handle, not the message. |
| `cat`    | string   | Area. Exactly one id from `themes`. Drives the coloured badge. |
| `voice`  | string   | Exactly one id from `voices`. |
| `moment` | string   | Exactly one id from `moments`. Drives the pill. |
| `kind`   | string   | `"quote"` or `"idea"`. See above — this one matters. |
| `src`    | string   | Provenance. For a quote, where it is from; for an idea, the work it draws on. |
| `q`      | string   | The line itself. Rendered in quotation marks only when `kind` is `"quote"`. |
| `d`      | string   | Two or three sentences of context. What the idea actually claims. |
| `p`      | string   | The "Try this" line. One concrete action, doable today. |
| `form`   | string[] | One or more ids from `forms`. |
| `time`   | number   | Minutes the practice realistically takes. Feeds the "Under 2 minutes" stat. |
| `tags`   | string[] | Free text. These are the small tags under the practice block. |

The four lookup tables sit directly above `data` and define every valid id:

- **`themes`** — `inspiration`, `gratitude`, `motivation`, `joy`, `reminders`, `calm`, `focus`,
  `resilience`, `connection`, `reflection`
- **`moments`** — `morning`, `midday`, `evening`, `hard`, `anytime`
- **`forms`** — `read`, `reframe`, `practice`, `write`, `ask`, `ritual`
- **`voices`** — 27 entries, each with `name`, `note` (what they are known for) and `url`

A new area needs an entry in `themes` **and** a matching `.cat-<id>` rule in the CSS palette
block; the same applies to a new moment (`.moment-<id>`). A new form also needs an `icon` value
pointing at a `<symbol>` in the SVG sprite at the top of `<body>` — add the symbol there first. A
new voice needs a real, working `url`. Nothing else needs to change: the stats, the filter chips,
the counts and today's three all derive from the data.

## A note on the content

The practices are drawn from published work by named people, and every card says which. Where a
claim is a research finding (the gratitude-journal studies, the spotlight effect, deliberate
practice) the `src` names the study or the book rather than gesturing at "science". Where a line
is popularly attributed but textually shaky, the card says that too.

None of it is medical or psychological advice, and a page of short readings is not a substitute
for talking to someone when a hard day turns out to be a hard year.
