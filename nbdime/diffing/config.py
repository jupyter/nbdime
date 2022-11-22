
class DiffConfig:
    """Set of predicates/differs/other configs to pass around"""

    def __init__(self, *, predicates=None, differs=None, atomic_paths=None):
        if predicates is None:
            from .generic import default_predicates
            predicates = default_predicates()

        if differs is None:
            from .generic import default_differs
            differs = default_differs()

        self.predicates = predicates
        self.differs = differs
        self._atomic_paths = atomic_paths or {}

    def diff_item_at_path(self, a, b, path):
        """Calculate the diff for path."""
        self.differs[path](a, b, path=path, config=self)

    def is_atomic(self, x, path=None):
        "Return True for values that diff should treat as a single atomic value."
        try:
            return self._atomic_paths[path]
        except KeyError:
            return not isinstance(x, (str, list, dict))

    def __copy__(self):
        return DiffConfig(
            predicates=self.predicates.copy(),
            differs=self.differs.copy(),
            atomic_paths=self._atomic_paths.copy(),
        )
