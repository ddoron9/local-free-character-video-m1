#!/usr/bin/env python3
import os
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
os.environ.setdefault('PYTORCH_MPS_HIGH_WATERMARK_RATIO', '0.0')

import sys
import argparse
import importlib.util
from pathlib import Path
import numpy as np
import imageio.v2 as imageio
from PIL import Image
import torch


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--comfy-root', required=True)
    ap.add_argument('--image', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--prompt', default='A cinematic astronaut floating gently in outer space, subtle body movement, Earth glowing in the background, highly detailed, realistic, smooth motion')
    ap.add_argument('--negative', default='blurry, low quality, distorted anatomy, flicker, warped face, ugly, noisy, oversaturated')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--steps', type=int, default=2)
    args = ap.parse_args()

    root = Path(args.comfy_root).resolve()
    img_path = Path(args.image).resolve()
    out_path = Path(args.out).resolve()

    sys.path.insert(0, str(root))
    os.chdir(root)

    import nodes
    import comfy.model_management

    gg_path = root / 'custom_nodes/ComfyUI-GGUF'
    link_path = root / 'custom_nodes/ComfyUI_GGUF'
    if gg_path.exists() and not link_path.exists():
        link_path.symlink_to(gg_path)

    import custom_nodes.ComfyUI_GGUF.nodes as gg
    wan_nodes = load_module('comfyui_wan_nodes', root / 'comfy_extras/nodes_wan.py')

    print('[1] loading image', img_path)
    img = Image.open(img_path).convert('RGB').resize((832, 480))
    arr = np.asarray(img).astype(np.float32) / 255.0
    image = torch.from_numpy(arr)[None, ...]

    print('[2] loading text encoder')
    clip = nodes.CLIPLoader().load_clip('umt5_xxl_fp8_e4m3fn_scaled.safetensors', 'wan', 'default')[0]
    print('[3] loading clip vision')
    clip_vision = nodes.CLIPVisionLoader().load_clip('clip_vision_h.safetensors')[0]
    print('[4] loading vae')
    vae = nodes.VAELoader().load_vae('wan_2.1_vae.safetensors')[0]
    print('[5] loading wan gguf unet')
    model = gg.UnetLoaderGGUFAdvanced().load_unet('wan2.1-i2v-14b-480p-Q4_K_M.gguf', 'target', 'target', False)[0]

    print('[6] encoding prompts')
    pos = nodes.CLIPTextEncode().encode(clip, args.prompt)[0]
    neg = nodes.CLIPTextEncode().encode(clip, args.negative)[0]
    print('[7] encoding clip vision')
    cv = nodes.CLIPVisionEncode().encode(clip_vision, image, 'center')[0]
    print('[8] creating wan i2v latent')
    pos, neg, latent = wan_nodes.WanImageToVideo.execute(pos, neg, vae, 832, 480, 8, 1, start_image=image, clip_vision_output=cv)
    print(f'[9] sampling with {args.steps} steps')
    latent_out = nodes.KSampler().sample(model, args.seed, args.steps, 4.5, 'euler', 'simple', pos, neg, latent, 1.0)[0]
    print('[10] decoding')
    frames = nodes.VAEDecode().decode(vae, latent_out)[0]
    frames = (frames.clamp(0, 1).detach().cpu().numpy() * 255).astype(np.uint8)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(out_path, frames, fps=8)
    print('[done]', out_path, frames.shape)


if __name__ == '__main__':
    main()
