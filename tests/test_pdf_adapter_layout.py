from __future__ import annotations

from backend.adapters.pdf import _layout_reading_order


def _block(x0: float, y0: float, x1: float, y1: float, text: str) -> tuple:
    return (x0, y0, x1, y1, text, 0, 0)


def _texts(ordered: list[tuple[int, tuple]]) -> list[str]:
    return [str(block[4]) for _, block in ordered]


def test_two_column_manual_is_column_major_not_row_interleaved() -> None:
    blocks = [
        _block(40, 70, 290, 100, "left problem"),
        _block(320, 70, 570, 100, "right problem"),
        _block(40, 120, 290, 150, "left cause"),
        _block(320, 120, 570, 150, "right cause"),
        _block(40, 170, 290, 200, "left action"),
        _block(320, 170, 570, 200, "right action"),
    ]

    assert _texts(_layout_reading_order(blocks, page_width=612, page_height=792)) == [
        "left problem",
        "left cause",
        "left action",
        "right problem",
        "right cause",
        "right action",
    ]


def test_full_width_heading_and_footer_keep_band_position() -> None:
    blocks = [
        _block(40, 20, 570, 40, "heading"),
        _block(40, 70, 290, 100, "left one"),
        _block(320, 70, 570, 100, "right one"),
        _block(40, 120, 290, 150, "left two"),
        _block(320, 120, 570, 150, "right two"),
        _block(40, 730, 570, 750, "footer"),
    ]

    assert _texts(_layout_reading_order(blocks, page_width=612, page_height=792)) == [
        "heading",
        "left one",
        "left two",
        "right one",
        "right two",
        "footer",
    ]


def test_single_column_falls_back_to_vertical_order() -> None:
    blocks = [
        _block(80, 160, 530, 190, "second"),
        _block(80, 80, 530, 110, "first"),
        _block(80, 240, 530, 270, "third"),
    ]

    assert _texts(_layout_reading_order(blocks, page_width=612, page_height=792)) == [
        "first",
        "second",
        "third",
    ]
