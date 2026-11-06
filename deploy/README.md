# Deployment runtime for SWAG + RRFlow + Connectome

This bundle defines the deployment envelope for the project-aware routing stack:

- RRFlow is the authority and effect gate.
- SWAG is the project-aware routing and preview layer.
- Connectome consumes only public status and route evidence.
- local devtools remain bounded and read-only by default.

The boot order is intentionally explicit:

1. RRFlow
2. SWAG
3. Connectome

This keeps the engine as the single authority while making SWAG and the UI easily absorbable into a unified developer surface.
