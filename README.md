# Agentic Job Search — EU Job Sources Directory

A machine-readable directory of job sources reachable from Europe, for people building
**agentic job-search tools**: AI agents, crawlers, aggregators, labour-market research.

Every source is one YAML file covering coverage, access method, authentication, rate limits,
licensing posture, and honest notes on what breaks in practice.

**57 sources · 49 active in production · 34 countries**

---

## What makes this different from an awesome-list

Two things.

**1. Every status is measured, not asserted.** `kitsuno_status` comes from production crawl
logs, not from whether the site looked alive when someone added it. Four sources in here are
marked `inactive` because we wired them, ran them, and they produced nothing. That negative
result is in the directory on purpose.

**2. We publish yield.** For each source: how many postings it returns, and how many of those
are actually new.

| Source | Found | Unique | Yield |
|---|---:|---:|---:|
| ats-direct | 19,039,517 | 6,347,397 | 33.3% |
| jobs-ch | 2,328,810 | 1,237,123 | 53.1% |
| nofluffjobs | 2,024,247 | 1,772,188 | 87.5% |
| adzuna | 1,423,707 | 1,107,253 | 77.8% |
| indeed | 849,139 | 239,648 | 28.2% |
| linkedin | 203,000 | 46,238 | 22.8% |
| olx | 11,620 | 2,482 | 21.4% |

A source returning 850k results of which 28% are new costs you 850k requests worth of rate
limit for 240k postings. That ratio decides what is worth integrating, and as far as we can
tell nobody else publishes it. Full table: **[stats/yield.md](./stats/yield.md)**.

