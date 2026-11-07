import streamlit as st
import pandas as pd
import numpy as np
import io

# Page Configuration
st.set_page_config(
    page_title="Telco Asset & Rekon Quality Dashboard",
    page_icon="📡",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 14px;
        color: #4B5563;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 12px;
        border-left: 5px solid #2563EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📡 Telco Asset & SIRO Reconciliation Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated Reconciliation, Data Quality Control, and Accrual/Stop-Accrue Verification for Telecommunication Assets</div>', unsafe_allow_html=True)

# Helper function to generate dummy dataset for demonstration
def generate_sample_data():
    np.random.seed(42)
    site_ids = [f"MLG{i:03d}" for i in range(101, 126)]
    equipments = ["BBU V9200", "RRU R8862", "Microwave RTN", "Rectifier 48V", "Antenna Kathrein"]
    
    siro_records = []
    for i in range(40):
        s_id = np.random.choice(site_ids)
        eq = np.random.choice(equipments)
        sn = f"SN-ZTE-{1000 + i}"
        status = np.random.choice(["Active", "Standby", "Dismantled"], p=[0.8, 0.15, 0.05])
        siro_records.append({
            "Site_ID": s_id,
            "Serial_Number": sn,
            "Equipment_Type": eq,
            "SIRO_Status": status,
            "STIP_Ref": f"STIP-2026-{np.random.randint(10, 99)}",
            "PO_Number": f"PO-45000{np.random.randint(100, 999)}"
        })
    df_siro = pd.DataFrame(siro_records)
    
    erp_records = []
    # Match mostly, introduce some discrepancies
    for i, row in df_siro.iterrows():
        if i == 5:  # Missing in ERP
            continue
        erp_status = row["SIRO_Status"]
        if i in [2, 11]:  # Discrepancy in status
            erp_status = "Decommissioned" if row["SIRO_Status"] == "Active" else "Active"
        
        accrue_status = "Accrued" if row["SIRO_Status"] == "Active" else "Stop Accrue"
        if i in [7, 18]: # Accrue mismatch
            accrue_status = "Pending Verification"
            
        erp_records.append({
            "Site_ID": row["Site_ID"],
            "Serial_Number": row["Serial_Number"],
            "Equipment_Name": row["Equipment_Type"],
            "ERP_Asset_Status": erp_status,
            "PO_Number": row["PO_Number"],
            "Accrual_Status": accrue_status,
            "Book_Value_IDR": np.random.randint(15, 80) * 1_000_000
        })
    # Add a ghost asset in ERP not in SIRO
    erp_records.append({
        "Site_ID": "MLG999",
        "Serial_Number": "SN-ZTE-9999",
        "Equipment_Name": "RRU R8862",
        "ERP_Asset_Status": "Active",
        "PO_Number": "PO-45000888",
        "Accrual_Status": "Accrued",
        "Book_Value_IDR": 45_000_000
    })
    df_erp = pd.DataFrame(erp_records)
    return df_siro, df_erp

# Sidebar Data Ingestion
st.sidebar.header("📁 Data Ingestion & Sources")
data_mode = st.sidebar.radio("Pilih Sumber Data:", ["Gunakan Data Simulasi (Sample Data)", "Unggah File Sendiri (Excel/CSV)"])

if data_mode == "Gunakan Data Simulasi (Sample Data)":
    df_siro, df_erp = generate_sample_data()
    st.sidebar.success("✓ Data simulasi SIRO & ERP berhasil dimuat.")
else:
    file_siro = st.sidebar.file_uploader("Upload Data SIRO (Site Inventory)", type=["xlsx", "csv"])
    file_erp = st.sidebar.file_uploader("Upload Data ERP / Asset Register", type=["xlsx", "csv"])
    if file_siro and file_erp:
        try:
            df_siro = pd.read_excel(file_siro) if file_siro.name.endswith(".xlsx") else pd.read_csv(file_siro)
            df_erp = pd.read_excel(file_erp) if file_erp.name.endswith(".xlsx") else pd.read_csv(file_erp)
            st.sidebar.success("✓ File berhasil diunggah!")
        except Exception as e:
            st.sidebar.error(f"Error membaca file: {e}")
            st.stop()
    else:
        st.info("Silakan unggah kedua file (SIRO & ERP) melalui sidebar, atau pilih mode Data Simulasi di sidebar kiri.")
        st.stop()

# Reconciliation Engine
with st.spinner("Menjalankan rekonsiliasi data..."):
    # Outer join on Serial_Number
    rekon_df = pd.merge(
        df_siro,
        df_erp,
        on="Serial_Number",
        how="outer",
        suffixes=("_SIRO", "_ERP")
    )

    # Classify Reconciliation Findings
    def evaluate_rekon(row):
        if pd.isna(row.get("Site_ID_SIRO")):
            return "Ghost Asset (Di ERP tapi tidak tercatat di SIRO)"
        elif pd.isna(row.get("ERP_Asset_Status")):
            return "Unregistered Asset (Ada di SIRO fisik tapi belum tercatat di ERP)"
        elif row.get("SIRO_Status") != row.get("ERP_Asset_Status"):
            return "Status Mismatch (Perbedaan Status Fisik vs Sistem)"
        elif row.get("Accrual_Status") == "Pending Verification":
            return "Accrual Discrepancy (Perlu Validasi Stop Accrue/PO)"
        else:
            return "Clean Matched (Sesuai & Valid)"

    rekon_df["Rekon_Result"] = rekon_df.apply(evaluate_rekon, axis=1)

# Metrics Summary
total_siro = len(df_siro)
total_erp = len(df_erp)
clean_matched = (rekon_df["Rekon_Result"] == "Clean Matched (Sesuai & Valid)").sum()
discrepancy_count = len(rekon_df) - clean_matched
dq_score = (clean_matched / len(rekon_df)) * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Aset SIRO (Fisik)", f"{total_siro:,}")
with col2:
    st.metric("Total Aset ERP (Finansial)", f"{total_erp:,}")
with col3:
    st.metric("Data Quality Score", f"{dq_score:.1f}%")
with col4:
    st.metric("Temuan Selisih (Discrepancy)", f"{discrepancy_count:,}", delta=-discrepancy_count, delta_color="inverse")

# Tabs for Organized Views
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary & DQ", "🔍 Detail Rekonsiliasi & Filter", "📥 Export Weekly Report"])

with tab1:
    st.subheader("Ringkasan Kategori Rekonsiliasi Data")
    category_counts = rekon_df["Rekon_Result"].value_counts().reset_index()
    category_counts.columns = ["Kategori Hasil", "Jumlah Unit"]
    
    col_chart, col_desc = st.columns([3, 2])
    with col_chart:
        st.bar_chart(category_counts.set_index("Kategori Hasil"))
    with col_desc:
        st.markdown("**Status Breakdown:**")
        for _, r in category_counts.iterrows():
            st.write(f"- **{r['Kategori Hasil']}**: `{r['Jumlah Unit']}` unit")
        
        st.info("💡 **Aksi Rekomendasi:** Aset dengan status *Unregistered* atau *Accrual Discrepancy* harus divalidasi dokumen PO & STIP-nya untuk menghindari kesalahan beban finansial.")

with tab2:
    st.subheader("Tabel Rekonsiliasi Data Perangkat")
    filter_status = st.multiselect(
        "Filter Hasil Rekonsiliasi:",
        options=rekon_df["Rekon_Result"].unique(),
        default=rekon_df["Rekon_Result"].unique()
    )
    filtered_df = rekon_df[rekon_df["Rekon_Result"].isin(filter_status)]
    
    display_cols = [
        "Serial_Number", "Site_ID_SIRO", "Equipment_Type", "SIRO_Status", 
        "ERP_Asset_Status", "Accrual_Status", "PO_Number_SIRO", "Rekon_Result"
    ]
    actual_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(filtered_df[actual_cols], use_container_width=True)

with tab3:
    st.subheader("Generate Weekly Data Quality & Rekon Report")
    st.write("Unduh hasil rekonsiliasi data lengkap dalam format Excel untuk bahan Weekly Meeting Directorate:")
    
    # Generate Excel in-memory
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        rekon_df.to_excel(writer, sheet_name='Recon_Detail', index=False)
        category_counts.to_excel(writer, sheet_name='Summary_DQ', index=False)
    
    st.download_button(
        label="📥 Unduh Laporan Rekonsiliasi (Excel .xlsx)",
        data=excel_buffer.getvalue(),
        file_name="Weekly_Report_SIRO_Rekon_Asset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")
st.caption("Aplikasi ini dibuat untuk portofolio: **Himawan Wahono** | Posisi: *Data Quality & Reporting Specialist (Telecommunication)*")
