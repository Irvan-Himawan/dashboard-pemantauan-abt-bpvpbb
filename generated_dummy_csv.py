import pandas as pd
import random
from datetime import datetime, timedelta

# Target DIPA
target_paket = {"PBK-Reguler": 237, "TMT DUDI": 238, "LPKS": 31, "BLKK": 32, "UPTD": 46, "Produktivitas": 2}

katalog_kejuruan = {
    "Bisnis Manajemen": ["Digital Marketing", "Administrasi Perkantoran", "Customer Service"],
    "Teknologi Informasi (TIK)": ["Desain Grafis", "Web Development", "Network Administrator"],
    "Pariwisata": ["Barista", "Housekeeping", "Tour Guide"],
    "Teknik Manufaktur": ["Las SMAW", "Operator Mesin Bubut"],
    "Garmen Apparel": ["Fashion Technology", "Menjahit Komponen Pakaian"],
    "Otomotif": ["Mekanik Sepeda Motor", "Teknisi AC Mobil"],
    "Produktivitas": ["Peningkatan Produktivitas Perusahaan"]
}

instruktur_asli = [
    "Asep Suherman, S.T", "Iwan Hermawan, S.Kom.", "Dian Rahim, S.Tr.T.", "Rakka Putri Ranati, S.TP.", 
    "Syani Ghozali Fauzan, S.Tr.T.", "Suci Pebrianti Putri, S.Par.", "Salwa Caesar Ramadhanty Supratman, S.Pd.", 
    "Ratih Azizah, S.Pi.", "Zeaty Abdillah, S.Pi.", "Firdausi Nurfalah, S.Pi.", 
    "I Nyoman Didi Harizena, S.P., M.Si.", "Zulzamal Zepri, S.P.", "Alexander Julius Simamora, S.P.", 
    "Lucy Natami Figna, S.P., M.Si.", "Egi Setiana, S.P.", "Muhamad Najibulloh, S.Pt., M.Si.", 
    "Nita Wulandari, S.Pt.", "Velayati Nurrachma Rizqi, S.Pt.", "Alya Rahmaisyanti, S.Pt.", 
    "Danu Unggul Ardiyanto, S.M.", "Hendra Gunawan, S.M", "Ulfimarjan, S.TP.", "Ervin Puluhulawa, S.TP.", 
    "Lina Aulia Rahmah, S.TP.", "Resya Rhema Malinda, S.TP."
]
instruktur_dummy = ["Budi Santoso", "Siti Aminah", "Agus Setiawan", "Rina Marlina", "Hendra Wijaya"]
uptd_mitra = ["UPTD BLK Indramayu", "UPTD BLK Bandung Barat", "UPTD BLK Kab. Bandung", "UPTD BLK Subang", "UPTD BLK Kab. Cirebon"]
kandidat_pic = ["Fajar Nugraha", "Rizky Ramadhan", "Annisa Fitriani", "Bagus Wicaksono", "Dinda Maharani"]

jadwal_instruktur = {nama: [] for nama in instruktur_asli + instruktur_dummy}

def cek_bentrok(start1, end1, start2, end2):
    return max(start1, start2) <= min(end1, end2)

def cari_instruktur_kosong(start_date, end_date, daftar_kandidat):
    kandidat_kosong = []
    for instruktur in daftar_kandidat:
        bentrok = False
        for (s, e) in jadwal_instruktur[instruktur]:
            if cek_bentrok(start_date, end_date, s, e):
                bentrok = True
                break
        if not bentrok:
            kandidat_kosong.append(instruktur)
    return kandidat_kosong

start_date_global = datetime(2026, 8, 10)
end_date_global = datetime(2026, 12, 20)
delta_days_global = (end_date_global - start_date_global).days

data = []
paket_counter = 1

print("Membangun data dummy V7 (Skema Kolom Database Baru)...")

