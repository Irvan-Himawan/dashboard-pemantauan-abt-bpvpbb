import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Monitoring ABT", layout="wide")

TARGET_DIPA_PAKET = {"PBK-Reguler": 237, "TMT DUDI": 238, "LPKS": 31, "BLKK": 32, "UPTD": 58, "Produktivitas": 2}
TARGET_DIPA_PESERTA = {pos: (paket * 25 if pos == "Produktivitas" else paket * 16) for pos, paket in TARGET_DIPA_PAKET.items()}

KAMUS_BULAN = {
    'Januari': 'January', 'Februari': 'February', 'Maret': 'March',
    'April': 'April', 'Mei': 'May', 'Juni': 'June', 'Juli': 'July',
    'Agustus': 'August', 'September': 'September', 'Oktober': 'October',
    'November': 'November', 'Desember': 'December'
}

@st.cache_data(ttl=600)
def load_data():
    sheet_id = st.secrets["SHEET_ID"]
    gid = st.secrets["SHEET_GID"]
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    df = pd.read_csv(csv_url)
    
    # 1. STANDARISASI TEKS KOSONG
    cols_to_clean = ['nama_tempat_pelatihan', 'pelatihan', 'kejuruan', 'status_kegiatan_pelatihan']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].replace(r'^\s*$', float('nan'), regex=True)
            
    # 2. SYARAT MUTLAK (Selama ada id_program, data sah)
    df = df.dropna(subset=['id_program'])
    
    # 3. LOGIKA AUTO-FILL & PENYELARASAN TEKS
    if 'status_kegiatan_pelatihan' in df.columns:
        df['status_kegiatan_pelatihan'] = df['status_kegiatan_pelatihan'].fillna('Rencana')
        df['status_kegiatan_pelatihan'] = df['status_kegiatan_pelatihan'].str.title()
    
    if 'nama_tempat_pelatihan' in df.columns:
        df['nama_tempat_pelatihan'] = df['nama_tempat_pelatihan'].fillna('Belum Ditentukan')
    if 'pelatihan' in df.columns:
        df['pelatihan'] = df['pelatihan'].fillna('Belum Ditentukan')
   
    
   # 4. EKSTRAK POS ANGGARAN (SISTEM HIJACKING / TITIP PAKET)
    def tentukan_pos(row):
        # Lapis 1: Cek kolom 'sumber_anggaran' terlebih dahulu
        if 'sumber_anggaran' in row and pd.notna(row['sumber_anggaran']):
            sumber = str(row['sumber_anggaran']).upper()
            
            # Jika anggarannya dari pusat (UPTP), paksa masuk ke tab PBK-Reguler!
            if "UPTP" in sumber:
                return "PBK-Reguler"
            
            # Jika anggarannya murni daerah (UPTD), paksa masuk ke tab UPTD
            elif "UPTD" in sumber:
                return "UPTD"
            
        # Lapis 2: Jika sumber_anggaran kosong, gunakan identitas default dari id_program
        id_prog = str(row['id_program']).upper()
        if "PBK" in id_prog: return "PBK-Reguler"
        elif "TMT" in id_prog or "DUDI" in id_prog: return "TMT DUDI"
        elif "LPKS" in id_prog: return "LPKS"
        elif "BLK" in id_prog: return "BLKK"
        elif "UPTD" in id_prog: return "UPTD"
        elif "PRD" in id_prog or "PROD" in id_prog: return "Produktivitas"
        else: return "Lainnya"
        
    # Terapkan fungsi ke seluruh baris (axis=1)
    df['pos_anggaran'] = df.apply(tentukan_pos, axis=1)
    
    # 5. PENERJEMAH & KONVERSI TANGGAL
    def konversi_tgl(val):
        if pd.isna(val) or str(val).strip() == "":
            return pd.NaT 
        
        val_str = str(val).strip()
        
        if val_str.replace('.', '', 1).isdigit():
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=float(val_str))
        
        for id_bln, en_bln in KAMUS_BULAN.items():
            val_str = val_str.replace(id_bln, en_bln)
            
        try:
            return pd.to_datetime(val_str)
        except:
            return pd.NaT

    df['tgl_awal_pelatihan'] = df['tgl_awal_pelatihan'].apply(konversi_tgl)
    df['tgl_akhir_pelatihan'] = df['tgl_akhir_pelatihan'].apply(konversi_tgl)
    
    # 6. PENANGANAN TANGGAL KOSONG UNTUK HEATMAP (VERSI BULAN INDONESIA)
    NAMA_BULAN_INDO = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                       'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    
    def format_bulan_indo(dt_val):
        if pd.isna(dt_val):
            return 'Belum terjadwal'
        return NAMA_BULAN_INDO[dt_val.month - 1]

    df['Bulan_Tahun'] = df['tgl_awal_pelatihan'].apply(format_bulan_indo)

    # 7. PASTIKAN DATA NUMERIK VALID
    df['rencana_peserta'] = pd.to_numeric(df['rencana_peserta'], errors='coerce').fillna(0)
    df['realisasi_peserta'] = pd.to_numeric(df['realisasi_peserta'], errors='coerce').fillna(0)
    
    return df

