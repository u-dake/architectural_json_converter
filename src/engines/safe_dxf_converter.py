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


class SafeDXFConverter:
    """安全なDXFコンバーター"""

    def __init__(self):
        self.layer_info = {}
        self.block_definitions = {}
        # 追加: DXF図面単位→mm換算係数 (初期値1.0)
        self.unit_factor = 1.0

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
        # 単位係数を検出
        self.unit_factor = self._detect_unit_factor(doc)

        logging.info(f"DXF version: {doc.dxfversion}")
        logging.info(f"DXF units: {getattr(doc, 'units', 'N/A')}")
        logging.info(f"Initial unit factor: {self.unit_factor}")

        collection = GeometryCollection()
        collection.metadata["unit_factor_mm"] = self.unit_factor
        collection.metadata["insunits_code"] = getattr(doc, "units", 0)

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

        # 変換後の実際の座標範囲を計算して単位補正を決定
        # ヘッダー情報に依存せず、実際の図面要素（ブロック展開後）から判定
        actual_bounds = self._calculate_actual_bounds(collection)
        if actual_bounds:
            width = actual_bounds[2] - actual_bounds[0]
            height = actual_bounds[3] - actual_bounds[1]
            logging.info(f"Actual converted bounds: {width:.1f} x {height:.1f} (unit factor: {self.unit_factor})")
            logging.info(f"INSUNITS code: {collection.metadata.get('insunits_code', 'N/A')}")
            
            # 実際のサイズに基づいて単位補正
            # INSUNITSがmm(4)でも、実際の座標値が異なる単位の場合がある
            if self.unit_factor == 1.0 and collection.metadata.get('insunits_code') == 4:  # INSUNITSがmm(4)の場合
                # 建築図面の典型的なサイズ範囲をチェック
                if 10 < width < 100 and 10 < height < 100:
                    # メートル単位と判断して1000倍
                    logging.info(f"Detected meter units: {width:.1f} x {height:.1f} (should be mm)")
                    logging.info("Applying 1000x scale correction for m to mm conversion")
                    self._apply_unit_factor_to_collection(collection, 1000.0)
                    collection.metadata["unit_factor_mm"] = 1000.0
                    collection.metadata["auto_scaled"] = True
                elif 100 < width < 5000 and 100 < height < 5000:
                    # デシメートル単位と判断して100倍（建築図面の典型的なサイズ）
                    logging.info(f"Detected decimeter units: {width:.1f} x {height:.1f} (should be mm)")
                    logging.info("Applying 100x scale correction for dm to mm conversion")
                    self._apply_unit_factor_to_collection(collection, 100.0)
                    collection.metadata["unit_factor_mm"] = 100.0
                    collection.metadata["auto_scaled"] = True
                else:
                    collection.metadata["auto_scaled"] = False
                    
                # 更新後の範囲を再計算
                if collection.metadata.get("auto_scaled"):
                    actual_bounds = self._calculate_actual_bounds(collection)
                    if actual_bounds:
                        width = actual_bounds[2] - actual_bounds[0]
                        height = actual_bounds[3] - actual_bounds[1]
                        logging.info(f"After scaling bounds: {width:.1f} x {height:.1f} mm")
            else:
                collection.metadata["auto_scaled"] = False
                
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
