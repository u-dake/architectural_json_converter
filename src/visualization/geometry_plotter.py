"""
共通ジオメトリプロッター

異なる視覚化モジュール間で共有されるジオメトリ描画機能
"""

from typing import Optional, Dict, Any, Union
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from dataclasses import dataclass

from src.data_structures.simple_geometry import (
    Point, Line, Circle, Arc, Polyline, Text, GeometryCollection
)


@dataclass
class PlotStyle:
    """プロットスタイル設定"""
    color: str = 'black'
    alpha: float = 1.0
    linewidth: float = 0.5
    linestyle: str = '-'
    marker_size: float = 1
    fill: bool = False
    
    @classmethod
    def from_dict(cls, style_dict: Dict[str, Any]) -> 'PlotStyle':
        """辞書からスタイルを作成"""
        return cls(**{k: v for k, v in style_dict.items() if k in cls.__dataclass_fields__})


class GeometryPlotter:
    """共通ジオメトリプロッター
    
    異なる視覚化モジュール間で共有される描画機能を提供
    """
    
    def __init__(self, default_style: Optional[PlotStyle] = None):
        """
        Args:
            default_style: デフォルトのプロットスタイル
        """
        self.default_style = default_style or PlotStyle()
    
    def plot_element(self, ax: plt.Axes, element: Any, 
                    style: Optional[Union[PlotStyle, Dict[str, Any]]] = None) -> None:
        """単一の要素をプロット
        
        Args:
            ax: Matplotlibの軸オブジェクト
            element: プロットする要素
            style: プロットスタイル（PlotStyleまたは辞書）
        """
        # スタイルを準備
        if style is None:
            style = self.default_style
        elif isinstance(style, dict):
            style = PlotStyle.from_dict(style)
        
        # 要素タイプに応じてプロット
        if isinstance(element, Line):
            self._plot_line(ax, element, style)
        elif isinstance(element, Circle):
            self._plot_circle(ax, element, style)
        elif isinstance(element, Arc):
            self._plot_arc(ax, element, style)
        elif isinstance(element, Polyline):
            self._plot_polyline(ax, element, style)
        elif isinstance(element, Text):
            self._plot_text(ax, element, style)
        elif isinstance(element, Point):
            self._plot_point(ax, element, style)
    
    def plot_collection(self, ax: plt.Axes, collection: GeometryCollection,
                       style: Optional[Union[PlotStyle, Dict[str, Any]]] = None) -> None:
        """GeometryCollectionの全要素をプロット
        
        Args:
            ax: Matplotlibの軸オブジェクト
            collection: プロットするコレクション
            style: プロットスタイル
        """
        for element in collection.elements:
            self.plot_element(ax, element, style)
    
    def _plot_line(self, ax: plt.Axes, line: Line, style: PlotStyle) -> None:
        """線分をプロット"""
        x_vals = [line.start.x, line.end.x]
        y_vals = [line.start.y, line.end.y]
        ax.plot(x_vals, y_vals, 
               color=style.color, 
               alpha=style.alpha, 
               linewidth=style.linewidth,
               linestyle=style.linestyle)
    
    def _plot_circle(self, ax: plt.Axes, circle: Circle, style: PlotStyle) -> None:
        """円をプロット"""
        circle_patch = plt.Circle(
            (circle.center.x, circle.center.y), 
            circle.radius,
            fill=style.fill,
            color=style.color,
            alpha=style.alpha,
            linewidth=style.linewidth,
            linestyle=style.linestyle
        )
        ax.add_patch(circle_patch)
    
    def _plot_arc(self, ax: plt.Axes, arc: Arc, style: PlotStyle) -> None:
        """円弧をプロット（複数の線分で近似）"""
        # 角度の範囲を調整
        start_angle_rad = np.radians(arc.start_angle)
        end_angle_rad = np.radians(arc.end_angle)
        
        if end_angle_rad < start_angle_rad:
            end_angle_rad += 2 * np.pi
        
        # 円弧を線分で近似
        num_segments = max(int((end_angle_rad - start_angle_rad) * 180 / np.pi / 5), 10)
        angles = np.linspace(start_angle_rad, end_angle_rad, num_segments)
        
        x_vals = arc.center.x + arc.radius * np.cos(angles)
        y_vals = arc.center.y + arc.radius * np.sin(angles)
        
        ax.plot(x_vals, y_vals,
               color=style.color,
               alpha=style.alpha,
               linewidth=style.linewidth,
               linestyle=style.linestyle)
    
    def _plot_polyline(self, ax: plt.Axes, polyline: Polyline, style: PlotStyle) -> None:
        """ポリラインをプロット"""
        if not polyline.points:
            return
        
        x_vals = [p.x for p in polyline.points]
        y_vals = [p.y for p in polyline.points]
        
        # 閉じたポリラインの場合は最初の点を最後に追加
        if polyline.closed and len(polyline.points) > 2:
            x_vals.append(x_vals[0])
            y_vals.append(y_vals[0])
        
        ax.plot(x_vals, y_vals,
               color=style.color,
               alpha=style.alpha,
               linewidth=style.linewidth,
               linestyle=style.linestyle)
    
    def _plot_text(self, ax: plt.Axes, text: Text, style: PlotStyle) -> None:
        """テキストをプロット（位置を小さな点で表示）"""
        ax.plot(text.position.x, text.position.y,
               marker='o',
               markersize=style.marker_size,
               color=style.color,
               alpha=style.alpha)
        
        # オプション：実際のテキストも表示（小さいサイズで）
        # ax.text(text.position.x, text.position.y, text.content,
        #         fontsize=4, color=style.color, alpha=style.alpha)
    
    def _plot_point(self, ax: plt.Axes, point: Point, style: PlotStyle) -> None:
        """点をプロット"""
        ax.plot(point.x, point.y,
               marker='o',
               markersize=style.marker_size,
               color=style.color,
               alpha=style.alpha)
    
    @staticmethod
    def setup_axis(ax: plt.Axes, xlim: tuple, ylim: tuple, 
                  aspect: str = 'equal', grid: bool = True) -> None:
        """軸の共通設定
        
        Args:
            ax: 設定する軸
            xlim: X軸の範囲 (min, max)
            ylim: Y軸の範囲 (min, max)
            aspect: アスペクト比設定
            grid: グリッド表示
        """
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_aspect(aspect)
        if grid:
            ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
    
    @staticmethod
    def calculate_bounds(collection: GeometryCollection, 
                        margin_ratio: float = 0.05) -> tuple:
        """GeometryCollectionの境界を計算（マージン付き）
        
        Args:
            collection: 境界を計算するコレクション
            margin_ratio: 境界に追加するマージンの割合
            
        Returns:
            (xlim, ylim) のタプル
        """
        if not collection.elements:
            return ((0, 100), (0, 100))
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for element in collection.elements:
            if isinstance(element, Line):
                min_x = min(min_x, element.start.x, element.end.x)
                min_y = min(min_y, element.start.y, element.end.y)
                max_x = max(max_x, element.start.x, element.end.x)
                max_y = max(max_y, element.start.y, element.end.y)
            elif isinstance(element, Circle):
                min_x = min(min_x, element.center.x - element.radius)
                min_y = min(min_y, element.center.y - element.radius)
                max_x = max(max_x, element.center.x + element.radius)
                max_y = max(max_y, element.center.y + element.radius)
            elif isinstance(element, Arc):
                # 簡易的に円全体の境界を使用
                min_x = min(min_x, element.center.x - element.radius)
                min_y = min(min_y, element.center.y - element.radius)
                max_x = max(max_x, element.center.x + element.radius)
                max_y = max(max_y, element.center.y + element.radius)
            elif isinstance(element, Polyline):
                for p in element.points:
                    min_x = min(min_x, p.x)
                    min_y = min(min_y, p.y)
                    max_x = max(max_x, p.x)
                    max_y = max(max_y, p.y)
            elif isinstance(element, Text):
                min_x = min(min_x, element.position.x)
                min_y = min(min_y, element.position.y)
                max_x = max(max_x, element.position.x)
                max_y = max(max_y, element.position.y)
            elif isinstance(element, Point):
                min_x = min(min_x, element.x)
                min_y = min(min_y, element.y)
                max_x = max(max_x, element.x)
                max_y = max(max_y, element.y)
        
        # マージンを追加
        width = max_x - min_x
        height = max_y - min_y
        margin = max(width, height) * margin_ratio
        
        xlim = (min_x - margin, max_x + margin)
        ylim = (min_y - margin, max_y + margin)
        
        return (xlim, ylim)