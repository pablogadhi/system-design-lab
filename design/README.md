# design/ — the input and the contract

| File | Who writes it | What it is |
|---|---|---|
| `diagram.excalidraw` | you | the Excalidraw scene (File → Save to… `.excalidraw`) |
| `diagram.png` | you | an exported image of the same scene (layout + visual grouping) |
| `diagram.graph.md` | `make graph` | compact components / connections / notes parsed from the scene |
| `spec.md` | architect (you approve) | requirements, scale-down, components, services, flows, chaos — from `SPEC_TEMPLATE.md` |
| `contracts/openapi/<service>.yaml` | architect | HTTP API of each service; services are tested against it, the client generates types from it |
| `contracts/events/<topic>.schema.json` | architect | JSON Schema of each event/message |
| `contracts/db/<component>.sql` | architect | authoritative schemas; owning services copy them into migrations |
| `contracts/config.md` | architect | which connections/env each service gets |
| `RESULTS.md` | orchestrator | what was built, how to run it, what the load/chaos runs showed |

## Drawing tips (so parsing is exact, not guessed)
- **Snap arrows onto shapes** (the shape highlights when you drag the arrow end over it). Unsnapped
  arrows are resolved by proximity and flagged `(inferred)`.
- **Put text inside shapes** by double-clicking the shape (binds the label). Loose text on top of a
  shape still works but is flagged.
- **Label arrows** by double-clicking the arrow — e.g. `POST /click`, `produce clicks`, `TTL 10m`.
- Use **frames** or an enclosing rectangle for pools/clusters ("Kafka cluster" around 3 brokers).
- Requirements, entities, tables and data-flow notes as free text anywhere — they land in *Notes*.
