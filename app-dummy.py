import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Monitoring ABT", layout="wide")

TARGET_DIPA_PAKET = {"PBK-Reguler": 237, "TMT DUDI": 238, "LPKS": 31, "BLKK": 32, "UPTD": 46, "Produktivitas": 2}
TARGET_DIPA_PESERTA = {pos: (paket * 25 if pos == "Produktivitas" else paket * 16) for pos, paket in TARGET_DIPA_PAKET.items()}

@st.cache_data
def load_data():
    df = pd.read_csv("dummy_master_abt_final.csv")
    df['tgl_awal_pelatihan'] = pd.to_datetime(df['tgl_awal_pelatihan'])
    df['tgl_akhir_pelatihan'] = pd.to_datetime(df['tgl_akhir_pelatihan'])
    df['Bulan_Tahun'] = df['tgl_awal_pelatihan'].dt.strftime('%Y-%m')
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

st.title("📊 Dashboard Eksekutif Pelatihan ABT")
st.markdown("**Balai Pelatihan Vokasi dan Produktivitas (BPVP) Bandung Barat**")
st.write(f"*Data per tanggal: {hari_ini.strftime('%d %B %Y')}*")

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
    col2.metric("📝 Persentase Rencana Paket", f"{persen_ren_paket:.1f}%", f"{tot_ren_paket} Paket Terencana", delta_color="off")
    col3.metric("🔄 Persentase Paket (Proses/Selesai)", f"{persen_real_paket:.1f}%", f"{tot_real_paket} Paket Terlaksana")
    
    st.write("")
    
    st.markdown("#### 👥 Dimensi Output (Jumlah Orang)")
    col4, col5, col6 = st.columns(3)
    col4.metric("🎯 Target Peserta (DIPA)", f"{tot_tgt_peserta:,}")
    col5.metric("📝 Rencana Peserta", f"{tot_ren_peserta:,}", f"{persen_ren_peserta:.1f}% dari Target", delta_color="off")
    col6.metric("🔄 Peserta Terlatih", f"{tot_real_peserta:,}", f"{persen_real_peserta:.1f}% dari Target")
    
    st.divider()
    
    st.markdown("#### 📅 Matriks Kinerja Bulanan per Pos Anggaran")
    st.info("💡 Warna pekat menyoroti konsentrasi jadwal. Anda kini bisa fokus melihat siklus Rencana ➔ Proses ➔ Selesai di masing-masing Pos Anggaran.")
    
    hm_cols = st.columns(2) 
    
    all_months = sorted(df_aktif['Bulan_Tahun'].unique())
    status_order = ['Rencana', 'Proses', 'Selesai'] 
    
    for idx, pos_name in enumerate(TARGET_DIPA_PAKET.keys()):
        with hm_cols[idx % 2]:
            df_pos_hm = df_aktif[df_aktif['pos_anggaran'] == pos_name]
            
            t_paket_hm = TARGET_DIPA_PAKET[pos_name]
            total_paket_hm = len(df_pos_hm)
            r_paket_hm = len(df_pos_hm[df_pos_hm['status_kegiatan_pelatihan'] == 'Rencana'])
            s_paket_hm = len(df_pos_hm[df_pos_hm['status_kegiatan_pelatihan'].isin(['Proses', 'Selesai'])])
            
            st.markdown(f"**{pos_name}** | Target: **{t_paket_hm}** | Rencana: **{r_paket_hm}** | Terlaksana: **{s_paket_hm}**")
            
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
            st.plotly_chart(fig_hm, use_container_width=True)

    st.divider()
    
    st.markdown("#### 🎓 Status Eksekusi Paket Pelatihan Bersertifikasi (Khusus UJK = Ya)")
    df_ujk_ya = df_aktif[df_aktif['sertifikasi'] == 'Ya']
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
    st.plotly_chart(fig_ujk_master, use_container_width=True)

