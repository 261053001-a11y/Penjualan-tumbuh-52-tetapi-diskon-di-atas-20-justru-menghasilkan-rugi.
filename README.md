# Dashboard Interaktif Penjualan & Profitabilitas Superstore

**UTS Visualisasi Data · Program Studi Sistem Informasi · Universitas Dirgantara Marsekal Suryadarma**
Semester Ganjil 2026/2027 · Dosen: Muryan Awaludin, S.Kom., M.Kom.

| | |
|---|---|
| **Nama** | _Hudzaifah Aini_ |
| **NPM** | _261053001_ |
| **Live Dashboard** | http://localhost:8501/_ |
| **Dataset Kaggle** | https://www.kaggle.com/datasets/vivek468/superstore-dataset-final |

---

## 1. Latar Belakang

Perusahaan ritel sering mengukur keberhasilan dari besarnya penjualan, padahal penjualan yang
tinggi belum tentu menghasilkan laba. Diskon yang terlalu agresif, produk dengan biaya tinggi,
dan perbedaan kinerja antarwilayah dapat menggerus laba tanpa terlihat dari angka penjualan.

Projek ini menggunakan **Superstore Dataset** (Kaggle), yaitu data transaksi sebuah toko ritel
di Amerika Serikat periode 2014–2017. Dataset berisi **9.994 baris** dan **21 kolom** (9.993 baris setelah 1 duplikat dihapus), dengan
kombinasi variabel:

- **Kualitatif/kategori:** Segment, Region, State, City, Category, Sub-Category, Ship Mode, Product Name
- **Kuantitatif/angka:** Sales, Quantity, Discount, Profit
- **Waktu:** Order Date, Ship Date

Pertanyaan utama yang dijawab dashboard: **dari mana laba perusahaan datang, dan ke mana laba itu bocor?**

## 2. Fitur Dashboard

| Komponen | Isi |
|---|---|
| **KPI Cards (4)** | Total penjualan, total laba, margin laba, jumlah pesanan & pelanggan unik, lengkap dengan perbandingan terhadap periode sebelumnya |
| **Visualisasi (6, 5 jenis)** | Line chart tren bulanan · Horizontal bar laba per sub-kategori · Donut porsi segmen · Scatter diskon vs laba per produk · Column chart margin per kelompok diskon · Heatmap margin wilayah × kategori |
| **Filter interaktif (4)** | Rentang tanggal, wilayah, kategori produk, segmen pelanggan (+ tombol atur ulang) |
| **Storytelling** | Judul utama dan catatan di bawah setiap grafik disusun otomatis dari data yang sedang difilter, anotasi puncak penjualan, garis batas diskon 20%, serta panel ringkasan wawasan dan rekomendasi |
| **Desain** | Palet konsisten (oker = penjualan, hijau tua = laba, merah bata = rugi), warna kategori sama di semua grafik, tata letak responsif |

## 3. Wawasan Utama (Key Insights)

1. **Penjualan tumbuh 51%, tetapi margin hanya 12,5%.** Penjualan naik dari US$ 484 ribu (2014)
   menjadi US$ 733 ribu (2017), dengan total US$ 2,30 juta dan laba US$ 286 ribu dari 5.009 pesanan
   dan 793 pelanggan. Penjualan sempat turun tipis pada 2015 sebelum melonjak pada 2016–2017.
2. **Diskon di atas 20% adalah sumber kebocoran laba terbesar.** Transaksi tanpa diskon bermargin
   29,5% dan hampir tidak pernah rugi. Sebaliknya, diskon 21–40% bermargin −15,3% dengan 90% transaksi
   merugi, dan diskon di atas 40% bermargin −77,4% dengan seluruh transaksinya merugi.
3. **Furniture laku, tetapi hampir tidak menghasilkan laba.** Laba Furniture hanya US$ 18 ribu,
   jauh di bawah Technology (US$ 145 ribu) dan Office Supplies (US$ 122 ribu). Tiga sub-kategori
   merugi: **Tables** (−US$ 17,7 ribu), **Bookcases** (−US$ 3,5 ribu), dan **Supplies** (−US$ 1,2 ribu).
4. **Wilayah West paling efisien, Central paling lemah.** Margin West 14,9% dan East 13,5%,
   sedangkan South 11,9% dan Central hanya 7,9%, hampir separuh margin West.
5. **Segmen Consumer menyumbang sekitar separuh penjualan**, sehingga program loyalitas dan promosi
   paling berdampak bila diarahkan ke segmen ini, tanpa diskon berlebihan.

**Rekomendasi:** batasi diskon maksimal 20%, evaluasi harga dan biaya sub-kategori Tables,
Bookcases, dan Supplies, serta pelajari praktik wilayah West untuk diterapkan di Central.

> Angka di atas dapat dicek ulang melalui keluaran `python data_cleaning.py`
> (bagian *RINGKASAN UNTUK README*).

## 4. Pengolahan Data (Data Cleaning)

Skrip `data_cleaning.py` melakukan:

1. Membaca file mentah dengan encoding yang sesuai (cp1252).
2. Menstandarkan nama kolom menjadi `snake_case` dan menghapus kolom `Row ID`.
3. Merapikan spasi pada kolom teks dan menghapus baris duplikat.
4. Mengubah `Order Date` dan `Ship Date` menjadi tipe tanggal (format asli bulan/hari/tahun),
   serta `Postal Code` menjadi teks 5 digit.
5. Memeriksa nilai kosong dan memvalidasi logika bisnis (penjualan dan kuantitas > 0,
   diskon 0–1, tanggal kirim ≥ tanggal pesan).
6. Menambahkan fitur turunan: tahun, bulan, kuartal, lama pengiriman, margin laba,
   penanda transaksi rugi, dan kelompok diskon.

Hasilnya disimpan di `data/superstore_clean.csv`.

## 5. Struktur Repositori

```
├── app.py                  # Aplikasi dashboard Streamlit (berkas utama)
├── analysis.py             # Fungsi agregasi & penyusun wawasan otomatis
├── data_cleaning.py        # Skrip pra-pemrosesan data
├── requirements.txt        # Daftar library untuk deployment
├── .streamlit/config.toml  # Tema warna dashboard
├── data/
│   ├── raw/                # Data mentah dari Kaggle
│   └── superstore_clean.csv
└── README.md
```

## 6. Menjalankan Secara Lokal

```bash
# 1. Clone repositori
git clone https://github.com/USERNAME/NAMA-REPO.git
cd NAMA-REPO

# 2. (Opsional) buat virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instal library
pip install -r requirements.txt

# 4. Bersihkan data (jika data/superstore_clean.csv belum ada)
python data_cleaning.py

# 5. Jalankan dashboard
streamlit run app.py
```

Dashboard akan terbuka di `http://localhost:8501`.

## 7. Teknologi

Python · Pandas · Plotly · Streamlit · Streamlit Community Cloud