Totals across the sources in this directory: **30,311,358 found, 13,828,153 unique**, over
roughly 70,000 crawl runs since March 2026. Figures as of 2026-07-23; these move every three
hours, so treat them as a snapshot and see [kitsuno.ai/stats](https://kitsuno.ai/stats) for live
numbers.

---

## Why it exists

Most job-board lists stop at a URL and a one-liner. Building an agent needs more:

- Which countries and languages the source actually covers
- Whether there is an API, an RSS feed, or only HTML
- What the ToS says about automated aggregation
- Where the rate limits are
- What breaks: pagination, geo-restriction, anti-bot challenges, stale listings, silent cutoffs

We run these sources in production at [Kitsuno](https://kitsuno.ai). This is the reference we
wanted when we started.

---

## Coverage

| Region | Active sources |
|---|---|
| 🇨🇭 Switzerland | jobs-ch, swissdevjobs, publicjobs-ch, job-room |
| 🇩🇪 Germany | arbeitsagentur, germantechjobs |
| 🇫🇷 France | francetravail, devitjobs-fr |
| 🇬🇧 United Kingdom | reed, devitjobs-uk |
| 🇦🇹 Austria | karriere-at |
| 🇳🇱 Netherlands | devitjobs-nl, iamexpat |
| 🇸🇪 Sweden | platsbanken |
| 🇳🇴 Norway | nav |
| 🇩🇰🇫🇮 Nordics | thehub |
| 🇵🇱 Poland | pracuj, nofluffjobs |
| 🇨🇿 Czechia | prace-cz, uradprace-cz |
| 🇸🇰 Slovakia | profesia-sk |
| 🇭🇺 Hungary | profession-hu |
| 🇵🇹 Portugal | netempregos |
| 🇪🇸 Spain | tecnoempleo |
| 🇷🇴 Romania | ejobs-ro, devjob-ro, olx |
| 🇱🇺 Luxembourg | moovijob |
| 🇪🇪🇱🇻🇱🇹 Baltics | cvonline |
| EU-wide | arbeitnow, euremotejobs |
| Aggregators | adzuna, indeed, linkedin, jooble, themuse |
| Remote | remoteok, remotive, jobicy, working-nomads, himalayas, weworkremotely |
| ATS direct | ats-direct (Greenhouse / Lever / Ashby / Recruitee / SmartRecruiters) |
| Sector | reliefweb, devex, 80000hours |

Full breakdown by focus, access type and licence posture:
**[stats/coverage.md](./stats/coverage.md)**.

### Sources worth knowing about

- **uradprace-cz** — the Czech labour ministry publishes vacancies as genuine open data at
  `data.mpsv.cz`. Bulk incremental files, no auth, companion geocoding datasets. This is what a
  public employment service should look like to an integrator.
- **job-room** — Switzerland's registration duty means employers must post qualifying vacancies
  here first, with a head start before advertising elsewhere. A real early-warning surface.
- **netempregos** — a plain RSS feed, no auth, no anti-bot layer, and it out-produces several
  pan-European aggregators. Best effort-to-yield ratio in the directory.
- **nofluffjobs** — mandatory salary ranges and structured tech stacks on every posting. Very
  little European hiring data is this clean.

---

## Using it

### Python

```python
import yaml
from pathlib import Path

sources = [
    yaml.safe_load(f.read_text())
    for f in Path("sources").glob("*.yml")
    if not f.name.startswith("_")
]

# Active sources with a real API, no auth, covering Czechia
easy_cz = [
    s for s in sources
    if s["kitsuno_status"] == "active"
    and s["access_type"] in ("api", "rss")
    and not s["requires_auth"]
    and "CZ" in s["countries"]
]

for s in easy_cz:
    print(f'{s["name"]:30} {s.get("api_docs_url", s["url"])}')
```

### JavaScript

```javascript
import { readdir, readFile } from 'fs/promises';
import { parse } from 'yaml';

const files = await readdir('sources');
const sources = await Promise.all(
  files
    .filter(f => f.endsWith('.yml') && !f.startsWith('_'))
    .map(async f => parse(await readFile(`sources/${f}`, 'utf8')))
);

// Everything you can integrate in an afternoon
const lowFriction = sources.filter(s =>
  s.kitsuno_status === 'active' &&
  ['api', 'rss'].includes(s.access_type) &&
  !s.requires_auth &&
  ['aggregator-friendly', 'neutral'].includes(s.license_posture)
);
```

More in [`examples/`](./examples/).

---

## Schema

Each file follows [`sources/_schema.yml`](./sources/_schema.yml).

```yaml
name: Jobs.ch
slug: jobs-ch
url: https://www.jobs.ch
countries: [CH]
languages: [de, fr, it, en]
focus: general              # general | tech | remote | sector | aggregator
access_type: hybrid         # api | rss | scrape | hybrid
requires_auth: true
license_posture: neutral    # aggregator-friendly | neutral | restricted | hostile | unknown
kitsuno_status: active      # active | inactive | wishlist
last_verified: 2026-07-23
notes: |
  Strong CH coverage across all three language regions.
  Italian listings sparse outside Ticino.
```

Note on ISO codes in YAML: `NO` (Norway) and `no` (Norwegian) parse as boolean false, and `*`
opens an alias. Quote them. We got this wrong first time round.

Full field reference: [`sources/README.md`](./sources/README.md).

---

## Agent-to-agent: the Handshake protocol

This directory is the crawl side of the problem: how an agent working for a job seeker finds
openings. The other half is what happens when a seeker-side agent and an employer-side system
need to talk to each other without either party dumping a candidate database on the internet.

That is a separate open specification: **[kitso-handshake-agents](https://github.com/kitsuno-ai/kitso-handshake-agents)**
(Apache 2.0). Consent-scoped candidate and vacancy cards, policy-based matching, state hashing.
If you are building on the employer side and want an interoperable way to receive consented
candidate interest rather than being crawled, that is the repo to read.

We would rather agree on a protocol than have every party scrape every other party.

---

## Contributing

Missing a source? Open an issue with the
[new-source template](.github/ISSUE_TEMPLATE/new-source.md), or send a PR with a YAML file.

Spotted something wrong? PRs very welcome. `notes` and `last_verified` are where the real
knowledge lives, and ours goes stale like everyone else's.

Every PR runs [`tools/validate.py`](./tools/validate.py) in CI.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## Scope

This directory covers sources we operate in production and can speak to from evidence. It is
not exhaustive, and it deliberately does not document every channel we run. Sources are added
when we have enough production history to write something honest in `notes`.

---

## About

Maintained by [Kitsuno](https://kitsuno.ai), a consent-first AI job-search agent for European
careers. We opened this up because cataloguing EU job sources should not be something every
team redoes from scratch.

Building something agentic in this space? [hello@kitsuno.ai](mailto:hello@kitsuno.ai).

---

## License

- **Data** (`sources/`, `stats/`): [CC-BY-SA 4.0](./DATA-LICENSE.md) — attribution and share-alike.
- **Code** (`tools/`, `examples/`, schema): [MIT](./LICENSE).

Attribution is a link back to this repo or to [kitsuno.ai](https://kitsuno.ai).
