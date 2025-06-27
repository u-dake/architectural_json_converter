# リファクタリング実行計画書

作成日: 2025-06-28
対象プロジェクト: architectural_json_converter

## 1. リファクタリング目標

1. **ディレクトリ構造の整理**
   - 散乱したファイルを適切なディレクトリに整理
   - 不要なファイル・ディレクトリを削除

2. **コードの簡素化**
   - 重複機能の統合
   - レガシーコードの削除

3. **スケール処理の改善**
   - CAD標準スケールの徹底
   - 動的スケール調整の制限

## 2. 実行計画（フェーズ別）

### フェーズ1: ディレクトリ整理（即実行可能）

```bash
# 1. バックアップの作成
git add -A
git commit -m "Before refactoring: backup current state"

# 2. 出力ディレクトリの統合
mkdir -p output
rm -rf test_output test_output_fixed output_test output_final debug_output

# 3. デバッグツールの整理
mkdir -p tools/debug
mv analyze_*.py tools/debug/
mv test_*.py tools/debug/
mv simple_bounds_check.py tools/debug/

# 4. レガシーファイルの移動
mkdir -p legacy
mv src/main_legacy.py legacy/
mv "250618_図面セット" legacy/ 2>/dev/null || true

# 5. .gitignoreの更新
echo "output/" >> .gitignore
echo "tools/debug/output/" >> .gitignore
echo "legacy/" >> .gitignore
```

### フェーズ2: コード整理（要確認）

#### 2.1 Visualizerの統合

**現状の問題:**
- `safe_pdf_visualizer.py`と`cad_standard_visualizer.py`の機能重複
- エラー処理が分散

**対応:**
```python
# cad_standard_visualizer.pyに以下を追加
def _save_pdf_safely(self, output_path: str, dpi: int):
    """PDFを安全に保存（safe_pdf_visualizerから移植）"""
    try:
        # 既存のコード
    except Exception as e:
        # PNG fallbackなどの安全機能を追加
```

#### 2.2 main.pyの改善

**改善内容:**
- コマンド体系の整理
- ヘルプメッセージの充実
- バッチ処理の改善

### フェーズ3: スケール処理の改善

#### 3.1 layout_util.pyの制限

**問題点:**
- `compute_fit_scale`が動的にスケールを変更
- CAD標準（1:100）との競合

**対応案:**
```python
# オプション1: 関数を削除して固定スケールのみ使用
# オプション2: フラグで動的調整を無効化
def compute_fit_scale(..., allow_dynamic_scaling=False):
    if not allow_dynamic_scaling:
        return base_scale_factor, scaled_w, scaled_h
```

#### 3.2 スケール設定の一元化

```python
# config.pyを新規作成
class CADConfig:
    DEFAULT_SCALE = "1:100"
    ALLOWED_SCALES = ["1:50", "1:100", "1:200"]
    ENABLE_AUTO_SCALING = False
```

## 3. 実行スケジュール

| 時刻 | タスク | 状態 |
|------|--------|------|
| 15:00-15:30 | フェーズ1実行（ディレクトリ整理） | 準備完了 |
| 15:30-16:00 | フェーズ2準備（コード整理の詳細設計） | 計画中 |
| 16:00-16:30 | フェーズ2実行（承認後） | 承認待ち |
| 16:30-17:00 | テスト実行・動作確認 | 予定 |
| 17:00 | 成果物提出 | 締切 |

## 4. リスクと対策

### リスク1: 既存機能の破壊
**対策:** 
- Gitでバックアップ作成
- 段階的な実行
- 各フェーズ後のテスト

### リスク2: 依存関係の破損
**対策:**
- importパスの慎重な更新
- pytest実行による確認

### リスク3: 時間不足
**対策:**
- フェーズ1（ディレクトリ整理）を優先
- フェーズ2以降は設計のみでも可

## 5. 成果物リスト

1. **調査報告書** 
   - ✅ `_docs/2025-06-28_refactoring_inventory.md`

2. **実行計画書**
   - ✅ `_docs/2025-06-28_refactoring_plan.md`（本書）

3. **実行結果**
   - 整理されたディレクトリ構造
   - 更新された.gitignore
   - テスト実行結果

4. **今後の課題リスト**
   - スケール問題の根本解決案
   - Phase 3（JSON変換）の設計案

## 6. 承認事項

以下の実行について承認をお願いします：

1. **フェーズ1（ディレクトリ整理）の即時実行**
   - 出力ディレクトリの統合
   - デバッグツールの移動
   - レガシーファイルの移動

2. **フェーズ2以降の方針**
   - 実行するか設計のみに留めるか
   - 優先順位の確認

## 7. 次のアクション

1. ユーザーからの承認待ち
2. 承認後、フェーズ1を即実行
3. 残り時間でフェーズ2以降を進める
4. 17:00までに全成果物を提出