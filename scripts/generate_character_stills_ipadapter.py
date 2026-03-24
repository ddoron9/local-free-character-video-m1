#!/usr/bin/env python3
from pathlib import Path
import argparse, json, urllib.request, urllib.error


def queue_prompt(server: str, workflow: dict):
    data = json.dumps({'prompt': workflow}).encode('utf-8')
    req = urllib.request.Request(
        server.rstrip('/') + '/prompt',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def apply_scene_to_workflow(workflow: dict, scene: dict, reference: str, outdir: str, seed: int):
    wf = json.loads(json.dumps(workflow))
    meta = {
        'scene_id': scene['id'],
        'scene_index': scene['index'],
        'seed': seed,
        'reference': reference,
        'prompt': scene['prompt'],
        'controlnet': scene.get('controlnet'),
        'output_dir': outdir,
    }
    for node_id, node in wf.items():
        if not isinstance(node, dict):
            continue
        inputs = node.get('inputs', {})
        title = (node.get('_meta') or {}).get('title', '')
        class_type = node.get('class_type', '')
        if 'prompt' in inputs and title in ('POSITIVE_PROMPT', 'Positive Prompt', ''):
            if class_type in ('CLIPTextEncode', 'CLIPTextEncodeSDXL'):
                inputs['text'] = scene['prompt']
        if 'text' in inputs and title in ('POSITIVE_PROMPT', 'Positive Prompt'):
            inputs['text'] = scene['prompt']
        if 'seed' in inputs:
            inputs['seed'] = seed
        if 'image' in inputs and title in ('REFERENCE_IMAGE', 'Reference Image'):
            inputs['image'] = reference
        if 'filename_prefix' in inputs:
            inputs['filename_prefix'] = f"{outdir}/scene_{scene['index']:02d}_seed{seed}"
        node.setdefault('_openclaw_meta', meta)
    return wf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reference', required=True)
    ap.add_argument('--spec', required=True)
    ap.add_argument('--workflow', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--server', default='http://127.0.0.1:8188')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    reference = Path(args.reference)
    spec_path = Path(args.spec)
    workflow_path = Path(args.workflow)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    spec = load_json(spec_path)
    workflow_template = load_json(workflow_path)
    seeds = spec.get('seeds', [42])

    submissions = []
    for scene in spec['scenes']:
        for seed in seeds:
            wf = apply_scene_to_workflow(
                workflow_template,
                scene=scene,
                reference=reference.as_posix(),
                outdir=outdir.as_posix(),
                seed=int(seed),
            )
            payload_path = outdir / f"workflow_scene_{scene['index']:02d}_seed{seed}.json"
            payload_path.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding='utf-8')
            if args.dry_run:
                print(f'[dry-run] wrote {payload_path}')
                submissions.append({'scene': scene['id'], 'seed': seed, 'payload': payload_path.as_posix()})
                continue
            try:
                resp = queue_prompt(args.server, wf)
                print(f"[queued] scene={scene['id']} seed={seed} prompt_id={resp.get('prompt_id')}")
                submissions.append({'scene': scene['id'], 'seed': seed, 'response': resp})
            except urllib.error.URLError as e:
                print(f"[error] failed queueing scene={scene['id']} seed={seed}: {e}")
                submissions.append({'scene': scene['id'], 'seed': seed, 'error': str(e)})
    manifest = outdir / 'submission_manifest.json'
    manifest.write_text(json.dumps(submissions, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[ok] manifest: {manifest}')


if __name__ == '__main__':
    main()
