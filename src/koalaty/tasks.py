"""The bundled tasks koalaty ships with.

This slice hardcodes a single task; file-loaded task bundles arrive later.
"""

# The one bundled task: an id mapped to its one-line prompt.
BUNDLED_TASKS: dict[str, str] = {
    "quokka": "Write a function that returns the string 'quokka'.",
}


def is_known_task(task: str) -> bool:
    """Return whether `task` is one of the bundled task ids."""
    return task in BUNDLED_TASKS
