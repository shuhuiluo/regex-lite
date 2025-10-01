from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from regex_lite.parser import RegexSyntaxError

from .adapters import get_engine
from .schemas import (
    CompileRequest,
    CompileResponse,
    ErrorResponse,  # noqa: F401
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
            matches = engine.match(req.pattern, req.flags, req.text)
            return MatchResponse(matches=matches)
        except RegexSyntaxError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": str(exc),
                    "position": exc.position,
                },
            )
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")

    @app.post("/regex/replace", response_model=ReplaceResponse)
    def regex_replace(req: ReplaceRequest) -> ReplaceResponse:
        try:
            output, count = engine.replace(req.pattern, req.flags, req.text, req.repl)
            return ReplaceResponse(output=output, count=count)
        except RegexSyntaxError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": str(exc),
                    "position": exc.position,
                },
            )
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")

    @app.post("/regex/split", response_model=SplitResponse)
    def regex_split(req: SplitRequest) -> SplitResponse:
        try:
            pieces = engine.split(req.pattern, req.flags, req.text)
            return SplitResponse(pieces=pieces)
        except RegexSyntaxError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": str(exc),
                    "position": exc.position,
                },
            )
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")

    @app.post("/regex/compile", response_model=CompileResponse)
    def regex_compile(req: CompileRequest) -> CompileResponse:
        try:
            pieces = engine.compile(req.pattern, req.flags, req.text)
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        return CompileResponse(pieces=pieces)

    return app
