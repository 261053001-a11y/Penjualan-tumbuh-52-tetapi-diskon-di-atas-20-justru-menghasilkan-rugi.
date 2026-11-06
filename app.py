"""
app.py — Dashboard Interaktif Penjualan & Profitabilitas Superstore
UTS Visualisasi Data, Program Studi Sistem Informasi, Unsurya (Ganjil 2026/2027)

Jalankan lokal:  streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analysis as an

# ------------------------------------------------------------------ identitas
NAMA = "Hudzaifah Aini"      
NPM = "261053001"             
KAGGLE_URL = "https://www.kaggle.com/datasets/vivek468/superstore-dataset-final"

# ------------------------------------------------------------------ palet warna
INK, MUTED, GRID, PAPER = "#1F2633", "#5F6773", "#DADDD5", "#F4F5F1"
SALES, PROFIT, LOSS = "#C2852F", "#1E6E68", "#B4483A"
CATEGORY_COLORS = {"Furniture": "#9A6B43", "Office Supplies": "#4C76A3", "Technology": "#5E8C5A"}
SEGMENT_COLORS = {"Consumer": INK, "Corporate": SALES, "Home Office": "#9AA7A5"}
FONT = "Plus Jakarta Sans, sans-serif"
PLOT_CONFIG = {"displayModeBar": False}

st.set_page_config(page_title="Dashboard Superstore | UTS Visualisasi Data",
                   page_icon="🛒", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stMarkdown p, .stMarkdown li, h1, h2, h3, h4, label,
input, button, textarea, [data-testid="stCaptionContainer"] {{ font-family: {FONT}; }}
.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px; }}
.context {{ color: {MUTED}; font-size: .95rem; font-weight: 500; margin: 0 0 .35rem; }}
.headline {{ color: {INK}; font-size: clamp(1.6rem, 3.1vw, 2.5rem); font-weight: 800;
            line-height: 1.15; letter-spacing: -.02em; max-width: 34ch; margin: 0 0 .6rem; }}
.lead {{ color: {MUTED}; font-size: 1rem; max-width: 70ch; margin: 0; }}
.kpi-row {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
           border-top: 2px solid {INK}; border-bottom: 1px solid {GRID}; margin: 1.4rem 0 1.8rem; }}
.kpi {{ padding: .9rem 1.1rem; border-left: 1px solid {GRID}; }}
.kpi:first-child {{ border-left: none; padding-left: 0; }}
.kpi-label {{ color: {MUTED}; font-size: .85rem; font-weight: 600; }}
.kpi-value {{ color: {INK}; font-size: 1.8rem; font-weight: 700; margin: .1rem 0;
             font-variant-numeric: tabular-nums; }}
.kpi-sub {{ color: {MUTED}; font-size: .8rem; }}
.kpi-sub .up {{ color: {PROFIT}; font-weight: 700; }}
.kpi-sub .down {{ color: {LOSS}; font-weight: 700; }}
h3.q {{ color: {INK}; font-size: 1.1rem; font-weight: 700; margin: .4rem 0 0; padding: 0; }}
p.note {{ color: {INK}; font-size: .92rem; border-left: 3px solid {SALES};
         padding: .1rem 0 .1rem .7rem; margin: .2rem 0 1.4rem; max-width: 75ch; }}
.insight {{ margin: 0 0 .8rem; font-size: .93rem; color: {INK}; }}
.insight b {{ display: block; color: {MUTED}; font-size: .8rem; font-weight: 600; }}
.footer {{ color: {MUTED}; font-size: .82rem; border-top: 1px solid {GRID};
          padding-top: .8rem; margin-top: 2rem; }}
@media (max-width: 760px) {{
  .kpi-row {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .kpi:nth-child(3) {{ border-left: none; padding-left: 0; }}
  .kpi {{ border-top: 1px solid {GRID}; }}
}}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data(show_spinner="Memuat data…")
def get_data() -> pd.DataFrame:
    if not an.DATA_PATH.exists():
        import data_cleaning  # buat data bersih dari file mentah bila belum ada
        raw = data_cleaning.read_raw(data_cleaning.RAW_PATH)
        data_cleaning.clean(raw, verbose=False).to_csv(an.DATA_PATH, index=False)
    return an.load_clean()


try:
    df = get_data()
except Exception as err:  # pesan jelas bila data belum disiapkan
    st.error("Data belum tersedia. Jalankan `python data_cleaning.py` setelah menyimpan "
             "file Kaggle di `data/raw/Sample - Superstore.csv`.")
    st.caption(f"Detail: {err}")
    st.stop()

MIN_DATE, MAX_DATE = df["order_date"].min().date(), df["order_date"].max().date()


def style(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=30, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=13), separators=",.",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""),
        hoverlabel=dict(font_family=FONT, bgcolor="white"),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, title_font=dict(color=MUTED, size=12))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title_font=dict(color=MUTED, size=12))
    return fig


def title(question: str) -> None:
    st.markdown(f"<h3 class='q'>{question}</h3>", unsafe_allow_html=True)


def note(text: str | None) -> None:
    if text:
        st.markdown(f"<p class='note'>{text}</p>", unsafe_allow_html=True)


# ------------------------------------------------------------------ sidebar filter
def reset_filters() -> None:
    st.session_state.f_date = (MIN_DATE, MAX_DATE)
    for key in ("f_region", "f_cat", "f_seg"):
        st.session_state[key] = []


st.session_state.setdefault("f_date", (MIN_DATE, MAX_DATE))
for _key in ("f_region", "f_cat", "f_seg"):
    st.session_state.setdefault(_key, [])

with st.sidebar:
    st.header("Filter")
    date_value = st.date_input("Rentang tanggal pesanan",
                               min_value=MIN_DATE, max_value=MAX_DATE,
                               format="DD/MM/YYYY", key="f_date")
    regions = st.multiselect("Wilayah", sorted(df["region"].unique()), key="f_region",
                             format_func=lambda r: an.WILAYAH.get(r, r),
                             placeholder="Semua wilayah")
    categories = st.multiselect("Kategori produk", sorted(df["category"].unique()),
                                key="f_cat", placeholder="Semua kategori")
    segments = st.multiselect("Segmen pelanggan", sorted(df["segment"].unique()),
                              key="f_seg", placeholder="Semua segmen")
    st.button("Atur ulang filter", on_click=reset_filters, width="stretch")
    st.divider()
    st.caption(f"Data: [Superstore Dataset, Kaggle]({KAGGLE_URL}). "
               f"{an.fmt_int(len(df))} transaksi ritel di Amerika Serikat. "
               "Nilai uang dalam dolar AS.")

if isinstance(date_value, (tuple, list)):
    start, end = (date_value[0], date_value[-1]) if date_value else (MIN_DATE, MAX_DATE)
else:
    start = end = date_value

dff = an.filter_data(df, start, end, regions, categories, segments)
if dff.empty:
    st.warning("Tidak ada transaksi untuk kombinasi filter ini. Perluas rentang tanggal "
               "atau kosongkan salah satu filter.")
    st.stop()

ps, pe = an.previous_period(start, end)
prev = an.filter_data(df, ps, pe, regions, categories, segments)
k = an.compute_kpis(dff)
kp = an.compute_kpis(prev) if not prev.empty else None
ins = an.build_insights(dff)

# ------------------------------------------------------------------ hero & KPI
st.markdown(
    f"<p class='context'>Dashboard penjualan Superstore, "
    f"{pd.Timestamp(start):%d/%m/%Y} sampai {pd.Timestamp(end):%d/%m/%Y}</p>"
    f"<h1 class='headline'>{ins['headline']}</h1>"
    f"<p class='lead'>Dashboard ini menelusuri dari mana laba datang dan ke mana laba bocor: "
    f"tren bulanan, produk, segmen pelanggan, kebijakan diskon, dan wilayah.</p>",
    unsafe_allow_html=True)


def delta_html(cur, prv, kind="pct") -> str:
    if kp is None:
        return "Tidak ada periode pembanding"
    if kind == "pp":  # selisih poin persentase (untuk margin)
        d = cur - prv
        if pd.isna(d):
            return "–"
        cls, arrow = ("up", "▲") if d >= 0 else ("down", "▼")
        return f"<span class='{cls}'>{arrow} {an._id_sep(f'{abs(d) * 100:.1f}')} poin</span> vs periode sebelumnya"
    d = an.pct_change(cur, prv)
    if d is None:
        return "–"
    cls, arrow = ("up", "▲") if d >= 0 else ("down", "▼")
    return f"<span class='{cls}'>{arrow} {an.fmt_pct(abs(d))}</span> vs periode sebelumnya"


cards = [
    ("Total penjualan", an.fmt_money(k["sales"]), delta_html(k["sales"], kp and kp["sales"])),
    ("Total laba", an.fmt_money(k["profit"]), delta_html(k["profit"], kp and kp["profit"])),
    ("Margin laba", an.fmt_pct(k["margin"]), delta_html(k["margin"], kp and kp["margin"], "pp")),
    ("Jumlah pesanan", an.fmt_int(k["orders"]),
     f"dari {an.fmt_int(k['customers'])} pelanggan unik"),
]
st.markdown("<div class='kpi-row'>" + "".join(
    f"<div class='kpi'><div class='kpi-label'>{lbl}</div><div class='kpi-value'>{val}</div>"
    f"<div class='kpi-sub'>{sub}</div></div>" for lbl, val, sub in cards) + "</div>",
    unsafe_allow_html=True)

# ------------------------------------------------------------------ 1. Line chart tren
title("Bagaimana penjualan dan laba bergerak setiap bulan?")
trend = an.monthly_trend(dff)
fig = go.Figure()
fig.add_scatter(x=trend["order_date"], y=trend["sales"], name="Penjualan", mode="lines",
                line=dict(color=SALES, width=2.6), customdata=trend["label"],
                hovertemplate="%{customdata}<br>Penjualan: US$ %{y:,.0f}<extra></extra>")
fig.add_scatter(x=trend["order_date"], y=trend["profit"], name="Laba", mode="lines",
                line=dict(color=PROFIT, width=2.6), customdata=trend["label"],
                hovertemplate="%{customdata}<br>Laba: US$ %{y:,.0f}<extra></extra>")
fig.add_hline(y=0, line_color=MUTED, line_width=1)
if len(trend) > 1:
    peak = trend.loc[trend["sales"].idxmax()]
    fig.add_annotation(x=peak["order_date"], y=peak["sales"], showarrow=True, arrowhead=0,
                       arrowcolor=MUTED, ax=0, ay=-34, font=dict(size=12, color=INK),
                       text=f"Puncak {peak['label']}: {an.fmt_money(peak['sales'])}")
fig.update_xaxes(title_text="Bulan pesanan", tickformat="%b %Y")
fig.update_yaxes(title_text="Nilai (US$)", tickprefix="$")
st.plotly_chart(style(fig, 380), width="stretch", config=PLOT_CONFIG)
note(" ".join(t for t in (ins.get("trend"), ins.get("season")) if t))

# ------------------------------------------------------------------ 2 & 3. Bar + Donut
c1, c2 = st.columns([3, 2], gap="large")
with c1:
    title("Sub-kategori mana yang menghasilkan dan menggerus laba?")
    sub = an.subcategory_profit(dff)
    fig = px.bar(sub, x="profit", y="sub_category", orientation="h", color="status",
                 color_discrete_map={"Untung": PROFIT, "Rugi": LOSS},
                 custom_data=["category", "sales", "margin"])
    fig.update_traces(hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>Laba: US$ %{x:,.0f}"
                                    "<br>Penjualan: US$ %{customdata[1]:,.0f}"
                                    "<br>Margin: %{customdata[2]:.1%}<extra></extra>")
    fig.update_xaxes(title_text="Total laba (US$)", tickprefix="$", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title_text="", categoryorder="total ascending", gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(style(fig, max(320, 28 * len(sub) + 60)), width="stretch",
                    config=PLOT_CONFIG)
    note(ins.get("subcat"))

with c2:
    title("Segmen pelanggan mana yang paling besar?")
    seg = an.segment_share(dff)
    fig = go.Figure(go.Pie(
        labels=seg["segment"], values=seg["sales"], hole=.62, sort=False,
        marker=dict(colors=[SEGMENT_COLORS.get(s, MUTED) for s in seg["segment"]],
                    line=dict(color="white", width=2)),
        textinfo="percent", textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>Penjualan: US$ %{value:,.0f}<br>%{percent}<extra></extra>"))
    top = seg.iloc[0]
    fig.add_annotation(text=f"<b>{an.fmt_pct(top['share'], 0)}</b><br>{top['segment']}",
                       showarrow=False, font=dict(size=16, color=INK))
    st.plotly_chart(style(fig, 360), width="stretch", config=PLOT_CONFIG)
    note(ins.get("segment"))

# ------------------------------------------------------------------ 4 & 5. Scatter + Column
c3, c4 = st.columns([3, 2], gap="large")
with c3:
    title("Apakah diskon besar membuat produk merugi?")
    prod = an.product_discount_profit(dff)
    fig = px.scatter(prod, x="avg_discount", y="profit", color="category", size="sales",
                     size_max=22, opacity=.65, color_discrete_map=CATEGORY_COLORS,
                     custom_data=["product_name", "sales", "transactions"])
    fig.update_traces(marker=dict(line=dict(width=0)),
                      hovertemplate="<b>%{customdata[0]}</b><br>Rata-rata diskon: %{x:.0%}"
                                    "<br>Laba: US$ %{y:,.0f}<br>Penjualan: US$ %{customdata[1]:,.0f}"
                                    "<br>Transaksi: %{customdata[2]}<extra></extra>")
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    fig.add_vline(x=0.2, line_dash="dot", line_color=LOSS,
                  annotation_text="Diskon 20%", annotation_position="top right",
                  annotation_font=dict(color=LOSS, size=12))
    fig.update_xaxes(title_text="Rata-rata diskon per produk", tickformat=".0%")
    fig.update_yaxes(title_text="Total laba per produk (US$)", tickprefix="$")
    st.plotly_chart(style(fig, 400), width="stretch", config=PLOT_CONFIG)
    st.caption("Satu titik mewakili satu produk; ukuran titik menunjukkan nilai penjualan.")

with c4:
    title("Berapa margin di setiap tingkat diskon?")
    band = an.discount_band_summary(dff)
    fig = go.Figure(go.Bar(
        x=band["discount_band"].astype(str), y=band["margin"],
        marker_color=[PROFIT if m >= 0 else LOSS for m in band["margin"]],
        text=[an.fmt_pct(m) for m in band["margin"]], textposition="outside",
        customdata=band[["transactions", "loss_share"]],
        hovertemplate="<b>Diskon %{x}</b><br>Margin: %{y:.1%}<br>Transaksi: %{customdata[0]:,}"
                      "<br>Transaksi rugi: %{customdata[1]:.0%}<extra></extra>"))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    lo, hi = min(band["margin"].min(), 0), max(band["margin"].max(), 0)
    pad = (hi - lo) * .18 or .05
    fig.update_yaxes(title_text="Margin laba", tickformat=".0%", range=[lo - pad, hi + pad])
    fig.update_xaxes(title_text="Kelompok diskon")
    st.plotly_chart(style(fig, 400), width="stretch", config=PLOT_CONFIG)

note(ins.get("discount"))

# ------------------------------------------------------------------ 6. Heatmap + ringkasan
c5, c6 = st.columns([3, 2], gap="large")
with c5:
    title("Di wilayah dan kategori mana margin paling sehat?")
    piv = an.region_category_margin(dff)
    zmax = float(piv.abs().max().max()) if piv.size else 0.0
    zmax = zmax if zmax > 0 else 0.01
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=list(piv.columns), y=[an.WILAYAH.get(r, r) for r in piv.index],
        text=[[an.fmt_pct(v) for v in row] for row in piv.values], texttemplate="%{text}",
        textfont=dict(size=14), colorscale=[[0, "#C25E4E"], [.5, "#F4F5F1"], [1, "#3B8B83"]],
        zmid=0, zmin=-zmax, zmax=zmax, xgap=3, ygap=3,
        colorbar=dict(title="Margin", tickformat=".0%", thickness=12),
        hovertemplate="%{y} / %{x}<br>Margin: %{z:.1%}<extra></extra>"))
    fig.update_xaxes(title_text="Kategori produk", side="bottom")
    fig.update_yaxes(title_text="Wilayah", autorange="reversed", gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(style(fig, 340), width="stretch", config=PLOT_CONFIG)
    note(ins.get("region"))

with c6:
    title("Ringkasan wawasan")
    with st.container(border=True):
        items = [("Tren", ins.get("trend")), ("Produk", ins.get("subcat")),
                 ("Diskon", ins.get("discount")), ("Wilayah", ins.get("region")),
                 ("Musim", ins.get("season"))]
        st.markdown("".join(f"<p class='insight'><b>{h}</b>{t}</p>" for h, t in items if t),
                    unsafe_allow_html=True)
        if ins.get("high_disc_margin", 0) < 0:
            st.markdown(f"<p class='insight'><b>Rekomendasi</b>Batasi diskon maksimal 20% dan "
                        f"tinjau ulang harga sub-kategori yang merugi sebelum menambah volume.</p>",
                        unsafe_allow_html=True)

# ------------------------------------------------------------------ data detail
with st.expander(f"Lihat data transaksi terfilter ({an.fmt_int(len(dff))} baris)"):
    cols = ["order_date", "order_id", "segment", "region", "state", "category",
            "sub_category", "product_name", "sales", "quantity", "discount", "profit"]
    st.dataframe(dff[cols].sort_values("order_date", ascending=False),
                 width="stretch", hide_index=True,
                 column_config={
                     "order_date": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                     "sales": st.column_config.NumberColumn("Penjualan", format="$%.2f"),
                     "profit": st.column_config.NumberColumn("Laba", format="$%.2f"),
                     "discount": st.column_config.NumberColumn("Diskon", format="%.2f"),
                 })
    st.download_button("Unduh CSV data terfilter", dff[cols].to_csv(index=False).encode("utf-8"),
                       file_name="superstore_terfilter.csv", mime="text/csv")

st.markdown(f"<div class='footer'>Sumber data: <a href='{KAGGLE_URL}'>Superstore Dataset "
            f"(Kaggle)</a>. Dibuat oleh {NAMA} ({NPM}) untuk UTS Visualisasi Data, "
            f"Universitas Dirgantara Marsekal Suryadarma, 2026.</div>", unsafe_allow_html=True)
