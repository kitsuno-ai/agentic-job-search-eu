# Agentic Job Search — EU Job Sources Directory

A community-maintained, machine-readable directory of job sources reachable from Europe, designed for people building **agentic job-search tools**: AI agents, crawlers, aggregators, and research projects.

Every source is documented in a single YAML file with coverage, access method, rate limits, licensing posture, and real-world crawl notes.

---

## See this in action

The coverage volumes and source statuses in this directory reflect [Kitsuno](https://kitsuno.ai)'s production crawl. Live operational numbers — total jobs crawled, unique postings ingested, per-source run counts, strong matches surfaced — are published at:

**→ [kitsuno.ai/stats](https://kitsuno.ai/stats)**

As far as we can tell, no other EU job-search operator publishes these numbers. If you're evaluating whether any of the sources below are worth integrating, the live stats tell you whether they're actually producing.

---

## Why this exists

Most "awesome job board" lists stop at a URL and a one-liner. That's not enough to build anything agentic.

Building an AI job-search agent means knowing, per source:
- Which countries and languages it actually covers
- Whether there's a public API, an RSS feed, or just HTML to scrape
- What the ToS says about aggregation and automation
- Where the rate limits are
- What breaks in practice (pagination, region-locking, stale listings, silent cutoffs)

We've been crawling these sources for a year at [Kitsuno](https://kitsuno.ai). This repo is the shared reference we wished existed when we started.

---

## What's in v1

**30+ active EU-reachable sources**, documented one YAML per source, with fields covering:

- Countries and languages
- Access type (API / RSS / scrape / hybrid)
- Authentication requirements
- Update frequency and estimated volume
- Rate limits and practical notes
- License posture (aggregator-friendly / neutral / restricted)
- Status: `active`, `inactive`, or `wishlist`

**Coverage today:**

| Region | Active sources |
|---|---|
| 🇨🇭 Switzerland | jobs_ch, swissdevjobs, publicjobs_ch |
| 🇩🇪 Germany | germantechjobs, arbeitsagentur |
| 🇫🇷 France | francetravail, devitjobs_fr |
| 🇬🇧 United Kingdom | reed, devitjobs_uk |
| 🇳🇱 Netherlands | devitjobs_nl |
| 🇸🇪 Sweden | platsbanken |
| 🇳🇴 Norway | nav |
| 🇷🇴 Romania | devjob_ro, olx |
| EU-wide | arbeitnow, 80000hours |
| Global / remote | adzuna, indeed, linkedin, jooble, themuse, remoteok, remotive, jobicy, working_nomads, himalayas |
| Specialized | reliefweb (UN/humanitarian), google_xray (22 ATS platforms) |

Total job volume observed across sources: **900,000+ postings**.

**Wishlist sources** (documented but not yet integrated): StepStone, Jobindex, Totaljobs, HelloWork, Karriere.at, plus community suggestions.

---

## How to use the data

### Python

```python
import yaml
from pathlib import Path

sources = []
for f in Path("sources").glob("*.yml"):
    if f.name.startswith("_"):
        continue
    with open(f) as fh:
        sources.append(yaml.safe_load(fh))

# Filter: active sources with a public API covering Germany
api_de = [
    s for s in sources
    if s["kitsuno_status"] == "active"
    and s["access_type"] == "api"
    and "DE" in s["countries"]
]

for s in api_de:
    print(f"{s['name']:25} {s['api_docs_url']}")
```

### JavaScript / Node

```javascript
import { readdir, readFile } from 'fs/promises';
import { parse } from 'yaml';

const files = await readdir('sources');
const sources = await Promise.all(
  files
    .filter(f => f.endsWith('.yml') && !f.startsWith('_'))
    .map(async f => parse(await readFile(`sources/${f}`, 'utf8')))
);

const remoteEu = sources.filter(s =>
  s.kitsuno_status === 'active' &&
  s.focus === 'remote' &&
  s.countries.some(c => ['DE','FR','NL','CH','UK'].includes(c))
);
```

More examples in [`examples/`](./examples/).

---

## The schema

Each YAML follows [`sources/_schema.yml`](./sources/_schema.yml). At minimum:

```yaml
name: Jobs.ch
slug: jobs-ch
url: https://www.jobs.ch
countries: [CH]
languages: [de, fr, it, en]
access_type: api            # api | rss | scrape | hybrid
requires_auth: true
license_posture: aggregator-friendly
focus: general              # general | tech | remote | sector
kitsuno_status: active      # active | inactive | wishlist
last_verified: 2026-04-23
notes: |
  Strong CH coverage including FR/IT cantons.
  Italian listings sparse outside Ticino.
```

See [`sources/README.md`](./sources/README.md) for the full field reference.

---

## Contributing

**Missing a source?** Open an issue using the [new-source template](.github/ISSUE_TEMPLATE/new-source.md) or submit a PR with a new YAML file.

**Spotted incorrect info?** PRs welcome — the `notes` and `last_verified` fields are where real-world crawl wisdom lives.

Every PR runs through [`tools/validate.py`](./tools/validate.py) in CI to check schema compliance.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for full guidelines.

---

## About

This directory is maintained by the team at [Kitsuno](https://kitsuno.ai) — an AI job search agent built for European careers. We open-sourced our source directory because cataloging EU job sources shouldn't be something every team has to redo from scratch.

If you're building an agentic job-search tool, we'd love to hear about it — [hello@kitsuno.ai](mailto:hello@kitsuno.ai).

---

## License

- **Source data** (contents of `sources/` and `stats/`): [CC-BY-SA 4.0](./DATA-LICENSE.md) — free to use, requires attribution and share-alike.
- **Code** (`tools/`, `examples/`, schema): [MIT](./LICENSE) — use it however you want.

Attribution for the data is a link back to this repo and/or [kitsuno.ai](https://kitsuno.ai).
