# The pouch is the product; two feeds fill it as equals

Koalaty's center of gravity is the results store (the *pouch*), not the orchestration layer. Results enter via two equal feeds: **automated** runs (koalaty invokes a harness headlessly, then harvests the session) and **manual** runs (a human drives the harness, then hands koalaty a session ID to harvest). Both produce the same normalized **result** shape so they compare side by side.

We chose this over the draft's adapter-centric framing because much benchmarking is genuinely interactive and cannot be scripted without injecting bias — manual sessions must be first-class, not a bolted-on import path. The shared capability across both feeds is **harvest** (read a finished session by ID and normalize it); only automated runs additionally *invoke*. Consequently the `driver` (koalaty vs human) is *derived* from the task's `turns` plus harness capability, not authored.

## Consequences

- The linchpin is the stored **result** schema, not the adapter interface.
- A harness adapter needs a *harvest* capability always, and an *invoke* capability only to support automation.
- Tasks that are `interactive`, or run on harnesses lacking a headless mode, only ever reach the pouch through the manual feed.
