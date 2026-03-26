# LTX-2 Local Generation Research (2026-03-26)

## Key takeaways from NVIDIA GTC 2026

- Runway + NVIDIA demonstrated a model generating HD video in <100ms.
- NVIDIA LTX-2 pipeline enables RTX GPUs to generate up to 20 seconds of 4K video **locally**.
- Claimed 3x faster than cloud alternatives.

## Implications for local character consistency

- On‑device generation removes cloud latency, making it feasible to integrate reference‑guided tools (IP-Adapter, ControlNet, LoRA) directly into the generation loop.
- Allows real‑time iterative refinement and consistency checks on consumer hardware.

## Relevance to this repo

Our current still‑first pipeline (SDXL Turbo) already runs locally. LTX‑2 could become an alternative motion generation backend once widely available.
