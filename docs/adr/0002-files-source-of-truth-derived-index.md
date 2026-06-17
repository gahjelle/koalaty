# Pouch is plain files; the query index is derived and disposable

The pouch stores one directory per run, keyed by a self-describing run ID (e.g. `<task>-<harness>-<model>-<date>-<shortid>`; see [ADR-0003](./0003-run-id-ordering-and-canonical-names.md)), each holding raw harvested artifacts plus a normalized `result.json`. These files are the **source of truth**. The query layer (SQLite/DuckDB) is a **derived index** rebuilt from the `result.json` files — disposable, never authoritative, not git-tracked.

We chose files-first over a database-first design so the product stays diffable, reproducible, and free of a heavy DB dependency, consistent with "the pouch is the product" ([ADR-0001](./0001-pouch-is-the-product-two-feeds.md)). Each `result.json` carries reproducibility metadata (harness + CLI version, model + version, date, gum commit). The pouch is a separate, configurable location — koalaty is the tool, the pouch is the user's data.

## Consequences

- The `result.json` schema is the real linchpin; the index can be regenerated at will.
- Large transcripts and any secrets live in the user's pouch, not koalaty's repo.
