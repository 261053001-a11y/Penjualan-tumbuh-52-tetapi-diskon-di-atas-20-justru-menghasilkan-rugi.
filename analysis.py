"""
analysis.py
===========
Fungsi pengolahan data untuk dashboard (murni pandas, tanpa Streamlit),
sehingga bisa diuji terpisah dan dipakai ulang oleh app.py.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent / "data" / "superstore_clean.csv"

DISCOUNT_ORDER = ["Tanpa diskon", "1–20%", "21–40%", ">40%"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
         "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
BULAN_PANJANG = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
                 "Agustus", "September", "Oktober", "November", "Desember"]
WILAYAH = {"West": "Barat", "East": "Timur", "Central": "Tengah", "South": "Selatan"}


# ---------------------------------------------------------------- format angka
def _id_sep(text: str) -> str:
    """Ubah 1,234.5 -> 1.234,5 (format Indonesia)."""
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_money(x: float, short: bool = True) -> str:
    if x is None or pd.isna(x):
        return "–"
    sign = "−" if x < 0 else ""
    x = abs(x)
    if short and x >= 1e6:
        return f"{sign}US$ {_id_sep(f'{x / 1e6:,.2f}')} jt"
    if short and x >= 1e3:
        return f"{sign}US$ {_id_sep(f'{x / 1e3:,.1f}')} rb"
    return f"{sign}US$ {_id_sep(f'{x:,.0f}')}"


def fmt_pct(x: float, digits: int = 1) -> str:
    if x is None or pd.isna(x):
        return "–"
    sign = "−" if x < 0 else ""
    return sign + _id_sep(f"{abs(x) * 100:.{digits}f}") + "%"


def fmt_int(x: float) -> str:
    return _id_sep(f"{int(x):,}")


# ---------------------------------------------------------------- data & filter
def load_clean(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["order_date", "ship_date"],
                     dtype={"postal_code": "string"})
    df["discount_band"] = pd.Categorical(df["discount_band"],
                                         categories=DISCOUNT_ORDER, ordered=True)
    return df


def filter_data(df: pd.DataFrame, start, end, regions=None,
                categories=None, segments=None) -> pd.DataFrame:
    """Pilihan kosong pada filter kategori berarti 'semua'."""
    mask = df["order_date"].between(pd.Timestamp(start), pd.Timestamp(end))
    if regions:
        mask &= df["region"].isin(regions)
    if categories:
        mask &= df["category"].isin(categories)
    if segments:
        mask &= df["segment"].isin(segments)
    return df.loc[mask]


def previous_period(start, end) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Periode pembanding dengan panjang sama, tepat sebelum periode terpilih."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    span = end - start + pd.Timedelta(days=1)
    return start - span, start - pd.Timedelta(days=1)


# ---------------------------------------------------------------- agregasi
def compute_kpis(df: pd.DataFrame) -> dict:
    sales, profit = df["sales"].sum(), df["profit"].sum()
    return {
        "sales": sales,
        "profit": profit,
        "margin": profit / sales if sales else np.nan,
        "orders": df["order_id"].nunique(),
        "customers": df["customer_id"].nunique(),
    }


def pct_change(current: float, previous: float):
    if previous is None or pd.isna(previous) or previous == 0:
        return None
    return (current - previous) / abs(previous)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    m = (df.set_index("order_date")[["sales", "profit"]]
         .resample("MS").sum().reset_index())
    m["label"] = m["order_date"].apply(lambda d: f"{BULAN[d.month - 1]} {d.year}")
    return m


def subcategory_profit(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby(["sub_category", "category"], as_index=False)
         .agg(sales=("sales", "sum"), profit=("profit", "sum")))
    g["margin"] = g["profit"] / g["sales"]
    g["status"] = np.where(g["profit"] >= 0, "Untung", "Rugi")
    return g.sort_values("profit")


def segment_share(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("segment", as_index=False)["sales"].sum()
    g["share"] = g["sales"] / g["sales"].sum()
    return g.sort_values("sales", ascending=False)


def product_discount_profit(df: pd.DataFrame) -> pd.DataFrame:
    """Satu titik = satu produk: rata-rata diskon vs total laba."""
    return (df.groupby("product_id", as_index=False)
            .agg(product_name=("product_name", "first"),
                 category=("category", "first"),
                 avg_discount=("discount", "mean"),
                 sales=("sales", "sum"),
                 profit=("profit", "sum"),
                 transactions=("sales", "size")))


def discount_band_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby("discount_band", observed=False)
         .agg(transactions=("sales", "size"), sales=("sales", "sum"),
              profit=("profit", "sum"), loss_share=("is_loss", "mean"))
         .reset_index())
    g["margin"] = np.where(g["sales"] > 0, g["profit"] / g["sales"].replace(0, np.nan), np.nan)
    return g[g["transactions"] > 0]


def region_category_margin(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["region", "category"])[["sales", "profit"]].sum()
    g["margin"] = g["profit"] / g["sales"]
    pivot = g["margin"].unstack("category")
    order = (df.groupby("region")["profit"].sum() / df.groupby("region")["sales"].sum())
    return pivot.loc[order.sort_values(ascending=False).index]


# ---------------------------------------------------------------- storytelling
def build_insights(df: pd.DataFrame) -> dict:
    """Menyusun kalimat wawasan secara dinamis mengikuti data yang terfilter."""
    out: dict[str, str] = {}

    # Tren tahunan (hanya tahun dengan data 12 bulan agar adil)
    months_per_year = df.groupby("order_year")["order_month"].nunique()
    full_years = months_per_year[months_per_year == 12].index
    yearly = df[df["order_year"].isin(full_years)].groupby("order_year")["sales"].sum()
    if len(yearly) >= 2:
        g = yearly.iloc[-1] / yearly.iloc[0] - 1
        arah = "naik" if g >= 0 else "turun"
        out["trend"] = (f"Penjualan {arah} {fmt_pct(abs(g), 0)} dari {yearly.index[0]} "
                        f"({fmt_money(yearly.iloc[0])}) ke {yearly.index[-1]} "
                        f"({fmt_money(yearly.iloc[-1])}).")
        out["growth"] = g

    # Musim puncak
    by_month = df.groupby("order_month")["sales"].sum()
    if by_month.size >= 6:
        top = by_month.sort_values(ascending=False).index[:2]
        nama = " dan ".join(BULAN_PANJANG[m - 1] for m in sorted(top))
        out["season"] = f"{nama} adalah bulan dengan penjualan tertinggi; stok dan promosi sebaiknya disiapkan sebelum periode ini."

    # Sub-kategori
    sub = subcategory_profit(df)
    if not sub.empty:
        best, worst = sub.iloc[-1], sub.iloc[0]
        loss = sub[sub["profit"] < 0]
        out["n_loss_sub"] = len(loss)
        if len(loss):
            out["subcat"] = (f"{best.sub_category} menyumbang laba terbesar ({fmt_money(best.profit)}), "
                             f"sedangkan {len(loss)} sub-kategori merugi dengan kerugian terdalam di "
                             f"{worst.sub_category} ({fmt_money(worst.profit)}).")
        else:
            out["subcat"] = (f"Semua sub-kategori untung; {best.sub_category} terbesar "
                             f"({fmt_money(best.profit)}), {worst.sub_category} terkecil.")

    # Diskon
    band = discount_band_summary(df).set_index("discount_band")
    if "Tanpa diskon" in band.index and band.index.size >= 2:
        high = df[df["discount"] > 0.20]
        if len(high):
            m_high = high["profit"].sum() / high["sales"].sum()
            out["discount"] = (f"Transaksi tanpa diskon bermargin {fmt_pct(band.loc['Tanpa diskon', 'margin'])}, "
                               f"tetapi diskon di atas 20% bermargin {fmt_pct(m_high)} dan "
                               f"{fmt_pct(high['is_loss'].mean(), 0)} transaksinya merugi.")
            out["high_disc_margin"] = m_high

    # Wilayah
    reg = df.groupby("region")[["sales", "profit"]].sum()
    if len(reg) >= 2:
        reg["margin"] = reg["profit"] / reg["sales"]
        r = reg["margin"].sort_values()
        out["region"] = (f"Wilayah {WILAYAH.get(r.index[-1], r.index[-1])} paling efisien "
                         f"(margin {fmt_pct(r.iloc[-1])}), sementara {WILAYAH.get(r.index[0], r.index[0])} "
                         f"paling rendah ({fmt_pct(r.iloc[0])}).")

    # Segmen
    seg = segment_share(df)
    if len(seg) >= 2:
        s = seg.iloc[0]
        out["segment"] = f"Segmen {s.segment} menyumbang {fmt_pct(s.share, 0)} penjualan."

    # Kalimat utama (headline)
    parts = []
    if "growth" in out:
        parts.append(f"Penjualan {'tumbuh' if out['growth'] >= 0 else 'menyusut'} "
                     f"{fmt_pct(abs(out['growth']), 0)}")
    if out.get("high_disc_margin", 0) < 0:
        parts.append("diskon di atas 20% justru menghasilkan rugi")
    elif out.get("n_loss_sub"):
        parts.append(f"{out['n_loss_sub']} sub-kategori masih merugi")
    if len(parts) == 2:
        sambung = "tetapi" if out.get("growth", 0) >= 0 else "dan"
        out["headline"] = f"{parts[0]}, {sambung} {parts[1]}."
    elif parts:
        out["headline"] = parts[0][0].upper() + parts[0][1:] + "."
    else:
        k = compute_kpis(df)
        out["headline"] = f"Margin laba periode ini {fmt_pct(k['margin'])}."
    return out
