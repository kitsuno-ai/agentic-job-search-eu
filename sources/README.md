# `sources/` — how this works

One YAML file per source. Filename is the source's `slug` (e.g. `jobs-ch.yml` for slug `jobs-ch`).

## Required fields at a glance

| Field | Type | Example |
|---|---|---|
| `name` | string | `Jobs.ch` |
| `slug` | string (kebab-case) | `jobs-ch` |
| `url` | URL | `https://www.jobs.ch` |
| `countries` | array of ISO 3166-1 alpha-2 | `[CH]` |
| `languages` | array of ISO 639-1 | `[de, fr, it, en]` |
| `focus` | enum | `general` / `tech` / `remote` / `sector` / `aggregator` |
| `access_type` | enum | `api` / `rss` / `scrape` / `hybrid` |
| `requires_auth` | boolean | `true` |
| `kitsuno_status` | enum | `active` / `inactive` / `wishlist` |
| `license_posture` | enum | `aggregator-friendly` / `neutral` / `restricted` / `hostile` / `unknown` |
| `last_verified` | date (YYYY-MM-DD) | `2026-04-23` |

## Optional but valuable fields

| Field | Why it matters |
|---|---|
| `api_docs_url` | Direct link to the source's API/feed docs |
| `auth_type` | `api_key` / `oauth` / `token` / `cookie` — helps planning |
| `terms_url` | Link to ToS for legal-posture verification |
| `update_frequency` | `realtime` / `hourly` / `daily` / `weekly` |
| `estimated_volume` | Order-of-magnitude live posting count |
| `rate_limits` | Free-text description |
| `notes` | **The most valuable field.** Real-world crawl wisdom. |
| `aliases` | Former/alternative names |
| `operator` | Company running the source |
| `headquartered_in` | ISO country code of the operator |

## The `notes` field

The `notes` field is where this directory earns its keep. Anyone can scrape an API doc page. Only people who've actually run a crawler know:

- Which endpoints silently return stale data
- Where pagination breaks
- Whether the "50,000 listings" is 50,000 distinct jobs or the same 500 jobs indexed 100 times
- Which fields are filled reliably vs. missing half the time
- Regional quirks (e.g. Italian listings on Jobs.ch are sparse outside Ticino)
- What happens at the rate limit

Write `notes` in plain English. Keep it factual. Avoid marketing language.

## The `kitsuno_status` field

Be honest about status. If a source is integrated but returns zero jobs, mark it `inactive`. If it's documented here but not yet crawled, mark it `wishlist`. The directory is more useful when the status reflects reality.

## Validation

Before submitting a PR, run:

```bash
python tools/validate.py sources/your-source.yml
```

Or validate everything:

```bash
python tools/validate.py
```

CI runs the same check on every PR.

## Full schema

The canonical schema is in [`_schema.yml`](./_schema.yml). Field definitions, enum values, and validation rules live there.

## Template

For a skeleton to copy: [`_template.yml`](./_template.yml).
