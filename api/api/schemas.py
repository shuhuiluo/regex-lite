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


class CompileRequest(BaseModel):
    pattern: str
    flags: str = ""


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


class ErrorResponse(BaseModel):
    error: str
    position: Optional[int] = None


class StateInfo(BaseModel):
    """Information about a single NFA state."""

    index: int
    accept: bool
    edges: List[dict]  # List of edge information
    epsilon_transitions: List[int]  # List of state indices
    require_bol: bool = False
    require_eol: bool = False


class CompileResponse(BaseModel):
    """Response containing NFA structure information."""

    start_state: int
    accept_states: List[int]
    state_count: int
    states: List[StateInfo]
