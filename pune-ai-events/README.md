# Pune AI Events

**Live:** https://aditya-kabra.github.io/Claude_Test/pune-ai-events/

A calendar of upcoming artificial intelligence meetups, hackathons, workshops and conferences in
and around Pune — hackathons run by AI Tinkerers, community meetups from the Pune AI Group and
Pune AI & Data Science Community, corporate tech sessions, and academic AI conferences.

Design is inspired by [kochi.buzz](https://www.kochi.buzz/) (source:
[vaishakh3/kochibuzz](https://github.com/vaishakh3/kochibuzz)) — a list view grouped by date, a
month calendar grid with clickable event dots, filter chips with live counts, and per-event
calendar export. Unlike kochi.buzz this page has no backend or sync pipeline: it is a single
static `index.html` with the event data hand-curated straight into the page, matching the rest of
this repo's pages (no build step, nothing to install, no external requests, follows your system
light or dark theme).

## Viewing it

Open `index.html` in any browser, or serve it:

```
python3 -m http.server 8000
```

Then go to `http://localhost:8000/pune-ai-events/`.

## What you can do with it

- **Search** across title, organizer, description and event type.
- **Filter** by type (Hackathon, Meetup, Workshop, Conference, Corporate / Vendor) and by format
  (In-person, Online). Chip counts update live as you filter.
- **Switch views.** List groups events by month; Calendar shows a month grid (September and
  October 2026) with a dot on any date that has an event — click a date to filter the list to
  just that day, click again to clear it.
- **Add to calendar** downloads a per-event `.ics` file generated client-side (no server, no
  network request) for events with a confirmed date.

## Adding or editing an event

All content is the `events` array near the top of the `<script>` block. Each event is one object:

| Field     | Type   | Notes |
| --------- | ------ | ----- |
| `id`      | string | kebab-case, unique, used as the `.ics` filename. |
| `date`    | string | ISO `YYYY-MM-DD`, or `null` if only "date TBA" is known. |
| `dateEnd` | string | Optional ISO end date for multi-day events. |
| `time`    | string | Free-text time label, e.g. `"10:00 AM – 5:00 PM IST"`. |
| `title`   | string | Event name, also the link text. |
| `format`  | string | `"online"` or `"inperson"`. |
| `venue`   | string | Shown next to the location pin/globe icon. |
| `org`     | string | Organizing community or company. |
| `category`| string | One id from the `categories` lookup: `hackathon`, `meetup`, `workshop`, `conference`, `corporate`. |
| `desc`    | string | One-sentence description. |
| `link`    | string | Registration or details URL, opened in a new tab. |

A new category needs an entry in the `categories` lookup object; the chip, its count, and the tag
on each card all derive from that. The calendar automatically picks up any event with a `date`
across the two months it renders (`calMonths` in the script) — add a third month there if the
list grows into November.

## On the data

All 15 events were found via public listings on AI Tinkerers Pune, the Pune AI Group (Meetup),
the Meetup.com Pune machine-learning aggregator, and public academic-conference directories
(10Times, ConferenceAlerts) — see the in-page footer for the full source list. Several of the
listed sessions are run online by Pune-based communities rather than held in a physical Pune
venue; those are marked "Online" in the format tag rather than misrepresented as in-person.
Community meetup schedules can shift after listing, so the page footer tells readers to confirm
date, time and venue on the organizer's own registration page before attending.
