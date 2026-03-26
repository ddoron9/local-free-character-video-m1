# Notes

## 2026-03-25

- Doyi clarified that the benchmark must be artifact-first: make actual outputs, compare final deliverables, and update docs continuously rather than only summarizing in chat.
- Verified existing local outputs on this machine before re-running anything: `final_anime_rerun_fixed.mp4`, `final_anime_rabbit.mp4`, `baseline_wan_quick_test.mp4`, `wan_quick_test.mp4`, and associated logs.
- Re-ran prompt-only SDXL Turbo still generation into `out/bench_20260325_sdxl_turbo/stills/` using the existing storyboard spec.
- Measured rerun result: 5 scenes in 47.95s, peak memory footprint ~13.58GB.
- Practical finding: prompt adherence at the scene level is decent, but same-character consistency still drifts significantly without reference guidance; one scene can read as a human astronaut while another reads as the intended rabbit astronaut.
- Practical finding: Wan 2.1 GGUF i2v preserves the initial input image better than the prompt-only still baseline, but the current local quick-test output is too short/weak (~0.625s, 5 frames, 480x832) to function as the main Shorts engine.
- Current best production path on this Mac remains: still-first generation -> vertical edit/render -> selective motion only where needed.
- Wrote a benchmark summary report at `results/reviews/2026-03-25_m1_shorts_benchmark.md` documenting the current ranking and evidence paths.
- Added GIF artifacts for docs embedding under `assets/bench_20260325/` so the README can show current outputs visually.
- First diffusers-based SDXL IP-Adapter run was attempted with the existing rabbit still as reference and failed after ~418.72s due to an image-encoder dimension mismatch (`2x1280` vs `1024x8192`). This is now treated as a concrete compatibility issue to fix, not a vague TODO.
- Follow-up hypothesis after inspecting the Hugging Face repo: `ip-adapter_sdxl_vit-h` appears incompatible with the currently loaded 1280-dim SDXL image encoder in this setup, so the next retry is switching to `ip-adapter_sdxl.safetensors` instead of the vit-h variant.
- Important repo note: nested repo ignore rules currently exclude `results/reviews/*.md`, so human-readable benchmark notes in that path are not tracked by the nested git repo unless the ignore rule is changed or docs are moved.

## 2026-03-24

- Re-ran Wan quick i2v on Apple Silicon using existing ComfyUI + GGUF setup.
- Re-ran SDXL Turbo storyboard still generation.
- Reproduced ffmpeg concat bug due to relative paths in concat list.
- Fixed concat generation to use absolute resolved paths.
- Confirmed final 24s vertical video render after patch.
