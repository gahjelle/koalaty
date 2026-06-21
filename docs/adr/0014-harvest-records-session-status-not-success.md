# Harvest records session status, not task success

Harvest records how the *session* ended — `completed | interrupted | errored` — which it can observe from the transcript (`stop_reason`, an `interrupted` flag on tool results, error events). Whether the task's done-condition was actually met is a separate **verdict** that paws (mechanical) and the survey produce later. The old `outcome: success | failure` is retired from harvest.

## Why

A transcript carries no success/failure marker, and harvest is explicitly not a quality judge — that is paws' and the survey's job (see the evaluation split in the PRD). `success | failure` conflated "the session ended" with "the task was accomplished"; the harness only knows the former. Modelling session status honestly stops harvest from asserting an outcome it cannot know.

## Consequences

- `Outcome` (success/failure) is replaced by a `session_status` enum on the harvested session and result; the fake adapter, `runs.py`, and existing tests move to it.
- A nullable done-condition verdict is left for a later paws/survey slice; harvest does not fill it.