# ==========================================
# TAB 2-7: DETAIL PER POS
# ==========================================
for i, pos_name in enumerate(TARGET_DIPA_PAKET.keys(), start=1):
    with tabs[i]:
        st.subheader(f"Dashboard Pengendalian: {pos_name}")
        df_pos_detail = df_aktif[df_aktif['pos_anggaran'] == pos_name]
        
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
        c2.metric("📝 Persentase Rencana Paket", f"{p_ren_paket:.1f}%", f"{r_paket} Paket Terencana", delta_color="off")
        c3.metric("🔄 Persentase Paket (Proses/Selesai)", f"{p_real_paket:.1f}%", f"{rl_paket} Paket Terlaksana")

        c4, c5, c6 = st.columns(3)
        c4.metric("🎯 Target Peserta", f"{t_peserta:,}")
        c5.metric("📝 Rencana Peserta", f"{r_peserta:,}", f"{p_ren_peserta:.1f}% dari Target", delta_color="off")
        c6.metric("🔄 Peserta Terlatih", f"{rl_peserta:,}", f"{p_real_peserta:.1f}% dari Target")
        
        st.divider()

        df_warning = df_pos_detail[
            (df_pos_detail['status_kegiatan_pelatihan'] == 'Rencana') & 
            (df_pos_detail['tgl_awal_pelatihan'] <= batas_h12)
        ]
        
        if not df_warning.empty:
            st.error(f"🚨 **PERHATIAN:** Terdapat **{len(df_warning)} Paket** yang dijadwalkan mulai dalam waktu kurang dari 12 hari namun belum berubah status menjadi 'Proses'!")
            st.dataframe(df_warning[['id_program', 'pelatihan', 'tgl_awal_pelatihan', 'pic_pelatihan']], column_config=date_col_config, use_container_width=True)
        else:
            st.success("✅ Terkendali: Tidak ada kegiatan Rencana yang terancam meleset dari jadwal (H-12).")
            
        st.divider()

        # --- REKOMENDASI BARU: ANALISIS KINERJA PER BATCH (GELOMBANG) ---
        st.markdown("#### 🌊 Analisis Kinerja Eksekusi Berdasarkan Gelombang (Batch)")
        st.info("💡 Grafik ini membantu mendeteksi kemacetan. Jika batch awal (contoh: Batch 4) masih didominasi warna Oranye (Rencana), berarti ada penundaan pelaksanaan oleh PIC.")
        
        df_batch = df_pos_detail.groupby(['batch_pelatihan', 'status_kegiatan_pelatihan']).size().reset_index(name='Jumlah_Paket')
        fig_batch = px.bar(
            df_batch, 
            y='batch_pelatihan', 
            x='Jumlah_Paket', 
            color='status_kegiatan_pelatihan',
            barmode='stack',
            orientation='h',
            color_discrete_map=warna_status,
            text_auto=True,
            title="Sebaran Status Eksekusi Paket Pelatihan per Gelombang"
        )
        # Mengurutkan y-axis agar berurutan logis secara kronologis
        fig_batch.update_layout(yaxis={'categoryorder':'array', 'categoryarray':['non-batch', 'batch 4', 'batch 5', 'batch 6', 'batch 7']}, yaxis_title="Gelombang Pelatihan", xaxis_title="Jumlah Paket")
        st.plotly_chart(fig_batch, use_container_width=True)
        st.divider()

        st.markdown("#### 🎓 Silang Data: Keberadaan UJK vs Status Pelaksanaan")
        df_ujk_pos = df_pos_detail.groupby(['sertifikasi', 'status_kegiatan_pelatihan']).size().reset_index(name='Jumlah_Paket')
        fig_ujk_pos = px.bar(
            df_ujk_pos, 
            x='sertifikasi', 
            y='Jumlah_Paket', 
            color='status_kegiatan_pelatihan',
            barmode='group',
            color_discrete_map=warna_status,
            text_auto=True,
            title="Sebaran Status Kegiatan Berdasarkan Target Sertifikasi"
        )
        fig_ujk_pos.update_layout(xaxis_title="Apakah Memiliki UJK?", yaxis_title="Jumlah Paket")
        st.plotly_chart(fig_ujk_pos, use_container_width=True)
        st.divider()

        st.markdown("#### 🎯 Tren Popularitas: Kejuruan & Program Pelatihan")
        df_kejuruan = df_pos_detail.groupby(['kejuruan', 'pelatihan']).size().reset_index(name='Frekuensi')
        df_kejuruan = df_kejuruan.sort_values(by='Frekuensi', ascending=True) 
        
        fig_kejuruan = px.bar(
            df_kejuruan, 
            x='Frekuensi', 
            y='pelatihan', 
            color='kejuruan',
            orientation='h',
            text_auto=True,
            title="Distribusi Program Pelatihan (Dikelompokkan berdasarkan Kejuruan)"
        )
        fig_kejuruan.update_layout(yaxis_title=None, xaxis_title="Jumlah Paket Dibuka")
        st.plotly_chart(fig_kejuruan, use_container_width=True)
        st.divider()
        
        if pos_name in ["TMT DUDI", "UPTD"]:
            st.markdown(f"#### 🏢 Evaluasi Kinerja Mitra ({pos_name})")
            df_mitra = df_pos_detail.groupby(['nama_tempat_pelatihan', 'status_kegiatan_pelatihan']).size().reset_index(name='Jumlah_Paket')
            fig_mitra = px.bar(
                df_mitra, y='nama_tempat_pelatihan', x='Jumlah_Paket', color='status_kegiatan_pelatihan',
                orientation='h', barmode='stack', color_discrete_map=warna_status
            )
            fig_mitra.update_layout(yaxis={'categoryorder':'total ascending'}, yaxis_title=None)
            st.plotly_chart(fig_mitra, use_container_width=True)
            st.divider()
            
        if pos_name == "PBK-Reguler":
            st.markdown("#### 👨‍🏫 Distribusi Beban Mengajar Instruktur")
            df_instruktur = df_pos_detail[df_pos_detail['instruktur'] != '-']
            beban_mengajar = df_instruktur['instruktur'].value_counts().reset_index()
            beban_mengajar.columns = ['instruktur', 'Jumlah_Paket']
            fig_instruktur = px.bar(
                beban_mengajar, x='instruktur', y='Jumlah_Paket',
                text='Jumlah_Paket', color='Jumlah_Paket', color_continuous_scale='Blues'
            )
            fig_instruktur.update_layout(xaxis_title=None, yaxis_title="Jumlah Paket Dipegang")
            st.plotly_chart(fig_instruktur, use_container_width=True)
            st.divider()
        
        st.write("Tabel Rincian Paket Pelatihan:")
        # Render ulang urutan kolom persis dengan permintaan Anda
        st.dataframe(
            df_pos_detail[['no', 'id_program', 'batch_pelatihan', 'kejuruan', 'pelatihan', 'nama_tempat_pelatihan', 'tgl_awal_pelatihan', 'tgl_akhir_pelatihan', 'rencana_peserta', 'realisasi_peserta', 'sertifikasi', 'status_kegiatan_pelatihan', 'pic_pelatihan']], 
            column_config=date_col_config, 
            use_container_width=True,
            hide_index=True
        )