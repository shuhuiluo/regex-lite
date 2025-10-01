from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from regex_lite import matcher


class EngineAdapter:
    def match(self, pattern: str, flags: str, text: str) -> List[dict]:
        raise NotImplementedError

    def replace(
        self, pattern: str, flags: str, text: str, repl: str
    ) -> Tuple[str, int]:
        raise NotImplementedError

    def split(self, pattern: str, flags: str, text: str) -> List[str]:
        raise NotImplementedError

    def compile(self, pattern: str, flags: str) -> Dict[str, Any]:
        """Compile pattern and return NFA structure information."""
        raise NotImplementedError


def _translate_flags(flag_str: str) -> int:
    mapping = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL}
    value = 0
    for ch in flag_str:
        value |= mapping.get(ch, 0)
    return value


class MockEngine(EngineAdapter):
    def match(self, pattern: str, flags: str, text: str) -> List[dict]:
        regex = re.compile(pattern, _translate_flags(flags))
        matches = []
        for m in regex.finditer(text):
            groups: List[Optional[Tuple[int, int]]] = []
            for i in range(1, m.re.groups + 1):
                span = m.span(i)
                groups.append(span if m.group(i) is not None else None)
            matches.append({"span": m.span(), "groups": groups})
        return matches

    def replace(
        self, pattern: str, flags: str, text: str, repl: str
    ) -> Tuple[str, int]:
        regex = re.compile(pattern, _translate_flags(flags))
        result, count = regex.subn(repl, text)
        return result, count

    def split(self, pattern: str, flags: str, text: str) -> List[str]:
        regex = re.compile(pattern, _translate_flags(flags))
        return regex.split(text)

    def compile(self, pattern: str, flags: str) -> Dict[str, Any]:
        """MockEngine doesn't expose NFA structure."""
        raise NotImplementedError(
            "Compile endpoint not available with mock engine - use real engine"
        )


class RealEngine(EngineAdapter):
    def match(self, pattern: str, flags: str, text: str) -> List[dict]:
        return matcher.match_with_groups(pattern, text, flags)

    def replace(
        self, pattern: str, flags: str, text: str, repl: str
    ) -> Tuple[str, int]:
        return matcher.replace(pattern, flags, text, repl)

    def split(self, pattern: str, flags: str, text: str) -> List[str]:
        return matcher.split(pattern, text, flags)

    def compile(self, pattern: str, flags: str) -> Dict[str, Any]:
        raise NotImplementedError("Compile endpoint not yet implemented in RealEngine")


def get_engine() -> EngineAdapter:
    use_mock = os.getenv("USE_MOCK_ENGINE", "1") != "0"
    return MockEngine() if use_mock else RealEngine()
