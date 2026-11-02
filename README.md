# Factorio 設計→検証→修正ループ（試作 v0.1）

## 目的
ゲーム内で成立する工場へ近づけるために、同じBlueprintを正本として維持し、変更ごとに**自動検証→差分確認→不合格なら再修正**を繰り返す仕組みの最小実装です。

対象の試験データは、既存の4基原子炉（776エンティティ）です。**元データは変更しません**。`designs/nuclear_baseline.txt` が修正前、`revisions/r001/blueprint.txt` が修正候補です。

## 検証対象（試作の範囲）

- 各設備の中心座標と占有タイルの整合性（原子炉・配管・熱交換器・タービン・タンク・ヒートパイプ）
- 指定範囲の設備同士の重複
- 液体設備ごとの接続口の位置と向き
- 地下パイプの向き、ペア探索、最大距離（最大10マスの地下距離）
- 水源からすべての熱交換器の水入力までの到達性
- 熱交換器の蒸気出力からすべてのタービンまでの到達性
- 修正前後のエンティティ差分
- 既存のFactorioTools/FactoryGameFanへ渡すリンク

### 未実装＝未検証

- **Factorio本体の実行試験（最優先）**、地形・水際の設置可能性
- 原子炉から熱交換器までの熱ネットワークと熱損失、核燃料投入・回収
- Fluid throughput/液面/流量、回路制御、電力供給、ベルト搬送、レシピ
- サブセット外の全Space Age設備の形状・接続

`PASS_STATIC_LIMITED` は「対象サブセットの静的検査に合格」であり、「ゲームで正常動作する」という意味では**ありません**。原則としてFactorio本体でのテスト後にのみ「稼働確認済み」にします。

## 実行方法（Python 3.10以上、外部パッケージ不要）

```bash
# 現在の設計を検証（FAILなら終了コード1）
python loop.py validate designs/nuclear_baseline.txt

# 原案を修正するループを実行（原案は不変）
python cycle.py --base designs/nuclear_baseline.txt --patch designs/water_patch_proposal.json --output-dir revisions/r001

# 変更内容を出力
python loop.py diff designs/nuclear_baseline.txt revisions/r001/blueprint.txt

# 自動テスト8件を実行
python -m unittest discover -s tests -v
```

`revisions/r001/open_viewers.html` は**ビューアではなく、公開済みの2つのWebビューアへのリンクだけ**を載せたランチャーです。Androidでも利用できます。URLにBlueprint文字列を埋め込むため、将来的な固定URLの自動更新には別途保存・配信連携が必要です。

## 1回の作業単位

1. 指示に応じてBlueprint変更案を作成し、差分をパッチに記録します。
2. `cycle.py` で新しいリビジョンを作り、自動検証します。
3. `BLOCKED_BY_STATIC_VALIDATION` の場合は修正案を再検討し、元データは維持します。
4. `STATIC_PASS_GAME_NOT_TESTED` ならWebビューアで確認します。**稼働保証はしません**。
5. 将来的には Factorio 2.0.77 の `--test-scenario` などで配置・稼働を自動検査し、そのログを判定に追加します。

## 今回の結果

| 対象 | 給水到達 | 蒸気到達 | 静的ゲート |
|---|---:|---:|---|
| 修正前 | 0 / 48 | 84 / 84 | FAIL |
| 修正候補 r001 | 48 / 48 | 84 / 84 | PASS_STATIC_LIMITED |

修正内容は通常パイプへの変更1個、通常パイプの追加1個、地下パイプの撤去1個です。元データを置き換える操作は行っていません。

## GitHubでの運用（公開リポジトリ）

- GitHub `k-katanoda/factorio-design-loop` を正本とし、`main` 更新時にGitHub Actionsでテスト・整合性チェックを実行します。
- `revisions/current.json` が現在候補を指します。既存リビジョンは上書きしません。
- `python verify_release.py` は原案＋パッチからの再生成一致、SHA256、レポート整合性、限定的静的ゲートを検査します。
- `python build_pages.py` で `docs/` を生成します。`python build_pages.py --check` で生成物が最新か検査します。
- Pages の公開モードをGitHub Actionsに設定すれば、検査成功時のみ固定URL `https://k-katanoda.github.io/factorio-design-loop/` にリンクページを公開します。
- `docs/` のページは独自ビューアではなくFactorioTools / FactoryGameFanへの外部リンクを提供するだけです。
- **自動修正AIやFactorio本体での実機テストはまだ実装していません。** 修正候補の作成→検証の反復はChatGPTまたは人間が行います。静的検証でPASSでもゲームで動くとは断言しません。

