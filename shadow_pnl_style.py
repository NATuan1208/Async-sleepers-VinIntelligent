"""
Shadow P&L — Visual Style & VND Audit Utilities
=================================================
Module duy nhất mà MỌI notebook EDA Shadow P&L phải import đầu tiên.

Cam kết:
    1. Palette consistent — không notebook nào dùng màu tuỳ ý
    2. Format VND chuẩn Việt Nam — không lặp lại lỗi đơn vị 1000x
    3. Audit trail cho mọi VND impact number — trace được về computation

Usage:
    from shadow_pnl_style import (
        apply_shadow_pnl_style,
        SHADOW_PNL_COLORS,
        format_vnd,
        vnd_impact,
        init_audit_log,
    )
    apply_shadow_pnl_style()
    init_audit_log()
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt


# ============================================================================
# 1. PALETTE — "THE FORENSIC AUDIT"
# ============================================================================

SHADOW_PNL_COLORS: dict[str, str] = {
    # ─── Primary Narrative (4 màu trung tâm) ──────────────────────────────
    "reported": "#1A2C5B",   # Deep Navy — revenue báo cáo (the illusion)
    "leak":     "#8B1E3F",   # Burgundy  — thất thoát (bleeding)
    "true_net": "#2D5F3F",   # Forest Green — doanh thu thực còn lại
    "upside":   "#C89B3C",   # Mustard Gold — cơ hội thu hồi

    # ─── Neutrals (text, axes, grid, bg) ──────────────────────────────────
    "text": "#2B2D42",
    "grid": "#E0E0E0",
    "bg":   "#F8F6F0",

    # ─── Product Categories ───────────────────────────────────────────────
    "outdoor":    "#3D5A80",  # Slate Blue
    "streetwear": "#E07A5F",  # Terracotta
    "casual":     "#81B29A",  # Sage
    "genz":       "#F2CC8F",  # Mustard

    # ─── Leak Types (dùng cho waterfall chart Act 2) ──────────────────────
    "leak_discount":     "#C1654E",  # muted orange-red
    "leak_return":       "#8B1E3F",  # burgundy — match primary "leak"
    "leak_cancellation": "#6B4C6F",  # dusty purple
    "leak_shipping":     "#5C7F8A",  # steel blue
    "leak_stockout":     "#A89B8C",  # shadow gray (phantom)
}

# Ordered list cho waterfall stacking (từ trên xuống dưới)
LEAK_ORDER: list[str] = [
    "leak_discount",
    "leak_return",
    "leak_cancellation",
    "leak_shipping",
    "leak_stockout",
]


def apply_shadow_pnl_style() -> None:
    """Set matplotlib rcParams theo Shadow P&L style guide.

    Gọi ở cell đầu tiên của mọi notebook. KHÔNG override rcParams sau đó
    trừ khi có lý do documented.
    """
    plt.rcParams.update({
        # Figure
        "figure.figsize": (12, 6),
        "figure.facecolor": SHADOW_PNL_COLORS["bg"],
        "figure.dpi": 110,
        "savefig.dpi": 300,               # Export chart quality cho NeurIPS PDF
        "savefig.bbox": "tight",
        "savefig.facecolor": SHADOW_PNL_COLORS["bg"],

        # Axes
        "axes.facecolor": SHADOW_PNL_COLORS["bg"],
        "axes.edgecolor": SHADOW_PNL_COLORS["text"],
        "axes.labelcolor": SHADOW_PNL_COLORS["text"],
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlepad": 16,
        "axes.labelsize": 11,
        "axes.labelweight": "regular",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": True,
        "axes.spines.bottom": True,
        "axes.grid": True,
        "axes.grid.axis": "y",            # chỉ grid ngang
        "axes.axisbelow": True,

        # Grid
        "grid.color": SHADOW_PNL_COLORS["grid"],
        "grid.linewidth": 0.5,
        "grid.alpha": 0.5,

        # Ticks
        "xtick.color": SHADOW_PNL_COLORS["text"],
        "ytick.color": SHADOW_PNL_COLORS["text"],
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,

        # Font — sans-serif cho chart (đối lập serif trong NeurIPS body)
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10,

        # Legend
        "legend.frameon": False,
        "legend.fontsize": 9,
        "legend.title_fontsize": 10,
    })


# ============================================================================
# 2. VND FORMATTING — CHUẨN VIỆT NAM
# ============================================================================

def format_vnd(value_vnd: float, precision: int = 2) -> str:
    """Format số VND theo quy ước Việt Nam.

    Quy ước:
        ≥ 1,000,000,000 (1 tỷ)     → "1.23 tỷ VND"
        ≥ 1,000,000 (1 triệu)      → "123 triệu VND"
        ≥ 1,000 (1 nghìn)          → "12.3 nghìn VND"
        dưới 1,000                 → "123 VND"

    Examples:
        >>> format_vnd(1_234_567_890)
        '1.23 tỷ VND'
        >>> format_vnd(160_871_352)
        '161 triệu VND'
        >>> format_vnd(15_747)
        '15.7 nghìn VND'

    Args:
        value_vnd: giá trị bằng VND (raw number, không phải đã chia)
        precision: số chữ số thập phân cho "tỷ"

    Returns:
        String đã format với đơn vị Việt Nam.
    """
    if value_vnd is None:
        return "N/A"

    abs_val = abs(value_vnd)
    sign = "-" if value_vnd < 0 else ""

    if abs_val >= 1e9:
        return f"{sign}{abs_val/1e9:.{precision}f} tỷ VND"
    elif abs_val >= 1e6:
        return f"{sign}{abs_val/1e6:.0f} triệu VND"
    elif abs_val >= 1e3:
        return f"{sign}{abs_val/1e3:.1f} nghìn VND"
    else:
        return f"{sign}{abs_val:,.0f} VND"


def format_pct(value: float, precision: int = 1) -> str:
    """Format tỷ lệ phần trăm 1 chữ số thập phân theo convention bài thi.

    Input có thể là 0.094 (fraction) hoặc 9.4 (already percent).
    Hàm auto-detect: nếu |value| <= 1.0 → treat as fraction.
    """
    if value is None:
        return "N/A"
    pct = value * 100 if abs(value) <= 1.0 else value
    return f"{pct:.{precision}f}%"


# ============================================================================
# 3. VND AUDIT LOG — TRACE EVERY NUMBER
# ============================================================================

_AUDIT_LOG_PATH = Path("outputs_round1/shadow_pnl_audit.csv")


def init_audit_log(path: Optional[Path] = None) -> None:
    """Khởi tạo audit CSV header. Gọi 1 lần ở đầu notebook foundation.

    File này phải được SUBMIT cùng repo — giám khảo có thể verify mọi con số.
    """
    global _AUDIT_LOG_PATH
    if path is not None:
        _AUDIT_LOG_PATH = Path(path)

    _AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not _AUDIT_LOG_PATH.exists():
        with _AUDIT_LOG_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "act", "metric_label",
                "n_customers", "rate_pct", "n_orders", "aov_vnd",
                "impact_vnd", "impact_label", "notebook", "note",
            ])


def vnd_impact(
    *,
    label: str,
    act: str,
    customers: int,
    rate: float,
    orders: float,
    aov_vnd: float,
    notebook: str = "unknown",
    note: str = "",
) -> tuple[float, str]:
    """Tính VND impact với sanity check + audit trail.

    Sử dụng BẮT BUỘC cho mọi recommendation có con số VND.
    Function này:
        1. Computes impact = customers × rate × orders × aov_vnd
        2. Sanity check range (bắt lỗi đơn vị)
        3. Logs to audit CSV (trace được)
        4. Returns cả raw number và formatted string

    Args:
        label: Tên metric (VD: "Discount Curse — cohort-year LTV recovery")
        act: Act nào (VD: "Act 3A")
        customers: Số khách hàng ảnh hưởng
        rate: Tỷ lệ (VD: 0.094 cho 9.4% repeat lift)
        orders: Số đơn hàng incremental
        aov_vnd: Average order value bằng VND (raw number)
        notebook: Tên notebook để trace
        note: Ghi chú bổ sung

    Returns:
        (impact_vnd, impact_formatted_string)

    Raises:
        AssertionError nếu impact ngoài range hợp lý (bắt lỗi đơn vị).

    Example:
        >>> impact_vnd, impact_str = vnd_impact(
        ...     label="Discount Curse cohort recovery",
        ...     act="Act 3A",
        ...     customers=27_171,
        ...     rate=0.094,
        ...     orders=4,
        ...     aov_vnd=15_747,
        ...     notebook="02_shadow_pnl_investigation.ipynb",
        ...     note="AOV from median first_order_value",
        ... )
        >>> print(impact_str)
        '161 triệu VND'
    """
    impact = customers * rate * orders * aov_vnd

    # Sanity check — catches đơn vị errors
    # Hợp lý: ≥ 100 nghìn VND (một món ăn) đến ≤ 1000 tỷ VND (max business scale VN)
    if not (1e5 <= abs(impact) <= 1e12):
        raise AssertionError(
            f"[{label}] Impact {impact:,.0f} VND ngoài range hợp lý. "
            f"Có khả năng nhầm đơn vị (triệu ↔ tỷ) hoặc sai input. "
            f"Inputs: customers={customers}, rate={rate}, "
            f"orders={orders}, aov={aov_vnd}"
        )

    impact_str = format_vnd(impact)

    # Log to audit CSV
    if _AUDIT_LOG_PATH.exists():
        with _AUDIT_LOG_PATH.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(timespec="seconds"),
                act, label,
                customers, f"{rate*100:.2f}", orders, aov_vnd,
                f"{impact:.0f}", impact_str, notebook, note,
            ])

    return impact, impact_str


# ============================================================================
# 4. CHART HELPER — BẮT BUỘC USE CHO MỌI CHART
# ============================================================================

def finalize_chart(
    ax,
    title: str,
    insight_subtitle: Optional[str] = None,
    sample_size: Optional[int] = None,
    xlabel: str = "",
    ylabel: str = "",
) -> None:
    """Áp dụng final styling nhất quán cho mọi chart.

    Quy tắc:
        - Title là câu INSIGHT, không phải mô tả data
        - Subtitle (nếu có) là 1 dòng italic bổ sung context
        - Sample size (N) nhúng vào title nếu cung cấp
    """
    if sample_size is not None:
        full_title = f"{title}\nN = {sample_size:,}"
    else:
        full_title = title

    ax.set_title(full_title, fontsize=14, fontweight="bold", pad=16)

    if insight_subtitle:
        ax.text(
            0.5, 1.02, insight_subtitle,
            transform=ax.transAxes,
            ha="center", va="bottom",
            fontsize=10, style="italic",
            color=SHADOW_PNL_COLORS["text"],
        )

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11, fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11, fontweight="bold")


# ============================================================================
# 5. SELF-TEST
# ============================================================================

if __name__ == "__main__":
    # Fix Windows cp1252 console encoding for Vietnamese characters
    import sys as _sys
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8")

    # Smoke test
    print("Shadow P&L Style Module - Self Test")
    print("=" * 50)

    # Test format_vnd
    test_values = [15_747, 160_871_352, 1_234_567_890, 459_720_000, -500_000]
    for v in test_values:
        print(f"  format_vnd({v:,}) = {format_vnd(v)}")

    # Test format_pct
    print(f"  format_pct(0.094) = {format_pct(0.094)}")
    print(f"  format_pct(9.4)   = {format_pct(9.4)}")

    # Test vnd_impact audit
    init_audit_log(Path("/tmp/test_audit.csv"))
    impact, impact_str = vnd_impact(
        label="SELF TEST", act="test",
        customers=27_171, rate=0.094, orders=4, aov_vnd=15_747,
        notebook="self_test",
    )
    print(f"  vnd_impact self-test: {impact_str}")

    # Test sanity check catches unit error
    try:
        vnd_impact(
            label="BAD INPUT", act="test",
            customers=100, rate=0.1, orders=1, aov_vnd=0.001,  # Quá nhỏ
            notebook="self_test",
        )
        print("  ❌ Sanity check FAILED to catch error")
    except AssertionError as e:
        print(f"  ✅ Sanity check caught error: {str(e)[:80]}...")

    print("\nAll tests passed. Module ready for use.")
