from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .adapters import get_engine
from .schemas import (
    MatchRequest,
    MatchResponse,
    ReplaceRequest,
    ReplaceResponse,
    SplitRequest,
    SplitResponse,
)


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    engine = get_engine()

    @app.get("/healthz")
    def healthz() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/regex/match", response_model=MatchResponse)
    def regex_match(req: MatchRequest) -> MatchResponse:
        try:
            matches = engine.match(req.pattern, req.text, req.flags)
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        return MatchResponse(matches=matches)

    @app.post("/regex/replace", response_model=ReplaceResponse)
    def regex_replace(req: ReplaceRequest) -> ReplaceResponse:
        try:
            output, count = engine.replace(req.pattern, req.flags, req.text, req.repl)
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        return ReplaceResponse(output=output, count=count)

    @app.post("/regex/split", response_model=SplitResponse)
    def regex_split(req: SplitRequest) -> SplitResponse:
        try:
            pieces = engine.split(req.pattern, req.flags, req.text)
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        return SplitResponse(pieces=pieces)

    return app
