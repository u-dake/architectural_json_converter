"""
Test cases for DXF scale detection and paper space coordinate handling
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.engines.safe_dxf_converter import SafeDXFConverter


class TestDXFScaleDetection:
    
    def setup_method(self):
        self.converter = SafeDXFConverter()
    
    def test_is_paper_space_coordinates_a3_landscape(self):
        """A3横向き (420×297) のペーパー空間座標を検出"""
        assert self.converter._is_paper_space_coordinates(420, 297) == True
    
    def test_is_paper_space_coordinates_a3_portrait(self):
        """A3縦向き (297×420) のペーパー空間座標を検出"""
        assert self.converter._is_paper_space_coordinates(297, 420) == True
    
    def test_is_paper_space_coordinates_a4_landscape(self):
        """A4横向き (297×210) のペーパー空間座標を検出"""
        assert self.converter._is_paper_space_coordinates(297, 210) == True
    
    def test_is_paper_space_coordinates_a4_portrait(self):
        """A4縦向き (210×297) のペーパー空間座標を検出"""
        assert self.converter._is_paper_space_coordinates(210, 297) == True
    
    def test_is_paper_space_coordinates_with_tolerance(self):
        """許容誤差内でのペーパー空間座標を検出"""
        # A3 (420×297) から±30mmの誤差
        assert self.converter._is_paper_space_coordinates(390, 280) == True
        assert self.converter._is_paper_space_coordinates(450, 320) == True
    
    def test_is_paper_space_coordinates_boundary_case(self):
        """境界値でのペーパー空間座標検出"""
        # A3 (420×297) から±50mmの境界値
        assert self.converter._is_paper_space_coordinates(370, 247) == True  # -50mm
        assert self.converter._is_paper_space_coordinates(470, 347) == True  # +50mm
        
        # 許容誤差を超える場合
        assert self.converter._is_paper_space_coordinates(360, 240) == False  # -60mm
        assert self.converter._is_paper_space_coordinates(480, 360) == False  # +60mm
    
    def test_is_paper_space_coordinates_model_space(self):
        """モデル空間座標（大きなサイズ）は検出しない"""
        assert self.converter._is_paper_space_coordinates(10000, 8000) == False
        assert self.converter._is_paper_space_coordinates(1000, 800) == False
        assert self.converter._is_paper_space_coordinates(100, 80) == False
    
    def test_estimate_raw_height_empty_model(self):
        """空のモデル空間では高さ0を返す"""
        mock_doc = Mock()
        mock_doc.modelspace.return_value = []
        
        height = self.converter._estimate_raw_height(mock_doc)
        assert height == 0.0
    
    def test_estimate_raw_height_with_line(self):
        """LINE エンティティから高さを計算"""
        mock_doc = Mock()
        mock_line = Mock()
        mock_line.dxftype.return_value = 'LINE'
        mock_line.dxf.start.y = 10.0
        mock_line.dxf.end.y = 50.0
        
        mock_doc.modelspace.return_value = [mock_line]
        
        height = self.converter._estimate_raw_height(mock_doc)
        assert height == 40.0
    
    def test_estimate_raw_height_with_circle(self):
        """CIRCLE エンティティから高さを計算"""
        mock_doc = Mock()
        mock_circle = Mock()
        mock_circle.dxftype.return_value = 'CIRCLE'
        mock_circle.dxf.center.y = 100.0
        mock_circle.dxf.radius = 25.0
        
        mock_doc.modelspace.return_value = [mock_circle]
        
        height = self.converter._estimate_raw_height(mock_doc)
        assert height == 50.0  # (100+25) - (100-25) = 50
    
    def test_scale_detection_integration_paper_space(self):
        """ペーパー空間座標の場合、スケール補正をスキップ"""
        # A3サイズの座標を持つモックを作成
        mock_doc = Mock()
        mock_doc.units = 4  # millimeter
        
        # A3サイズ (385×154) に近い座標を持つエンティティ
        mock_line = Mock()
        mock_line.dxftype.return_value = 'LINE'
        mock_line.dxf.start.x = 12.0
        mock_line.dxf.start.y = 12.0
        mock_line.dxf.end.x = 397.8
        mock_line.dxf.end.y = 167.0
        
        mock_doc.modelspace.return_value = [mock_line]
        mock_doc.layers = []
        mock_doc.blocks = []
        mock_doc.layouts = []
        
        # _detect_unit_factor をモック
        self.converter._detect_unit_factor = Mock(return_value=1.0)
        
        # convert_entity をモック（実際の変換処理はスキップ）
        self.converter.convert_entity = Mock(return_value=None)
        
        # テスト実行
        result = self.converter.convert_dxf_file.__wrapped__(self.converter, "dummy_path.dxf", False)
        
        # アサーション
        assert result.metadata["coordinate_type"] == "paper_space"
        assert result.metadata["unit_factor_mm"] == 1.0  # スケール補正なし
        assert abs(result.metadata["raw_dimensions"]["width"] - 385.8) < 1
        assert abs(result.metadata["raw_dimensions"]["height"] - 155.0) < 1
    
    def test_scale_detection_integration_model_space(self):
        """モデル空間座標の場合、従来のスケール補正を適用"""
        # 小さな座標 (cm単位想定) を持つモックを作成
        mock_doc = Mock()
        mock_doc.units = 0  # unknown/none
        
        # 小さな座標を持つエンティティ
        mock_line = Mock()
        mock_line.dxftype.return_value = 'LINE'
        mock_line.dxf.start.x = 0.0
        mock_line.dxf.start.y = 0.0
        mock_line.dxf.end.x = 100.0  # 100cm = 1000mm
        mock_line.dxf.end.y = 80.0   # 80cm = 800mm
        
        mock_doc.modelspace.return_value = [mock_line]
        mock_doc.layers = []
        mock_doc.blocks = []
        mock_doc.layouts = []
        
        # _detect_unit_factor をモック
        self.converter._detect_unit_factor = Mock(return_value=1.0)
        
        # convert_entity をモック
        self.converter.convert_entity = Mock(return_value=None)
        
        # テスト実行
        result = self.converter.convert_dxf_file.__wrapped__(self.converter, "dummy_path.dxf", False)
        
        # アサーション
        assert result.metadata["coordinate_type"] == "model_space"
        assert result.metadata["unit_factor_mm"] == 10.0  # cm→mm 補正
        assert result.metadata["raw_dimensions"]["width"] == 100.0
        assert result.metadata["raw_dimensions"]["height"] == 80.0