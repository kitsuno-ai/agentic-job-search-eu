# Contributing

Thanks for your interest. This directory gets better every time someone adds a source they know well or corrects one that's gone stale.

## Ways to contribute

**Add a new source.** The highest-leverage contribution. Follow the steps below.

**Update an existing source.** If you've noticed rate limits shifted, a ToS changed, a source rebranded, or your real-world crawl experience differs from what's in the `notes` field — open a PR. Bump `last_verified` when you do.

**Fix a typo or broken link.** Small, welcome, no process needed.

## Adding a new source

1. **Check it isn't already listed.** Look in `sources/` or search the repo for the domain.
2. **Copy the template:**
   ```bash
   cp sources/_template.yml sources/{your-slug}.yml
   ```
3. **Fill in required fields.** Filename must match the `slug` field exactly.
4. **Be honest about `kitsuno_status`.** If this source isn't actively crawled by Kitsuno's production pipeline, mark it `wishlist`. We (the maintainers) will flip it to `active` if and when we integrate it.
5. **Fill in `notes` if you have real experience.** Regional quirks, pagination issues, data quality observations, rate-limit behavior. This field is the reason the directory is worth something.
6. **Validate locally:**
   ```bash
   pip install pyyaml
   python tools/validate.py sources/{your-slug}.yml
   ```
7. **Open a PR.** CI runs the same validator on every PR.

## YAML gotchas to avoid

A few YAML 1.1 quirks bite country-code arrays:

- `NO` (Norway), `NB` (no explicit country but YAML sees "nb"), and similar bare two-letter tokens that look like booleans — **quote them**: `"NO"`.
- Bare `yes`, `no`, `on`, `off`, `true`, `false` are parsed as booleans. Quote if they're meant as strings.
- Dates: write `last_verified: 2026-04-23` (no quotes, ISO format). If quoted, the validator rejects it.

## Review criteria

PRs are reviewed against:

1. **Schema compliance** — CI must pass.
2. **Accuracy** — values should match what the source's documentation or ToS actually say. When `notes` and docs disagree, prefer `notes` but flag the discrepancy.
3. **Honesty in `kitsuno_status`** — a source that isn't actively crawled by anyone isn't "active."
4. **License posture honesty** — if the ToS prohibits aggregation, say `hostile` or `restricted`. Don't soften the reality.
5. **No marketing language in `notes`** — this field is for practical observations, not product claims.

## Scope boundaries

This directory is specifically for **job sources reachable from Europe**. We welcome:

- EU/EEA/EFTA job boards (public or private)
- Aggregators that have meaningful EU coverage
- Global boards (remote, tech-focused, sector-focused) that EU-based jobseekers actually use
- National public employment services (France Travail, NAV, Platsbanken, Bundesagentur, etc.)
- Sector-specific boards (humanitarian, science, public sector)

We don't currently catalog:

- Purely regional non-EU sources (US-only, APAC-only) — even if individual EU workers might use them remotely
- Consultancies and staffing agencies (they're hirers, not sources)
- LinkedIn-post-based listings without a searchable backend

If you're unsure whether a source fits, open an issue and we'll discuss.

## License

By contributing, you agree that your contributions to the data files (`sources/`, `stats/`) are licensed under CC-BY-SA 4.0, and your contributions to code (`tools/`, `examples/`) are licensed under MIT.

## Maintainers

This directory is primarily maintained by the team at [Kitsuno](https://kitsuno.ai). Reach us at [hello@kitsuno.ai](mailto:hello@kitsuno.ai) for larger structural proposals.
