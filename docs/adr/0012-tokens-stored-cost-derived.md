# Harvest stores token counts; cost is derived at report time

A harness transcript records token usage but not dollar cost, and provider prices drift over time. We store the bucketed token counts (input / output / cache-creation / cache-read, per model in `models_seen`) on the result and **derive cost later** (in paws/compare) against *current* pricing — never freezing a price at harvest time.

## Why

The interesting question is "what would it cost me to run this model *today*", not "what did it nominally cost on the day it ran". A frozen price answers a question nobody asks and goes stale silently. Tokens are the durable, harness-reported fact; cost is a *view* over them. Storing tokens bucketed (and per-model, since sub-agents may use a different, differently-priced model) lets derivation apply the right rate to each bucket and re-price freely as rates change, with no re-harvest.

## Consequences

- The result carries no `cost` field; cost lives in the report layer (paws/compare), out of scope for the harvest slice.
- Token counts must be captured per bucket and per model (see `models_seen`), not as a single total.
