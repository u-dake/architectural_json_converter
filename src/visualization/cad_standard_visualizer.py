"""
CAD Standard PDF Visualizer

CAD標準のA3サイズ、1/100スケール固定のPDF出力
"""

from typing import List, Optional, Tuple, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle as MplCircle, Arc as MplArc, Polygon
from matplotlib.collections import LineCollection, PatchCollection
import matplotlib.font_manager as fm
import numpy as np
import platform
import warnings
from pathlib import Path

from src.data_structures.simple_geometry import (
    Point,
    Line,
    Circle,
    Arc,
    Polyline,
    Text,
    GeometryCollection,
)
from src.visualization.layout_util import compute_fit_scale


class CADStandardVisualizer:
    """CAD標準PDF可視化クラス（A3、1/100スケール固定）"""

    def __init__(self):
        self.fig = None
        self.ax = None
        self.layer_colors = {}
        self.default_colors = [
            '#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', 
            '#FF00FF', '#00FFFF', '#FFA500', '#800080', '#A52A2A'
        ]
        self._setup_matplotlib()

    def _setup_matplotlib(self):
        """Matplotlibの設定"""
        # 警告を抑制
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
        
        # PDF設定
        plt.rcParams['pdf.fonttype'] = 42
        plt.rcParams['ps.fonttype'] = 42
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def visualize_to_a3_pdf(
        self,
        geometry: GeometryCollection,
        output_path: str,
        scale: str = "1:100",
        dpi: int = 300,
        show_border: bool = True,
        title: Optional[str] = None
    ):
        """A3サイズ、指定スケールでPDF出力
        
        Args:
            geometry: 幾何データコレクション
            output_path: 出力PDFファイルパス
            scale: 図面スケール（例: "1:100", "1:50"）
            dpi: 解像度
            show_border: 図面枠表示
            title: 図面タイトル
        """
        try:
            # A3サイズ定義（横）
            a3_width_mm = 420  # A3横
            a3_height_mm = 297
            
            # CADスケール解析 - 1:100は実世界座標を100で割る
            scale_parts = scale.split(':')
            if len(scale_parts) != 2:
                raise ValueError(f"Invalid scale format: {scale}")
            
            scale_numerator = float(scale_parts[0])
            scale_denominator = float(scale_parts[1])
            # 1:100の場合、実世界座標を100で割って紙上サイズにする
            cad_scale_factor = scale_numerator / scale_denominator  # 1/100 = 0.01
            
            print(f"CAD scale: {scale} (factor: {cad_scale_factor}) - real coordinates ÷ {scale_denominator}")
            
            # 図面境界の計算（注針レイヤーを除外）
            bounds = self._calculate_bounds(geometry, ignore_annotation=True)
            if not bounds:
                print("Warning: No geometry found")
                self._create_empty_a3_pdf(output_path, dpi, title)
                return
            
            min_x, min_y, max_x, max_y = bounds
            drawing_width_mm = max_x - min_x
            drawing_height_mm = max_y - min_y
            
            print(f"Drawing size: {drawing_width_mm:.2f} x {drawing_height_mm:.2f} mm")
            print(f"Unit factor from metadata: {geometry.metadata.get('unit_factor_mm', 1.0)}")
            print(f"Auto-scaled: {geometry.metadata.get('auto_scaled', False)}")
            
            margin_mm = 12  # 余白を少し縮小
            available_width = a3_width_mm - 2 * margin_mm
            available_height = a3_height_mm - 2 * margin_mm

            # 1:100固定で描画（自動調整しない）
            effective_scale_factor = cad_scale_factor  # 0.01 for 1:100
            display_width_mm = drawing_width_mm * effective_scale_factor
            display_height_mm = drawing_height_mm * effective_scale_factor
            
            # デバッグログ追加
            print(f"DEBUG: CAD scale factor: {cad_scale_factor}")
            print(f"DEBUG: Drawing bounds: {bounds}")
            print(f"DEBUG: Effective scale: {effective_scale_factor}")
            print(f"DEBUG: Display size on paper: {display_width_mm:.1f} x {display_height_mm:.1f} mm")
            
            # A3用紙に収まるかチェック
            if display_width_mm > available_width or display_height_mm > available_height:
                print(f"WARNING: Drawing size ({display_width_mm:.1f} x {display_height_mm:.1f} mm) exceeds A3 paper at scale {scale}")
                print(f"Consider using a smaller scale (e.g., 1:200)")
            
            usage_w = (display_width_mm / a3_width_mm) * 100
            usage_h = (display_height_mm / a3_height_mm) * 100
            
            display_scale_label = scale  # Use the original scale parameter

            page_center_x = a3_width_mm / 2
            page_center_y = a3_height_mm / 2
            drawing_start_x = page_center_x - display_width_mm / 2
            drawing_start_y = page_center_y - display_height_mm / 2

            print(f"Real world size: {drawing_width_mm:.1f} × {drawing_height_mm:.1f} mm")
            print(f"Effective scale: {display_scale_label}  (page usage {usage_w:.1f}% × {usage_h:.1f}%)")

            # Matplotlibの図を作成（A3サイズ）
            mm_to_inch = 1 / 25.4
            fig_width_inch = a3_width_mm * mm_to_inch
            fig_height_inch = a3_height_mm * mm_to_inch
            
            self.fig, self.ax = plt.subplots(figsize=(fig_width_inch, fig_height_inch), dpi=dpi)
            
            # 基本設定
            self.ax.set_aspect('equal', adjustable='box')
            self.ax.set_facecolor('white')
            self.fig.patch.set_facecolor('white')
            
            # ページ座標系でのビュー設定
            self.ax.set_xlim(0, a3_width_mm)
            self.ax.set_ylim(0, a3_height_mm)
            
            # 軸とティックを非表示
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
            # レイヤーごとに要素を収集して描画
            layer_elements = self._organize_by_layer(geometry)
            
            # 座標変換パラメータ
            transform_params = {
                'drawing_min_x': min_x,
                'drawing_min_y': min_y,
                'drawing_width': drawing_width_mm,
                'drawing_height': drawing_height_mm,
                'drawing_start_x': drawing_start_x,
                'drawing_start_y': drawing_start_y,
                'scale': effective_scale_factor  # CADスケール（1:100 = 0.01）
            }
            
            for layer_name, elements in layer_elements.items():
                self._draw_layer_elements(elements, layer_name, transform_params)
            
            # 図面枠の描画
            if show_border:
                self._draw_a3_border(display_scale_label, title)
            
            # 余白設定（フルページ使用）
            self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
            
            # PDFに保存
            self._save_pdf_safely(output_path, dpi)
            
        except Exception as e:
            print(f"Error in A3 PDF generation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.fig:
                plt.close(self.fig)

    def _calculate_bounds(self, geometry: GeometryCollection, ignore_annotation: bool = True) -> Optional[Tuple[float, float, float, float]]:
        """幾何データの境界ボックスを計算
        ignore_annotation=True のときは寸法線やテキストなどの注針レイヤーを除外して建築本体の範囲を算出する
        """
        if not geometry.elements:
            return None
        dim_keywords = ["dim", "寸法", "annotation", "anno"]
        text_types = (Text,)
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        def consider(elem, x_vals, y_vals):
            nonlocal min_x, min_y, max_x, max_y
            for x in x_vals:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
            for y in y_vals:
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        
        for element in geometry.elements:
            try:
                layer_lower = getattr(element, 'layer', '0').lower()
                if ignore_annotation:
                    if any(k in layer_lower for k in dim_keywords):
                        continue  # 寸法や注針レイヤーを無視
                    if isinstance(element, text_types):
                        continue  # テキストは無視
                if isinstance(element, Line):
                    consider(element, [element.start.x, element.end.x], [element.start.y, element.end.y])
                elif isinstance(element, Circle):
                    consider(element, [element.center.x - element.radius, element.center.x + element.radius], [element.center.y - element.radius, element.center.y + element.radius])
                elif isinstance(element, Arc):
                    consider(element, [element.center.x - element.radius, element.center.x + element.radius], [element.center.y - element.radius, element.center.y + element.radius])
                elif isinstance(element, Polyline):
                    consider(element, [p.x for p in element.points], [p.y for p in element.points])
            except Exception:
                continue
        if min_x == float('inf'):
            return None
        return (min_x, min_y, max_x, max_y)

    def _organize_by_layer(self, geometry: GeometryCollection) -> Dict[str, List[Any]]:
        """要素をレイヤーごとに整理"""
        layer_elements = {}
        
        for element in geometry.elements:
            layer = getattr(element, 'layer', '0')
            if layer not in layer_elements:
                layer_elements[layer] = []
            layer_elements[layer].append(element)
        
        return layer_elements

    def _transform_point(self, x: float, y: float, transform_params: dict) -> tuple:
        """図面座標をA3ページ座標に変換（CADスケール適用）"""
        if not transform_params:
            return (x, y)
        
        # 図面座標を正規化 (0-1)
        norm_x = (x - transform_params['drawing_min_x']) / transform_params['drawing_width']
        norm_y = (y - transform_params['drawing_min_y']) / transform_params['drawing_height']
        
        # CADスケール適用済みの図面サイズ
        scaled_width = transform_params['drawing_width'] * transform_params['scale']
        scaled_height = transform_params['drawing_height'] * transform_params['scale']
        
        # A3ページ上での座標計算
        page_x = transform_params['drawing_start_x'] + norm_x * scaled_width
        page_y = transform_params['drawing_start_y'] + norm_y * scaled_height
        
        return (page_x, page_y)

    def _draw_layer_elements(self, elements: List[Any], layer_name: str, transform_params: dict = None):
        """レイヤーの要素を描画"""
        # レイヤーの色を取得または割り当て
        if layer_name not in self.layer_colors:
            color_index = hash(layer_name) % len(self.default_colors)
            self.layer_colors[layer_name] = self.default_colors[color_index]
        
        layer_color = self.layer_colors[layer_name]
        
        # 線の描画
        lines = []
        
        for element in elements:
            try:
                if isinstance(element, Line):
                    start_pt = self._transform_point(element.start.x, element.start.y, transform_params)
                    end_pt = self._transform_point(element.end.x, element.end.y, transform_params)
                    lines.append([start_pt, end_pt])
                
                elif isinstance(element, Circle):
                    center_pt = self._transform_point(element.center.x, element.center.y, transform_params)
                    # 半径もスケール
                    scaled_radius = element.radius * transform_params['scale'] if transform_params else element.radius
                    circle = MplCircle(
                        center_pt,
                        scaled_radius,
                        fill=False,
                        edgecolor=layer_color,
                        linewidth=0.5
                    )
                    self.ax.add_patch(circle)
                
                elif isinstance(element, Arc):
                    # アークをポリラインで近似（変換前の座標で）
                    points = self._arc_to_points(element)
                    transformed_points = [self._transform_point(p[0], p[1], transform_params) for p in points]
                    for i in range(len(transformed_points) - 1):
                        lines.append([transformed_points[i], transformed_points[i + 1]])
                
                elif isinstance(element, Polyline):
                    if len(element.points) >= 2:
                        transformed_points = [self._transform_point(p.x, p.y, transform_params) for p in element.points]
                        for i in range(len(transformed_points) - 1):
                            lines.append([transformed_points[i], transformed_points[i+1]])
                        
                        if element.closed and len(element.points) > 2:
                            lines.append([transformed_points[-1], transformed_points[0]])
                
                elif isinstance(element, Text):
                    # ASCII文字のみに変換
                    safe_text = self._make_text_safe(element.content)
                    if safe_text:
                        text_pos = self._transform_point(element.position.x, element.position.y, transform_params)
                        # フォントサイズもスケール
                        scaled_fontsize = element.height * transform_params['scale'] * 0.7 if transform_params else element.height * 0.7
                        self.ax.text(
                            text_pos[0],
                            text_pos[1],
                            safe_text,
                            fontsize=max(0.5, scaled_fontsize),
                            rotation=element.rotation,
                            color=layer_color,
                            verticalalignment='bottom',
                            horizontalalignment='left',
                            fontfamily='sans-serif'
                        )
            except Exception:
                continue
        
        # 線のコレクションを一括描画
        if lines:
            try:
                lc = LineCollection(lines, colors=[layer_color] * len(lines), linewidths=0.5)
                self.ax.add_collection(lc)
            except Exception:
                pass

    def _arc_to_points(self, arc: Arc, num_points: int = 20) -> List[Tuple[float, float]]:
        """アークを点列に変換"""
        import math
        
        points = []
        start_rad = math.radians(arc.start_angle)
        end_rad = math.radians(arc.end_angle)
        
        # 角度の正規化
        if end_rad < start_rad:
            end_rad += 2 * math.pi
        
        for i in range(num_points + 1):
            t = i / num_points
            angle = start_rad + (end_rad - start_rad) * t
            x = arc.center.x + arc.radius * math.cos(angle)
            y = arc.center.y + arc.radius * math.sin(angle)
            points.append((x, y))
        
        return points

    def _make_text_safe(self, text: str) -> str:
        """テキストを安全な文字のみにする"""
        safe_text = ''.join(char for char in text if ord(char) < 128)
        return safe_text if safe_text else "[TEXT]"

    def _draw_a3_border(self, scale: str, title: Optional[str]):
        """A3図面枠を描画"""
        # A3ページ全体の枠を描画
        border_margin = 5  # 5mm マージン
        
        # 図面枠（外枠）
        border_x = [border_margin, 420-border_margin, 420-border_margin, border_margin, border_margin]
        border_y = [border_margin, border_margin, 297-border_margin, 297-border_margin, border_margin]
        
        self.ax.plot(border_x, border_y, 'k-', linewidth=1.0)
        
        # タイトルブロック（簡易版）
        if title or scale:
            # 右下角にスケール表示
            text_x = 420 - 10
            text_y = 10
            
            if scale:
                self.ax.text(text_x, text_y, f"SCALE {scale}", 
                           horizontalalignment='right', verticalalignment='bottom',
                           fontsize=8, fontweight='bold')
            
            if title:
                self.ax.text(text_x, text_y + 8, title,
                           horizontalalignment='right', verticalalignment='bottom',
                           fontsize=10, fontweight='bold')

    def _save_pdf_safely(self, output_path: str, dpi: int):
        """PDFを安全に保存"""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                self.fig.savefig(
                    output_path,
                    format='pdf',
                    dpi=dpi,
                    bbox_inches=None,  # フルページ使用
                    pad_inches=0,
                    facecolor='white',
                    edgecolor='none'
                )
            print(f"A3 PDF saved: {output_path}")
            
        except Exception as e:
            print(f"PDF save error: {e}")
            raise

    def _create_empty_a3_pdf(self, output_path: str, dpi: int, title: Optional[str]):
        """空のA3 PDFを作成"""
        mm_to_inch = 1 / 25.4
        fig_width_inch = 420 * mm_to_inch
        fig_height_inch = 297 * mm_to_inch
        
        fig, ax = plt.subplots(figsize=(fig_width_inch, fig_height_inch), dpi=dpi)
        ax.set_xlim(0, 420)
        ax.set_ylim(0, 297)
        ax.text(210, 148, title or 'No geometry found', ha='center', va='center', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        
        try:
            fig.savefig(output_path, format='pdf', dpi=dpi, bbox_inches=None, pad_inches=0)
            print(f"Empty A3 PDF created: {output_path}")
        except Exception as e:
            print(f"Failed to create empty A3 PDF: {e}")
        finally:
            plt.close(fig)