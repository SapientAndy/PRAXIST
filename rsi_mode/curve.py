"""Render the promotion score curve from append-only promotion records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape


def read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_svg(records: list[dict], title: str) -> str:
    width, height = 760, 380
    left, right, top, bottom = 78, 28, 42, 56
    plot_w = width - left - right
    plot_h = height - top - bottom
    points = sorted(records, key=lambda r: (int(r.get("generation", 0)), float(r.get("score", 0))))
    max_score = max([float(r.get("score", 0)) for r in points] + [1.0])
    max_gen = max([int(r.get("generation", 0)) for r in points] + [1])
    y_max = max_score * 1.08

    def x(gen: int) -> float:
        return left + (gen / max(max_gen, 1)) * plot_w

    def y(score: float) -> float:
        return top + plot_h - (score / y_max) * plot_h

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="26" font-family="Segoe UI, sans-serif" font-size="17" font-weight="600" fill="#111827">{escape(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#9ca3af" stroke-width="1"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#9ca3af" stroke-width="1"/>',
    ]
    for i in range(4):
        score = y_max * i / 3
        yy = y(score)
        lines.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + plot_w}" y2="{yy:.1f}" stroke="#e5e7eb" stroke-width="1"/>')
        lines.append(f'<text x="{left - 10}" y="{yy + 4:.1f}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="11" fill="#6b7280">{score:.2f}</text>')
    for gen in range(max_gen + 1):
        xx = x(gen)
        lines.append(f'<text x="{xx:.1f}" y="{top + plot_h + 20}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="11" fill="#6b7280">gen {gen}</text>')

    approved = [p for p in points if p.get("status") == "approved"]
    proposed = [p for p in points if p.get("status") != "approved"]
    for group, color, dash in ((proposed, "#f59e0b", ' stroke-dasharray="5 4"'), (approved, "#2563eb", "")):
        if len(group) >= 2:
            path = " ".join(
                ("M" if i == 0 else "L") + f"{x(int(p.get('generation', 0))):.1f},{y(float(p.get('score', 0))):.1f}"
                for i, p in enumerate(group)
            )
            lines.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"{dash}/>')
    for p in points:
        xx, yy = x(int(p.get("generation", 0))), y(float(p.get("score", 0)))
        color = "#2563eb" if p.get("status") == "approved" else "#f59e0b"
        lines.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="5" fill="{color}" stroke="#ffffff" stroke-width="2"/>')
        lines.append(f'<text x="{xx:.1f}" y="{yy - 10:.1f}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="11" fill="#111827">{float(p.get("score", 0)):.3f}</text>')

    lines.append(f'<text x="{left}" y="{height - 14}" font-family="Segoe UI, sans-serif" font-size="11" fill="#6b7280">blue = approved by human gate · amber = proposed</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promotions", default="promotions/promotions.jsonl")
    parser.add_argument("--out", default="promotions/curve.svg")
    parser.add_argument("--json-out", default="promotions/curve.json")
    parser.add_argument("--title", default="Capability curve")
    args = parser.parse_args()
    records = read_records(Path(args.promotions))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_svg(records, args.title), encoding="utf-8")
    Path(args.json_out).write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "svg": str(out), "json": args.json_out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