for pos, target in target_paket.items():
    rencana_input = target if pos == "Produktivitas" else int(target * random.uniform(0.8, 0.95))
    
    for _ in range(rencana_input):
        kode_pos = pos.replace("-", "").split()[0].upper()[:4]
        id_program = f"{kode_pos}-2026-{paket_counter:03d}"
        
        kejuruan = "Produktivitas" if pos == "Produktivitas" else random.choice(list(katalog_kejuruan.keys())[:-1])
        pelatihan = random.choice(katalog_kejuruan[kejuruan])
        
        if pos == "PBK-Reguler":
            lokasi = random.choice(["Dalam Balai", "Luar Balai"])
            nama_tempat_pelatihan = "-" if lokasi == "Dalam Balai" else f"LPK Mitra {random.randint(1,20)} (Dummy)"
        elif pos == "UPTD":
            lokasi, nama_tempat_pelatihan = "Luar Balai", random.choice(uptd_mitra)
        else:
            lokasi, nama_tempat_pelatihan = "Luar Balai", f"Perusahaan Mitra {random.randint(1,50)}"
            
        rencana_peserta = 25 if pos == "Produktivitas" else 16
        jumlah_jp = random.choice([80, 100, 120, 140, 160, 200, 240])
        durasi_hari = jumlah_jp // 10
        
        status_rand = random.random()
        if status_rand < 0.30: 
            status, realisasi_peserta = "Proses", rencana_peserta - random.choice([0, 0, 1])
        elif status_rand < 0.95:
            status, realisasi_peserta = "Rencana", 0
        else:
            status, realisasi_peserta = "Batal", 0

        kandidat_pool = instruktur_asli if pos == "PBK-Reguler" else instruktur_dummy
        pengajar = "-"
        
        if status != "Batal":
            for _ in range(50):
                tgl_mulai_coba = start_date_global + timedelta(days=random.randint(0, delta_days_global - durasi_hari))
                tgl_akhir_coba = tgl_mulai_coba + timedelta(days=durasi_hari - 1)
                
                kandidat_tersedia = cari_instruktur_kosong(tgl_mulai_coba, tgl_akhir_coba, kandidat_pool)
                if kandidat_tersedia:
                    pengajar = random.choice(kandidat_tersedia)
                    jadwal_instruktur[pengajar].append((tgl_mulai_coba, tgl_akhir_coba))
                    tgl_awal_pelatihan = tgl_mulai_coba
                    tgl_akhir_pelatihan = tgl_akhir_coba
                    break
            if pengajar == "-":
                tgl_awal_pelatihan = datetime(2026, 12, 1)
                tgl_akhir_pelatihan = tgl_awal_pelatihan + timedelta(days=durasi_hari - 1)
                pengajar = random.choice(kandidat_pool)
        else:
            tgl_awal_pelatihan = start_date_global + timedelta(days=random.randint(0, 100))
            tgl_akhir_pelatihan = tgl_awal_pelatihan + timedelta(days=durasi_hari - 1)

        # LOGIKA BATCH BERDASARKAN BULAN 
        bulan_mulai = tgl_awal_pelatihan.month
        if bulan_mulai <= 8:
            batch_pelatihan = random.choice(["batch 4", "batch 5"])
        elif bulan_mulai == 9:
            batch_pelatihan = random.choice(["batch 5", "batch 6"])
        elif bulan_mulai >= 10:
            batch_pelatihan = random.choice(["batch 6", "batch 7"])
        else:
            batch_pelatihan = "non-batch"
            
        # Beberapa paket di-set ke non-batch secara acak
        if random.random() < 0.15:
            batch_pelatihan = "non-batch"

        data.append({
            "no": paket_counter,
            "id_program": id_program,
            "pos_anggaran": pos, # WAJIB ADA UNTUK SISTEM DASHBOARD
            "nama_tempat_pelatihan": nama_tempat_pelatihan,
            "kejuruan": kejuruan,
            "pelatihan": pelatihan,
            "instruktur": pengajar,
            "jumlah_jp": jumlah_jp,
            "tgl_awal_pelatihan": tgl_awal_pelatihan.strftime("%Y-%m-%d"),
            "tgl_akhir_pelatihan": tgl_akhir_pelatihan.strftime("%Y-%m-%d"),
            "status_kegiatan_pelatihan": status,
            "rencana_peserta": rencana_peserta,
            "realisasi_peserta": realisasi_peserta,
            "sertifikasi": random.choice(["Ya", "Tidak"]),
            "pic_pelatihan": random.choice(kandidat_pic),
            "batch_pelatihan": batch_pelatihan
        })
        paket_counter += 1

df = pd.DataFrame(data)
df.to_csv("dummy_master_abt_final.csv", index=False)
print("File CSV V7 Berhasil Dibuat!")