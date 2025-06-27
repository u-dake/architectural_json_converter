"""
Safe PDF Visualizer

PDF構造エラーを回避する安全なPDF生成モジュール
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


class SafePDFVisualizer:
    """安全なPDF可視化クラス"""

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
        """Matplotlibの安全な設定"""
        # PDF生成時の警告を抑制
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
        
        # PDF設定
        plt.rcParams['pdf.fonttype'] = 42  # TrueTypeフォントを埋め込まない
        plt.rcParams['ps.fonttype'] = 42
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
        
        # 日本語フォントは使用しない（ASCII文字のみ）
        plt.rcParams['axes.unicode_minus'] = False

    def visualize_to_pdf(
        self,
        geometry: GeometryCollection,
        output_path: str,
        page_size: Tuple[float, float] = (420, 297),  # A3横 (mm)
        dpi: int = 300,
        show_grid: bool = False
    ):
        """幾何データを安全にPDFに出力
        
        Args:
            geometry: 幾何データコレクション
            output_path: 出力PDFファイルパス
            page_size: ページサイズ (幅, 高さ) mm単位
            dpi: 解像度
            show_grid: グリッド表示
        """
        try:
            # 図面の境界を計算
            bounds = self._calculate_bounds(geometry)
            if not bounds:
                print("Warning: No geometry found")
                self._create_empty_pdf(output_path, page_size, dpi)
                return
            
            min_x, min_y, max_x, max_y = bounds
            width = max_x - min_x
            height = max_y - min_y
            
            # ページサイズをインチに変換
            page_width_inch = page_size[0] / 25.4
            page_height_inch = page_size[1] / 25.4
            
            # 図の作成
            self.fig, self.ax = plt.subplots(figsize=(page_width_inch, page_height_inch), dpi=dpi)
            
            # 基本設定
            self.ax.set_aspect('equal', adjustable='box')
            self.ax.set_facecolor('white')
            self.fig.patch.set_facecolor('white')
            
            # 表示範囲の設定
            padding = max(width, height) * 0.05
            self.ax.set_xlim(min_x - padding, max_x + padding)
            self.ax.set_ylim(min_y - padding, max_y + padding)
            
            # グリッドの表示
            if show_grid:
                self.ax.grid(True, linestyle=':', alpha=0.3, linewidth=0.5)
            
            # 軸の非表示
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
            # 枠線の表示
            for spine in self.ax.spines.values():
                spine.set_edgecolor('black')
                spine.set_linewidth(0.5)
            
            # レイヤーごとに要素を収集して描画
            layer_elements = self._organize_by_layer(geometry)
            
            for layer_name, elements in layer_elements.items():
                self._draw_layer_elements(elements, layer_name)
            
            # 安全なPDF保存
            self._save_pdf_safely(output_path, dpi)
            
        except Exception as e:
            print(f"Error in PDF generation: {e}")
            # フォールバック: 高解像度PNG生成
            self._save_as_png_fallback(output_path, dpi)
        finally:
            if self.fig:
                plt.close(self.fig)

    def _calculate_bounds(self, geometry: GeometryCollection) -> Optional[Tuple[float, float, float, float]]:
        """幾何データの境界ボックスを計算"""
        if not geometry.elements:
            return None
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element in geometry.elements:
            try:
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
                    # 簡易的な境界計算
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
                    # テキストの境界は概算
                    min_x = min(min_x, element.position.x)
                    max_x = max(max_x, element.position.x + len(element.content) * element.height * 0.6)
                    min_y = min(min_y, element.position.y)
                    max_y = max(max_y, element.position.y + element.height)
            except Exception:
                # 個別の要素でエラーが発生しても続行
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

    def _draw_layer_elements(self, elements: List[Any], layer_name: str):
        """レイヤーの要素を描画"""
        # レイヤーの色を取得または割り当て
        if layer_name not in self.layer_colors:
            color_index = hash(layer_name) % len(self.default_colors)
            self.layer_colors[layer_name] = self.default_colors[color_index]
        
        layer_color = self.layer_colors[layer_name]
        
        # 線のコレクション
        lines = []
        
        # パッチのコレクション
        patches = []
        
        for element in elements:
            try:
                if isinstance(element, Line):
                    lines.append([(element.start.x, element.start.y), 
                                 (element.end.x, element.end.y)])
                
                elif isinstance(element, Circle):
                    circle = MplCircle(
                        (element.center.x, element.center.y),
                        element.radius,
                        fill=False,
                        edgecolor=layer_color,
                        linewidth=0.5
                    )
                    patches.append(circle)
                
                elif isinstance(element, Arc):
                    # アークをポリラインで近似
                    points = self._arc_to_points(element)
                    for i in range(len(points) - 1):
                        lines.append([points[i], points[i + 1]])
                
                elif isinstance(element, Polyline):
                    if len(element.points) >= 2:
                        # ポリラインを線分に分解
                        for i in range(len(element.points) - 1):
                            lines.append([(element.points[i].x, element.points[i].y),
                                         (element.points[i+1].x, element.points[i+1].y)])
                        
                        # 閉じたポリラインの場合
                        if element.closed and len(element.points) > 2:
                            lines.append([(element.points[-1].x, element.points[-1].y),
                                         (element.points[0].x, element.points[0].y)])
                
                elif isinstance(element, Text):
                    # テキストは安全な文字のみ描画
                    safe_text = self._make_text_safe(element.content)
                    if safe_text:
                        self.ax.text(
                            element.position.x,
                            element.position.y,
                            safe_text,
                            fontsize=max(1, element.height * 0.7),
                            rotation=element.rotation,
                            color=layer_color,
                            verticalalignment='bottom',
                            horizontalalignment='left',
                            fontfamily='sans-serif'
                        )
            except Exception:
                # 個別の要素でエラーが発生しても続行
                continue
        
        # 線のコレクションを一括描画
        if lines:
            try:
                lc = LineCollection(lines, colors=[layer_color] * len(lines), linewidths=0.5)
                self.ax.add_collection(lc)
            except Exception:
                # ラインコレクション描画エラー時は個別描画
                for line in lines:
                    try:
                        self.ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], 
                                   color=layer_color, linewidth=0.5)
                    except Exception:
                        continue
        
        # パッチのコレクションを一括描画
        if patches:
            try:
                for patch in patches:
                    self.ax.add_patch(patch)
            except Exception:
                # パッチ描画エラー時はスキップ
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
        # ASCII文字のみを残す
        safe_text = ''.join(char for char in text if ord(char) < 128)
        return safe_text if safe_text else "[TEXT]"

    def _save_pdf_safely(self, output_path: str, dpi: int):
        """PDFを安全に保存"""
        try:
            # 一時的に警告を無効化
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                self.fig.savefig(
                    output_path,
                    format='pdf',
                    dpi=dpi,
                    bbox_inches='tight',
                    pad_inches=0.1,
                    facecolor='white',
                    edgecolor='none'
                )
            print(f"PDF saved: {output_path}")
            
        except Exception as e:
            print(f"PDF save error: {e}")
            raise

    def _save_as_png_fallback(self, output_path: str, dpi: int):
        """フォールバック: PNG保存"""
        png_path = output_path.replace('.pdf', '.png')
        try:
            if self.fig:
                self.fig.savefig(
                    png_path,
                    format='png',
                    dpi=dpi,
                    bbox_inches='tight',
                    pad_inches=0.1,
                    facecolor='white'
                )
                print(f"Fallback PNG saved: {png_path}")
        except Exception as e:
            print(f"PNG fallback also failed: {e}")

    def _create_empty_pdf(self, output_path: str, page_size: Tuple[float, float], dpi: int):
        """空のPDFを作成"""
        page_width_inch = page_size[0] / 25.4
        page_height_inch = page_size[1] / 25.4
        
        fig, ax = plt.subplots(figsize=(page_width_inch, page_height_inch), dpi=dpi)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.text(50, 50, 'No geometry found', ha='center', va='center', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        
        try:
            fig.savefig(output_path, format='pdf', dpi=dpi, bbox_inches='tight')
            print(f"Empty PDF created: {output_path}")
        except Exception as e:
            print(f"Failed to create empty PDF: {e}")
        finally:
            plt.close(fig)