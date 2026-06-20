Write a Python module `wombat.py` with a function `dig(depth)` that returns a
string describing a burrow dug to `depth` metres, e.g. `"burrow at 3m"`.

---

Now add a `Burrow` class to `wombat.py` that tracks total depth across repeated
`dig` calls and exposes the running total as `Burrow.total`.

---

Finally, write `tests/test_wombat.py` covering both `dig` and `Burrow`, and make
sure the whole suite passes.