df_raw = load_data()
df_aktif = df_raw[df_raw['status_kegiatan_pelatihan'] != 'Batal']

hari_ini = pd.Timestamp.now().normalize()
batas_h12 = hari_ini + pd.Timedelta(days=12)

date_col_config = {
    "tgl_awal_pelatihan": st.column_config.DateColumn("Mulai", format="DD MMMM YYYY"),
    "tgl_akhir_pelatihan": st.column_config.DateColumn("Akhir", format="DD MMMM YYYY")
}
warna_status = {'Proses': '#1f77b4', 'Rencana': '#ff7f0e', 'Selesai': '#2ca02c'}

# ==========================================
# BAGIAN HEADER & TOMBOL REFRESH
# ==========================================
st.title("📊 Dashboard Eksekutif Pelatihan ABT")
st.markdown("**Balai Pelatihan Vokasi dan Produktivitas (BPVP) Bandung Barat**")

col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.write(f"*Data Live tersinkronisasi. Akses terakhir: {hari_ini.strftime('%d %B %Y')}*")
with col_header_2:
    if st.button("🔄 Perbarui Data Sekarang", use_container_width=True):
        st.cache_data.clear() # Membersihkan memori (cache)
        st.rerun()            # Memaksa halaman memuat ulang seketika

tabs = st.tabs(["🌟 Master Overview", "PBK-Reguler", "TMT DUDI", "LPKS", "BLKK", "UPTD", "Produktivitas"])

