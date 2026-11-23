# notify

jobs

## What pushes

| Push | When |
|---|---|
| **High** | Any engineering intern role at a `target_companies` company or on a curated board (elite quant, frontier/AI labs, top startups), US, Summer 2027, BS-eligible |
| **Default** | Same, at a big-tech company; or a role at ANY other company whose duties + quals strongly match my resume (`resume_fit` >= `resume_fit_min`): sandboxes/isolation, RL envs + evals, ML serving/MLOps, LLM agents/MCP, low-latency systems, order books |
| Nothing | PhD/MS-only, wrong season, non-US, non-engineering, co-ops, companies in `exclude_companies` (already applied/rejected) |

Tune everything in `config.json`: `target_companies`, `exclude_companies`, `resume_fit`,
`resume_fit_min` (raise it if off-list alerts get noisy), curated `greenhouse`/`lever`/`ashby`
slugs, `pay_floor_hourly`. Any filter edit reseeds silently, so it never floods.

## Setup (5 min)

1. Create a **public** GitHub repo (public = unlimited free Actions minutes; it only
   contains company lists and code). Push this folder to it.
2. Repo Settings, Secrets and variables, Actions, New secret: `NTFY_TOPIC` = an
   unguessable string (anyone who knows it can read your alerts).
3. Actions tab, enable workflows, open "notify", Run workflow. The first run seeds
   silently (records everything already posted, pushes nothing).
4. Install the ntfy app (iOS/Android), Subscribe to topic, enter the same string.
5. Optional: `python watch.py --test-alert` locally with `NTFY_TOPIC` set to confirm a push arrives.

Debug: `python watch.py --dry` (per-source table, sends nothing),
`python watch.py --explain <job-id>` (why a role was kept or dropped).
Tests: `python test_fit.py && python test_dedup.py && python test_delivery.py`.
---

## How it works

Sources, all public JSON, stdlib only, no API keys and no paid tiers:

- curated **Greenhouse** (42), **Ashby** (14) and **Lever** (1) company boards, polled
  directly every run
- the `listings.json` behind `SimplifyJobs/Summer2027-Internships`
- an atom feed from the zshah101 Summer-2027 registry
- **NVIDIA**'s Workday board

Each source has a `policy` setting how hard it is filtered: curated boards skip the
keyword gate (an "Engineering Intern" req at a hand-picked company is wanted outright),
bulk/aggregator sources must hit `include_keywords`.

Every role is filtered (season, geography, seniority, pay floor), then **scored**
software/ML-first: ML / inference / infra / distributed / agents `+2`, generic software /
SWE / quant / trading `+1`, PhD / MBA / master's-only `-3`. Every relevant role is
pushed; company size only sets how loud:

- **high** - Tier A at a startup or other non-`big_companies` company.
- **default** - Tier A at a `big_companies` company, or a Tier B role that scored
  target-grade but missed Tier A only on an ambiguous location/season or mid-band pay.
- **not pushed** - everything else. Still recorded in `roles.json` for reference.

Each push shows pay when the posting states it (the ATS's structured range, or an hourly
figure from the description; salaries also show an hourly equivalent), plus absolute
**Posted** and **Found** stamps in US Eastern, so a notification still makes sense a week
later. Each notification has an Apply button.

`max_alerts_per_run` (25) caps one run; anything past the cap lands on the board instead
and is logged. Changing any filter bumps the config hash and forces a silent reseed, so
widening a filter never floods you with backfill.

## Config

Edit `config.json`, or put personal changes in `config.local.json` (gitignored, so your
topic and local filters stay out of the repo). A key there overrides the same key here
**wholesale**. The `NTFY_TOPIC` env var beats both.

**Targeting**

- `target_companies` (133): name regexes. Any engineering intern role at one of these
  clears the tier bar outright.
- `exclude_companies` (8): already applied, rejected, or signed. Remove a name to start
  alerting on it again.
- `big_companies` (115): established corporates. Their roles still push, just at default
  instead of high. Editing this list does not trigger a reseed.
- `greenhouse` / `lever` / `ashby` / `workday`: curated boards. Add your targets; a newly
  added board's currently-open roles push like new postings.

**Fit** - how an off-list company still reaches you

- `resume_fit`: 15 `[weight, regex]` rows built from the resume's distinctive skills
  (agent sandboxes/isolation, RL envs + evals, ML serving/MLOps, LLM agents/MCP,
  low-latency systems, order books). A generic SWE title at ANY company surfaces when its
  description scores at least `resume_fit_min` (8). Raise it if off-list alerts get noisy.
  Only the posting's duties + qualifications are scored: `fit.py` splits on headings and
  drops the company blurb and the benefits tail.
- `off_specialty_titles` (26): Android, Frontend, Infrastructure and friends. A title
  naming one of these is never rescued by fit.
- `fit_fetch_budget` (60): descriptions fetched per run for this.

**Filters**

- `season_a_terms` / `season_drop_terms` / `season_title_drop`: Summer 2027 in, every
  other season out.
- `us_places` (112): US city and state names, so "San Francisco" or "Massachusetts" with
  no ", CA"-style code still counts as US.
- `include_keywords`, `exclude_keywords`, `include_categories`.
- `pay_floor_hourly` (30) / `pay_preferred_hourly` (45) / `pay_midband_min_score` (4):
  only fires when a posting states an hourly $ figure, so no stated pay never drops a
  role. Below the floor is a hard drop; between the floor and the preferred rate, only a
  strong-scoring role still reaches Tier A.
- `max_age_days` / `push_max_age_days` (21): a role whose first-published date is known
  and older than this lands on the board without buzzing the phone.

**Inert in this fork**, kept only so upstream diffs stay small: `edge_companies` /
`edge_company_score`, `tagged_subregex`, `desc_hw_keywords`, `desc_clearance`,
`markdown_sources`, `soft_categories`, and `discovery` (`enabled: false` - an
auto-discovery pass for hardware/robotics ATS boards).

## Tools

    python watch.py --once               single pass (what Actions runs)
    python watch.py --dry                per-source/per-tier table, sends nothing
    python watch.py --explain <job-id>   full decision trace for one role
    python watch.py --backfill-board     fill roles.json with every open match
    python watch.py --test-alert         one real push in the live format

Tests: `python test_fit.py && python test_dedup.py && python test_delivery.py`.

## Differences from upstream vigil

- Scoring retuned from hardware/robotics to SWE / ML / AI-infra / quant.
- Added the `target_companies` tier bar and the `resume_fit` rescue path for off-list
  companies.
- The optional Cloudflare worker is gone (its filters were hardware-specific), so Actions
  owns every source. Leave the `SKIP_ATS` repo variable **unset** - setting it would skip
  the curated boards and nothing else would poll them.

## License

MIT. Forked from [AbhigyaGoel/vigil](https://github.com/AbhigyaGoel/vigil); upstream
copyright retained in `LICENSE`.
