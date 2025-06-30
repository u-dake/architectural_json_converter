"""
Matplotlib Visualization System

matplotlib を使用した図面差分の可視化
"""

from typing import List, Dict, Any, Optional, Tuple
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import LineCollection
import numpy as np
import os
from pathlib import Path

# 日本語フォントの設定（macOSで利用可能なフォント優先）
matplotlib.rcParams['pdf.fonttype'] = 42  # PDFのフォントをTrueTypeで埋め込む
matplotlib.rcParams['font.family'] = ['Hiragino Sans', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策

from data_structures.geometry_data import (
    GeometryData, DifferenceResult, GeometryElement,
    LineElement, CircleElement, ArcElement, PolylineElement,
    TextElement, BlockElement, ArchitecturalType
)


class ArchitecturalPlotter:
    """建築図面プロッター"""
    
    def __init__(self, figsize: Tuple[float, float] = (16, 12), dpi: int = 300):
        self.figsize = figsize
        self.dpi = dpi
        
        # 色設定
        self.colors = {
            'site_elements': '#0066CC',      # 敷地図要素（青）
            'new_elements': '#FF3300',       # 新規要素（赤）
            'walls': '#FF6600',              # 壁（オレンジ）
            'openings': '#00CC66',           # 開口部（緑）
            'fixtures': '#9900CC',           # 設備（紫）
            'text': '#666666',               # テキスト（灰色）
            'removed_elements': '#CCCCCC'    # 削除要素（薄灰色）
        }
        
        # スタイル設定
        self.styles = {
            'line_width': 1.5,
            'text_size': 8,
            'marker_size': 6,
            'alpha': 0.8
        }
    
    def plot_geometry_element(self, ax: plt.Axes, element: GeometryElement, 
                             color: str, alpha: float = 0.8) -> None:
        """
        幾何要素を描画
        
        Args:
            ax: matplotlib Axes
            element: 描画する要素
            color: 色
            alpha: 透明度
        """
        if isinstance(element, LineElement):
            ax.plot([element.start.x, element.end.x],
                   [element.start.y, element.end.y],
                   color=color, linewidth=self.styles['line_width'], alpha=alpha)
                   
        elif isinstance(element, CircleElement):
            circle = plt.Circle((element.center.x, element.center.y),
                               element.radius, fill=False, color=color,
                               linewidth=self.styles['line_width'], alpha=alpha)
            ax.add_patch(circle)
            
        elif isinstance(element, ArcElement):
            # 円弧を線分で近似
            angles = np.linspace(element.start_angle, element.end_angle, 20)
            x_coords = element.center.x + element.radius * np.cos(angles)
            y_coords = element.center.y + element.radius * np.sin(angles)
            ax.plot(x_coords, y_coords, color=color,
                   linewidth=self.styles['line_width'], alpha=alpha)
                   
        elif isinstance(element, PolylineElement):
            if len(element.vertices) < 2:
                return
            x_coords = [v.x for v in element.vertices]
            y_coords = [v.y for v in element.vertices]
            if element.is_closed:
                x_coords.append(element.vertices[0].x)
                y_coords.append(element.vertices[0].y)
            ax.plot(x_coords, y_coords, color=color,
                   linewidth=self.styles['line_width'], alpha=alpha)
                   
        elif isinstance(element, TextElement):
            ax.text(element.position.x, element.position.y, element.text,
                   fontsize=self.styles['text_size'], color=color,
                   alpha=alpha, rotation=np.degrees(element.rotation))
                   
        elif isinstance(element, BlockElement):
            ax.plot(element.position.x, element.position.y, 'o',
                   color=color, markersize=self.styles['marker_size'], alpha=alpha)
    
    def plot_geometry_data(self, ax: plt.Axes, geometry_data: GeometryData,
                          base_color: str = '#0066CC', show_legend: bool = True) -> None:
        """
        統一データ構造を描画
        
        Args:
            ax: matplotlib Axes
            geometry_data: 描画するデータ
            base_color: 基本色
            show_legend: 凡例表示フラグ
        """
        element_counts = {}
        
        for element in geometry_data.elements:
            # 建築要素タイプ別に色分け
            if element.architectural_type == ArchitecturalType.WALL:
                color = self.colors['walls']
                label = '壁'
            elif element.architectural_type in [ArchitecturalType.DOOR, ArchitecturalType.WINDOW, ArchitecturalType.OPENING]:
                color = self.colors['openings']
                label = '開口部'
            elif element.architectural_type == ArchitecturalType.FIXTURE:
                color = self.colors['fixtures']
                label = '設備'
            elif element.architectural_type == ArchitecturalType.TEXT_LABEL:
                color = self.colors['text']
                label = 'テキスト'
            else:
                color = base_color
                label = 'その他'
            
            self.plot_geometry_element(ax, element, color)
            
            # 凡例用のカウント
            if label not in element_counts:
                element_counts[label] = 0
            element_counts[label] += 1
        
        if show_legend and element_counts:
            legend_elements = []
            for label, count in element_counts.items():
                if label == '壁':
                    color = self.colors['walls']
                elif label == '開口部':
                    color = self.colors['openings']
                elif label == '設備':
                    color = self.colors['fixtures']
                elif label == 'テキスト':
                    color = self.colors['text']
                else:
                    color = base_color
                
                legend_elements.append(plt.Line2D([0], [0], color=color, lw=2,
                                                 label=f'{label} ({count})'))
            
            ax.legend(handles=legend_elements, loc='upper right')
    
    def plot_difference_result(self, difference_result: DifferenceResult,
                              output_path: str = "output/difference_visualization.png") -> str:
        """
        差分解析結果を可視化
        
        Args:
            difference_result: 差分解析結果
            output_path: 出力ファイルパス
            
        Returns:
            保存されたファイルパス
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize, dpi=self.dpi)
        
        # 共通の境界設定（全要素から計算）
        all_elements = []
        all_elements.extend(difference_result.site_only.elements)
        all_elements.extend(difference_result.site_with_plan.elements)
        all_elements.extend(difference_result.new_elements)
        
        if all_elements:
            bounds = []
            for elem in all_elements:
                try:
                    bounds.append(elem.get_bounding_box())
                except NotImplementedError:
                    continue
            
            if bounds:
                min_x = min(b.min_x for b in bounds)
                min_y = min(b.min_y for b in bounds)
                max_x = max(b.max_x for b in bounds)
                max_y = max(b.max_y for b in bounds)
                
                margin = max((max_x - min_x), (max_y - min_y)) * 0.1
                xlim = (min_x - margin, max_x + margin)
                ylim = (min_y - margin, max_y + margin)
            else:
                xlim = (-1000, 1000)
                ylim = (-1000, 1000)
        else:
            xlim = (-1000, 1000)
            ylim = (-1000, 1000)
        
        # 1. 敷地図のみ
        ax1.set_title('敷地図のみ', fontsize=14, fontweight='bold')
        self.plot_geometry_data(ax1, difference_result.site_only,
                               base_color=self.colors['site_elements'])
        ax1.set_xlim(xlim)
        ax1.set_ylim(ylim)
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        
        # 2. 間取り付き
        ax2.set_title('間取り付き', fontsize=14, fontweight='bold')
        self.plot_geometry_data(ax2, difference_result.site_with_plan,
                               base_color=self.colors['site_elements'])
        ax2.set_xlim(xlim)
        ax2.set_ylim(ylim)
        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        
        # 3. 差分のみ（新規要素）
        ax3.set_title(f'新規要素のみ ({len(difference_result.new_elements)}個)',
                     fontsize=14, fontweight='bold')
        for element in difference_result.new_elements:
            if element.architectural_type == ArchitecturalType.WALL:
                color = self.colors['walls']
            elif element.architectural_type in [ArchitecturalType.DOOR, ArchitecturalType.WINDOW, ArchitecturalType.OPENING]:
                color = self.colors['openings']
            elif element.architectural_type == ArchitecturalType.FIXTURE:
                color = self.colors['fixtures']
            else:
                color = self.colors['new_elements']
            
            self.plot_geometry_element(ax3, element, color)
        
        ax3.set_xlim(xlim)
        ax3.set_ylim(ylim)
        ax3.set_aspect('equal')
        ax3.grid(True, alpha=0.3)
        
        # 4. 重ね合わせ表示
        ax4.set_title('重ね合わせ（敷地図+新規要素）', fontsize=14, fontweight='bold')
        
        # 敷地図を薄く表示
        for element in difference_result.site_only.elements:
            self.plot_geometry_element(ax4, element, self.colors['site_elements'], alpha=0.3)
        
        # 新規要素を強調表示
        for element in difference_result.new_elements:
            if element.architectural_type == ArchitecturalType.WALL:
                color = self.colors['walls']
            elif element.architectural_type in [ArchitecturalType.DOOR, ArchitecturalType.WINDOW, ArchitecturalType.OPENING]:
                color = self.colors['openings']
            elif element.architectural_type == ArchitecturalType.FIXTURE:
                color = self.colors['fixtures']
            else:
                color = self.colors['new_elements']
            
            self.plot_geometry_element(ax4, element, color, alpha=1.0)
        
        ax4.set_xlim(xlim)
        ax4.set_ylim(ylim)
        ax4.set_aspect('equal')
        ax4.grid(True, alpha=0.3)
        
        # 全体のタイトル
        fig.suptitle('建築図面差分解析結果', fontsize=16, fontweight='bold')
        
        # レイアウト調整
        plt.tight_layout()
        
        # 保存
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        print(f"差分可視化を保存しました: {output_path}")
        return output_path
    
    def plot_architectural_analysis(self, difference_result: DifferenceResult,
                                   output_path: str = "output/architectural_analysis.png") -> str:
        """
        建築要素別の解析結果を可視化
        
        Args:
            difference_result: 差分解析結果
            output_path: 出力ファイルパス
            
        Returns:
            保存されたファイルパス
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize, dpi=self.dpi)
        
        # 共通の境界設定
        all_elements = difference_result.new_elements
        if all_elements:
            # 境界ボックスを安全に取得
            bounds = []
            for elem in all_elements:
                try:
                    bounds.append(elem.get_bounding_box())
                except NotImplementedError:
                    # 実装されていない場合はスキップ
                    continue
            
            if bounds:
                min_x = min(b.min_x for b in bounds)
                min_y = min(b.min_y for b in bounds)
                max_x = max(b.max_x for b in bounds)
                max_y = max(b.max_y for b in bounds)
                
                margin = max((max_x - min_x), (max_y - min_y)) * 0.1
                xlim = (min_x - margin, max_x + margin)
                ylim = (min_y - margin, max_y + margin)
            else:
                xlim = (-1000, 1000)
                ylim = (-1000, 1000)
        else:
            xlim = (-1000, 1000)
            ylim = (-1000, 1000)
        
        # 1. 壁の分析
        ax1.set_title(f'検出された壁 ({len(difference_result.walls)}個)',
                     fontsize=14, fontweight='bold')
        for wall in difference_result.walls:
            self.plot_geometry_element(ax1, wall, self.colors['walls'])
        ax1.set_xlim(xlim)
        ax1.set_ylim(ylim)
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        
        # 2. 開口部の分析
        ax2.set_title(f'検出された開口部 ({len(difference_result.openings)}個)',
                     fontsize=14, fontweight='bold')
        for opening in difference_result.openings:
            self.plot_geometry_element(ax2, opening, self.colors['openings'])
        ax2.set_xlim(xlim)
        ax2.set_ylim(ylim)
        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        
        # 3. 設備の分析
        ax3.set_title(f'検出された設備 ({len(difference_result.fixtures)}個)',
                     fontsize=14, fontweight='bold')
        for fixture in difference_result.fixtures:
            self.plot_geometry_element(ax3, fixture, self.colors['fixtures'])
        ax3.set_xlim(xlim)
        ax3.set_ylim(ylim)
        ax3.set_aspect('equal')
        ax3.grid(True, alpha=0.3)
        
        # 4. 統計情報（テキスト表示）
        ax4.set_title('解析統計', fontsize=14, fontweight='bold')
        ax4.axis('off')
        
        stats = difference_result.get_statistics()
        stats_text = []
        stats_text.append(f"総新規要素数: {stats['total_new_elements']}")
        stats_text.append(f"検出された壁: {stats['walls_detected']}")
        stats_text.append(f"検出された開口部: {stats['openings_detected']}")
        stats_text.append(f"検出された設備: {stats['fixtures_detected']}")
        stats_text.append(f"削除要素: {stats['removed_elements']}")
        
        # メタデータから追加情報
        metadata = difference_result.analysis_metadata
        if 'processing_time' in metadata:
            stats_text.append(f"処理時間: {metadata['processing_time']:.2f}秒")
        
        if 'classification_confidence' in metadata:
            conf = metadata['classification_confidence']
            stats_text.append("")
            stats_text.append("分類信頼度:")
            if conf['walls'] > 0:
                stats_text.append(f"  壁: {conf['walls']:.2f}")
            if conf['openings'] > 0:
                stats_text.append(f"  開口部: {conf['openings']:.2f}")
            if conf['fixtures'] > 0:
                stats_text.append(f"  設備: {conf['fixtures']:.2f}")
        
        y_pos = 0.9
        for line in stats_text:
            ax4.text(0.05, y_pos, line, transform=ax4.transAxes,
                    fontsize=12, verticalalignment='top')
            y_pos -= 0.08
        
        # 全体のタイトル
        fig.suptitle('建築要素別解析結果', fontsize=16, fontweight='bold')
        
        # レイアウト調整
        plt.tight_layout()
        
        # 保存
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 拡張子に応じて保存形式を選択
        if output_path.lower().endswith('.pdf'):
            plt.savefig(output_path, format='pdf', dpi=self.dpi, bbox_inches='tight')
        else:
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        print(f"建築要素解析を保存しました: {output_path}")
        return output_path

    def save_geometry_as_pdf(self, geometry_data: GeometryData, output_path: str) -> str:
        """
        単一のGeometryDataをPDFとして保存

        Args:
            geometry_data: 描画するデータ
            output_path: 出力PDFファイルパス

        Returns:
            保存されたファイルパス
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # 境界設定
        bounds = [elem.get_bounding_box() for elem in geometry_data.elements if hasattr(elem, 'get_bounding_box')]
        if bounds:
            min_x = min(b.min_x for b in bounds)
            min_y = min(b.min_y for b in bounds)
            max_x = max(b.max_x for b in bounds)
            max_y = max(b.max_y for b in bounds)
            margin = max((max_x - min_x), (max_y - min_y)) * 0.05
            ax.set_xlim(min_x - margin, max_x + margin)
            ax.set_ylim(min_y - margin, max_y + margin)
        
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        # タイトルを設定
        ax.set_title(f"図面: {Path(output_path).stem}", fontsize=14, fontweight='bold')

        # データの描画
        self.plot_geometry_data(ax, geometry_data, show_legend=True)

        # 保存
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plt.savefig(output_path, format='pdf', dpi=self.dpi, bbox_inches='tight')
        plt.close()

        print(f"ジオメトリをPDFとして保存しました: {output_path}")
        return output_path


def main():
    """テスト用メイン関数"""
    import sys
    import json
    from src.data_structures import DifferenceResult
    
    if len(sys.argv) > 1:
        result_file = sys.argv[1]
        
        try:
            print(f"差分解析結果を読み込み中: {result_file}")
            
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # DifferenceResultオブジェクトを再構築
            result = DifferenceResult.model_validate(result_data)
            
            print("可視化を生成中...")
            plotter = ArchitecturalPlotter()
            
            # 差分可視化
            viz_path = plotter.plot_difference_result(result)
            
            # 建築要素解析
            analysis_path = plotter.plot_architectural_analysis(result)
            
            print(f"可視化完了:")
            print(f"  差分可視化: {viz_path}")
            print(f"  建築要素解析: {analysis_path}")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("使用方法: python matplotlib_visualizer.py <差分解析結果JSONファイル>")
        print("例: python matplotlib_visualizer.py data/difference_analysis_result.json")


if __name__ == "__main__":
    main()