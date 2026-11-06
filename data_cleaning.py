"""
data_cleaning.py
================
Pra-pemrosesan (data cleaning) dataset Superstore dari Kaggle.

Sumber  : https://www.kaggle.com/datasets/vivek468/superstore-dataset-final
Input   : data/raw/Sample - Superstore.csv   (file asli hasil unduhan Kaggle)
Output  : data/superstore_clean.csv          (dipakai oleh app.py)

Jalankan:
    python data_cleaning.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / "data" / "raw" / "Sample - Superstore.csv"
CLEAN_PATH = BASE_DIR / "data" / "superstore_clean.csv"

KEY_COLUMNS = [
    "order_id", "order_date", "ship_date", "customer_id", "segment",
    "region", "state", "category", "sub_category", "product_id",
    "sales", "quantity", "discount", "profit",
]

DISCOUNT_BINS = [-0.001, 0.0, 0.20, 0.40, 1.0]
DISCOUNT_LABELS = ["Tanpa diskon", "1–20%", "21–40%", ">40%"]


def read_raw(path: Path) -> pd.DataFrame:
    """Membaca CSV mentah. File Kaggle ini memakai encoding Windows (cp1252)."""
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Encoding file {path} tidak dikenali.")


def to_snake_case(col: str) -> str:
    return (
        col.strip().lower()
        .replace("-", "_").replace(" ", "_").replace("__", "_")
    )


def parse_date(series: pd.Series) -> pd.Series:
    """Format asli tanggal adalah bulan/hari/tahun (mis. 11/8/2016)."""
    parsed = pd.to_datetime(series, format="%m/%d/%Y", errors="coerce")
    if parsed.isna().mean() > 0.5:  # cadangan bila versi file berbeda format
        parsed = pd.to_datetime(series, errors="coerce")
    return parsed


def clean(raw: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    log = []
    df = raw.copy()
    log.append(f"Baris awal                     : {len(df):,}")

    # 1. Standarisasi nama kolom -> snake_case
    df.columns = [to_snake_case(c) for c in df.columns]

    # 2. Hapus kolom nomor urut (tidak bermakna analitis)
    df = df.drop(columns=["row_id"], errors="ignore")

    # 3. Rapikan spasi pada kolom teks
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for c in text_cols:
        df[c] = df[c].astype("string").str.strip()

    # 4. Hapus duplikat persis
    n_before = len(df)
    df = df.drop_duplicates()
    log.append(f"Duplikat dihapus               : {n_before - len(df):,}")

    # 5. Konversi tipe data
    df["order_date"] = parse_date(df["order_date"])
    df["ship_date"] = parse_date(df["ship_date"])
    for c in ["sales", "quantity", "discount", "profit"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "postal_code" in df.columns:
        df["postal_code"] = (
            pd.to_numeric(df["postal_code"], errors="coerce")
            .astype("Int64").astype("string").str.zfill(5)
        )

    # 6. Nilai kosong pada kolom kunci
    missing = df[KEY_COLUMNS].isna().sum()
    log.append(f"Nilai kosong (kolom kunci)     : {int(missing.sum()):,}")
    df = df.dropna(subset=KEY_COLUMNS)

    # 7. Validasi logika bisnis
    valid = (
        (df["sales"] > 0)
        & (df["quantity"] > 0)
        & df["discount"].between(0, 1)
        & (df["ship_date"] >= df["order_date"])
    )
    log.append(f"Baris tidak valid dihapus      : {int((~valid).sum()):,}")
    df = df[valid].copy()

    # 8. Fitur turunan untuk analisis & visualisasi
    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.month
    df["order_quarter"] = "Q" + df["order_date"].dt.quarter.astype(str)
    df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days
    df["profit_margin"] = (df["profit"] / df["sales"]).round(4)
    df["is_loss"] = df["profit"] < 0
    df["discount_band"] = pd.cut(
        df["discount"], bins=DISCOUNT_BINS, labels=DISCOUNT_LABELS
    ).astype("string")

    df = df.sort_values("order_date").reset_index(drop=True)
    log.append(f"Baris akhir (bersih)           : {len(df):,}")
    log.append(f"Jumlah kolom                   : {df.shape[1]}")

    if verbose:
        print("\n=== LAPORAN PEMBERSIHAN DATA ===")
        print("\n".join(log))
    return df


def print_insight_summary(df: pd.DataFrame) -> None:
    """Ringkasan angka untuk bagian Key Insights di README."""
    sales, profit = df["sales"].sum(), df["profit"].sum()
    print("\n=== RINGKASAN UNTUK README ===")
    print(f"Periode         : {df['order_date'].min():%d-%m-%Y} s.d. {df['order_date'].max():%d-%m-%Y}")
    print(f"Total penjualan : US$ {sales:,.2f}")
    print(f"Total laba      : US$ {profit:,.2f} (margin {profit / sales:.1%})")
    print(f"Pesanan unik    : {df['order_id'].nunique():,} | Pelanggan: {df['customer_id'].nunique():,}")

    print("\nPenjualan per tahun:")
    print(df.groupby("order_year")["sales"].sum().round(0).to_string())

    print("\nLaba per kategori:")
    print(df.groupby("category")["profit"].sum().sort_values().round(0).to_string())

    print("\nSub-kategori merugi:")
    sub = df.groupby("sub_category")["profit"].sum().sort_values()
    print(sub[sub < 0].round(0).to_string())

    print("\nMargin per wilayah:")
    reg = df.groupby("region")[["sales", "profit"]].sum()
    print((reg["profit"] / reg["sales"]).sort_values().map("{:.1%}".format).to_string())

    print("\nMargin & porsi transaksi rugi per kelompok diskon:")
    band = df.groupby("discount_band").agg(
        transaksi=("sales", "size"),
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        porsi_rugi=("is_loss", "mean"),
    )
    band["margin"] = band["profit"] / band["sales"]
    band = band.reindex([b for b in DISCOUNT_LABELS if b in band.index])
    print(band[["transaksi", "margin", "porsi_rugi"]].to_string(
        formatters={"margin": "{:.1%}".format, "porsi_rugi": "{:.0%}".format}))


def main() -> None:
    if not RAW_PATH.exists():
        raise SystemExit(
            f"File mentah tidak ditemukan: {RAW_PATH}\n"
            "Unduh dataset dari Kaggle lalu simpan dengan nama "
            "'Sample - Superstore.csv' di folder data/raw/."
        )
    df = clean(read_raw(RAW_PATH))
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)
    print(f"\nData bersih disimpan ke: {CLEAN_PATH.relative_to(BASE_DIR)}")
    print_insight_summary(df)


if __name__ == "__main__":
    main()
