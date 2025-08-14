# regex-lite

Minimal monorepo containing a toy regex engine, a FastAPI API, and a React UI.

## Quickstart

```bash
make install
USE_MOCK_ENGINE=1 make dev-api
make dev-web
```

Open [http://localhost:5173](http://localhost:5173) and try the pattern `\\d+` on the text `abc 123 xyz`.
