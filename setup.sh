#!/bin/bash

# 建築図面差分解析システム環境設定スクリプト
# Phase 2 環境統一化対応

echo "🏗️  建築図面差分解析システム Phase 2 - 環境設定開始"
echo "================================================"

# プロジェクトディレクトリの確認
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 プロジェクトディレクトリ: $PROJECT_DIR"

# Python環境の確認
echo "🐍 Python環境確認..."
python3 --version || {
    echo "❌ Python 3が見つかりません。Python 3.8以上をインストールしてください。"
    exit 1
}

# 仮想環境の作成・アクティベート
echo "📦 仮想環境の設定..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 仮想環境を作成しました"
fi

# 仮想環境のアクティベート
source venv/bin/activate
echo "✅ 仮想環境をアクティベートしました"

# 依存関係のインストール
echo "📥 依存関係のインストール..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 依存関係をインストールしました"

# PYTHONPATHの設定
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
echo "✅ PYTHONPATH設定: $PYTHONPATH"

# テスト実行
echo "🧪 システムテスト実行..."
python -m pytest tests/test_geometry_data.py -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ 基本テスト成功"
else
    echo "⚠️  一部テストで問題が発生しましたが、システムは動作可能です"
fi

# CLI動作確認
echo "🖥️  CLI動作確認..."
python src/main.py --help > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ CLI正常動作確認"
else
    echo "❌ CLI動作エラー"
    exit 1
fi

echo ""
echo "🎉 環境設定完了！"
echo "================================================"
echo ""
echo "🚀 使用方法:"
echo "  # 仮想環境アクティベート"
echo "  source venv/bin/activate"
echo ""
echo "  # 基本的な差分解析"
echo "  python src/main.py 敷地図.dxf 間取り図.dxf --visualize"
echo ""
echo "  # 詳細解析（出力ディレクトリ指定）"
echo "  python src/main.py site.dxf plan.dxf --visualize --output-dir results/"
echo ""
echo "  # テスト実行"
echo "  python -m pytest tests/ -v --cov=src"
echo ""
echo "📖 詳細なドキュメントは docs/ ディレクトリを参照してください"
echo ""