# ==========================================
# TAB 1: MASTER OVERVIEW
# ==========================================
with tabs[0]:
    st.subheader("Ringkasan Eksekutif: Target vs Rencana vs Realisasi")
    
    tot_tgt_paket = sum(TARGET_DIPA_PAKET.values())
    tot_ren_paket = len(df_aktif) 
    tot_real_paket = len(df_aktif[df_aktif['status_kegiatan_pelatihan'].isin(['Proses', 'Selesai'])]) 
    
    tot_tgt_peserta = sum(TARGET_DIPA_PESERTA.values())
    tot_ren_peserta = df_aktif['rencana_peserta'].sum()
    tot_real_peserta = df_aktif['realisasi_peserta'].sum()
    
    persen_ren_paket = (tot_ren_paket / tot_tgt_paket) * 100 if tot_tgt_paket > 0 else 0
    persen_real_paket = (tot_real_paket / tot_tgt_paket) * 100 if tot_tgt_paket > 0 else 0
    persen_ren_peserta = (tot_ren_peserta / tot_tgt_peserta) * 100 if tot_tgt_peserta > 0 else 0
    persen_real_peserta = (tot_real_peserta / tot_tgt_peserta) * 100 if tot_tgt_peserta > 0 else 0
    
    st.markdown("#### 📦 Dimensi Administratif (Jumlah Paket)")
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Target Paket (DIPA)", tot_tgt_paket)
    col2.metric("📝 Persentase Total Rencana", f"{persen_ren_paket:.1f}%", f"{tot_ren_paket} Paket Terdata", delta_color="off")
    col3.metric("🔄 Persentase Paket (Proses/Selesai)", f"{persen_real_paket:.1f}%", f"{tot_real_paket} Paket Terlaksana")
    
    st.write("")
    
    st.markdown("#### 👥 Dimensi Output (Jumlah Orang)")
    col4, col5, col6 = st.columns(3)
    col4.metric("🎯 Target Peserta (DIPA)", f"{tot_tgt_peserta:,}")
    col5.metric("📝 Total Rencana Peserta", f"{int(tot_ren_peserta):,}", f"{persen_ren_peserta:.1f}% dari Target", delta_color="off")
    col6.metric("🔄 Peserta Terlatih", f"{int(tot_real_peserta):,}", f"{persen_real_peserta:.1f}% dari Target")
    
    st.divider()
    
    st.markdown("#### 📅 Matriks Kinerja Bulanan per Pos Anggaran")
    st.info("💡 Paket yang belum memiliki jadwal akan terkumpul di kolom **'Belum terjadwal'** di sebelah kiri.")
    
    hm_cols = st.columns(2) 
    
    all_months_raw = df_aktif['Bulan_Tahun'].unique().tolist()
    
    # Memaksa urutan array sesuai kalender, bukan urutan abjad
    NAMA_BULAN_INDO = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                       'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    urutan_pakem = ['Belum terjadwal'] + NAMA_BULAN_INDO
    
    all_months = [m for m in urutan_pakem if m in all_months_raw]
        
    status_order = ['Rencana', 'Proses', 'Selesai'] 
    
    for idx, pos_name in enumerate(TARGET_DIPA_PAKET.keys()):
        with hm_cols[idx % 2]:
            df_pos_hm = df_aktif[df_aktif['pos_anggaran'] == pos_name]
            t_paket_hm = TARGET_DIPA_PAKET[pos_name]
            
            if df_pos_hm.empty:
                st.markdown(f"**{pos_name}** | Target = **{t_paket_hm} Paket** | Total Rencana (%) = **0.0 %** | Terlaksana = **0.0%**")
                st.info("BELUM ADA DATA RENCANA PELATIHAN")
                continue 
                
            r_paket_hm = len(df_pos_hm) 
            s_paket_hm = len(df_pos_hm[df_pos_hm['status_kegiatan_pelatihan'].isin(['Proses', 'Selesai'])])
            
            persen_rencana_hm = (r_paket_hm / t_paket_hm) * 100 if t_paket_hm > 0 else 0
            persen_terlaksana_hm = (s_paket_hm / t_paket_hm) * 100 if t_paket_hm > 0 else 0
            
            st.markdown(f"**{pos_name}** | Target = **{t_paket_hm} Paket** | Total Rencana (%) = **{persen_rencana_hm:.1f} %** | Terlaksana = **{persen_terlaksana_hm:.1f}%**")
            
            df_agregat = df_pos_hm.groupby(['status_kegiatan_pelatihan', 'Bulan_Tahun']).size().reset_index(name='Jumlah')
            pivot_hm = df_agregat.pivot(index='status_kegiatan_pelatihan', columns='Bulan_Tahun', values='Jumlah').fillna(0)
            pivot_hm = pivot_hm.reindex(index=status_order, columns=all_months).fillna(0)
            
            fig_hm = px.imshow(
                pivot_hm,
                text_auto=True,
                aspect="auto", 
                color_continuous_scale='Blues',
                labels=dict(x="", y="", color="Paket")
            )
            fig_hm.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(t=10, b=20, l=0, r=0), height=180, coloraxis_showscale=False)
            fig_hm.update_xaxes(type='category') 
            
            st.plotly_chart(fig_hm, use_container_width=True, key=f"heatmap_{pos_name}")

    st.divider()
    
    st.markdown("#### 🎓 Status Eksekusi Paket Pelatihan Bersertifikasi (Khusus UJK = Ya)")
    if 'sertifikasi' in df_aktif.columns:
        df_ujk_ya = df_aktif[df_aktif['sertifikasi'] == 'Ya']
        
        if not df_ujk_ya.empty:
            df_ujk_master_stacked = df_ujk_ya.groupby(['pos_anggaran', 'status_kegiatan_pelatihan']).size().reset_index(name='Jumlah_Paket')
            fig_ujk_master = px.bar(
                df_ujk_master_stacked, 
                x='pos_anggaran', 
                y='Jumlah_Paket', 
                color='status_kegiatan_pelatihan',
                barmode='stack',
                color_discrete_map=warna_status,
                text_auto=True,
            )
            fig_ujk_master.update_layout(xaxis_title="Pos Anggaran", yaxis_title="Jumlah Paket UJK")
            st.plotly_chart(fig_ujk_master, use_container_width=True, key="ujk_master")
        else:
            st.info("BELUM ADA DATA RENCANA PELATIHAN BER-UJK")

