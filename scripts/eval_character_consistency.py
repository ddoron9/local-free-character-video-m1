#!/usr/bin/env python3
from pathlib import Path
import argparse, csv, json

CRITERIA = [
    'face_head_similarity',
    'silhouette_body_similarity',
    'costume_color_consistency',
    'prompt_adherence',
    'overall_quality',
]

FAILURE_TAGS = [
    'face_drift',
    'ear_shape_drift',
    'costume_color_drift',
    'extra_character',
    'bad_hands',
    'pose_mismatch',
    'background_overpowering_subject',
    'low_detail',
    'other',
]


def ensure_review_csv(path: Path, spec: dict, method: str):
    if path.exists():
        return
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'scene_index', 'scene_id', 'seed', 'method', 'image_path',
            *CRITERIA, 'failure_tags', 'notes'
        ])
        for scene in spec['scenes']:
            seeds = spec.get('seeds', [scene.get('seed', 42)])
            for seed in seeds:
                writer.writerow([
                    scene['index'], scene['id'], seed, method,
                    f"scene_{scene['index']:02d}_seed{seed}.png",
                    '', '', '', '', '', '', ''
                ])


def summarize_csv(path: Path):
    rows = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    scored = []
    for row in rows:
        vals = []
        for c in CRITERIA:
            try:
                vals.append(float(row[c]))
            except Exception:
                pass
        if vals:
            row['_mean'] = sum(vals) / len(vals)
            scored.append(row)
    return rows, scored


def write_markdown(out: Path, rows: list, scored: list, method: str):
    lines = []
    lines.append(f"# Character consistency review summary: {method}")
    lines.append('')
    if scored:
        mean_total = sum(r['_mean'] for r in scored) / len(scored)
        lines.append(f"- Reviewed samples with numeric scores: **{len(scored)}**")
        lines.append(f"- Mean aggregate score: **{mean_total:.2f} / 5.00**")
    else:
        lines.append('- No numeric scores entered yet.')
    lines.append('')
    lines.append('## Failure tag frequency')
    counts = {k: 0 for k in FAILURE_TAGS}
    for row in rows:
        tags = [t.strip() for t in (row.get('failure_tags') or '').split(',') if t.strip()]
        for t in tags:
            counts[t] = counts.get(t, 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        if v:
            lines.append(f"- {k}: {v}")
    if not any(counts.values()):
        lines.append('- none yet')
    lines.append('')
    lines.append('## Per-sample summary')
    for row in scored:
        lines.append(
            f"- scene {row['scene_index']} / seed {row['seed']}: {row['_mean']:.2f}"
            f" ({row.get('failure_tags') or 'no tags'})"
        )
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--method', required=True, help='e.g. ipadapter_sdxl_basic')
    ap.add_argument('--review-csv', required=True)
    ap.add_argument('--summary-md', required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    review_csv = Path(args.review_csv)
    summary_md = Path(args.summary_md)
    review_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_md.parent.mkdir(parents=True, exist_ok=True)

    ensure_review_csv(review_csv, spec, args.method)
    rows, scored = summarize_csv(review_csv)
    write_markdown(summary_md, rows, scored, args.method)
    print(f'[ok] review sheet: {review_csv}')
    print(f'[ok] summary: {summary_md}')


if __name__ == '__main__':
    main()
