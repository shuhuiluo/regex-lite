# regex-lite

A toy regex engine implementation demonstrating compiler design principles. This project includes a complete development
stack with a Python engine, FastAPI service, and React frontend for interactive regex testing.

## Project Structure

This is a UV workspace monorepo with three main components:

```
regex-lite/
├── engine/         # Core regex engine (Python package)
├── api/           # FastAPI service (Python package)
├── web/           # React frontend
└── pyproject.toml # UV workspace configuration
```

## Quick Start

```bash
# Install all dependencies
make install

# Start API with mock engine (faster development)
USE_MOCK_ENGINE=1 make dev-api

# Start frontend development server
make dev-web
```

Open [http://localhost:5173](http://localhost:5173) and try the pattern `\d+` on the text `abc 123 xyz`.

## Architecture

### Engine (`regex_lite`)

Core regex engine following a classic compiler design pipeline:

1. **Lexer** - Tokenizes regex patterns with position tracking and escape sequence handling
2. **Parser** - Builds AST using Pratt parsing with proper operator precedence
3. **AST** - Represents regex constructs (literals, quantifiers, groups, character classes, etc.)
4. **Compiler** - Transforms AST to executable form *(not yet implemented)*
5. **Matcher** - Executes compiled regex against input text *(not yet implemented)*

Pure Python implementation with comprehensive error handling and warnings for non-standard escape sequences.

### API (`api`)

FastAPI service that exposes the regex engine via REST endpoints:

- Pydantic schemas for request/response validation
- Error handling with proper HTTP status codes
- Optional mock mode for frontend development
- Workspace dependency on the engine package

### Web (`web`)

React + TypeScript frontend for interactive regex testing:

- Vite for fast development and building
- Real-time pattern testing interface
- Input validation and error display
- Modern React patterns with TypeScript

## Development Setup

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) for Python dependency management
- [Bun](https://bun.sh/) for frontend dependency management

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd regex-lite
   uv sync  # Installs all Python packages and dev dependencies
   ```

2. **Install frontend dependencies:**
   ```bash
   cd web && bun install && cd ..
   ```

## Development Workflow

### Python Development

```bash
# Run all tests
uv run pytest

# Run tests for specific package
uv run pytest engine/tests/
uv run pytest api/tests/

# Code formatting and linting
uv run black .
uv run ruff check .
uv run ruff check . --fix

# Add workspace dependencies
uv add <package>
uv add --dev <package>
```

**Code Quality Tools:**

- **Black**: Code formatting (88 character line length)
- **Ruff**: Fast linting with import sorting
- **Pytest**: Testing with hypothesis for property-based tests

### Frontend Development

```bash
cd web

# Development server
bun run dev

# Production build
bun run build && bun run preview

# Type checking, linting, and formatting
bun run type-check
bun run lint
bun run format
bun run format:check
```

## Contributing

1. Follow existing code style (enforced by Black and Ruff)
2. Write tests for new functionality
3. Ensure all tests pass: `uv run pytest`
4. Format and lint: `uv run black . && uv run ruff check .`

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
