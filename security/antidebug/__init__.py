"""
Anti-debug and VM detection package.
Пакет обнаружения отладчиков и виртуальных машин.
Пакет виявлення відладчиків та віртуальних машин.

Sub-modules
-----------
windows  — Windows-specific detection (IsDebuggerPresent, NtQueryInformationProcess …)
unix     — Linux/macOS detection (ptrace, /proc, sysctl …)
checks   — cross-platform wrappers, VM/sandbox, protection, integrity, background checks
"""
from __future__ import annotations
from security.antidebug.windows import *  # noqa: F401,F403
from security.antidebug.unix    import *  # noqa: F401,F403
from security.antidebug.checks  import *  # noqa: F401,F403
