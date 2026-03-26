#!/usr/bin/env python3
from pathlib import Path
import argparse, json
import torch
from PIL import Image
from diffusers import AutoPipelineForText2Image


def load_spec(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--reference', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--base-model', default='stabilityai/sdxl-turbo')
    ap.add_argument('--ip-repo', default='h94/IP-Adapter')
    ap.add_argument('--ip-weight', default='ip-adapter_sdxl.safetensors')
    ap.add_argument('--negative-prompt', default='blurry, low quality, bad anatomy, duplicate character, multiple characters, text, watermark, logo, distorted ears, wrong costume colors')
    ap.add_argument('--steps', type=int, default=6)
    ap.add_argument('--guidance-scale', type=float, default=1.5)
    ap.add_argument('--ip-scale', type=float, default=0.7)
    args = ap.parse_args()

    spec = load_spec(Path(args.spec))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    dtype = torch.float16 if device == 'mps' else torch.float32

    pipe = AutoPipelineForText2Image.from_pretrained(
        args.base_model,
        torch_dtype=dtype,
        variant='fp16' if device == 'mps' else None,
    )
    pipe = pipe.to(device)
    pipe.load_ip_adapter(
        args.ip_repo,
        subfolder='sdxl_models',
        weight_name=args.ip_weight,
        image_encoder_folder='sdxl_models/image_encoder',
    )
    pipe.set_ip_adapter_scale(args.ip_scale)
    pipe.set_progress_bar_config(disable=False)

    ref = Image.open(args.reference).convert('RGB').resize((512, 512))

    for scene in spec['scenes']:
        seed = int(scene.get('seed', 42))
        generator = torch.Generator(device='cpu').manual_seed(seed)
        prompt = scene['prompt']
        img = pipe(
            prompt=prompt,
            negative_prompt=args.negative_prompt,
            ip_adapter_image=ref,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance_scale,
            height=1024,
            width=576,
            generator=generator,
        ).images[0]
        out = outdir / f"scene_{scene['index']:02d}.png"
        img.save(out)
        print(f'[ok] wrote {out}')


if __name__ == '__main__':
    main()
