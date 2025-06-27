from typing import Tuple


def compute_fit_scale(
    drawing_width_mm: float,
    drawing_height_mm: float,
    available_width_mm: float,
    available_height_mm: float,
    base_scale_factor: float,
    fit_margin_ratio: float = 0.95,
    mode_priority: str = "width",
) -> Tuple[float, float, float]:
    """用紙に合わせた実効スケール係数を計算するユーティリティ

    Args:
        drawing_width_mm: 図面実寸幅 (mm)
        drawing_height_mm: 図面実寸高さ (mm)
        available_width_mm: 用紙の利用可能幅 (mm)
        available_height_mm: 用紙の利用可能高さ (mm)
        base_scale_factor: 指定 CAD スケール (例 1:100 → 0.01)
        fit_margin_ratio: フィット後に確保する余裕率 (0.95 = 5% 余白)
        mode_priority: "width" または "height"。優先して 90% 以上使いたい方向。

    Returns:
        (effective_scale, display_width_mm, display_height_mm)
    """
    # 最初に CAD スケールを適用したサイズ
    scaled_w = drawing_width_mm * base_scale_factor
    scaled_h = drawing_height_mm * base_scale_factor

    # 初期状態で領域に収まらない場合はそのまま (拡大禁止)
    if scaled_w > available_width_mm or scaled_h > available_height_mm:
        return base_scale_factor, scaled_w, scaled_h

    # 拡大係数を計算
    if mode_priority == "height":
        zoom = available_height_mm / scaled_h
    else:
        zoom = available_width_mm / scaled_w

    # 高さオーバーをチェック
    if scaled_h * zoom > available_height_mm:
        zoom = available_height_mm / scaled_h

    # 少し余裕を残す
    zoom *= fit_margin_ratio

    effective_scale = base_scale_factor * zoom
    return effective_scale, scaled_w * zoom, scaled_h * zoom 