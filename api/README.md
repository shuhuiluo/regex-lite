# API Checklist

* [ ] **EngineAdapter** with toggle: `MockEngine` (Python `re`) and `RealEngine` (ours)
* [ ] **Endpoints** (FastAPI):

    * [ ] `POST /regex/match` → `{matches:[{span:[s,e],groups:[ [s,e]|null … ]}]}`
    * [ ] `POST /regex/replace` → `{output,count}`
    * [ ] `POST /regex/split` → `{pieces}`
    * [ ] *(Optional for viz)* `POST /regex/compile` → `{ast,nfa}`
* [ ] **Schemas** (Pydantic): pattern, flags, input, replacement
* [ ] **Config & errors**: `USE_MOCK_ENGINE` env; map engine errors → 4xx JSON
* [ ] **Contract tests**: same request works against mock & real (allowing diff for unimpl until swapped)
