#!/usr/bin/env python3
from pathlib import Path
import argparse, json
import torch
from diffusers import AutoPipelineForText2Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--model', default='stabilityai/sdxl-turbo')
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    dtype = torch.float16 if device == 'mps' else torch.float32

    pipe = AutoPipelineForText2Image.from_pretrained(args.model, torch_dtype=dtype, variant='fp16' if device == 'mps' else None)
    pipe = pipe.to(device)
    pipe.set_progress_bar_config(disable=False)

    negative = 'blurry, low quality, deformed hands, extra fingers, text, watermark, logo, gore, ugly, bad anatomy'

    for s in spec['scenes']:
        seed = int(s.get('seed', 42))
        generator = torch.Generator(device='cpu').manual_seed(seed)
        image = pipe(
            prompt=s['prompt'] + ', rabbit-based character design, anime movie still, polished shading, expressive lighting, clean line art, consistent bunny mascot character',
            negative_prompt=negative,
            num_inference_steps=4,
            guidance_scale=0.0,
            height=1024,
            width=576,
            generator=generator,
        ).images[0]
        out = outdir / f"scene_{s['index']:02d}.png"
        image.save(out)
        print(f'[ok] wrote {out}')


if __name__ == '__main__':
    main()
