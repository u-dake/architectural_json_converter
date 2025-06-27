"""
DXF File Analyzer Module

このモジュールはDXFファイルの構造を詳細に解析し、
JSON形式で構造化された情報を出力します。

開発チームへ:
1. ezdxfライブラリを使用してDXFファイルを解析
2. すべてのエンティティタイプを網羅的に抽出
3. レイヤー情報、座標情報を詳細に記録
4. 出力はJSON形式で可読性を重視
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import ezdxf
from pathlib import Path
import os


def update_bounds(min_x, min_y, max_x, max_y, points):
    for p in points:
        min_x = min(min_x, p.x)
        min_y = min(min_y, p.y)
        max_x = max(max_x, p.x)
        max_y = max(max_y, p.y)
    return min_x, min_y, max_x, max_y

def update_bounds_circle(min_x, min_y, max_x, max_y, center, radius):
    min_x = min(min_x, center.x - radius)
    min_y = min(min_y, center.y - radius)
    max_x = max(max_x, center.x + radius)
    max_y = max(max_y, center.y + radius)
    return min_x, min_y, max_x, max_y



def analyze_dxf_structure(filepath: str) -> Dict[str, Any]:
    """
    DXFファイルの全構造を詳細に解析

    Args:
        filepath: DXFファイルのパス

    Returns:
        DXFファイルの構造情報を含む辞書

    Raises:
        FileNotFoundError: ファイルが見つからない場合
        ezdxf.DXFError: DXFファイルの読み込みエラー
    """
    # ファイルの存在確認
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"DXFファイルが見つかりません: {filepath}")

    # ファイルサイズ取得
    file_size = os.path.getsize(filepath)

    # DXFファイル読み込み
    try:
        doc = ezdxf.readfile(filepath)
    except ezdxf.DXFError as e:
        raise ezdxf.DXFError(f"DXFファイルの読み込みエラー: {e}")

    # DXFバージョン取得
    dxf_version = doc.dxfversion

    # ヘッダー情報の抽出
    header_info = {}
    try:
        # ヘッダーセクションの全ての変数を取得
        for var in doc.header:
            try:
                value = var.value
                # ベクター値は文字列に変換
                if hasattr(value, "x"):
                    header_info[var.name] = f"({value.x}, {value.y}, {value.z})"
                else:
                    header_info[var.name] = str(value)
            except:
                header_info[var.name] = (
                    str(var.value) if hasattr(var, "value") else "N/A"
                )
    except Exception as e:
        # ヘッダー情報の取得に失敗した場合は空の辞書を使用
        header_info = {"error": str(e)}

    # レイヤー情報の解析
    layers = []
    for layer in doc.layers:
        layer_info = {
            "name": layer.dxf.name,
            "color": layer.dxf.color,
            "line_type": layer.dxf.linetype,
            "is_on": layer.is_on(),
            "is_locked": layer.is_locked(),
            "is_frozen": layer.is_frozen(),
        }
        # 説明属性は存在しない場合があるので別途チェック
        try:
            layer_info["description"] = layer.dxf.description
        except:
            layer_info["description"] = ""
        layers.append(layer_info)

    # エンティティの統計情報収集
    entities_summary = {}
    entities_detail = []

    # 図面の境界情報を計算するための変数
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")

    # モデルスペースのエンティティを解析
    for entity in doc.modelspace():
        entity_type = entity.dxftype()

        # エンティティタイプごとの統計
        if entity_type not in entities_summary:
            entities_summary[entity_type] = 0
        entities_summary[entity_type] += 1

        # エンティティの詳細情報を抽出
        entity_detail = {
            "type": entity_type,
            "handle": entity.dxf.handle,
            "layer": entity.dxf.layer,
            "color": entity.dxf.color if hasattr(entity.dxf, "color") else None,
        }

        # エンティティタイプ別の追加情報
        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            entity_detail.update(
                {
                    "start": {"x": start.x, "y": start.y, "z": start.z},
                    "end": {"x": end.x, "y": end.y, "z": end.z},
                    "length": (
                        (end.x - start.x) ** 2
                        + (end.y - start.y) ** 2
                        + (end.z - start.z) ** 2
                    )
                    ** 0.5,
                }
            )
            # 境界更新
            min_x = min(min_x, start.x, end.x)
            min_y = min(min_y, start.y, end.y)
            max_x = max(max_x, start.x, end.x)
            max_y = max(max_y, start.y, end.y)

        elif entity_type == "CIRCLE":
            center = entity.dxf.center
            entity_detail.update(
                {
                    "center": {"x": center.x, "y": center.y, "z": center.z},
                    "radius": entity.dxf.radius,
                }
            )
            # 境界更新
            min_x = min(min_x, center.x - entity.dxf.radius)
            min_y = min(min_y, center.y - entity.dxf.radius)
            max_x = max(max_x, center.x + entity.dxf.radius)
            max_y = max(max_y, center.y + entity.dxf.radius)

        elif entity_type == "ARC":
            center = entity.dxf.center
            entity_detail.update(
                {
                    "center": {"x": center.x, "y": center.y, "z": center.z},
                    "radius": entity.dxf.radius,
                    "start_angle": entity.dxf.start_angle,
                    "end_angle": entity.dxf.end_angle,
                }
            )
            # 境界更新（簡易的に円として計算）
            min_x = min(min_x, center.x - entity.dxf.radius)
            min_y = min(min_y, center.y - entity.dxf.radius)
            max_x = max(max_x, center.x + entity.dxf.radius)
            max_y = max(max_y, center.y + entity.dxf.radius)

        elif entity_type == "POLYLINE" or entity_type == "LWPOLYLINE":
            vertices = []
            if entity_type == "LWPOLYLINE":
                for vertex in entity.vertices():
                    vertices.append({"x": vertex[0], "y": vertex[1], "z": 0.0})
                    min_x = min(min_x, vertex[0])
                    min_y = min(min_y, vertex[1])
                    max_x = max(max_x, vertex[0])
                    max_y = max(max_y, vertex[1])
            else:
                for vertex in entity.vertices:
                    point = vertex.dxf.location
                    vertices.append({"x": point.x, "y": point.y, "z": point.z})
                    min_x = min(min_x, point.x)
                    min_y = min(min_y, point.y)
                    max_x = max(max_x, point.x)
                    max_y = max(max_y, point.y)

            entity_detail.update(
                {
                    "vertices": vertices,
                    "is_closed": (
                        entity.is_closed if hasattr(entity, "is_closed") else False
                    ),
                }
            )

        elif entity_type == "TEXT":
            insert = entity.dxf.insert
            entity_detail.update(
                {
                    "text": entity.dxf.text,
                    "insert": {"x": insert.x, "y": insert.y, "z": insert.z},
                    "height": entity.dxf.height,
                    "rotation": (
                        entity.dxf.rotation if hasattr(entity.dxf, "rotation") else 0
                    ),
                }
            )
            # 境界更新
            min_x = min(min_x, insert.x)
            min_y = min(min_y, insert.y)
            max_x = max(max_x, insert.x)
            max_y = max(max_y, insert.y)

        elif entity_type == "MTEXT":
            insert = entity.dxf.insert
            entity_detail.update(
                {
                    "text": entity.text,
                    "insert": {"x": insert.x, "y": insert.y, "z": insert.z},
                    "char_height": entity.dxf.char_height,
                    "width": entity.dxf.width if hasattr(entity.dxf, "width") else None,
                }
            )
            # 境界更新
            min_x = min(min_x, insert.x)
            min_y = min(min_y, insert.y)
            max_x = max(max_x, insert.x)
            max_y = max(max_y, insert.y)

        elif entity_type == "INSERT":
            # ブロック参照を展開して個別のエンティティとして処理
            try:
                for sub_entity in entity.explode():
                    # 展開されたサブエンティティを再帰的に処理する代わりに、
                    # ここで直接詳細を抽出してリストに追加する
                    sub_entity_type = sub_entity.dxftype()
                    if sub_entity_type not in entities_summary:
                        entities_summary[sub_entity_type] = 0
                    entities_summary[sub_entity_type] += 1

                    # サブエンティティの詳細情報を抽出（主要なもののみ）
                    sub_entity_detail = {
                        "type": sub_entity_type,
                        "handle": sub_entity.dxf.handle if hasattr(sub_entity.dxf, 'handle') else None,
                        "layer": sub_entity.dxf.layer if hasattr(sub_entity.dxf, 'layer') else entity.dxf.layer,
                        "color": sub_entity.dxf.color if hasattr(sub_entity.dxf, 'color') else entity.dxf.color,
                        "is_sub_entity": True, # ブロック内の要素であることを示すフラグ
                        "block_name": entity.dxf.name
                    }

                    if sub_entity_type == "LINE":
                        start, end = sub_entity.dxf.start, sub_entity.dxf.end
                        sub_entity_detail.update({
                            "start": {"x": start.x, "y": start.y, "z": start.z},
                            "end": {"x": end.x, "y": end.y, "z": end.z}
                        })
                        min_x, min_y, max_x, max_y = update_bounds(min_x, min_y, max_x, max_y, [start, end])
                    
                    elif sub_entity_type == "CIRCLE":
                        center, radius = sub_entity.dxf.center, sub_entity.dxf.radius
                        sub_entity_detail.update({
                            "center": {"x": center.x, "y": center.y, "z": center.z},
                            "radius": radius
                        })
                        min_x, min_y, max_x, max_y = update_bounds_circle(min_x, min_y, max_x, max_y, center, radius)

                    elif sub_entity_type in ["POLYLINE", "LWPOLYLINE"]:
                        points = []
                        if sub_entity.is_lwpolyline:
                            for p in sub_entity.vertices():
                                points.append(ezdxf.math.Vec3(p[0], p[1], 0))
                        else:
                            for v in sub_entity.vertices:
                                points.append(v.dxf.location)
                        
                        sub_entity_detail.update({
                            "vertices": [{"x": p.x, "y": p.y, "z": p.z} for p in points],
                            "is_closed": sub_entity.is_closed
                        })
                        min_x, min_y, max_x, max_y = update_bounds(min_x, min_y, max_x, max_y, points)

                    elif sub_entity_type == "ARC":
                        center, radius = sub_entity.dxf.center, sub_entity.dxf.radius
                        sub_entity_detail.update({
                            "center": {"x": center.x, "y": center.y, "z": center.z},
                            "radius": radius,
                            "start_angle": sub_entity.dxf.start_angle,
                            "end_angle": sub_entity.dxf.end_angle,
                        })
                        min_x, min_y, max_x, max_y = update_bounds_circle(min_x, min_y, max_x, max_y, center, radius)

                    elif sub_entity_type == "TEXT":
                        insert = sub_entity.dxf.insert
                        sub_entity_detail.update({
                            "text": sub_entity.dxf.text,
                            "insert": {"x": insert.x, "y": insert.y, "z": insert.z},
                            "height": sub_entity.dxf.height,
                        })
                        min_x, min_y, max_x, max_y = update_bounds(min_x, min_y, max_x, max_y, [insert])

                    # 他のサブエンティティタイプも同様に追加可能
                    # ...

                    entities_detail.append(sub_entity_detail)

            except Exception as e:
                # explodeに失敗した場合など
                # 元のINSERTエンティティ情報を保持
                insert = entity.dxf.insert
                entity_detail.update({
                    "block_name": entity.dxf.name,
                    "insert": {"x": insert.x, "y": insert.y, "z": insert.z},
                    "error_exploding": str(e)
                })
                entities_detail.append(entity_detail)
            continue # 元のINSERTエンティティは追加しない

        elif entity_type == "DIMENSION":
            # 寸法
            entity_detail.update(
                {
                    "measurement": (
                        entity.dxf.measurement
                        if hasattr(entity.dxf, "measurement")
                        else None
                    ),
                    "text": entity.dxf.text if hasattr(entity.dxf, "text") else None,
                }
            )

        entities_detail.append(entity_detail)

    # 境界情報が無限大の場合は0に設定
    if min_x == float("inf"):
        min_x = min_y = max_x = max_y = 0.0

    analysis_result = {
        "file_info": {
            "filepath": filepath,
            "file_size": file_size,
            "dxf_version": dxf_version,
        },
        "header_info": header_info,
        "layers": layers,
        "entities_summary": entities_summary,
        "entities_detail": entities_detail,
        "bounds": {
            "min_x": round(min_x, 3),
            "min_y": round(min_y, 3),
            "max_x": round(max_x, 3),
            "max_y": round(max_y, 3),
            "width": round(max_x - min_x, 3),
            "height": round(max_y - min_y, 3),
        },
    }

    return analysis_result


def save_analysis_to_json(analysis_result: Dict[str, Any], output_path: str) -> None:
    """
    解析結果をJSONファイルに保存

    Args:
        analysis_result: analyze_dxf_structure()の戻り値
        output_path: 出力JSONファイルのパス
    """
    # ディレクトリが存在しない場合は作成
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # JSON形式で保存（日本語対応、インデント付き）
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    print(f"解析結果を保存しました: {output_path}")


def main():
    """
    テスト用メイン関数
    開発チームは実際のDXFファイルでテストしてください
    """
    import sys

    if len(sys.argv) > 1:
        # コマンドライン引数からファイルパスを取得
        dxf_path = sys.argv[1]

        try:
            print(f"DXFファイルを解析中: {dxf_path}")
            analysis = analyze_dxf_structure(dxf_path)

            # 出力ファイル名を生成
            base_name = os.path.splitext(os.path.basename(dxf_path))[0]
            output_path = f"data/dxf_analysis_{base_name}.json"

            save_analysis_to_json(analysis, output_path)

            # サマリー情報を表示
            print("\n=== 解析結果サマリー ===")
            print(f"DXFバージョン: {analysis['file_info']['dxf_version']}")
            print(f"ファイルサイズ: {analysis['file_info']['file_size']:,} bytes")
            print(f"レイヤー数: {len(analysis['layers'])}")
            print(f"エンティティ総数: {sum(analysis['entities_summary'].values())}")
            print("\nエンティティ種別:")
            for entity_type, count in sorted(analysis["entities_summary"].items()):
                print(f"  {entity_type}: {count}")
            print(f"\n図面境界:")
            bounds = analysis["bounds"]
            print(
                f"  X: {bounds['min_x']} ~ {bounds['max_x']} (幅: {bounds['width']}mm)"
            )
            print(
                f"  Y: {bounds['min_y']} ~ {bounds['max_y']} (高さ: {bounds['height']}mm)"
            )

        except FileNotFoundError as e:
            print(f"エラー: {e}")
        except ezdxf.DXFError as e:
            print(f"エラー: {e}")
        except Exception as e:
            print(f"予期しないエラー: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("使用方法: python dxf_analyzer.py <DXFファイルパス>")
        print("例: python dxf_analyzer.py data/sample_dxf/test.dxf")


if __name__ == "__main__":
    main()
