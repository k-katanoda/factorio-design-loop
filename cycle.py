#!/usr/bin/env python3
"""Create an immutable candidate from a blueprint and patch; fail gate on static errors."""
import argparse, hashlib, json, sys
from pathlib import Path
from html import escape
from loop import load, encode, patch_data, inspect, diff_data, viewer_links, save

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--base',required=True);p.add_argument('--patch',required=True)
 p.add_argument('--output-dir',required=True)
 a=p.parse_args()
 root=Path(a.output_dir);root.mkdir(parents=True,exist_ok=True)
 src=load(a.base)
 patch=json.loads(Path(a.patch).read_text(encoding='utf-8'))
 sha=hashlib.sha256(encode(src).encode()).hexdigest()
 if patch.get('base_sha256') and patch['base_sha256']!=sha:
  raise ValueError('Source changed since patch generated; aborting')
 original=inspect(src)
 working, changes=patch_data(__import__('copy').deepcopy(src),patch)
 current=inspect(working)
 links=viewer_links(working)
 save(root/'blueprint.txt',working)
 (root/'baseline-validation.json').write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (root/'validation.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (root/'diff.json').write_text(json.dumps(diff_data(src,working),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (root/'viewer_urls.json').write_text(json.dumps(links,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 # Link launcher is NOT a diagram or new viewer; it only links to existing apps.
 (root/'open_viewers.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Factorio ビューアを開く</title><body><h1>設計候補</h1><p>検証: '+escape(current['status'])+'</p><p><a href="'+escape(links['factorio_tools'],quote=True)+'">FactorioToolsで開く</a></p><p><a href="'+escape(links['factorygamefan'],quote=True)+'">FactoryGameFanで開く</a></p><p>表示ができてもゲーム内動作の検証とは異なります。</p></body></html>',encoding='utf-8')
 manifest={
  'source':a.base,'base_sha256':sha,
  'blueprint_sha256':hashlib.sha256(encode(working).encode()).hexdigest(),
  'patch_description':patch.get('description',''),
  'operation_count':len(changes),
  'gate':'STATIC_PASS_GAME_NOT_TESTED' if current['status']=='PASS_STATIC_LIMITED' else 'BLOCKED_BY_STATIC_VALIDATION',
  'known_limitations':['Subset-only fluid model','Static topology not real flow','Heat network not checked','Fuel/circuits not checked','No Factorio runtime placement test','No terrain verification'],
 }
 (root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Gate:',manifest['gate'])
 print('Water:',f"{current['water']['reachable']}/{current['water']['inputs']}", 'Steam:',f"{current['steam']['reachable']}/{current['steam']['turbines']}")
 print('Updated output directory:',root)
 if manifest['gate'].startswith('BLOCKED'):return 2
 return 0

if __name__=='__main__':raise SystemExit(main())
