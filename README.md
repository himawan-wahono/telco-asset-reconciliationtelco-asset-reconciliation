# 📡 Telco Asset & SIRO Reconciliation Dashboard

Aplikasi Dashboard Rekonsiliasi Aset Telekomunikasi, Pengawasan **Data Quality**, dan Verifikasi **Accrual / Stop Accrue** berbasis **Streamlit & Python**.



---

## 🎯 Fitur Utama

1. **Rekonsiliasi Otomatis (Reconciliation Engine):**
   - Membandingkan data fisik lapangan (**SIRO - Site Inventory Record**) terhadap register aset finansial (**ERP**).
   - Mendeteksi anomali:
     - *Ghost Asset*: Aset tercatat di ERP tetapi tidak ada di site fisik.
     - *Unregistered Asset*: Fisik terpasang di site tapi belum teregistrasi di sistem inventaris/ERP.
     - *Status Mismatch*: Perbedaan status operasional (misal: Active vs Decommissioned).
     - *Accrual Discrepancy*: Status akrual yang memerlukan konfirmasi dokumen PO / STIP / Stop Accrue.
2. **Data Quality Scorecard:**
   - Menghitung persentase kebersihan data (*Clean Matched vs Discrepancies*) secara real-time.
3. **Ekspor Weekly Report:**
   - Menghasilkan laporan mingguan siap unduh berformat `.xlsx` (Excel) dengan rincian detail rekon dan ringkasan eksekutif.
4. **Fleksibilitas Input:**
   - Dilengkapi data dummy simulasi langsung pakai, atau opsi unggah file Excel/CSV riil.

---

## 🛠️ Kebutuhan & Menjalankan Aplikasi

Pastikan Python atau `uv` sudah terpasang. Jalankan perintah berikut di terminal:

```bash
uv run --with streamlit --with pandas --with openpyxl streamlit run app.py
```

atau menggunakan pip:

```bash
pip install streamlit pandas openpyxl
streamlit run app.py
```
