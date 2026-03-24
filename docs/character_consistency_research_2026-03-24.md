# Character consistency research (2026-03-24)

## Goal
Improve character consistency for image-to-image / reference-guided generation from **one front-facing character image** on **Apple Silicon M1 Pro 32GB**, prioritizing **local + free** workflows.

---

## Bottom line

For this machine, the most practical stack is:

1. **SDXL or SD 1.5 + IP-Adapter / IP-Adapter Plus in ComfyUI**
   - best first step for one-image character guidance
   - works locally, no training, controllable cost
2. **Pose/depth/edge ControlNet combined with IP-Adapter**
   - use ControlNet for scene structure, IP-Adapter for identity/style retention
3. **Reference-only / attention-sharing workflows**
   - useful lightweight baseline, but weaker identity lock than IP-Adapter
4. **Optional face-only branch: InstantID / PhotoMaker / PuLID if the character is human-like and face fidelity matters**
   - stronger for face identity than full-body/cartoon identity
5. **LoRA/DreamBooth only after collecting more views or generating a synthetic multi-view dataset**
   - one front image alone is usually not enough for robust character LoRA training

---

## Practical recommendation stack for M1 Pro 32GB

### Tier 1: likely to work well locally

#### A. SDXL Turbo/Lightning + IP-Adapter Plus + ControlNet
- Best overall first experiment.
- Use a single reference image for identity/style.
- Use OpenPose / depth / canny / softedge ControlNet to keep composition stable across scenes.
- Good fit with your current shot-based pipeline.

Recommended use:
- anime/stylized character stills across multiple scenes
- same clothing/colors/face silhouette across storyboard frames
- later pass only selected frames into i2v

Why this fits M1:
- no training required
- cheaper than DreamBooth
- more realistic than pure prompt-only img2img
- can be run one image at a time, which is important on MPS

#### B. SD 1.5 + IP-Adapter Plus / Plus-Face for faster iteration
- Lower quality ceiling than SDXL, but often easier on Apple Silicon.
- Good for fast parameter sweeps before rerunning best setup on SDXL.

Recommended use:
- rapid ablation of adapter strength / denoise / prompt templates
- early pipeline debugging

### Tier 2: useful but narrower

#### C. Reference-only / style-reference workflows
- Usually implemented via attention sharing / reference latent features.
- Cheap and simple baseline.
- Good at style/color carryover; weaker at hard identity consistency.

Recommended use:
- as a baseline in your repo
- to quantify how much IP-Adapter actually improves consistency

#### D. InstantID / PhotoMaker / PuLID (human-like face characters)
- These are strongest when the key identity is **the face**.
- Great for realistic or semi-realistic human characters.
- Less ideal as the only method for non-human mascots or full-body costume retention.

Notes:
- **InstantID**: strong zero-shot face identity with one image, SDXL-based.
- **PhotoMaker / PhotoMaker V2**: good identity + editability, still face-centric.
- **PuLID / PuLID v1.1**: strong ID customization; FLUX variant exists but FLUX on this hardware is usually not the practical first choice.

### Tier 3: promising research, but not first choice on this machine

#### E. StoryMaker / multi-character consistency methods
- Research direction explicitly targeting face + clothing + body consistency.
- Promising for stories/comics.
- But less mature operationally than plain IP-Adapter stacks, and likely heavier / more fragile on M1.

Use only after establishing a strong SDXL+IP-Adapter baseline.

### Tier 4: probably too heavy / low ROI initially

#### F. DreamBooth / full fine-tune
- Too expensive in time/memory for this hardware for routine iteration.
- Also fundamentally weak when starting from only one front image.

#### G. FLUX-based character consistency as primary workflow
- FLUX quality is excellent, and MLX-native runtimes such as `mflux` make local FLUX possible on Mac.
- But FLUX customization/control stacks are still heavier and less straightforward than SDXL on M1 Pro 32GB.
- For this repo’s current goal, FLUX should be treated as an optional future comparison, not the main path.

---

## Method comparison

