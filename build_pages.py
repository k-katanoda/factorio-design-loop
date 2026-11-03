#!/usr/bin/env python3
"""Generate a tiny Android-friendly *link launcher*, not a new Factorio renderer."""
from __future__ import annotations
import argparse, html, json, shutil
from pathlib import Path
from verify_release import ROOT, check
from loop import load, viewer_links

def generate(out: Path):
    revision = check()
    folder = ROOT / 'revisions' / revision
    validation = json.loads((folder/'validation.json').read_text(encoding='utf-8'))
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    links = json.loads((folder/'viewer_urls.json').read_text(encoding='utf-8'))
    fuel_blueprint = load(ROOT/'designs/nuclear_fuel_optimised_circuit_v1.txt')
    fuel_links = viewer_links(fuel_blueprint)
    fuel_report = json.loads((ROOT/'reports/nuclear_fuel_optimised_circuit_v1.json').read_text(encoding='utf-8'))
    integrated = load(ROOT/'designs/nuclear_uranium_ore_candidate.txt')
    integrated_links = viewer_links(integrated)
    mining = load(ROOT/'designs/nuclear_mining_provisional.txt')
    mining_links = viewer_links(mining)
    def esc(v): return html.escape(str(v), quote=True)
    def li(s): return f'<li>{esc(s)}</li>'
    page = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Factorio Design Loop · {esc(revision)}</title><style>
:root{{color-scheme:light dark;font-family:system-ui,sans-serif}} body{{max-width:720px;margin:0 auto;padding:22px 16px;line-height:1.65}}
article{{border:1px solid #8b8b8b55;border-radius:12px;padding:18px;margin:15px 0}}a.action{{display:block;padding:14px;margin:10px 0;border:1px solid #8b8b8b;border-radius:10px;text-decoration:none;font-weight:700}}
small{{color:gray}} th,td{{padding:6px 14px 6px 0;text-align:left}} table{{border-collapse:collapse}} .warning{{font-weight:700}} code{{overflow-wrap:anywhere}}
</style></head><body>
<h1>Factorio 工場設計</h1><p>現在の候補：<strong>{esc(revision)}</strong> ／ 4基原子炉</p>
<article><h2>採掘・硫酸供給を追加した仮配置</h2>
<p>電気採掘機、油井、石油処理、硫黄・硫酸製造、水ポンプ、硫酸タンクを追加した実験候補です。</p>
<p class="warning">鉱床・油田・海岸は仮定です。図面は資源や水面を生成しません。ゲーム内の設置・運転・循環は未検証（UNKNOWN）です。</p>
<a class="action" href="{esc(mining_links['factorio_tools'])}" rel="noopener noreferrer">仮配置をFactorioToolsで開く</a>
<a class="action" href="{esc(mining_links['factorygamefan'])}" rel="noopener noreferrer">仮配置をFactoryGameFanで開く</a>
<p><a href="nuclear-mining-provisional.txt" download>仮配置Blueprint</a> ・ <a href="mining-acid-provisional.md">出典・収支と未確認事項</a></p></article>
<article><h2>原子炉＋燃料製造・再処理プラント</h2>
<p>4基原子炉に燃料セル製造・再処理、電気炉1基、ウラン鉱石処理設備を接続した統合候補です。ウラン鉱石と鉄鉱石は外部から供給します。</p>
<p class="warning">ゲーム内動作、旧形式からの変換、ベルト流量は未検証です（UNKNOWN）。</p>
<p>回収ベルトの誤接続と原子炉インサータの回路条件を修正しました。使用済みセルの返送先は再処理設備の入力ベルトです。レーン詰まりの有無は未確認です。</p>
<a class="action" href="{esc(integrated_links['factorio_tools'])}" rel="noopener noreferrer">統合候補をFactorioToolsで開く</a>
<a class="action" href="{esc(integrated_links['factorygamefan'])}" rel="noopener noreferrer">統合候補をFactoryGameFanで開く</a>
<p><a href="nuclear-fuel-integrated.txt" download>統合Blueprint</a> ・ <a href="nuclear-fuel-integrated-report.json">検証状況</a></p></article>
<article><h2>検証状況</h2><p class="warning">静的検証は限定的に合格・ゲーム内稼働は未検証</p>
<table><tr><th>水入力への到達</th><td>{validation['water']['reachable']} / {validation['water']['inputs']} 基</td></tr>
<tr><th>蒸気タービンへの到達</th><td>{validation['steam']['reachable']} / {validation['steam']['turbines']} 基</td></tr>
<tr><th>地下パイプ未ペア</th><td>{len(validation['underground_unpaired'])}</td></tr><tr><th>静的ゲート</th><td>{esc(manifest['gate'])}</td></tr></table>
<p><small>地形、熱伝導、燃料搬送、流量、回路、Factorio本体での設置・稼働は未検証です。</small></p></article>
<article><h2>Fuel-Optimisedベース：回路修正版 v1</h2>
<p>公開ブループリントを複製し、4基それぞれの燃料投入・使用済み燃料回収回路を修正した候補です。</p>
<p class="warning">回路のゲーム内動作は未検証です（UNKNOWN）。</p>
<a class="action" href="{esc(fuel_links['factorio_tools'])}" rel="noopener noreferrer">回路修正版をFactorioToolsで開く</a>
<a class="action" href="{esc(fuel_links['factorygamefan'])}" rel="noopener noreferrer">回路修正版をFactoryGameFanで開く</a>
<p><a href="fuel-optimised-blueprint.txt" download>回路修正版Blueprint</a> ・ <a href="fuel-optimised-source.txt" download>元のBlueprint</a> ・ <a href="fuel-optimised-circuit-report.json">回路変更記録</a></p>
<p><small>SHA-256: <code>{esc(fuel_report['candidate_sha256'])}</code></small></p></article>
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
    shutil.copyfile(ROOT/'designs/nuclear_fuel_optimised_circuit_v1.txt', out/'fuel-optimised-blueprint.txt')
    shutil.copyfile(ROOT/'designs/nuclear_fuel_optimised_source.txt', out/'fuel-optimised-source.txt')
    shutil.copyfile(ROOT/'reports/nuclear_fuel_optimised_circuit_v1.json', out/'fuel-optimised-circuit-report.json')
    shutil.copyfile(ROOT/'designs/nuclear_uranium_ore_candidate.txt', out/'nuclear-fuel-integrated.txt')
    shutil.copyfile(ROOT/'reports/nuclear_uranium_ore_candidate.json', out/'nuclear-fuel-integrated-report.json')
    shutil.copyfile(ROOT/'designs/nuclear_mining_provisional.txt', out/'nuclear-mining-provisional.txt')
    shutil.copyfile(ROOT/'reports/mining_acid_provisional.md', out/'mining-acid-provisional.md')
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
