from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import BaseModel


class MatchRequest(BaseModel):
    pattern: str
    text: str
    flags: str = ""


class ReplaceRequest(MatchRequest):
    repl: str


class SplitRequest(MatchRequest):
    pass


class CompileRequest(MatchRequest):
    pass


class Match(BaseModel):
    span: Tuple[int, int]
    groups: List[Optional[Tuple[int, int]]]


class MatchResponse(BaseModel):
    matches: List[Match]


class ReplaceResponse(BaseModel):
    output: str
    count: int


class SplitResponse(BaseModel):
    pieces: List[str]


class CompileResponse(BaseModel):
    pass