| Method | What it preserves best | Training needed | Pros | Cons | M1 Pro 32GB feasibility | Recommendation |
|---|---|---:|---|---|---|---|
| Prompt-only img2img | rough style / color | No | simplest | weak identity consistency | Excellent | baseline only |
| Reference-only / attention-sharing | style, palette, broad look | No | lightweight, easy baseline | identity drift | Good | include as baseline |
| IP-Adapter SD 1.5 | subject/style | No | fast, cheap, easy sweeps | lower quality than SDXL | Excellent | yes |
| IP-Adapter Plus SDXL | strongest no-training full-image reference option | No | best practical local/free starting point | still struggles with unseen back/side views from one front image | Good | highest priority |
| IP-Adapter FaceID / Face models | face identity | No | better face lock than generic IP-Adapter | face-centric; not enough for whole costume/body | Good | use for human-like characters |
| ControlNet + IP-Adapter | structure + identity | No | best controllability combo | more setup/tuning | Good | yes |
| InstantID | human face identity | No | excellent one-image face fidelity | requires face pipeline; less useful for mascots/full-body | Medium-Good | use if character is human-like |
| PhotoMaker V2 | realistic human identity | No | good fidelity/editability | mostly for photo/human identity | Medium | optional |
| PuLID v1.1 (SDXL) | human identity | No | strong recent ID method | more complex stack; face-focused | Medium | optional advanced branch |
| StoryMaker | face + clothes + body story consistency | Usually no at inference | promising for story sequences | newer, heavier, less battle-tested | Medium-Low | research branch only |
| LoRA from true multi-image dataset | character identity/style | Yes | strongest reusable consistency once trained well | needs multiple views/images; training time | Medium | later stage |
| DreamBooth full fine-tune | strong specialization | Yes | strong when dataset is good | too heavy/slow, high overfit risk | Low | not recommended first |
| FLUX + PuLID / other ID stack | high quality, prompt following | No/Maybe | future-facing quality ceiling | heavier and less practical on current Mac workflow | Low-Medium | defer |

---

## What likely works vs what probably does not

### Likely to work
- **Single reference + IP-Adapter Plus + good prompt template**
- **Single reference + IP-Adapter + OpenPose/depth ControlNet**
- **Scene-by-scene still generation followed by short i2v only on chosen shots**
- **Human-like face character + InstantID**
- **Fast SD 1.5 sweeps, then SDXL rerun on best settings**

### Likely to disappoint
- Expecting one front-facing image to generate perfect side/back views without drift
- Training a high-quality character LoRA from that one image alone
- Using pure img2img denoise tuning as the main identity strategy
- Making FLUX the first production path on M1 Pro 32GB
- Long end-to-end video generation with strong consistency on this hardware

Key limitation:
- From **one front-only image**, the missing information about side/back hair, body proportions, and costume details is real. No adapter fully invents those consistently. The best workaround is controlled scene design (mostly front/3/4 views), plus pose/depth guidance, plus optional synthetic dataset expansion.

---

## Recommended experiment plan

### Phase 0. Build a proper test set
Use 8 fixed prompts/scenes for the same character:
1. neutral portrait front
2. portrait 3/4 view
3. waist-up indoor scene
4. full-body standing pose
5. walking outdoors
6. sitting at desk
7. dramatic lighting close-up
8. action pose with large background change

For each scene, prepare:
- prompt
- optional negative prompt
- optional ControlNet condition image (pose/depth/edge)
- fixed seed set (e.g. 3 seeds)

### Phase 1. Establish baselines
Run the same 8 scenes with:
1. prompt-only SDXL/SDXL Turbo
2. img2img only
3. reference-only baseline
4. IP-Adapter SD 1.5
5. IP-Adapter SDXL

Goal:
- measure how much identity retention improves before adding more complexity

### Phase 2. Add structure control
For the best IP-Adapter setup, add:
- OpenPose ControlNet for body pose scenes
- depth or canny/softedge ControlNet for environment/layout scenes

Tune:
- adapter weight
- start/end step ratio
- denoise strength
- ControlNet weight

### Phase 3. Human-face branch (if relevant)
If the character is human-like enough:
- compare IP-Adapter FaceID vs InstantID on portrait scenes only
- judge whether face fidelity gain is worth the heavier stack