# ==========================================
# TAB 2-7: DETAIL PER POS
# ==========================================
for i, pos_name in enumerate(TARGET_DIPA_PAKET.keys(), start=1):
    with tabs[i]:
        st.subheader(f"Dashboard Pengendalian: {pos_name}")
        df_pos_detail = df_aktif[df_aktif['pos_anggaran'] == pos_name]
        
        if df_pos_detail.empty:
            st.info("BELUM ADA DATA RENCANA PELATIHAN")
            continue 
        
        t_paket = TARGET_DIPA_PAKET[pos_name]
        t_peserta = TARGET_DIPA_PESERTA[pos_name]
        
        r_paket = len(df_pos_detail)
        r_peserta = df_pos_detail['rencana_peserta'].sum()
        
        df_pos_proses = df_pos_detail[df_pos_detail['status_kegiatan_pelatihan'].isin(['Proses', 'Selesai'])]
        rl_paket = len(df_pos_proses)
        rl_peserta = df_pos_detail['realisasi_peserta'].sum()
        
        p_ren_paket = (r_paket/t_paket)*100 if t_paket>0 else 0
        p_real_paket = (rl_paket/t_paket)*100 if t_paket>0 else 0
        p_ren_peserta = (r_peserta/t_peserta)*100 if t_peserta>0 else 0
        p_real_peserta = (rl_peserta/t_peserta)*100 if t_peserta>0 else 0
        
        st.markdown("**Perbandingan Target dan Capaian Aktif**")
        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 Target Paket", t_paket)
        c2.metric("📝 Persentase Total Rencana", f"{p_ren_paket:.1f}%", f"{r_paket} Paket Terdata", delta_color="off")
        c3.metric("🔄 Persentase Paket (Proses/Selesai)", f"{p_real_paket:.1f}%", f"{rl_paket} Paket Terlaksana")

        c4, c5, c6 = st.columns(3)
        c4.metric("🎯 Target Peserta", f"{t_peserta:,}")
        c5.metric("📝 Total Rencana Peserta", f"{int(r_peserta):,}", f"{p_ren_peserta:.1f}% dari Target", delta_color="off")
        c6.metric("🔄 Peserta Terlatih", f"{int(rl_peserta):,}", f"{p_real_peserta:.1f}% dari Target")
        
        st.divider()

        df_warning = df_pos_detail[
            (df_pos_detail['status_kegiatan_pelatihan'] == 'Rencana') & 
            (df_pos_detail['tgl_awal_pelatihan'].notna()) &
            (df_pos_detail['tgl_awal_pelatihan'] <= batas_h12)
        ]
        
        if not df_warning.empty:
            st.error(f"🚨 **PERHATIAN:** Terdapat **{len(df_warning)} Paket** yang dijadwalkan mulai dalam waktu kurang dari 12 hari namun belum berubah status menjadi 'Proses'!")
            st.dataframe(df_warning[['id_program', 'batch_pelatihan','pelatihan', 'tgl_awal_pelatihan', 'pic_pelatihan']], column_config=date_col_config, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Terkendali: Tidak ada kegiatan Rencana yang terancam meleset dari jadwal (H-12).")
            
        st.divider()

        st.markdown("#### 🌊 Analisis Kinerja Eksekusi Berdasarkan Gelombang (Batch)")
        if 'batch_pelatihan' in df_pos_detail.columns:
            df_batch = df_pos_detail.groupby(['batch_pelatihan', 'status_kegiatan_pelatihan']).size().reset_index(name='Jumlah_Paket')
            if not df_batch.empty:
                fig_batch = px.bar(
                    df_batch, 
                    y='batch_pelatihan', 
                    x='Jumlah_Paket', 
                    color='status_kegiatan_pelatihan',
                    barmode='stack',
                    orientation='h',
                    color_discrete_map=warna_status,
                    text_auto=True,
                )
                fig_batch.update_layout(yaxis={'categoryorder':'array', 'categoryarray':['non-batch', 'batch 4', 'batch 5', 'batch 6', 'batch 7']}, yaxis_title="Gelombang Pelatihan", xaxis_title="Jumlah Paket")
                st.plotly_chart(fig_batch, use_container_width=True, key=f"batch_{pos_name}")
        st.divider()

        st.markdown("#### 🎓 Silang Data: Keberadaan UJK vs Status Pelaksanaan")
        if 'sertifikasi' in df_pos_detail.columns:
            df_ujk_pos = df_pos_detail.groupby(['sertifikasi', 'status_kegiatan_pelatihan']).size().reset_index(name='Jumlah_Paket')
            if not df_ujk_pos.empty:
                fig_ujk_pos = px.bar(
                    df_ujk_pos, 
                    x='sertifikasi', 
                    y='Jumlah_Paket', 
                    color='status_kegiatan_pelatihan',
                    barmode='group',
                    color_discrete_map=warna_status,
                    text_auto=True,
                )
                fig_ujk_pos.update_layout(xaxis_title="Apakah Memiliki UJK?", yaxis_title="Jumlah Paket")
                st.plotly_chart(fig_ujk_pos, use_container_width=True, key=f"ujk_{pos_name}")
        st.divider()

        st.markdown("#### 🎯 Tren Popularitas: Kejuruan & Program Pelatihan")
        df_kejuruan_valid = df_pos_detail[df_pos_detail['pelatihan'].notna()]
        if not df_kejuruan_valid.empty and 'kejuruan' in df_kejuruan_valid.columns:
            df_kejuruan = df_kejuruan_valid.groupby(['kejuruan', 'pelatihan']).size().reset_index(name='Frekuensi')
            df_kejuruan = df_kejuruan.sort_values(by='Frekuensi', ascending=True) 
            
            if not df_kejuruan.empty:
                fig_kejuruan = px.bar(
                    df_kejuruan, 
                    x='Frekuensi', 
                    y='pelatihan', 
                    color='kejuruan',
                    orientation='h',
                    text_auto=True,
                )
                fig_kejuruan.update_layout(yaxis_title=None, xaxis_title="Jumlah Paket Dibuka")
                st.plotly_chart(fig_kejuruan, use_container_width=True, key=f"kejuruan_{pos_name}")
        st.divider()
        
        if pos_name in ["TMT DUDI", "UPTD"]:
            st.markdown(f"#### 🏢 Evaluasi Kinerja Mitra ({pos_name})")
            df_mitra = df_pos_detail.groupby(['nama_tempat_pelatihan', 'status_kegiatan_pelatihan']).size().reset_index(name='Jumlah_Paket')
            if not df_mitra.empty:
                fig_mitra = px.bar(
                    df_mitra, y='nama_tempat_pelatihan', x='Jumlah_Paket', color='status_kegiatan_pelatihan',
                    orientation='h', barmode='stack', color_discrete_map=warna_status
                )
                fig_mitra.update_layout(yaxis={'categoryorder':'total ascending'}, yaxis_title=None)
                st.plotly_chart(fig_mitra, use_container_width=True, key=f"mitra_{pos_name}")
            st.divider()
            
        if pos_name == "PBK-Reguler":
            st.markdown("#### 👨‍🏫 Distribusi Beban Mengajar Instruktur")
            if 'instruktur' in df_pos_detail.columns:
                df_instruktur = df_pos_detail[df_pos_detail['instruktur'].notna()]
                df_instruktur = df_instruktur[df_instruktur['instruktur'] != '-']
                beban_mengajar = df_instruktur['instruktur'].value_counts().reset_index()
                beban_mengajar.columns = ['instruktur', 'Jumlah_Paket']
                if not beban_mengajar.empty:
                    fig_instruktur = px.bar(
                        beban_mengajar, x='instruktur', y='Jumlah_Paket',
                        text='Jumlah_Paket', color='Jumlah_Paket', color_continuous_scale='Blues'
                    )
                    fig_instruktur.update_layout(xaxis_title=None, yaxis_title="Jumlah Paket Dipegang")
                    st.plotly_chart(fig_instruktur, use_container_width=True, key=f"instruktur_{pos_name}")
            st.divider()
        
        st.write("Tabel Rincian Paket Pelatihan:")
        
        # --- PERBAIKAN NOMOR URUT DINAMIS ---
        # Buat salinan data agar tidak merubah data asli
        df_tabel = df_pos_detail.copy()
        
        # Timpa kolom 'no' dengan urutan baru dari 1 sampai jumlah baris data
        df_tabel['no'] = range(1, len(df_tabel) + 1)
        # -----------------------------------
        
        st.dataframe(
            df_tabel[['no', 'id_program', 'batch_pelatihan', 'kejuruan', 'pelatihan', 'nama_tempat_pelatihan', 'tgl_awal_pelatihan', 'tgl_akhir_pelatihan', 'rencana_peserta', 'realisasi_peserta', 'sertifikasi', 'status_kegiatan_pelatihan', 'pic_pelatihan']], 
            column_config=date_col_config, 
            use_container_width=True,
            hide_index=True
        )
