import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- SETTING PAGE STREAMLIT ---
st.set_page_config(
    page_title="Smart-Retail",
    page_icon="🛒",
    layout="wide"
)

# --- FUNGSI DATABASE ---
def init_db():
    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()
    
    # Tabel Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    
    # Tabel Produk
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_produk TEXT NOT NULL,
            harga_modal REAL NOT NULL,
            harga_jual REAL NOT NULL,
            stok INTEGER NOT NULL
        )
    """)
    
    # Tabel Transaksi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            total_bayar REAL NOT NULL,
            total_keuntungan REAL DEFAULT 0
        )
    """)
    
    # Tabel Detail_Transaksi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Detail_Transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_transaksi INTEGER NOT NULL,
            id_produk INTEGER NOT NULL,
            jumlah INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            keuntungan REAL DEFAULT 0,
            FOREIGN KEY (id_transaksi) REFERENCES Transaksi(id),
            FOREIGN KEY (id_produk) REFERENCES Produk(id)
        )
    """)
    
    # Auto Migration untuk Database Cloud (Tambah Kolom Jika Belum Ada)
    try:
        cursor.execute("ALTER TABLE Transaksi ADD COLUMN total_keuntungan REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE Detail_Transaksi ADD COLUMN keuntungan REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Tambah User Default jika kosong
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        cursor.execute("INSERT INTO Users (username, password, role) VALUES ('kasir', 'kasir123', 'Kasir')")
        
    # Tambah Produk Default jika kosong
    cursor.execute("SELECT COUNT(*) FROM Produk")
    if cursor.fetchone()[0] == 0:
        produk = [
            ('Telor ayam 1kg', 27000, 30000, 15),
            ('Gas melon 3kg', 20000, 24000, 15),
            ('Minyak nyawit 1L', 16000, 22000, 25),
            ('Air mineral 600ml', 2000, 4000, 55),
            ('Kopi item sachet', 1500, 2000, 40),
            ('Sabun batang', 3000, 5000, 20),
            ('Mie Goreng', 2500, 3500, 25),
            ('Dubai chewy cookie', 8000, 12000, 15),
            ('Salt bread cheese', 18000, 22000, 15),
            ('Minyak kayu putih 60ml', 12000, 16000, 20)
        ]
        cursor.executemany("INSERT INTO Produk (nama_produk, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?)", produk)
        
    conn.commit()
    conn.close()

# Inisialisasi Database
init_db()

# --- INITIALIZE SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# --- HALAMAN LOGIN ---
def login_page():
    st.title("🛒 SMART-RETAIL LOGISTIC SYSTEM")
    st.subheader("Silakan Login ke Akun Anda")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            conn = sqlite3.connect("smart_retail.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username, role FROM Users WHERE username = ? AND password = ?", (username, password))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                st.session_state.user = {"username": res[0], "role": res[1]}
                st.success(f"Selamat datang, {res[0]}!")
                st.rerun()
            else:
                st.error("Username atau password salah!")

# Jika belum login, tampilkan halaman login
if st.session_state.user is None:
    login_page()
    st.stop()

# --- SIDEBAR UTAMA ---
st.sidebar.title("🏪 SMART-RETAIL")
st.sidebar.write(f"👤 **User:** {st.session_state.user['username']}")
st.sidebar.write(f"🔑 **Role:** {st.session_state.user['role']}")

menu = st.sidebar.radio("MENU UTAMA", ["Kelola Produk", "Transaksi Penjualan", "Cari Produk", "Laporan Penjualan", "Logout"])

if menu == "Logout":
    st.session_state.user = None
    st.session_state.keranjang = []
    st.rerun()

# --- MENU 1: KELOLA PRODUK ---
elif menu == "Kelola Produk":
    st.title("📦 Kelola Inventaris Produk")
    
    conn = sqlite3.connect("smart_retail.db")
    
    # Form Tambah Produk
    with st.expander("➕ Tambah Produk Baru"):
        with st.form("form_tambah"):
            nama = st.text_input("Nama Produk")
            c1, c2, c3 = st.columns(3)
            modal = c1.number_input("Harga Modal (Rp)", min_value=0.0, step=1000.0)
            jual = c2.number_input("Harga Jual (Rp)", min_value=0.0, step=1000.0)
            stok = c3.number_input("Stok Awal", min_value=0, step=1)
            
            submitted = st.form_submit_button("Simpan Produk")
            if submitted:
                if nama:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Produk (nama_produk, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?)",
                                   (nama, modal, jual, stok))
                    conn.commit()
                    st.success(f"Produk '{nama}' berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Nama produk tidak boleh kosong!")
                    
    # Tabel Daftar Produk
    st.subheader("📋 Daftar Stok Produk Saat Ini")
    df_produk = pd.read_sql_query("SELECT id AS 'ID', nama_produk AS 'Nama Produk', harga_modal AS 'Harga Modal (Rp)', harga_jual AS 'Harga Jual (Rp)', stok AS 'Stok' FROM Produk", conn)
    
    if not df_produk.empty:
        df_produk.insert(0, 'No.', range(1, 1 + len(df_produk)))
        st.dataframe(df_produk, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada produk terdaftar.")

    # Edit & Hapus Produk (Khusus Admin)
    if st.session_state.user['role'] == 'Admin':
        st.markdown("---")
        st.subheader("⚙️ Edit / Hapus Produk")
        if not df_produk.empty:
            pilih_id = st.selectbox("Pilih Produk", df_produk['ID'].tolist(), format_func=lambda x: f"ID {x} - " + df_produk[df_produk['ID']==x]['Nama Produk'].values[0])
            
            p_data = df_produk[df_produk['ID'] == pilih_id].iloc[0]
            
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st.markdown("**Update Stok / Harga**")
                with st.form("edit_form"):
                    u_nama = st.text_input("Nama Produk", value=p_data['Nama Produk'])
                    u_modal = st.number_input("Harga Modal (Rp)", value=float(p_data['Harga Modal (Rp)']))
                    u_jual = st.number_input("Harga Jual (Rp)", value=float(p_data['Harga Jual (Rp)']))
                    u_stok = st.number_input("Stok", value=int(p_data['Stok']))
                    
                    if st.form_submit_button("Update Data"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Produk SET nama_produk=?, harga_modal=?, harga_jual=?, stok=? WHERE id=?",
                                       (u_nama, u_modal, u_jual, u_stok, pilih_id))
                        conn.commit()
                        st.success("Data produk berhasil diperbarui!")
                        st.rerun()
                        
            with col_e2:
                st.markdown("**Hapus Produk**")
                st.warning("Penghapusan produk bersifat permanen!")
                if st.button("🗑️ Hapus Produk Ini", type="primary"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Produk WHERE id=?", (pilih_id,))
                    conn.commit()
                    st.success("Produk berhasil dihapus!")
                    st.rerun()

    conn.close()

# --- MENU 2: TRANSAKSI PENJUALAN ---
elif menu == "Transaksi Penjualan":
    st.title("🛒 Kasir & Transaksi Penjualan")
    
    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nama_produk, harga_modal, harga_jual, stok FROM Produk WHERE stok > 0")
    list_produk = cursor.fetchall()
    
    if not list_produk:
        st.warning("Stok produk habis semua atau belum ada produk terdaftar!")
    else:
        dict_produk = {p[1]: {"id": p[0], "modal": p[2], "jual": p[3], "stok": p[4]} for p in list_produk}
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("1. Pilih Barang")
            pilihan_nama = st.selectbox("Nama Produk", list(dict_produk.keys()))
            item = dict_produk[pilihan_nama]
            
            st.info(f"📌 **Harga Jual:** Rp{item['jual']:,.0f} | 📦 **Stok Tersedia:** {item['stok']} pcs")
            
            jml = st.number_input("Jumlah Pembelian", min_value=1, max_value=item['stok'], value=1)
            
            if st.button("➕ Tambah ke Keranjang", use_container_width=True):
                subtotal = item['jual'] * jml
                keuntungan = (item['jual'] - item['modal']) * jml
                
                # Cek apakah produk sudah ada di keranjang
                found = False
                for k in st.session_state.keranjang:
                    if k['id'] == item['id']:
                        if k['jumlah'] + jml > item['stok']:
                            st.error("Jumlah melebihi stok yang tersedia!")
                            found = True
                            break
                        k['jumlah'] += jml
                        k['subtotal'] += subtotal
                        k['keuntungan'] += keuntungan
                        found = True
                        break
                if not found:
                    st.session_state.keranjang.append({
                        "id": item['id'],
                        "nama": pilihan_nama,
                        "harga": item['jual'],
                        "jumlah": jml,
                        "subtotal": subtotal,
                        "keuntungan": keuntungan
                    })
                st.success("Berhasil masuk keranjang!")
                st.rerun()
                
        with col_right:
            st.subheader("2. Keranjang Belanja")
            if st.session_state.keranjang:
                df_k = pd.DataFrame(st.session_state.keranjang)
                df_k_display = df_k[['nama', 'jumlah', 'harga', 'subtotal']].copy()
                df_k_display.columns = ['Nama Barang', 'Jumlah', 'Harga (Rp)', 'Subtotal (Rp)']
                df_k_display.insert(0, 'No.', range(1, 1 + len(df_k_display)))
                
                st.table(df_k_display)
                
                total_belanja = df_k['subtotal'].sum()
                total_untung = df_k['keuntungan'].sum()
                
                st.markdown(f"### **TOTAL BELANJA: Rp{total_belanja:,.0f}**")
                
                uang_bayar = st.number_input("Uang Bayar (Rp)", min_value=0.0, value=float(total_belanja), step=1000.0)
                kembalian = uang_bayar - total_belanja
                
                if uang_bayar < total_belanja:
                    st.error("Uang pembayaran kurang!")
                else:
                    st.success(f"Kembalian: Rp{kembalian:,.0f}")
                    
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("💳 Proses Pembayaran", type="primary", use_container_width=True):
                        tgl_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Simpan ke tabel Transaksi
                        cursor.execute("INSERT INTO Transaksi (tanggal, total_bayar, total_keuntungan) VALUES (?, ?, ?)",
                                       (tgl_now, total_belanja, total_untung))
                        id_tr = cursor.lastrowid
                        
                        # Simpan ke Detail_Transaksi & Potong Stok Produk
                        for k in st.session_state.keranjang:
                            cursor.execute("""
                                INSERT INTO Detail_Transaksi (id_transaksi, id_produk, jumlah, subtotal, keuntungan)
                                VALUES (?, ?, ?, ?, ?)
                            """, (id_tr, k['id'], k['jumlah'], k['subtotal'], k['keuntungan']))
                            
                            cursor.execute("UPDATE Produk SET stok = stok - ? WHERE id = ?", (k['jumlah'], k['id']))
                            
                        conn.commit()
                        st.session_state.keranjang = []
                        st.success("✅ Transaksi Berhasil Diproses!")
                        st.balloons()
                        st.rerun()
                        
                with col_b2:
                    if st.button("🗑️ Kosongkan Keranjang", use_container_width=True):
                        st.session_state.keranjang = []
                        st.rerun()
            else:
                st.info("Keranjang belanja masih kosong.")
                
    conn.close()

# --- MENU 3: CARI PRODUK ---
elif menu == "Cari Produk":
    st.title("🔍 Cari Produk & Cek Stok")
    
    keyword = st.text_input("Ketik nama produk yang dicari:")
    
    conn = sqlite3.connect("smart_retail.db")
    if keyword:
        query = "SELECT id AS 'ID', nama_produk AS 'Nama Produk', harga_jual AS 'Harga Jual (Rp)', stok AS 'Stok Tersedia' FROM Produk WHERE nama_produk LIKE ?"
        df_search = pd.read_sql_query(query, conn, params=(f"%{keyword}%",))
        if not df_search.empty:
            df_search.insert(0, 'No.', range(1, 1 + len(df_search)))
            st.dataframe(df_search, use_container_width=True, hide_index=True)
        else:
            st.warning("Produk tidak ditemukan!")
    else:
        df_all = pd.read_sql_query("SELECT id AS 'ID', nama_produk AS 'Nama Produk', harga_jual AS 'Harga Jual (Rp)', stok AS 'Stok Tersedia' FROM Produk", conn)
        if not df_all.empty:
            df_all.insert(0, 'No.', range(1, 1 + len(df_all)))
            st.dataframe(df_all, use_container_width=True, hide_index=True)
    conn.close()

# --- MENU 4: LAPORAN PENJUALAN ---
elif menu == "Laporan Penjualan":
    st.title("📊 Laporan Penjualan & Keuntungan")
    
    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_bayar), 0), COALESCE(SUM(total_keuntungan), 0) FROM Transaksi")
    res_summary = cursor.fetchone()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Transaksi", f"{res_summary[0]} Transaksi")
    c2.metric("Total Omset / Pendapatan", f"Rp{res_summary[1]:,.0f}")
    c3.metric("Total Keuntungan (Laba)", f"Rp{res_summary[2]:,.0f}")
    
    st.markdown("---")
    st.subheader("📜 Riwayat Seluruh Transaksi")
    
    df_tr = pd.read_sql_query("SELECT id AS 'ID Transaksi', tanggal AS 'Waktu Transaksi', total_bayar AS 'Total Bayar (Rp)', total_keuntungan AS 'Laba (Rp)' FROM Transaksi ORDER BY id DESC", conn)
    
    if not df_tr.empty:
        df_tr.insert(0, 'No.', range(1, 1 + len(df_tr)))
        st.dataframe(df_tr, use_container_width=True, hide_index=True)
        
        # Detail Rincian per Transaksi
        st.markdown("---")
        pilih_tr = st.selectbox("Pilih ID Transaksi untuk Lihat Detail Barang yang Dibeli", df_tr['ID Transaksi'].tolist())
        
        query_detail = f"""
            SELECT Produk.nama_produk AS 'Nama Barang', Detail_Transaksi.jumlah AS 'Jumlah', 
                   Detail_Transaksi.subtotal AS 'Subtotal (Rp)', Detail_Transaksi.keuntungan AS 'Laba (Rp)'
            FROM Detail_Transaksi
            JOIN Produk ON Produk.id = Detail_Transaksi.id_produk
            WHERE Detail_Transaksi.id_transaksi = {pilih_tr}
        """
        df_detail_tr = pd.read_sql_query(query_detail, conn)
        if not df_detail_tr.empty:
            df_detail_tr.insert(0, 'No.', range(1, 1 + len(df_detail_tr)))
            st.write(f"**Detail Barang pada Transaksi #{pilih_tr}:**")
            st.table(df_detail_tr)
    else:
        st.info("Belum ada riwayat transaksi.")
        
    st.markdown("---")
    st.subheader("⚠️ Produk Stok Hampir Habis (< 10 pcs)")
    df_low = pd.read_sql_query("SELECT nama_produk AS 'Nama Produk', stok AS 'Sisa Stok' FROM Produk WHERE stok < 10", conn)
    if not df_low.empty:
        df_low.insert(0, 'No.', range(1, 1 + len(df_low)))
        st.table(df_low)
    else:
        st.success("Stok semua produk masih melimpah (di atas 10 pcs)!")
        
    conn.close()