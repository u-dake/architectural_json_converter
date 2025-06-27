# インストールガイド

## 📋 システム要件

### 最小要件
- **OS**: macOS 10.14+, Windows 10+, Ubuntu 18.04+
- **Python**: 3.8以上（推奨: 3.10+）
- **メモリ**: 4GB RAM以上（大容量図面処理時は8GB推奨）
- **ストレージ**: 1GB以上の空き容量

### 推奨要件
- **Python**: 3.10以上
- **メモリ**: 8GB RAM以上
- **ストレージ**: 2GB以上（サンプルデータ・出力画像用）

## 🚀 自動インストール（推奨）

### 1. プロジェクトの取得

```bash
# GitHubからクローン
git clone https://github.com/example/architectural-json-converter.git
cd architectural-json-converter

# または ZIP ダウンロード
# https://github.com/example/architectural-json-converter/archive/main.zip
```

### 2. 自動環境構築

```bash
# 実行権限付与
chmod +x setup.sh

# 自動セットアップ実行
./setup.sh
```

**セットアップ内容**:
- Python仮想環境の作成
- 依存関係の自動インストール
- PYTHONPATH設定
- 基本動作テスト
- CLI動作確認

## 🔧 手動インストール

### 1. Python環境の確認

```bash
# Pythonバージョン確認
python3 --version
# Python 3.8.0 以上が必要

# pipの更新
python3 -m pip install --upgrade pip
```

### 2. 仮想環境の作成

```bash
# 仮想環境作成
python3 -m venv venv

# アクティベート (macOS/Linux)
source venv/bin/activate

# アクティベート (Windows)
venv\\Scripts\\activate
```

### 3. 依存関係のインストール

```bash
# requirements.txtから一括インストール
pip install -r requirements.txt

# または個別インストール
pip install pydantic>=2.0.0
pip install numpy>=1.21.0
pip install matplotlib>=3.5.0
pip install shapely>=2.0.0
pip install ezdxf>=1.0.0
pip install PyPDF2>=3.0.0
pip install plotly>=5.0.0
pip install pytest>=7.0.0
pip install pytest-cov>=4.0.0
```

### 4. 環境変数の設定

```bash
# PYTHONPATHの設定 (macOS/Linux)
export PYTHONPATH="/path/to/architectural_json_converter:$PYTHONPATH"

# 永続化 (bashの場合)
echo 'export PYTHONPATH="/path/to/architectural_json_converter:$PYTHONPATH"' >> ~/.bashrc
source ~/.bashrc

# PYTHONPATHの設定 (Windows)
set PYTHONPATH=C:\\path\\to\\architectural_json_converter;%PYTHONPATH%
```

## ✅ インストール確認

### 1. 基本動作テスト

```bash
# CLIヘルプ表示
python src/main.py --help

# 期待される出力:
# usage: main.py [-h] [--visualize] [--interactive] ...
```

### 2. テストスイート実行

```bash
# 基本テスト
python -m pytest tests/test_geometry_data.py -v

# コンバーターテスト
python -m pytest tests/test_engines/test_safe_dxf_converter.py -v

# 全テスト（時間がかかる場合があります）
python -m pytest tests/ -v
```

### 3. サンプルファイルでの動作確認

```bash
# DXF→PDF変換
python src/main.py dxf2pdf sample.dxf --scale 1:100

# 差分解析
python src/main.py diff site.dxf floor.dxf

# バッチ変換
python src/main.py batch /path/to/dxf/files/
```

## 🔧 トラブルシューティング

### よくある問題

#### 1. Import Error: ModuleNotFoundError

**症状**: `ModuleNotFoundError: No module named 'src'`

**解決法**:
```bash
# PYTHONPATHの確認
echo $PYTHONPATH

# PYTHONPATHの再設定
export PYTHONPATH="$(pwd):$PYTHONPATH"

# または明示的な実行
PYTHONPATH=/path/to/project python src/main.py --help
```

#### 2. DXF読み込みエラー

**症状**: `ezdxf関連のエラー`

**解決法**:
```bash
# ezdxfの再インストール
pip uninstall ezdxf
pip install ezdxf>=1.0.0

# または最新版
pip install ezdxf --upgrade
```

#### 3. 日本語フォントエラー

**症状**: matplotlib で文字化け

**解決法**:
```bash
# フォントキャッシュのクリア (macOS)
rm -rf ~/.matplotlib/fontList.json

# または手動でフォント確認
python -c "import matplotlib.pyplot as plt; print(plt.rcParams['font.family'])"
```

#### 4. メモリ不足エラー

**症状**: 大容量DXFファイルでメモリエラー

**解決法**:
```bash
# 仮想メモリの確認
free -h  # Linux
vm_stat  # macOS

# スワップファイルの増加を検討
# または分割処理の実装
```

## 🔄 アップデート

### 依存関係の更新

```bash
# requirements.txtの更新
pip install -r requirements.txt --upgrade

# 個別パッケージの更新
pip install --upgrade pydantic matplotlib numpy
```

### プロジェクトの更新

```bash
# Gitリポジトリの更新
git pull origin main

# 依存関係の再確認
pip install -r requirements.txt
```

## 🐳 Docker環境（オプション）

Docker利用者向けの環境構築:

```dockerfile
# Dockerfile例
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV PYTHONPATH=/app

CMD ["python", "src/main.py", "--help"]
```

```bash
# Docker実行
docker build -t arch-analyzer .
docker run -v $(pwd)/data:/app/data arch-analyzer python src/main.py --help
```

## 📞 サポート

### インストールに関する問題

1. **GitHub Issues**: https://github.com/example/architectural-json-converter/issues
2. **ドキュメント**: [トラブルシューティング](./TROUBLESHOOTING.md)
3. **FAQ**: [よくある質問](./FAQ.md)

### システム環境の報告

問題報告時は以下の情報を含めてください:

```bash
# 環境情報の収集
python --version
pip list | grep -E "(pydantic|numpy|matplotlib|ezdxf)"
echo $PYTHONPATH
uname -a  # macOS/Linux
```

---

**インストール完了後は [ユーザーガイド](./USER_GUIDE.md) をご確認ください。**