### Phase 4. Synthetic dataset expansion for LoRA (optional)
If Tier 1 still drifts too much:
- generate 20–60 curated pseudo-multi-view images using the best IP-Adapter setup
- manually filter to the most on-model images
- train a lightweight LoRA on SD 1.5 first, maybe SDXL later

Important:
- do **not** train from the single source image only; bootstrap a cleaner synthetic dataset first

### Phase 5. Selective i2v
Only convert the best stills to video:
- choose 2–3 strongest scenes
- keep motion subtle
- preserve face size and composition
- avoid large view changes inside a single i2v shot

---

## Suggested evaluation rubric

Score each generated image from 1–5 on:
- face/head similarity
- silhouette/body similarity
- costume/color consistency
- prompt adherence
- overall image quality

Add simple automated metrics where possible:
- CLIP image-image similarity against reference
- face embedding similarity (only for human-like faces; e.g. InsightFace)
- DINO/CLIP embedding similarity across generated set

Keep human rating primary; automation is only support.

---

## Concrete next steps for this repo

### 1. Add a reference-guided still generator script
New script idea:
- `scripts/generate_character_stills_ipadapter.py`

Inputs:
- `--reference path/to/ref.png`
- `--spec results/storyboard_x.json`
- `--workflow workflows/ipadapter_sdxl_basic.json` or direct diffusers mode
- `--outdir results/character_stills_ipadapter`
- optional `--controlnet pose|depth|canny`

Why:
- current repo has prompt-only still generation; this is the missing main capability

### 2. Add ComfyUI workflow JSONs under `workflows/`
Recommended starter workflows:
- `ipadapter_sdxl_basic.json`
- `ipadapter_sdxl_pose.json`
- `ipadapter_sd15_fast.json`
- optional `instantid_portrait.json`

### 3. Add a consistency benchmark spec
Create:
- `results/storyboard_character_consistency_v1.json`

Include fixed prompts, seeds, and expected framing categories.

### 4. Add evaluation script
New script idea:
- `scripts/eval_character_consistency.py`

Outputs:
- CSV with per-scene scores/metadata
- optional CLIP similarity summary
- markdown report table

### 5. Add a lightweight human-review sheet
Create markdown/CSV template for:
- scene id
- method
- seed
- similarity score
- failure mode tags

### 6. Keep Wan/i2v downstream, not upstream
Use current Wan path only after still consistency is improved.
The repo already shows that i2v is feasible but expensive; identity should be solved at still-generation stage first.

---

## Suggested implementation order

1. **IP-Adapter SD 1.5 fast baseline**
2. **IP-Adapter SDXL best-quality baseline**
3. **IP-Adapter SDXL + ControlNet pose/depth**
4. **Optional InstantID portrait branch**
5. **Synthetic-data LoRA branch if needed**
6. **Only then revisit FLUX / PuLID / StoryMaker**

---

## Useful references checked
- Tencent AI Lab — **IP-Adapter** (2023, SDXL support, diffusers + ComfyUI support)
- InstantX — **InstantID** (2024, single-image zero-shot ID preservation, SDXL)
- TencentARC — **PhotoMaker / PhotoMaker V2** (single/few image identity customization, human photo oriented)
- ByteDance — **PuLID** (2024, SDXL + FLUX identity customization)
- RED-AIGC — **StoryMaker** (2024, consistency beyond face: clothing/body/story scenes)
- Hugging Face diffusers docs — **MPS / Apple Silicon guidance**
- `mflux` project — evidence that FLUX-family local generation on Mac is possible, but not the easiest first production path for this repo

---

## Final recommendation

If the target is **local/free practical success on M1 Pro 32GB**, choose:

- **Main path:** SDXL + IP-Adapter Plus + ControlNet in ComfyUI
- **Fast sweep path:** SD 1.5 + IP-Adapter
- **Portrait-only branch:** InstantID if face realism matters
- **Training path:** LoRA only after synthetic multi-view set exists
- **Defer:** FLUX-first pipeline, DreamBooth-first pipeline, heavy research stacks before baseline is measured
