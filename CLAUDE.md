# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Dependencies
```bash
# Install all Python packages (workspace + dev dependencies)
uv sync

# Install frontend dependencies  
cd web && bun install
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific package tests
uv run pytest engine/tests/
uv run pytest api/tests/

# Run single test file
uv run pytest engine/tests/test_lexer.py
uv run pytest engine/tests/test_parser.py::TestParser::test_simple_literal
```

### Code Quality
```bash
# Format and lint (run both)
uv run black .
uv run ruff check . --fix

# Type checking and linting (frontend)
cd web && bun run type-check && bun run lint
```

### Development Servers
```bash
# API with mock engine (faster development)
USE_MOCK_ENGINE=1 make dev-api

# API with real engine
make dev-api

# Frontend development server
make dev-web  # or cd web && bun run dev
```

## Architecture Overview

### UV Workspace Monorepo Structure
- **engine/**: Core regex engine package (`regex_lite`)
- **api/**: FastAPI service package (`api`) 
- **web/**: React + TypeScript frontend
- **Root pyproject.toml**: Workspace configuration with shared dev dependencies

### Engine Package (`regex_lite`)
Classic compiler pipeline implemented in pure Python:

1. **Lexer** (`lexer.py`) → **Parser** (`parser.py`) → **AST** (`ast.py`)
2. **Compiler** (`compiler.py`) → **Matcher** (`matcher.py`) *(compilation/matching not yet implemented)*

**Key Design Patterns:**
- **Pratt parser**: Handles operator precedence for regex constructs
- **Position tracking**: All tokens/AST nodes track original pattern positions
- **Error handling**: `RegexSyntaxError` with position information
- **Escape sequences**: Supports standard sequences (`\t`, `\n`, `\x20`) and shorthands (`\d`, `\w`, `\s`)

**AST Hierarchy:**
- Base: `Expr` class
- Atoms: `Literal`, `Dot`, `AnchorStart/End`, `Shorthand`, `CharClass`, `Group`
- Combinators: `Concat`, `Alt`, `Repeat`
- Character classes: `Range` items within `CharClass`

### API Package (`api`)
FastAPI service with adapter pattern:

- **Engine abstraction**: `EngineAdapter` interface with `MockEngine` (Python `re` module) and `RealEngine` (regex_lite)
- **Environment switching**: `USE_MOCK_ENGINE=1` for development
- **REST endpoints**: `/regex/match`, `/regex/replace`, `/regex/split`
- **Pydantic schemas**: Request/response validation in `schemas.py`

### Workspace Dependencies
The API package depends on the engine package via workspace dependency:
```toml
# api/pyproject.toml
dependencies = ["regex-lite-engine"]

[tool.uv.sources]
regex-lite-engine = { workspace = true }
```

## Key Implementation Notes

### Parser Quantifier Handling
The parser correctly handles lazy quantifiers (`*?`, `+?`, `??`) by allowing `?` after quantifiers to be parsed as separate tokens, enabling proper lazy quantifier support.

### Lexer Error Handling  
Unknown escape sequences raise `ValueError` immediately rather than warnings, providing strict validation for regex patterns.

### Testing Strategy
- **Hypothesis**: Property-based testing for lexer/parser fuzzing
- **Unit tests**: Comprehensive coverage of edge cases and error conditions
- **API contract tests**: Validate FastAPI endpoints and schemas

### Code Quality Configuration
- **Black**: 88 character line length, Python 3.11+ target
- **Ruff**: Fast linting with import sorting (`extend-select = ["I"]`)
- **TypeScript**: Strict mode with ESLint for frontend