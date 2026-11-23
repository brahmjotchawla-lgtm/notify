"""Tests for the target-company gate + resume fit (Brahmjot's fork).

Aggregator rows (Simplify listings, policy=tagged):
  - target company + engineering title -> Tier A on the title alone, no fetch
  - off-list company: strong resume fit -> Tier B (quieter push); weak fit -> drop
  - off-list, no description yet -> fit-pending (retried next run, not marked seen)
  - off-list non-engineering / off-specialty title -> dropped without a fetch
  - excluded (applied/rejected) company, wrong season, PhD -> dropped
Curated boards: a non-engineering title is dropped, not pushed.

Run:  python test_fit.py    (exit 0 = all pass)
"""
import watch

FAILS = []
STRONG = ("<h3>What you'll do</h3><p>Build sandboxed Linux environments (namespaces, seccomp) for "
          "RL rollouts and evals of LLM agents. Ship low-latency Python services.</p>"
          "<h3>Qualifications</h3><p>Python, Linux, Docker.</p>")
WEAK = "<h3>What you'll do</h3><p>Maintain internal dashboards in React.</p><h3>Qualifications</h3><p>Python.</p>"


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}: got {got!r} want {want!r}")


def row(company="Acme Corp", title="Software Engineer Intern", jid="ls:t1", terms=("Summer 2027",),
        loc="San Francisco, CA"):
    return {"id": jid, "company": company, "title": title, "location": loc,
            "url": "https://example.com/job", "category": "Software", "terms": list(terms),
            "posted": 0, "src": "listings", "policy": "tagged"}


def run(job, desc):
    calls = []
    orig, orig_fetch = watch.listing_html, watch.ENRICH_FETCH
    watch.listing_html = lambda url: calls.append(url) or desc
    watch.ENRICH_FETCH = True
    watch.FIT_BUDGET[0] = 5
    try:
        return watch.classify(job, {}), calls
    finally:
        watch.listing_html, watch.ENRICH_FETCH = orig, orig_fetch


def test_target_tier_a():
    for co, title in [("Jane Street", "Software Engineer Intern"), ("Two Sigma", "Quantitative Researcher Intern"),
                      ("Modal", "Machine Learning Intern"), ("Google", "Software Engineering Intern, BS")]:
        (dec, _), _ = run(row(company=co, title=title, jid="ls:" + co), WEAK)
        check(f"target {co}", dec, "A")


def test_offlist_strong_fit_tier_b():
    (dec, score), calls = run(row(jid="ls:t2"), STRONG)
    check("off-list strong fit tier", dec, "B")
    check("off-list strong fit fetched", len(calls), 1)


def test_offlist_weak_fit_dropped():
    (res, _) = run(row(jid="ls:t3"), WEAK)
    check("off-list weak fit", res, ("drop", "weak-fit"))


def test_offlist_pending():
    watch.ENRICH_FETCH = False
    res = watch.classify(row(jid="ls:t4"), {})
    check("off-list pending", res, ("drop", "fit-pending"))


def test_offlist_offtarget_no_fetch():
    for title in ["Android Engineer Intern", "Business Operations Intern", "Frontend Developer Intern"]:
        (res, calls) = run(row(title=title, jid="ls:" + title), STRONG)
        check(f"off-target {title}", res[0], "drop")
        check(f"off-target {title} not fetched", len(calls), 0)


def test_hard_drops():
    check("rejected company", run(row(company="Stripe", jid="ls:s"), STRONG)[0], ("drop", "excluded"))
    check("wrong season", run(row(company="Citadel", terms=("Fall 2027",), jid="ls:f"), STRONG)[0][1], "season")
    check("phd", run(row(company="Citadel", title="PhD Quant Research Intern", jid="ls:p"), STRONG)[0][0], "drop")
    check("non-eng at target", run(row(company="Citadel", title="Investment Analyst Intern", jid="ls:i"), STRONG)[0][0], "drop")


def test_curated_nonengineering_dropped():
    job = {"id": "gh:x:1", "company": "databricks", "title": "Recruiting Coordinator Intern",
           "location": "San Francisco, CA", "url": "https://x/1", "terms": None, "posted": 0,
           "src": "greenhouse", "policy": "curated", "desc": ""}
    check("curated recruiting", watch.classify(job, {})[0], "drop")
    job = {**job, "id": "gh:x:2", "title": "Business Development Intern"}
    check("curated BD", watch.classify(job, {})[0], "drop")
    job = {**job, "id": "gh:x:3", "title": "Software Engineering Intern"}
    check("curated SWE", watch.classify(job, {})[0], "A")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    if FAILS:
        print("\n".join(FAILS))
        raise SystemExit(f"FAIL - {len(FAILS)} check(s)")
    print("OK - all fit tests passed")
