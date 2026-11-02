#!/usr/bin/env python3
"""Generate a tiny Android-friendly *link launcher*, not a new Factorio renderer."""
from __future__ import annotations
import argparse, html, json, shutil
from pathlib import Path
from verify_release import ROOT, check

def generate(out: Path):
    revision = check()
    folder = ROOT / 'revisions' / revision
    validation = json.loads((folder/'validation.json').read_text(encoding='utf-8'))
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    links = json.loads((folder/'viewer_urls.json').read_text(encoding='utf-8'))
    def esc(v): return html.escape(str(v), quote=True)
    def li(s): return f'<li>{esc(s)}</li>'
    page = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Factorio Design Loop · {esc(revision)}</title><style>
:root{{color-scheme:light dark;font-family:system-ui,sans-serif}} body{{max-width:720px;margin:0 auto;padding:22px 16px;line-height:1.65}}
article{{border:1px solid #8b8b8b55;border-radius:12px;padding:18px;margin:15px 0}}a.action{{display:block;padding:14px;margin:10px 0;border:1px solid #8b8b8b;border-radius:10px;text-decoration:none;font-weight:700}}
small{{color:gray}} th,td{{padding:6px 14px 6px 0;text-align:left}} table{{border-collapse:collapse}} .warning{{font-weight:700}} code{{overflow-wrap:anywhere}}
</style></head><body>
<h1>Factorio 工場設計</h1><p>現在の候補：<strong>{esc(revision)}</strong> ／ 4基原子炉</p>
<article><h2>検証状況</h2><p class="warning">静的検証は限定的に合格・ゲーム内稼働は未検証</p>
<table><tr><th>水入力への到達</th><td>{validation['water']['reachable']} / {validation['water']['inputs']} 基</td></tr>
<tr><th>蒸気タービンへの到達</th><td>{validation['steam']['reachable']} / {validation['steam']['turbines']} 基</td></tr>
<tr><th>地下パイプ未ペア</th><td>{len(validation['underground_unpaired'])}</td></tr><tr><th>静的ゲート</th><td>{esc(manifest['gate'])}</td></tr></table>
<p><small>地形、熱伝導、燃料搬送、流量、回路、Factorio本体での設置・稼働は未検証です。</small></p></article>
<article><h2>Androidで図面を開く</h2>
<a class="action" href="{esc(links['factorio_tools'])}" rel="noopener noreferrer">FactorioToolsで開く</a>
<a class="action" href="{esc(links['factorygamefan'])}" rel="noopener noreferrer">FactoryGameFanで開く</a>
<p><small>外部のWebビューアを使います。このページは専用描画アプリではありません。</small></p></article>
<article><h2>設計データと結果</h2>
<p><a href="blueprint.txt" download>Blueprint文字列</a> ・ <a href="validation.json">検証詳細</a> ・ <a href="diff.json">修正差分</a> ・ <a href="manifest.json">変更記録</a></p>
<p><a href="https://github.com/k-katanoda/factorio-design-loop">GitHubの正本へ</a></p></article>
</body></html>'''
    out.mkdir(parents=True, exist_ok=True)
    (out/'index.html').write_text(page+'\n',encoding='utf-8')
    for name in ('blueprint.txt','validation.json','diff.json','manifest.json'):
        shutil.copyfile(folder/name, out/name)
    (out/'.nojekyll').write_text('', encoding='utf-8')

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='docs'); ap.add_argument('--check',action='store_true')
    a=ap.parse_args()
    out=Path(a.out)
    if a.check:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            generate(Path(tmp))
            for p in Path(tmp).iterdir():
                original=out/p.name
                if not original.exists() or original.read_bytes()!=p.read_bytes():
                    raise SystemExit(f'Stale site file: {original}')
        print('Pages content is in sync')
    else:
        generate(out);print('Built Pages:', out)
