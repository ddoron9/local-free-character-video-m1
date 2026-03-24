#!/usr/bin/env python3
from pathlib import Path
import argparse, json, subprocess

W, H = 1080, 1920

CAPTIONS = {
    1: '보호복 없이 우주로 나가면',
    2: '먼저 산소 부족으로 의식이 흐려지고',
    3: '체액은 낮은 압력 때문에 끓듯 팽창하고',
    4: '결국 수 초 안에 생존이 어려워진다',
}


def run(cmd):
    subprocess.run(cmd, check=True)


def esc(s: str) -> str:
    return s.replace("'", "\\'").replace(':', '\\:')


def clip_from_image(img: Path, out: Path, seconds: int, idx: int):
    fps = 30
    total = seconds * fps
    zoom = 1.0 + idx * 0.015
    caption = esc(CAPTIONS.get(idx, ''))
    vf = (
        f"scale={W}:{H},"
        f"zoompan=z='min({zoom}+on*0.0007,{zoom+0.10})':x='iw/2-(iw/zoom/2)+sin(on/20)*18':y='ih/2-(ih/zoom/2)+cos(on/24)*24':d={total}:s={W}x{H}:fps={fps},"
        f"eq=saturation=1.15:contrast=1.08,"
        f"drawbox=x=40:y=1500:w={W-80}:h=250:color=black@0.35:t=fill,"
        f"drawtext=fontfile=/System/Library/Fonts/Supplemental/Verdana\ Bold.ttf:text='{caption}':fontcolor=white:fontsize=58:x=80:y=1580:line_spacing=12,"
        f"fade=t=in:st=0:d=0.35,fade=t=out:st={max(seconds-0.45,0)}:d=0.45"
    )
    run(['ffmpeg','-y','-loop','1','-i',str(img),'-vf',vf,'-t',str(seconds),'-pix_fmt','yuv420p','-r',str(fps),str(out)])


def concat(clips, out):
    lst = out.parent / 'concat_list.txt'
    lines = []
    for c in clips:
        lines.append(f"file '{c.resolve().as_posix()}'\n")
    lst.write_text(''.join(lines), encoding='utf-8')
    run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(lst.resolve()),'-c:v','libx264','-pix_fmt','yuv420p',str(out.resolve())])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    img_dir = Path(args.images)
    tmp = Path(args.out).parent / 'anime_clips'
    tmp.mkdir(parents=True, exist_ok=True)
    clips = []
    for s in spec['scenes']:
        img = img_dir / f"scene_{s['index']:02d}.png"
        clip = tmp / f"scene_{s['index']:02d}.mp4"
        clip_from_image(img, clip, int(s['seconds']), int(s['index']))
        clips.append(clip)
    concat(clips, Path(args.out))
    print(f'[ok] wrote {args.out}')


if __name__ == '__main__':
    main()
