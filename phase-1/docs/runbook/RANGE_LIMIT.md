# Range limit on `/dsp/v0.1/calendar/range`

## Why

The previous handler accepted any `start`, `end` so long as `end >= start`
and the dates were ISO-formatted. A single unauthenticated request could
force the dewata-api process to compose tens of thousands of calendar
days in a tight loop — verified by an auditor's local benchmark of a
200-year window (~64 MiB response, ~10 s blocking). That made the
route a denial-of-service vector to anyone reachable on the API
hostname.

## The cap

The handler now enforces an inclusive-day cap. The default is **366**,
which covers any single civil year including a leap day. A well-formed
but oversize request is rejected with HTTP **413 (Request Entity Too
Large)** before the engine is invoked.

**366 is a hard safety ceiling.** It is not a starting point for a
"set higher" knob. The `DEWATA_MAX_RANGE_DAYS` environment variable may
*lower* the public cap (down to 1), but it cannot raise it above 366.
Any configuration outside that range falls back to the default 366 and
emits a WARN log entry.

## How `DEWATA_MAX_RANGE_DAYS` is interpreted

| Value | Effect |
|---|---|
| unset / empty string | default `366` |
| integer 1..366 inclusive | applied at startup as the new cap |
| anything else (non-integer, ≤ 0, > 366, "1.5", "730", "abc") | falls back to default `366`, WARN log |

The cap is read once at module import. Restart the API process after
changing it.

## Error response shape

When a request exceeds the cap:

```
HTTP/1.1 413 Request Entity Too Large
Content-Type: application/json

{
  "detail": {
    "error": "range_too_large",
    "code": "RANGE_LIMIT_EXCEEDED",
    "max_days": 366,
    "requested_days": <int>
  }
}
```

`error` is the stable machine-readable identifier; `code` mirrors the
project's existing dispute-vocabulary naming for downstream
consistency; `max_days` and `requested_days` are integers the client
can act on. **No filesystem paths, no internal error text.** The body
key is `detail` because FastAPI wraps `HTTPException(detail=…)` inside
its standard envelope.

## Why HTTP 413

- 400 is taken for malformed dates / reversed ranges (a syntactic
  defect).
- 413 is RFC 7231 §6.5.11 ("the request is larger than the server is
  willing to process") which is the closest semantic match for a
  capability-bound, well-formed request.
- 422 (FastAPI's default for body validation) is rejected because the
  cap is a query-parameter policy, not a payload validation error.
- 403 is rejected because the cap is not an authorisation issue.

## If a longer range is needed

If a caller genuinely needs more than 366 days of calendar data in
a single response, **do not "raise the cap."** The 366-day ceiling is
the audited safety boundary. A longer-range need must be designed as
a separate capacity-reviewed path that addresses the underlying
constraint:

- **Pagination** — make the caller issue multiple 366-day
  requests.
- **Streaming** — emit a record per day as the engine computes it.
- **Authentication + rate limiting** — bound aggregate CPU.
- **Asynchronous export** — accept a request, enqueue a job, deliver
  a signed artefact over an authenticated channel.

Each of those is its own design with its own PROTOCOL/§1 audit trail.

## Things explicitly NOT changed

- `/dsp/v0.1/calendar/date/{date}` — single-day response and shape.
- `/dsp/v0.1/calendar/ruleset` — unchanged.
- `/dsp/v0.1/calendar/range` valid response shape (`{start, end,
  count, items}` for `fmt=json`).
- Calendar computation, ruleset version, evidence, dispute records.

## Audit context

This safeguard was added in response to the 2026-09-16 dewata.org
independent audit (Blocker #3 / §6). The audit also flagged the live
public endpoint as the source of evidence for the unbounded
behaviour; this change makes that class of request no longer
deliverable through the API process at all.

A follow-up revision tightened the upper bound: the first version of
this doc listed 36600 as the upper limit and supported values like 730
(which would silently re-open the DoS path under operator
misconfiguration). The current revision makes 366 the hard ceiling
with no knob to raise it.

The handler-exception message was also tightened in the same
revision: parser-level `ValueError` text is no longer reflected into
the response body — the public 400 response carries a fixed stable
message ("must be a valid Gregorian date in YYYY-MM-DD format")
instead, with no internal paths or exception traces exposed.
