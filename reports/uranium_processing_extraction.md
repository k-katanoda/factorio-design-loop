# ウラン鉱石処理の抽出

- 出典: https://www.factorio.school/view/-LXzozjgsU36ONhpW7tP
- 取得元ミラー: https://github.com/motlin/factorio-blueprint-firebase-cdn/blob/main/-lx/-LXzozjgsU36ONhpW7tP.json
- ブック原本: `designs/uranium_processing_book_source.txt`
- 抽出した図面: `designs/uranium_processing_no_modules_red_legacy.txt`
- 対象ラベル: `Uranium Processing - No Modules - Red`
- 原本のバージョン: Factorio 0.16.51.0
- 抽出結果のSHA-256: `a457383d565861e69f3876632f5190fc7892be3fbba51e7842b681760434f5c3`

## 内容

ブック内の独立した鉱石処理図面を丸ごと抽出した。遠心分離機10基はすべてウラン鉱石処理レシピで、ベルト・フィルター・分配器・鋼鉄のチェスト5個・変電所3基を含む。Kovarex濃縮設備や燃料セル製造設備は含まない。

抽出前後のデコード結果を比較し、対象ページのデータが変わっていないことを確認した。

## 2.0統合候補

`integrate_uranium.py` は元の図面の方向を2.0形式に変換し、フィルターインサータをフィルター有効の高速インサータに置き換える。処理設備を180度回して既存プラントの北側に配置し、ウラン235・238の2出口を既存の分配器へ別々につないだ。原子炉側の電力網へ電柱と電線を追加した。

- 単独の変換候補: `designs/uranium_processing_red_2_0_candidate.txt`
- 統合候補: `designs/nuclear_uranium_ore_candidate.txt`
- ウラン鉱石の外部入力: `(-21.5, -257.5)` の西向き高速ベルト
- 別途、鉄鉱石とウラン鉱石を供給する必要がある。ウラン鉱石の採掘には硫酸が必要。

静的検査では設備間の矩形の重複、追加ベルトの接続点と電線長を検査した。0.16から2.0への移行、フィルター、バッファ、個々のベルトレーン、通電、起動とゲーム内動作は `UNKNOWN`。
