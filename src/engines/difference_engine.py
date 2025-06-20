"""
Difference Extraction Engine

建築図面の差分を抽出・解析するエンジン
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from data_structures.geometry_data import (
    GeometryData, GeometryElement, DifferenceResult, Point2D,
    ElementType, ArchitecturalType, LineElement, PolylineElement,
    TextElement, BoundingBox
)


def calculate_similarity_score(element1: GeometryElement, element2: GeometryElement) -> float:
    """
    2つの要素の類似度を計算
    
    Args:
        element1: 比較する要素1
        element2: 比較する要素2
        
    Returns:
        類似度スコア (0.0-1.0)
    """
    try:
        # 要素タイプが異なる場合は類似度0
        if element1.element_type != element2.element_type:
            return 0.0
        
        # 空間的類似度を計算
        spatial_similarity = 0.0
        
        # 線分要素の場合は特別な処理
        if isinstance(element1, LineElement) and isinstance(element2, LineElement):
            # 線分の重複計算：開始点と終点の距離で判定
            dist_start1_start2 = element1.start.distance_to(element2.start)
            dist_start1_end2 = element1.start.distance_to(element2.end)
            dist_end1_start2 = element1.end.distance_to(element2.start)
            dist_end1_end2 = element1.end.distance_to(element2.end)
            
            # 最も近い端点ペアの距離を計算
            min_endpoint_dist = min(
                dist_start1_start2 + dist_end1_end2,  # 同じ向き
                dist_start1_end2 + dist_end1_start2   # 逆向き
            )
            
            # 線分の長さの平均
            avg_length = (element1.length + element2.length) / 2
            
            # 距離に基づく類似度（近いほど高い類似度）
            if avg_length > 0:
                spatial_similarity = max(0, 1 - min_endpoint_dist / (avg_length * 2))
            else:
                spatial_similarity = 1.0 if min_endpoint_dist < 1e-6 else 0.0
        else:
            # 他の要素は境界ボックスベースの計算
            bbox1 = element1.get_bounding_box()
            bbox2 = element2.get_bounding_box()
            
            # 重複領域を計算
            overlap_x = max(0, min(bbox1.max_x, bbox2.max_x) - max(bbox1.min_x, bbox2.min_x))
            overlap_y = max(0, min(bbox1.max_y, bbox2.max_y) - max(bbox1.min_y, bbox2.min_y))
            overlap_area = overlap_x * overlap_y
            
            # 全体領域を計算
            area1 = max(bbox1.width * bbox1.height, 1e-6)  # 最小面積保証
            area2 = max(bbox2.width * bbox2.height, 1e-6)  # 最小面積保証
            total_area = area1 + area2 - overlap_area
            
            if total_area > 0:
                spatial_similarity = overlap_area / total_area
            else:
                spatial_similarity = 0.0
        
        # 要素タイプ別の追加チェック
        type_similarity = 0.0
        
        if isinstance(element1, LineElement) and isinstance(element2, LineElement):
            # 線分の場合：長さと角度の類似度
            length_diff = abs(element1.length - element2.length)
            angle_diff = abs(element1.angle - element2.angle)
            
            length_similarity = max(0, 1 - length_diff / max(element1.length, element2.length, 1))
            angle_similarity = max(0, 1 - angle_diff / np.pi)
            
            type_similarity = (length_similarity + angle_similarity) / 2
            
        elif isinstance(element1, TextElement) and isinstance(element2, TextElement):
            # テキストの場合：内容の類似度
            if element1.text == element2.text:
                type_similarity = 1.0
            elif element1.text.lower() in element2.text.lower() or element2.text.lower() in element1.text.lower():
                type_similarity = 0.5
            else:
                type_similarity = 0.0
        
        # 空間的類似度と要素タイプ別類似度の加重平均
        return 0.7 * spatial_similarity + 0.3 * type_similarity
    
    except Exception as e:
        # デバッグ用：エラーが発生した場合
        print(f"Error in calculate_similarity_score: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


def find_matching_elements(elements1: List[GeometryElement], 
                          elements2: List[GeometryElement],
                          similarity_threshold: float = 0.5) -> Dict[str, str]:
    """
    2つの要素リスト間でマッチする要素を検索
    
    Args:
        elements1: 要素リスト1
        elements2: 要素リスト2
        similarity_threshold: 類似度の閾値
        
    Returns:
        要素ID1 -> 要素ID2のマッピング辞書
    """
    matches = {}
    used_elements2 = set()
    
    for elem1 in elements1:
        best_match = None
        best_score = similarity_threshold
        
        for elem2 in elements2:
            if elem2.id in used_elements2:
                continue
                
            score = calculate_similarity_score(elem1, elem2)
            if score > best_score:
                best_match = elem2
                best_score = score
        
        if best_match:
            matches[elem1.id] = best_match.id
            used_elements2.add(best_match.id)
    
    return matches


def classify_wall_elements(elements: List[GeometryElement]) -> List[GeometryElement]:
    """
    線分要素から壁を分類
    
    Args:
        elements: 要素リスト
        
    Returns:
        壁として分類された要素のリスト
    """
    walls = []
    
    for element in elements:
        if isinstance(element, LineElement):
            # 長さが一定以上の線分を壁候補とする
            if element.length > 500:  # 500mm以上
                # レイヤー名や他の特徴も考慮
                if any(wall_keyword in element.style.layer.lower() 
                      for wall_keyword in ["wall", "壁", "w-", "w_"]):
                    element.architectural_type = ArchitecturalType.WALL
                    walls.append(element)
                elif element.length > 1000:  # 1m以上は壁の可能性が高い
                    element.architectural_type = ArchitecturalType.WALL
                    element.confidence = 0.7
                    walls.append(element)
        
        elif isinstance(element, PolylineElement):
            # ポリラインも壁の可能性
            if len(element.vertices) >= 2:
                total_length = 0
                for i in range(len(element.vertices) - 1):
                    total_length += element.vertices[i].distance_to(element.vertices[i + 1])
                
                if total_length > 500:
                    element.architectural_type = ArchitecturalType.WALL
                    walls.append(element)
    
    return walls


def classify_opening_elements(elements: List[GeometryElement], 
                            walls: List[GeometryElement]) -> List[GeometryElement]:
    """
    開口部（ドア・窓）を分類
    
    Args:
        elements: 要素リスト
        walls: 壁要素のリスト
        
    Returns:
        開口部として分類された要素のリスト
    """
    openings = []
    
    for element in elements:
        # レイヤー名による分類
        layer_lower = element.style.layer.lower()
        
        if any(door_keyword in layer_lower for door_keyword in ["door", "扉", "ドア"]):
            element.architectural_type = ArchitecturalType.DOOR
            openings.append(element)
        elif any(window_keyword in layer_lower for window_keyword in ["window", "窓", "サッシ"]):
            element.architectural_type = ArchitecturalType.WINDOW
            openings.append(element)
        
        # 短い線分で壁に近いものは開口部の可能性
        elif isinstance(element, LineElement):
            if 100 < element.length < 3000:  # 10cm-3mの線分
                # 壁との距離をチェック
                for wall in walls:
                    if isinstance(wall, LineElement):
                        # 簡易的な距離計算
                        wall_line = wall.to_shapely()
                        element_line = element.to_shapely()
                        distance = wall_line.distance(element_line)
                        
                        if distance < 100:  # 10cm以内
                            element.architectural_type = ArchitecturalType.OPENING
                            element.confidence = 0.6
                            openings.append(element)
                            break
    
    return openings


def classify_fixture_elements(elements: List[GeometryElement]) -> List[GeometryElement]:
    """
    設備・器具を分類
    
    Args:
        elements: 要素リスト
        
    Returns:
        設備として分類された要素のリスト
    """
    fixtures = []
    
    for element in elements:
        layer_lower = element.style.layer.lower()
        
        # レイヤー名による分類
        if any(fixture_keyword in layer_lower 
              for fixture_keyword in ["fixture", "設備", "fix", "equipment"]):
            element.architectural_type = ArchitecturalType.FIXTURE
            fixtures.append(element)
        
        # 円形要素は設備の可能性
        elif element.element_type == ElementType.CIRCLE:
            element.architectural_type = ArchitecturalType.FIXTURE
            element.confidence = 0.7
            fixtures.append(element)
        
        # ブロック要素も設備の可能性
        elif element.element_type == ElementType.BLOCK:
            element.architectural_type = ArchitecturalType.FIXTURE
            element.confidence = 0.8
            fixtures.append(element)
    
    return fixtures


def extract_differences(site_only: GeometryData, 
                       site_with_plan: GeometryData,
                       similarity_threshold: float = 0.5) -> DifferenceResult:
    """
    2つの図面データから差分を抽出
    
    Args:
        site_only: 敷地図のみのデータ
        site_with_plan: 間取り付きデータ
        similarity_threshold: 類似度の閾値
        
    Returns:
        差分解析結果
    """
    # 要素のマッチングを実行
    matches = find_matching_elements(
        site_only.elements, 
        site_with_plan.elements,
        similarity_threshold
    )
    
    # 新規要素を特定（間取り付きにあって敷地図のみにない要素）
    matched_ids_in_plan = set(matches.values())
    new_elements = [
        elem for elem in site_with_plan.elements 
        if elem.id not in matched_ids_in_plan
    ]
    
    # 削除要素を特定（敷地図のみにあって間取り付きにない要素）
    matched_ids_in_site = set(matches.keys())
    removed_elements = [
        elem for elem in site_only.elements
        if elem.id not in matched_ids_in_site
    ]
    
    # 建築要素の分類
    walls = classify_wall_elements(new_elements)
    openings = classify_opening_elements(new_elements, walls)
    fixtures = classify_fixture_elements(new_elements)
    
    # 解析メタデータ
    analysis_metadata = {
        "similarity_threshold": similarity_threshold,
        "total_matches": len(matches),
        "processing_time": None,  # 実際の処理時間は呼び出し側で設定
        "classification_confidence": {
            "walls": np.mean([w.confidence for w in walls]) if walls else 0.0,
            "openings": np.mean([o.confidence for o in openings]) if openings else 0.0,
            "fixtures": np.mean([f.confidence for f in fixtures]) if fixtures else 0.0
        }
    }
    
    return DifferenceResult(
        site_only=site_only,
        site_with_plan=site_with_plan,
        new_elements=new_elements,
        removed_elements=removed_elements,
        modified_elements=[],  # 後で実装
        walls=walls,
        openings=openings,
        fixtures=fixtures,
        analysis_metadata=analysis_metadata
    )


def analyze_spatial_distribution(elements: List[GeometryElement]) -> Dict[str, Any]:
    """
    要素の空間分布を解析
    
    Args:
        elements: 解析対象の要素リスト
        
    Returns:
        空間分布の統計情報
    """
    if not elements:
        return {}
    
    # 境界ボックスを取得
    boxes = [elem.get_bounding_box() for elem in elements]
    
    # 中心点を計算
    centers = [box.center for box in boxes]
    x_coords = [c.x for c in centers]
    y_coords = [c.y for c in centers]
    
    return {
        "count": len(elements),
        "bounding_box": {
            "min_x": min(box.min_x for box in boxes),
            "min_y": min(box.min_y for box in boxes),
            "max_x": max(box.max_x for box in boxes),
            "max_y": max(box.max_y for box in boxes)
        },
        "center_of_mass": {
            "x": np.mean(x_coords),
            "y": np.mean(y_coords)
        },
        "spread": {
            "x_std": np.std(x_coords),
            "y_std": np.std(y_coords)
        }
    }


def save_difference_result_to_json(result: DifferenceResult, output_path: str) -> None:
    """
    差分解析結果をJSONファイルに保存
    
    Args:
        result: 差分解析結果
        output_path: 出力ファイルパス
    """
    import json
    import os
    
    # ディレクトリが存在しない場合は作成
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Pydanticモデルの辞書化（JSON互換形式）
    data_dict = result.model_dump(mode='json')
    
    # JSON形式で保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2)
    
    print(f"差分解析結果を保存しました: {output_path}")


def main():
    """テスト用メイン関数"""
    import sys
    import time
    from src.engines.dxf_converter import convert_dxf_to_geometry_data
    from src.engines.pdf_converter import convert_pdf_to_geometry_data
    
    if len(sys.argv) > 2:
        site_file = sys.argv[1]
        plan_file = sys.argv[2]
        
        try:
            start_time = time.time()
            
            print(f"敷地図を読み込み中: {site_file}")
            if site_file.lower().endswith('.dxf'):
                site_data = convert_dxf_to_geometry_data(site_file)
            elif site_file.lower().endswith('.pdf'):
                site_data = convert_pdf_to_geometry_data(site_file)
            else:
                raise ValueError("対応していないファイル形式です")
            
            print(f"間取り図を読み込み中: {plan_file}")
            if plan_file.lower().endswith('.dxf'):
                plan_data = convert_dxf_to_geometry_data(plan_file)
            elif plan_file.lower().endswith('.pdf'):
                plan_data = convert_pdf_to_geometry_data(plan_file)
            else:
                raise ValueError("対応していないファイル形式です")
            
            print("差分解析を実行中...")
            result = extract_differences(site_data, plan_data)
            
            processing_time = time.time() - start_time
            result.analysis_metadata["processing_time"] = processing_time
            
            # 出力ファイル名を生成
            output_path = "data/difference_analysis_result.json"
            save_difference_result_to_json(result, output_path)
            
            # 結果サマリーを表示
            print("\n=== 差分解析結果サマリー ===")
            stats = result.get_statistics()
            for key, value in stats.items():
                print(f"{key}: {value}")
            
            print(f"\n処理時間: {processing_time:.2f}秒")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("使用方法: python difference_engine.py <敷地図ファイル> <間取り図ファイル>")
        print("例: python difference_engine.py site.dxf plan.dxf")


if __name__ == "__main__":
    main()