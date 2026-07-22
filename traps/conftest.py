"""`hidden/` is not collectable from here, by design.

Those suites import `shiftlog`, which only exists inside an executor's workdir.
They are run by `grade.py`, which copies them into a throwaway clone of the run's
workdir. Collecting them at the repo root produces four import errors that look
like a broken test suite and are not.
"""

collect_ignore_glob = ["hidden/*", "reference/*"]
