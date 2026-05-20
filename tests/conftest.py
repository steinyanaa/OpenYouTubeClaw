from __future__ import annotations

import os
import tempfile
from typing import Any

if os.name == "nt":
    _OriginalTemporaryDirectory = tempfile.TemporaryDirectory

    class _WindowsTolerantTemporaryDirectory(_OriginalTemporaryDirectory):
        """Default TemporaryDirectory cleanup to tolerant mode on Windows.

        Several tests intentionally keep SQLite-backed objects in local
        variables until the test function returns. On POSIX, unlinking an
        open database file during ``TemporaryDirectory.__exit__`` works; on
        Windows, it raises ``PermissionError`` because the connection handle
        is still open until locals are released. Keeping this shim in the
        test harness preserves the POSIX behavior those tests rely on while
        still letting full-suite cleanup continue on Windows.
        """

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("ignore_cleanup_errors", True)
            super().__init__(*args, **kwargs)

    tempfile.TemporaryDirectory = _WindowsTolerantTemporaryDirectory
