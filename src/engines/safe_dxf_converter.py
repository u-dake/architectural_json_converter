"""
Safe DXF Converter

Matrix44エラーを回避する安全なDXFコンバーター
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import ezdxf
from ezdxf.entities import (
    DXFEntity,
    Insert,
    Line as DXFLine,
    Circle as DXFCircle,
    Arc as DXFArc,
    LWPolyline,
    Polyline as DXFPolyline,
    Text as DXFText,
    MText,
)
import math
import logging
from src.data_structures.simple_geometry import (
    Point,
    Line,
    Circle,
    Arc,
    Polyline,
    Text,
    GeometryCollection,
)
from src.analyzers.unit_detector import UnitDetector, UnitDetectionResult


class SafeDXFConverter:
    """安全なDXFコンバーター"""

    def __init__(self, pattern_file: Optional[str] = None):
        self.layer_info = {}
        self.block_definitions = {}
        # 追加: DXF図面単位→mm換算係数 (初期値1.0)
        self.unit_factor = 1.0
        # 単位検出器を初期化
        self.unit_detector = UnitDetector(pattern_file)
        self.unit_detection_result: Optional[UnitDetectionResult] = None

    def _detect_unit_factor(self, doc: ezdxf.document.Drawing) -> float:
        """DXFヘッダーの $INSUNITS または doc.units から mm 換算係数を取得"""
        try:
            units_code = 0
            # ezdxf 1.0+: doc.units が直接整数コードを返す
            if hasattr(doc, "units") and isinstance(doc.units, int):
                units_code = doc.units
            else:
                # fallback
                units_code = int(doc.header.get("$INSUNITS", 0))
        except Exception:
            units_code = 0

        # AutoCAD $INSUNITS コード → mm 換算
        # 参考: 0=None,1=Inch,2=Foot,4=Millimeter,5=Centimeter,6=Meter,7=Kilometer
        unit_map = {
            0: 1.0,  # 不明 → mm とみなす
            1: 25.4,  # inch → mm
            2: 304.8,  # foot → mm
            3: 1.609e6,  # mile → mm (概算)
            4: 1.0,  # millimeter
            5: 10.0,  # centimeter → mm
            6: 1000.0,  # meter → mm
            7: 1.0e6,  # kilometer → mm
        }
        return unit_map.get(units_code, 1.0)

    def _validate_size_for_architectural_drawing(self, width_mm: float, height_mm: float) -> Tuple[bool, str]:
        """
        建築図面として妥当なサイズかをチェック
        
        Returns:
            (is_valid, reason)
        """
        # A3サイズ（横置き）
        A3_WIDTH_MM = 420
        A3_HEIGHT_MM = 297
        MARGIN_MM = 20  # 余白
        
        # 利用可能な描画エリア
        available_width = A3_WIDTH_MM - 2 * MARGIN_MM
        available_height = A3_HEIGHT_MM - 2 * MARGIN_MM
        
        # 一般的な建築図面スケールでの最大実世界サイズ
        scale_limits = {
            "1:50": (available_width * 50, available_height * 50),      # 約20m × 14m
            "1:100": (available_width * 100, available_height * 100),   # 約40m × 28m
            "1:200": (available_width * 200, available_height * 200),   # 約80m × 55m
            "1:500": (available_width * 500, available_height * 500),   # 約200m × 140m
            "1:1000": (available_width * 1000, available_height * 1000), # 約400m × 280m
            "1:2000": (available_width * 2000, available_height * 2000), # 約800m × 550m
            "1:5000": (available_width * 5000, available_height * 5000), # 約2000m × 1400m
        }
        
        # サイズをメートルに変換
        width_m = width_mm / 1000
        height_m = height_mm / 1000
        
        # 建築物として妥当なサイズかチェック
        # 建築図面は最低でも5m×5m程度は必要（小さな部屋でも）
        if width_m < 5 or height_m < 5:
            return False, f"Too small: {width_m:.1f}m × {height_m:.1f}m (smaller than 5m)"
        
        # 2kmを超える建物は非現実的（大規模施設・空港等を考慮）
        if width_m > 2000 or height_m > 2000:
            return False, f"Too large: {width_m:.0f}m × {height_m:.0f}m (larger than 2km)"
        
        # どのスケールで収まるかチェック
        suitable_scales = []
        for scale, (max_w, max_h) in scale_limits.items():
            if width_mm <= max_w and height_mm <= max_h:
                suitable_scales.append(scale)
        
        if not suitable_scales:
            return False, f"No suitable scale found for {width_m:.0f}m × {height_m:.0f}m"
        
        # 1:5000でしか収まらない場合は警告
        if suitable_scales[0] == "1:5000" and width_m < 500:
            logging.warning(f"Size {width_m:.0f}m × {height_m:.0f}m only fits at 1:5000 scale - might be incorrect")
        
        return True, f"Suitable scales: {', '.join(suitable_scales)}"

    def _detect_and_fix_unit_issue(self, collection: GeometryCollection, actual_bounds: Tuple[float, float, float, float]) -> bool:
        """
        単位の問題を検出して修正
        
        Returns:
            True if conversion was applied
        """
        width = actual_bounds[2] - actual_bounds[0]
        height = actual_bounds[3] - actual_bounds[1]
        
        # 現在のサイズの妥当性をチェック
        is_valid, reason = self._validate_size_for_architectural_drawing(width, height)
        logging.info(f"Current size check: {width:.1f}mm × {height:.1f}mm - {reason}")
        
        if not is_valid and "Too small" in reason:
            # 小さすぎる場合はメートル単位の可能性
            # 1000倍してみる
            test_width = width * 1000
            test_height = height * 1000
            test_valid, test_reason = self._validate_size_for_architectural_drawing(test_width, test_height)
            
            logging.info(f"Testing 1000x conversion: {test_width:.1f}mm × {test_height:.1f}mm")
            logging.info(f"Test result: valid={test_valid}, reason={test_reason}")
            
            if test_valid:
                logging.info(f"Converting from meters to mm: {width:.1f}m × {height:.1f}m → {test_width:.0f}mm × {test_height:.0f}mm")
                logging.info(f"After conversion: {test_reason}")
                self._apply_unit_factor_to_collection(collection, 1000.0)
                collection.metadata["unit_factor_mm"] = 1000.0
                collection.metadata["auto_scaled"] = True
                return True
            else:
                logging.info("1000x conversion did not produce valid size")
        
        elif not is_valid and "Too large" in reason:
            # 大きすぎる場合は誤変換の可能性
            # INSERT座標で実際のサイズを確認
            insert_bounds = collection.metadata.get("insert_bounds")
            if insert_bounds:
                insert_width, insert_height = insert_bounds
                # INSERTが200m程度なら、全体が1000倍されている可能性
                if 50 < insert_width < 500 and 50 < insert_height < 500:
                    logging.warning(f"Detected over-conversion: INSERT shows {insert_width:.0f}×{insert_height:.0f}m but total is {width/1000:.0f}×{height/1000:.0f}m")
                    logging.info("INSERT coordinates appear to be in meters, but block content was scaled")
                    # この場合は変換をスキップ（すでに正しいサイズ）
                    return False
            
            # それ以外の場合は1/1000してみる
            test_width = width / 1000
            test_height = height / 1000
            test_valid, test_reason = self._validate_size_for_architectural_drawing(test_width, test_height)
            
            if test_valid:
                logging.warning(f"Detected over-conversion: {width:.0f}mm × {height:.0f}mm seems incorrect")
                logging.info(f"Should be: {test_width:.1f}m × {test_height:.1f}m")
                # この場合は変換を取り消す必要がある
                self._apply_unit_factor_to_collection(collection, 0.001)
                collection.metadata["unit_factor_mm"] = 0.001
                collection.metadata["auto_scaled"] = True
                collection.metadata["conversion_error"] = True
                return True
        
        logging.info(f"Size validation: {reason}")
        return False

    def _calculate_actual_bounds(
        self, collection: GeometryCollection, exclude_border: bool = False
    ) -> Optional[Tuple[float, float, float, float]]:
        """変換後の実際の座標範囲を計算
        
        Args:
            collection: 幾何要素のコレクション
            exclude_border: 枠線と思われる大きな矩形を除外するか
        """
        if not collection.elements:
            return None

        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        # exclude_borderがTrueの場合、最初に全体の大まかな範囲を取得
        if exclude_border:
            temp_bounds = self._calculate_actual_bounds(collection, exclude_border=False)
            if temp_bounds:
                total_width = temp_bounds[2] - temp_bounds[0]
                total_height = temp_bounds[3] - temp_bounds[1]
                # 枠線の可能性がある大きさの閾値（全体の80%以上）
                border_threshold_w = total_width * 0.8
                border_threshold_h = total_height * 0.8

        for element in collection.elements:
            try:
                # 枠線の可能性があるポリラインをスキップ
                if exclude_border and isinstance(element, Polyline) and element.closed:
                    if len(element.points) == 4 or len(element.points) == 5:  # 矩形
                        poly_min_x = min(p.x for p in element.points)
                        poly_max_x = max(p.x for p in element.points)
                        poly_min_y = min(p.y for p in element.points)
                        poly_max_y = max(p.y for p in element.points)
                        poly_width = poly_max_x - poly_min_x
                        poly_height = poly_max_y - poly_min_y
                        
                        if (poly_width > border_threshold_w and 
                            poly_height > border_threshold_h):
                            continue  # 枠線と判断してスキップ
                
                if isinstance(element, Line):
                    min_x = min(min_x, element.start.x, element.end.x)
                    max_x = max(max_x, element.start.x, element.end.x)
                    min_y = min(min_y, element.start.y, element.end.y)
                    max_y = max(max_y, element.start.y, element.end.y)
                elif isinstance(element, Circle):
                    min_x = min(min_x, element.center.x - element.radius)
                    max_x = max(max_x, element.center.x + element.radius)
                    min_y = min(min_y, element.center.y - element.radius)
                    max_y = max(max_y, element.center.y + element.radius)
                elif isinstance(element, Arc):
                    min_x = min(min_x, element.center.x - element.radius)
                    max_x = max(max_x, element.center.x + element.radius)
                    min_y = min(min_y, element.center.y - element.radius)
                    max_y = max(max_y, element.center.y + element.radius)
                elif isinstance(element, Polyline):
                    for point in element.points:
                        min_x = min(min_x, point.x)
                        max_x = max(max_x, point.x)
                        min_y = min(min_y, point.y)
                        max_y = max(max_y, point.y)
                elif isinstance(element, Text):
                    min_x = min(min_x, element.position.x)
                    max_x = max(max_x, element.position.x)
                    min_y = min(min_y, element.position.y)
                    max_y = max(max_y, element.position.y)
            except Exception:
                continue

        if min_x == float("inf"):
            return None

        return (min_x, min_y, max_x, max_y)

    def _apply_unit_factor_to_collection(
        self, collection: GeometryCollection, factor: float
    ):
        """全要素に単位係数を適用"""
        for element in collection.elements:
            try:
                if isinstance(element, Line):
                    element.start.x *= factor
                    element.start.y *= factor
                    element.end.x *= factor
                    element.end.y *= factor
                elif isinstance(element, Circle):
                    element.center.x *= factor
                    element.center.y *= factor
                    element.radius *= factor
                elif isinstance(element, Arc):
                    element.center.x *= factor
                    element.center.y *= factor
                    element.radius *= factor
                elif isinstance(element, Polyline):
                    for point in element.points:
                        point.x *= factor
                        point.y *= factor
                elif isinstance(element, Text):
                    element.position.x *= factor
                    element.position.y *= factor
                    element.height *= factor
            except Exception:
                continue


    def convert_dxf_file(
        self, file_path: str, include_paperspace: bool = True
    ) -> GeometryCollection:
        """DXFファイル全体を変換

        Args:
            file_path: DXFファイルパス
            include_paperspace: ペーパー空間も変換するか

        Returns:
            変換された幾何要素のコレクション
        """
        doc = ezdxf.readfile(file_path)
        
        # 新しい単位検出システムを使用
        self.unit_detection_result = self.unit_detector.get_recommended_unit_factor(doc, file_path)
        self.unit_factor = self.unit_detection_result.unit_factor
        
        # 古い検出方法も参考として実行（後で削除予定）
        old_unit_factor = self._detect_unit_factor(doc)

        logging.info(f"DXF version: {doc.dxfversion}")
        logging.info(f"DXF units: {getattr(doc, 'units', 'N/A')}")
        logging.info(f"Unit detection result: method={self.unit_detection_result.detection_method}, "
                    f"factor={self.unit_factor}, confidence={self.unit_detection_result.confidence:.2f}")
        logging.info(f"Old unit factor (for comparison): {old_unit_factor}")

        collection = GeometryCollection()
        collection.metadata["unit_factor_mm"] = self.unit_factor
        collection.metadata["insunits_code"] = getattr(doc, "units", 0)
        collection.metadata["unit_detection"] = {
            "method": self.unit_detection_result.detection_method,
            "confidence": self.unit_detection_result.confidence,
            "details": self.unit_detection_result.details
        }

        # レイヤー情報を保存
        for layer in doc.layers:
            self.layer_info[layer.dxf.name] = {
                "color": layer.dxf.color,
                "linetype": layer.dxf.linetype,
            }

        # ブロック定義を保存
        for block in doc.blocks:
            if not block.name.startswith("*"):
                self.block_definitions[block.name] = block

        # モデル空間を変換
        modelspace = doc.modelspace()
        
        # 先にINSERT要素の座標範囲を確認（単位判定用）
        insert_min_x = insert_min_y = float('inf')
        insert_max_x = insert_max_y = float('-inf')
        has_inserts = False
        
        for entity in modelspace:
            if entity.dxftype() == 'INSERT':
                has_inserts = True
                x, y = entity.dxf.insert.x, entity.dxf.insert.y
                insert_min_x = min(insert_min_x, x)
                insert_max_x = max(insert_max_x, x)
                insert_min_y = min(insert_min_y, y)
                insert_max_y = max(insert_max_y, y)
        
        if has_inserts and insert_min_x != float('inf'):
            insert_width = insert_max_x - insert_min_x
            insert_height = insert_max_y - insert_min_y
            logging.info(f"INSERT bounds: {insert_width:.1f} x {insert_height:.1f}")
            collection.metadata["insert_bounds"] = (insert_width, insert_height)
        
        for entity in modelspace:
            converted = self.convert_entity(entity, doc)
            if converted:
                if isinstance(converted, list):
                    collection.add_elements(converted)
                else:
                    collection.add_element(converted)

        # ペーパー空間を変換
        if include_paperspace:
            for layout in doc.layouts:
                if layout.is_any_paperspace:
                    for entity in layout:
                        if entity.dxftype() != "VIEWPORT":
                            converted = self.convert_entity(entity, doc)
                            if converted:
                                if isinstance(converted, list):
                                    collection.add_elements(converted)
                                else:
                                    collection.add_element(converted)

        # 変換後の実際の座標範囲を計算
        actual_bounds = self._calculate_actual_bounds(collection)
        if actual_bounds:
            width = actual_bounds[2] - actual_bounds[0]
            height = actual_bounds[3] - actual_bounds[1]
            
            logging.info(f"Initial bounds: {width:.1f} × {height:.1f} mm")
            logging.info(f"INSUNITS code: {collection.metadata.get('insunits_code', 'N/A')}")
            
            # INSERT座標から推測される実際のサイズを確認
            conversion_applied = False
            insert_bounds = collection.metadata.get("insert_bounds")
            if insert_bounds and insert_bounds[0] > 50 and insert_bounds[1] > 50:
                # INSERT座標が50以上なら、建物サイズとしてメートル単位の可能性が高い
                insert_width_m = insert_bounds[0]
                insert_height_m = insert_bounds[1]
                
                # 現在の幅が小さすぎる場合（5000mm未満）、INSERT座標を信頼
                if width < 5000 and height < 5000:
                    logging.info(f"Small actual bounds ({width:.0f}×{height:.0f}mm) but INSERT shows {insert_width_m:.0f}×{insert_height_m:.0f}m")
                    logging.info("Trusting INSERT coordinates - applying meter to mm conversion")
                    # INSERT座標に基づいて1000倍
                    target_scale = 1000.0
                    self._apply_unit_factor_to_collection(collection, target_scale)
                    collection.metadata["unit_factor_mm"] = target_scale
                    collection.metadata["auto_scaled"] = True
                    collection.metadata["insert_based"] = True
                    conversion_applied = True
                else:
                    # 通常のスマート単位検出
                    conversion_applied = self._detect_and_fix_unit_issue(collection, actual_bounds)
            else:
                # 通常のスマート単位検出
                conversion_applied = self._detect_and_fix_unit_issue(collection, actual_bounds)
            
            if conversion_applied:
                # 変換後の範囲を再計算
                actual_bounds = self._calculate_actual_bounds(collection)
                if actual_bounds:
                    width = actual_bounds[2] - actual_bounds[0]
                    height = actual_bounds[3] - actual_bounds[1]
                    logging.info(f"Final bounds after conversion: {width:.1f} × {height:.1f} mm")
                
        return collection

    def convert_entity(
        self, entity: DXFEntity, doc: ezdxf.document.Drawing
    ) -> Optional[Union[Line, Circle, Arc, Polyline, Text, List[Any]]]:
        """DXFエンティティを内部データ構造に変換"""
        try:
            entity_type = entity.dxftype()

            # 基本的な図形要素
            if entity_type == "LINE":
                return self._convert_line(entity)
            elif entity_type == "CIRCLE":
                return self._convert_circle(entity)
            elif entity_type == "ARC":
                return self._convert_arc(entity)
            elif entity_type in ["LWPOLYLINE", "POLYLINE"]:
                return self._convert_polyline(entity)
            elif entity_type in ["TEXT", "MTEXT"]:
                return self._convert_text(entity)
            elif entity_type == "INSERT":
                return self._explode_block_safe(entity, doc)
            else:
                return None

        except Exception as e:
            print(f"Error converting {entity.dxftype()}: {e}")
            return None

    def _scale(self, value: float) -> float:
        """単位係数を掛けて mm に変換"""
        return value * self.unit_factor

    def _convert_line(self, entity: DXFLine) -> Line:
        """LINE エンティティを変換"""
        return Line(
            start=Point(
                self._scale(entity.dxf.start.x), self._scale(entity.dxf.start.y)
            ),
            end=Point(self._scale(entity.dxf.end.x), self._scale(entity.dxf.end.y)),
            layer=entity.dxf.layer,
        )

    def _convert_circle(self, entity: DXFCircle) -> Circle:
        """CIRCLE エンティティを変換"""
        return Circle(
            center=Point(
                self._scale(entity.dxf.center.x), self._scale(entity.dxf.center.y)
            ),
            radius=entity.dxf.radius * self.unit_factor,
            layer=entity.dxf.layer,
        )

    def _convert_arc(self, entity: DXFArc) -> Arc:
        """ARC エンティティを変換"""
        return Arc(
            center=Point(
                self._scale(entity.dxf.center.x), self._scale(entity.dxf.center.y)
            ),
            radius=entity.dxf.radius * self.unit_factor,
            start_angle=entity.dxf.start_angle,
            end_angle=entity.dxf.end_angle,
            layer=entity.dxf.layer,
        )

    def _convert_polyline(self, entity: Union[LWPolyline, DXFPolyline]) -> Polyline:
        """POLYLINE/LWPOLYLINE エンティティを変換"""
        points = []

        if entity.dxftype() == "LWPOLYLINE":
            # LWPolylineの処理
            for point in entity:
                points.append(Point(self._scale(point[0]), self._scale(point[1])))
            closed = entity.closed
        else:
            # 通常のPolylineの処理
            for vertex in entity.vertices:
                points.append(
                    Point(
                        self._scale(vertex.dxf.location.x),
                        self._scale(vertex.dxf.location.y),
                    )
                )
            closed = entity.is_closed

        return Polyline(
            points=points,
            closed=closed,
            layer=entity.dxf.layer,
        )

    def _convert_text(self, entity: Union[DXFText, MText]) -> Text:
        """TEXT/MTEXT エンティティを変換"""
        if entity.dxftype() == "TEXT":
            return Text(
                position=Point(
                    self._scale(entity.dxf.insert.x), self._scale(entity.dxf.insert.y)
                ),
                content=entity.dxf.text,
                height=entity.dxf.height * self.unit_factor,
                rotation=entity.dxf.rotation,
                layer=entity.dxf.layer,
            )
        else:  # MTEXT
            return Text(
                position=Point(
                    self._scale(entity.dxf.insert.x), self._scale(entity.dxf.insert.y)
                ),
                content=entity.text,
                height=entity.dxf.char_height * self.unit_factor,
                rotation=entity.dxf.rotation,
                layer=entity.dxf.layer,
            )

    def _explode_block_safe(
        self, insert: Insert, doc: ezdxf.document.Drawing
    ) -> List[Any]:
        """ブロック参照を安全に展開"""
        result = []

        # ブロック定義を取得
        block = self.block_definitions.get(insert.dxf.name)
        if not block and doc:
            block = doc.blocks.get(insert.dxf.name)

        if not block:
            return result

        # 変換パラメータを取得
        raw_insert = insert.dxf.insert
        # 挿入点も mm 換算
        insert_point = Point(self._scale(raw_insert.x), self._scale(raw_insert.y))

        x_scale = insert.dxf.xscale
        y_scale = insert.dxf.yscale
        rotation = insert.dxf.rotation

        for entity in block:
            # 各エンティティを変換
            converted = self.convert_entity(entity, doc)

            if converted:
                # リストの場合（複数要素）
                if isinstance(converted, list):
                    for item in converted:
                        transformed = self._apply_simple_transformation(
                            item, insert_point, x_scale, y_scale, rotation
                        )
                        if transformed:
                            result.append(transformed)
                else:
                    # 単一要素の場合
                    transformed = self._apply_simple_transformation(
                        converted, insert_point, x_scale, y_scale, rotation
                    )
                    if transformed:
                        result.append(transformed)

            # ネストされたブロックの処理
            if entity.dxftype() == "INSERT":
                # 再帰的にブロックを展開
                nested_elements = self._explode_block_safe(entity, doc)
                for elem in nested_elements:
                    # ネストされた要素にも変換を適用
                    transformed = self._apply_simple_transformation(
                        elem, insert_point, x_scale, y_scale, rotation
                    )
                    if transformed:
                        result.append(transformed)

        return result

    def _apply_simple_transformation(
        self,
        element: Any,
        insert_point,
        x_scale: float,
        y_scale: float,
        rotation: float,
    ) -> Optional[Any]:
        """シンプルな変換の適用（Matrix44を使わない）"""
        try:
            cos_r = math.cos(math.radians(rotation))
            sin_r = math.sin(math.radians(rotation))

            def transform_point(p: Point) -> Point:
                # スケール
                x = p.x * x_scale
                y = p.y * y_scale

                # 回転
                new_x = x * cos_r - y * sin_r
                new_y = x * sin_r + y * cos_r

                # 平行移動
                new_x += insert_point.x
                new_y += insert_point.y

                return Point(new_x, new_y)

            if isinstance(element, Line):
                return Line(
                    start=transform_point(element.start),
                    end=transform_point(element.end),
                    layer=element.layer,
                )

            elif isinstance(element, Circle):
                # 円は中心点のみ変換（半径は平均スケールを適用）
                avg_scale = (x_scale + y_scale) / 2
                return Circle(
                    center=transform_point(element.center),
                    radius=element.radius * avg_scale,
                    layer=element.layer,
                )

            elif isinstance(element, Arc):
                # アークは中心点と角度を変換
                avg_scale = (x_scale + y_scale) / 2
                return Arc(
                    center=transform_point(element.center),
                    radius=element.radius * avg_scale,
                    start_angle=element.start_angle + rotation,
                    end_angle=element.end_angle + rotation,
                    layer=element.layer,
                )

            elif isinstance(element, Polyline):
                transformed_points = []
                for point in element.points:
                    transformed_points.append(transform_point(point))
                return Polyline(
                    points=transformed_points,
                    closed=element.closed,
                    layer=element.layer,
                )

            elif isinstance(element, Text):
                # テキストは位置と回転を変換
                avg_scale = (x_scale + y_scale) / 2
                return Text(
                    position=transform_point(element.position),
                    content=element.content,
                    height=element.height * avg_scale,
                    rotation=element.rotation + rotation,
                    layer=element.layer,
                )

            else:
                return element

        except Exception as e:
            print(f"Error in simple transformation: {e}")
            return None
