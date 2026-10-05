import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIG HALAMAN WEB ---
st.set_page_config(
    page_title="Smart-Retail Toko Maju Jaya",
    layout="wide",
    page_icon="🛒"
)

# --- FUNGSI KONEKSI DATABASE ---
def get_db():
    return sqlite3.connect("smart_retail.db")

# --- INITIALIZE DATABASE (PAKAI LOGIKA KODE SQLite KAMU) ---
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT, password TEXT, role TEXT) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS Produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nama_produk TEXT, harga_modal INTEGER, harga_jual INTEGER, stok INTEGER) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS Transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tanggal TEXT, total_bayar INTEGER) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS Detail_Transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_transaksi INTEGER, id_produk INTEGER, jumlah INTEGER, subtotal INTEGER) """)

    # User bawaan
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        users = [("SYAHREZA", "EjaAdmin", "Admin"), ("FIRAAS", "FiraasKasir", "Kasir")]
        cursor.executemany("INSERT INTO Users (username, password, role) VALUES (?, ?, ?)", users)

    # Produk bawaan
    cursor.execute("SELECT COUNT(*) FROM Produk")
    if cursor.fetchone()[0] == 0:
        produk = [
            ('Telor ayam 1kg', 27000, 30000, 15), ('Gas melon 3kg', 20000, 24000, 15), 
            ('Minyak nyawit 1L', 16000, 22000, 25), ('Air mineral 600ml', 2000, 4000, 55),
            ('Kopi item sachet', 1500, 2000, 40), ('Sabun batang', 3000, 5000, 20),
            ('Mie Goreng', 2500, 3500, 25), ('Dubai chewy cookie', 8000, 12000, 15),
            ('Salt bread cheese', 18000, 22000, 15), ('Minyak kayu putih 60ml', 12000, 16000, 10)
        ]
        cursor.executemany("INSERT INTO Produk (nama_produk, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?)", produk)

    conn.commit()
    conn.close()

init_db()

# --- INITIALIZE SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []


# ==============================================================================
# 🔑 LOGIN SISTEM
# ==============================================================================
if st.session_state.user is None:
    st.title("🏬 SMART-RETAIL (TOKO MAJU JAYA)")
    st.markdown("### *Sistem Kasir Pintar Toko Kelontong Berbasis Web*")
    st.write("---")

    col_login, col_info = st.columns([1, 1])

    with col_login:
        st.subheader("Login Pengguna")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("LOGIN", use_container_width=True)

            if submit:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM Users WHERE username = ? AND password = ?", (username, password))
                res = cursor.fetchone()
                conn.close()

                if res:
                    st.session_state.user = {"username": username, "role": res[0]}
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")

    with col_info:
        st.info("""
        💡 **Akun Bawaan (Untuk Cek Sistem):**
        - **Admin:** Username: `SYAHREZA` | Password: `EjaAdmin`
        - **Kasir:** Username: `FIRAAS` | Password: `FiraasKasir`
        """)


# ==============================================================================
# 📊 DASHBOARD UTAMA
# ==============================================================================
else:
    role = st.session_state.user["role"]

    st.sidebar.title("🏪 SMART-RETAIL")
    st.sidebar.write(f"👤 User: **{st.session_state.user['username']}**")
    st.sidebar.write(f"🔑 Role: **{role}**")
    st.sidebar.markdown("---")

    # Hak akses menu berdasarkan role
    if role == "Admin":
        menu = st.sidebar.radio("MENU UTAMA", ["Kelola Produk", "Transaksi Penjualan", "Cari Produk", "Laporan Penjualan", "Logout"])
    else:
        menu = st.sidebar.radio("MENU UTAMA", ["Transaksi Penjualan", "Lihat Produk", "Cari Produk", "Logout"])

    if menu == "Logout":
        st.session_state.user = None
        st.session_state.keranjang = []
        st.rerun()

    # --------------------------------------------------------------------------
    # 📦 KELOLA PRODUK (ADMIN)
    # --------------------------------------------------------------------------
    elif menu == "Kelola Produk":
        st.header("📦 Kelola Produk (Admin)")
        
        conn = get_db()
        df_produk = pd.read_sql_query("SELECT id AS ID, nama_produk AS 'Nama Produk', harga_modal AS 'Harga Modal (Rp)', harga_jual AS 'Harga Jual (Rp)', stok AS 'Stok' FROM Produk", conn)
        conn.close()

        st.dataframe(df_produk, use_container_width=True)

        col_tambah, col_restock, col_hapus = st.columns(3)

        with col_tambah:
            with st.expander("➕ Tambah Produk"):
                with st.form("form_tambah"):
                    nama = st.text_input("Nama Barang")
                    modal = st.number_input("Harga Modal", min_value=0, step=500)
                    jual = st.number_input("Harga Jual", min_value=0, step=500)
                    stok = st.number_input("Stok Awal", min_value=0, step=1)
                    if st.form_submit_button("Simpan Produk"):
                        if nama:
                            conn = get_db()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO Produk (nama_produk, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?)", (nama, modal, jual, stok))
                            conn.commit()
                            conn.close()
                            st.success("Produk berhasil ditambahkan!")
                            st.rerun()

        with col_restock:
            with st.expander("🔄 Restock Produk"):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nama_produk FROM Produk")
                list_p = cursor.fetchall()
                conn.close()
                
                if list_p:
                    p_restock = st.selectbox("Pilih Produk", list_p, format_func=lambda x: f"ID {x[0]} - {x[1]}", key="restock")
                    j_restock = st.number_input("Jumlah Restock", min_value=1, value=1)
                    if st.button("Restock Sekarang"):
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Produk SET stok = stok + ? WHERE id = ?", (j_restock, p_restock[0]))
                        conn.commit()
                        conn.close()
                        st.success("Restock berhasil!")
                        st.rerun()

        with col_hapus:
            with st.expander("🗑️ Hapus Produk"):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nama_produk FROM Produk")
                list_p_hapus = cursor.fetchall()
                conn.close()

                if list_p_hapus:
                    p_hapus = st.selectbox("Pilih Produk Dihapus", list_p_hapus, format_func=lambda x: f"ID {x[0]} - {x[1]}", key="hapus")
                    if st.button("Hapus Produk", type="primary"):
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM Produk WHERE id = ?", (p_hapus[0],))
                        conn.commit()
                        conn.close()
                        st.success("Produk dihapus!")
                        st.rerun()

    # --------------------------------------------------------------------------
    # 🛒 TRANSAKSI PENJUALAN & VALIDASI STOK
    # --------------------------------------------------------------------------
    elif menu == "Transaksi Penjualan":
        st.header("🛒 Transaksi Penjualan")

        conn = get_db()
        df_produk = pd.read_sql_query("SELECT id, nama_produk, harga_jual, stok FROM Produk", conn)
        conn.close()

        col_kiri, col_kanan = st.columns([1, 1])

        with col_kiri:
            st.subheader("1. Pilih Produk")
            pilih_id = st.selectbox(
                "Pilih Barang", 
                df_produk['id'].tolist(), 
                format_func=lambda x: f"{df_produk[df_produk['id']==x]['nama_produk'].values[0]} (ID: {x})"
            )
            detail = df_produk[df_produk['id'] == pilih_id].iloc[0]

            st.info(f"📌 **Harga:** Rp{detail['harga_jual']:,} | 📦 **Stok Tersedia:** {detail['stok']} pcs")
            jumlah_beli = st.number_input("Jumlah Pembelian", min_value=1, value=1)

            if st.button("➕ Tambah ke Keranjang", use_container_width=True):
                stok_di_keranjang = sum(item['jumlah'] for item in st.session_state.keranjang if item['id'] == detail['id'])
                
                # Validasi stok
                if (jumlah_beli + stok_di_keranjang) > detail['stok']:
                    st.error(f"❌ **ERROR: Stok tidak mencukupi!**\nStok tersedia: {detail['stok']}")
                else:
                    ada = False
                    for item in st.session_state.keranjang:
                        if item['id'] == detail['id']:
                            item['jumlah'] += jumlah_beli
                            item['subtotal'] += detail['harga_jual'] * jumlah_beli
                            ada = True
                            break
                    if not ada:
                        st.session_state.keranjang.append({
                            "id": detail['id'],
                            "nama": detail['nama_produk'],
                            "harga": detail['harga_jual'],
                            "jumlah": jumlah_beli,
                            "subtotal": detail['harga_jual'] * jumlah_beli
                        })
                    st.success("Barang ditambahkan ke keranjang!")
                    st.rerun()

        with col_kanan:
            st.subheader("2. Struk Belanja / Keranjang")
            if st.session_state.keranjang:
                df_k = pd.DataFrame(st.session_state.keranjang)
                st.dataframe(df_k[['nama', 'jumlah', 'harga', 'subtotal']], use_container_width=True)

                total = sum(i['subtotal'] for i in st.session_state.keranjang)
                st.markdown(f"### **TOTAL BELANJA: Rp{total:,}**")

                uang_bayar = st.number_input("Uang Bayar (Rp)", min_value=0, step=1000)

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("💳 Proses Pembayaran", use_container_width=True, type="primary"):
                        if uang_bayar < total:
                            st.error("❌ Uang pembayaran kurang!")
                        else:
                            kembalian = uang_bayar - total
                            
                            # Simpan transaksi ke SQLite & kurangi stok
                            conn = get_db()
                            cursor = conn.cursor()
                            tgl = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            cursor.execute("INSERT INTO Transaksi (tanggal, total_bayar) VALUES (?, ?)", (tgl, total))
                            tr_id = cursor.lastrowid

                            for item in st.session_state.keranjang:
                                cursor.execute("INSERT INTO Detail_Transaksi (id_transaksi, id_produk, jumlah, subtotal) VALUES (?, ?, ?, ?)",
                                               (tr_id, item['id'], item['jumlah'], item['subtotal']))
                                cursor.execute("UPDATE Produk SET stok = stok - ? WHERE id = ?", (item['jumlah'], item['id']))

                            conn.commit()
                            conn.close()

                            st.balloons()
                            st.success(f"🎉 **TRANSAKSI BERHASIL!**\n\n- No. Transaksi: **#{tr_id}**\n- Kembalian: **Rp{kembalian:,}**")
                            st.session_state.keranjang = []
                
                with col_b2:
                    if st.button("🧹 Kosongkan Keranjang", use_container_width=True):
                        st.session_state.keranjang = []
                        st.rerun()
            else:
                st.warning("Keranjang belanjaan masih kosong.")

    # --------------------------------------------------------------------------
    # 🔍 CARI PRODUK
    # --------------------------------------------------------------------------
    elif menu in ["Cari Produk", "Lihat Produk"]:
        st.header("🔍 Cari & Lihat Produk")
        keyword = st.text_input("Ketik Nama Produk atau ID Produk:")

        conn = get_db()
        if keyword:
            if keyword.isdigit():
                query = f"SELECT id AS ID, nama_produk AS 'Nama Produk', harga_jual AS 'Harga Jual', stok AS Stok FROM Produk WHERE id = {int(keyword)}"
            else:
                query = f"SELECT id AS ID, nama_produk AS 'Nama Produk', harga_jual AS 'Harga Jual', stok AS Stok FROM Produk WHERE nama_produk LIKE '%{keyword}%'"
        else:
            query = "SELECT id AS ID, nama_produk AS 'Nama Produk', harga_jual AS 'Harga Jual', stok AS Stok FROM Produk"

        df_cari = pd.read_sql_query(query, conn)
        conn.close()

        st.dataframe(df_cari, use_container_width=True)

    # --------------------------------------------------------------------------
    # 📈 LAPORAN PENJUALAN
    # --------------------------------------------------------------------------
    elif menu == "Laporan Penjualan":
        st.header("📊 Laporan Penjualan")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_bayar), 0) FROM Transaksi")
        tot_tr, tot_penj = cursor.fetchone()

        cursor.execute(""" 
            SELECT Produk.nama_produk, SUM(Detail_Transaksi.jumlah)
            FROM Detail_Transaksi JOIN Produk ON Produk.id = Detail_Transaksi.id_produk
            GROUP BY Detail_Transaksi.id_produk ORDER BY SUM(Detail_Transaksi.jumlah) DESC LIMIT 1 
        """)
        terlaris = cursor.fetchone()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transaksi", f"{tot_tr} Transaksi")
        col2.metric("Total Pendapatan", f"Rp{tot_penj:,}")
        col3.metric("Produk Terlaris", f"{terlaris[0] if terlaris else '-'}", f"{terlaris[1] if terlaris else 0} pcs")

        st.markdown("---")
        st.subheader("⚠️ Produk Stok Hampir Habis (< 10 pcs)")
        df_low = pd.read_sql_query("SELECT id AS ID, nama_produk AS 'Nama Produk', stok AS 'Sisa Stok' FROM Produk WHERE stok < 10 ORDER BY stok ASC", conn)
        
        if not df_low.empty:
            st.warning("Produk ini perlu segera di-restock!")
            st.dataframe(df_low, use_container_width=True)
        else:
            st.success("Semua stok produk saat ini masih aman (>= 10 pcs).")

        st.markdown("---")
        st.subheader("📜 Riwayat Transaksi")
        df_tr = pd.read_sql_query("SELECT id AS 'ID Transaksi', tanggal AS 'Tanggal & Waktu', total_bayar AS 'Total Bayar (Rp)' FROM Transaksi ORDER BY id DESC", conn)
        st.dataframe(df_tr, use_container_width=True)

        conn.close()
        import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIG HALAMAN WEB ---
st.set_page_config(
    page_title="Smart-Retail Toko Maju Jaya",
    layout="wide",
    page_icon="🛒"
)

# --- FUNGSI KONEKSI DATABASE ---
def get_db():
    return sqlite3.connect("smart_retail.db")

# --- INITIALIZE DATABASE ---
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT, password TEXT, role TEXT) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS Produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nama_produk TEXT, harga_modal INTEGER, harga_jual INTEGER, stok INTEGER) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS Transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tanggal TEXT, total_bayar INTEGER, total_keuntungan INTEGER) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS Detail_Transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_transaksi INTEGER, id_produk INTEGER, jumlah INTEGER, subtotal INTEGER, keuntungan INTEGER) """)

    # User bawaan
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        users = [("SYAHREZA", "EjaAdmin", "Admin"), ("FIRAAS", "FiraasKasir", "Kasir")]
        cursor.executemany("INSERT INTO Users (username, password, role) VALUES (?, ?, ?)", users)

    # Produk bawaan
    cursor.execute("SELECT COUNT(*) FROM Produk")
    if cursor.fetchone()[0] == 0:
        produk = [
            ('Telor ayam 1kg', 27000, 30000, 15), ('Gas melon 3kg', 20000, 24000, 15), 
            ('Minyak nyawit 1L', 16000, 22000, 25), ('Air mineral 600ml', 2000, 4000, 55),
            ('Kopi item sachet', 1500, 2000, 40), ('Sabun batang', 3000, 5000, 20),
            ('Mie Goreng', 2500, 3500, 25), ('Dubai chewy cookie', 8000, 12000, 15),
            ('Salt bread cheese', 18000, 22000, 15), ('Minyak kayu putih 60ml', 12000, 16000, 10)
        ]
        cursor.executemany("INSERT INTO Produk (nama_produk, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?)", produk)

    conn.commit()
    conn.close()

init_db()

# --- INITIALIZE SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []


# ==============================================================================
# 🔑 LOGIN SISTEM
# ==============================================================================
if st.session_state.user is None:
    st.title("🏬 SMART-RETAIL (TOKO MAJU JAYA)")
    st.markdown("### *Sistem Kasir Pintar Toko Kelontong Berbasis Web*")
    st.write("---")

    col_login, col_info = st.columns([1, 1])

    with col_login:
        st.subheader("Login Pengguna")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("LOGIN", use_container_width=True)

            if submit:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM Users WHERE username = ? AND password = ?", (username, password))
                res = cursor.fetchone()
                conn.close()

                if res:
                    st.session_state.user = {"username": username, "role": res[0]}
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")

    with col_info:
        st.info("""
        💡 **Akun Bawaan (Untuk Cek Sistem):**
        - **Admin:** Username: `SYAHREZA` | Password: `EjaAdmin`
        - **Kasir:** Username: `FIRAAS` | Password: `FiraasKasir`
        """)


# ==============================================================================
# 📊 DASHBOARD UTAMA
# ==============================================================================
else:
    role = st.session_state.user["role"]

    st.sidebar.title("🏪 SMART-RETAIL")
    st.sidebar.write(f"👤 User: **{st.session_state.user['username']}**")
    st.sidebar.write(f"🔑 Role: **{role}**")
    st.sidebar.markdown("---")

    if role == "Admin":
        menu = st.sidebar.radio("MENU UTAMA", ["Kelola Produk", "Transaksi Penjualan", "Cari Produk", "Laporan Penjualan", "Logout"])
    else:
        menu = st.sidebar.radio("MENU UTAMA", ["Transaksi Penjualan", "Lihat Produk", "Cari Produk", "Logout"])

    if menu == "Logout":
        st.session_state.user = None
        st.session_state.keranjang = []
        st.rerun()

    # --------------------------------------------------------------------------
    # 📦 KELOLA PRODUK (ADMIN)
    # --------------------------------------------------------------------------
    elif menu == "Kelola Produk":
        st.header("📦 Kelola Produk (Admin)")
        
        conn = get_db()
        df_produk = pd.read_sql_query("SELECT id AS 'ID Sistem', nama_produk AS 'Nama Produk', harga_modal AS 'Harga Modal (Rp)', harga_jual AS 'Harga Jual (Rp)', stok AS 'Stok' FROM Produk", conn)
        conn.close()

        # PENOMORAN OTOMATIS URUT (1, 2, 3...) DITAMPILAN
        df_produk.insert(0, 'No.', range(1, 1 + len(df_produk)))
        st.dataframe(df_produk, use_container_width=True, hide_index=True)

        col_tambah, col_restock, col_hapus = st.columns(3)

        with col_tambah:
            with st.expander("➕ Tambah Produk"):
                with st.form("form_tambah"):
                    nama = st.text_input("Nama Barang")
                    modal = st.number_input("Harga Modal", min_value=0, step=500)
                    jual = st.number_input("Harga Jual", min_value=0, step=500)
                    stok = st.number_input("Stok Awal", min_value=0, step=1)
                    if st.form_submit_button("Simpan Produk"):
                        if nama:
                            conn = get_db()
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO Produk (nama_produk, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?)", (nama, modal, jual, stok))
                            conn.commit()
                            conn.close()
                            st.success("Produk berhasil ditambahkan!")
                            st.rerun()

        with col_restock:
            with st.expander("🔄 Restock Produk"):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nama_produk FROM Produk")
                list_p = cursor.fetchall()
                conn.close()
                
                if list_p:
                    p_restock = st.selectbox("Pilih Produk", list_p, format_func=lambda x: f"{x[1]} (ID: {x[0]})", key="restock")
                    j_restock = st.number_input("Jumlah Restock", min_value=1, value=1)
                    if st.button("Restock Sekarang"):
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Produk SET stok = stok + ? WHERE id = ?", (j_restock, p_restock[0]))
                        conn.commit()
                        conn.close()
                        st.success("Restock berhasil!")
                        st.rerun()

        with col_hapus:
            with st.expander("🗑️ Hapus Produk"):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nama_produk FROM Produk")
                list_p_hapus = cursor.fetchall()
                conn.close()

                if list_p_hapus:
                    p_hapus = st.selectbox("Pilih Produk Dihapus", list_p_hapus, format_func=lambda x: f"{x[1]} (ID: {x[0]})", key="hapus")
                    if st.button("Hapus Produk", type="primary"):
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM Produk WHERE id = ?", (p_hapus[0],))
                        conn.commit()
                        conn.close()
                        st.success("Produk dihapus!")
                        st.rerun()

    # --------------------------------------------------------------------------
    # 🛒 TRANSAKSI PENJUALAN & VALIDASI STOK
    # --------------------------------------------------------------------------
    elif menu == "Transaksi Penjualan":
        st.header("🛒 Transaksi Penjualan")

        conn = get_db()
        df_produk = pd.read_sql_query("SELECT id, nama_produk, harga_modal, harga_jual, stok FROM Produk", conn)
        conn.close()

        col_kiri, col_kanan = st.columns([1, 1])

        with col_kiri:
            st.subheader("1. Pilih Produk")
            pilih_id = st.selectbox(
                "Pilih Barang", 
                df_produk['id'].tolist(), 
                format_func=lambda x: f"{df_produk[df_produk['id']==x]['nama_produk'].values[0]}"
            )
            detail = df_produk[df_produk['id'] == pilih_id].iloc[0]

            st.info(f"📌 **Harga Jual:** Rp{detail['harga_jual']:,} | 📦 **Stok Tersedia:** {detail['stok']} pcs")
            jumlah_beli = st.number_input("Jumlah Pembelian", min_value=1, value=1)

            if st.button("➕ Tambah ke Keranjang", use_container_width=True):
                stok_di_keranjang = sum(item['jumlah'] for item in st.session_state.keranjang if item['id'] == detail['id'])
                
                if (jumlah_beli + stok_di_keranjang) > detail['stok']:
                    st.error(f"❌ **ERROR: Stok tidak mencukupi!** Sisa stok: {detail['stok']}")
                else:
                    keuntungan_per_unit = detail['harga_jual'] - detail['harga_modal']
                    ada = False
                    for item in st.session_state.keranjang:
                        if item['id'] == detail['id']:
                            item['jumlah'] += jumlah_beli
                            item['subtotal'] += detail['harga_jual'] * jumlah_beli
                            item['total_keuntungan'] += keuntungan_per_unit * jumlah_beli
                            ada = True
                            break
                    if not ada:
                        st.session_state.keranjang.append({
                            "id": detail['id'],
                            "nama": detail['nama_produk'],
                            "harga": detail['harga_jual'],
                            "jumlah": jumlah_beli,
                            "subtotal": detail['harga_jual'] * jumlah_beli,
                            "total_keuntungan": keuntungan_per_unit * jumlah_beli
                        })
                    st.success("Barang ditambahkan ke keranjang!")
                    st.rerun()

        with col_kanan:
            st.subheader("2. Struk Belanja / Keranjang")
            if st.session_state.keranjang:
                df_k = pd.DataFrame(st.session_state.keranjang)
                df_k.insert(0, 'No.', range(1, 1 + len(df_k)))
                st.dataframe(df_k[['No.', 'nama', 'jumlah', 'harga', 'subtotal']], use_container_width=True, hide_index=True)

                total = sum(i['subtotal'] for i in st.session_state.keranjang)
                total_untung = sum(i['total_keuntungan'] for i in st.session_state.keranjang)
                
                st.markdown(f"### **TOTAL BELANJA: Rp{total:,}**")

                uang_bayar = st.number_input("Uang Bayar (Rp)", min_value=0, step=1000)

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("💳 Proses Pembayaran", use_container_width=True, type="primary"):
                        if uang_bayar < total:
                            st.error("❌ Uang pembayaran kurang!")
                        else:
                            kembalian = uang_bayar - total
                            
                            conn = get_db()
                            cursor = conn.cursor()
                            tgl = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            cursor.execute("INSERT INTO Transaksi (tanggal, total_bayar, total_keuntungan) VALUES (?, ?, ?)", 
                                           (tgl, total, total_untung))
                            tr_id = cursor.lastrowid

                            for item in st.session_state.keranjang:
                                cursor.execute("INSERT INTO Detail_Transaksi (id_transaksi, id_produk, jumlah, subtotal, keuntungan) VALUES (?, ?, ?, ?, ?)",
                                               (tr_id, item['id'], item['jumlah'], item['subtotal'], item['total_keuntungan']))
                                
                                cursor.execute("UPDATE Produk SET stok = stok - ? WHERE id = ?", (item['jumlah'], item['id']))

                            conn.commit()
                            conn.close()

                            st.balloons()
                            st.success(f"🎉 **TRANSAKSI BERHASIL!**\n\n- No. Transaksi: **#{tr_id}**\n- Kembalian: **Rp{kembalian:,}**")
                            st.session_state.keranjang = []
                            st.rerun()
                
                with col_b2:
                    if st.button("🧹 Kosongkan Keranjang", use_container_width=True):
                        st.session_state.keranjang = []
                        st.rerun()
            else:
                st.warning("Keranjang belanjaan masih kosong.")

    # --------------------------------------------------------------------------
    # 🔍 CARI PRODUK
    # --------------------------------------------------------------------------
    elif menu in ["Cari Produk", "Lihat Produk"]:
        st.header("🔍 Cari & Lihat Produk")
        keyword = st.text_input("Ketik Nama Produk:")

        conn = get_db()
        if keyword:
            query = f"SELECT id AS 'ID Sistem', nama_produk AS 'Nama Produk', harga_jual AS 'Harga Jual', stok AS Stok FROM Produk WHERE nama_produk LIKE '%{keyword}%'"
        else:
            query = "SELECT id AS 'ID Sistem', nama_produk AS 'Nama Produk', harga_jual AS 'Harga Jual', stok AS Stok FROM Produk"

        df_cari = pd.read_sql_query(query, conn)
        conn.close()

        df_cari.insert(0, 'No.', range(1, 1 + len(df_cari)))
        st.dataframe(df_cari, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # 📈 LAPORAN PENJUALAN & DETAIL TRANSAKSI
    # --------------------------------------------------------------------------
    elif menu == "Laporan Penjualan":
        st.header("📊 Laporan Penjualan & Keuntungan")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_bayar), 0), COALESCE(SUM(total_keuntungan), 0) FROM Transaksi")
        tot_tr, tot_penj, tot_profit = cursor.fetchone()

        cursor.execute(""" 
            SELECT Produk.nama_produk, SUM(Detail_Transaksi.jumlah)
            FROM Detail_Transaksi JOIN Produk ON Produk.id = Detail_Transaksi.id_produk
            GROUP BY Detail_Transaksi.id_produk ORDER BY SUM(Detail_Transaksi.jumlah) DESC LIMIT 1 
        """)
        terlaris = cursor.fetchone()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Transaksi", f"{tot_tr} Transaksi")
        col2.metric("Total Omset", f"Rp{tot_penj:,}")
        col3.metric("Total Keuntungan (Laba)", f"Rp{tot_profit:,}")
        col4.metric("Produk Terlaris", f"{terlaris[0] if terlaris else '-'}", f"{terlaris[1] if terlaris else 0} pcs")

        st.markdown("---")
        st.subheader("📜 Riwayat & Detail Barang Yang Dibeli")
        
        df_tr = pd.read_sql_query("SELECT id AS 'ID Transaksi', tanggal AS 'Waktu', total_bayar AS 'Total Bayar (Rp)', total_keuntungan AS 'Keuntungan (Rp)' FROM Transaksi ORDER BY id DESC", conn)
        if not df_tr.empty:
            df_tr.insert(0, 'No.', range(1, 1 + len(df_tr)))
            st.dataframe(df_tr, use_container_width=True, hide_index=True)

            pilih_tr = st.selectbox("Pilih ID Transaksi untuk Lihat Detail Barang yang Dibeli:", df_tr['ID Transaksi'].tolist())
            
            query_detail = f"""
                SELECT Produk.nama_produk AS 'Nama Barang', Detail_Transaksi.jumlah AS 'Jumlah Dibeli', 
                       Detail_Transaksi.subtotal AS 'Subtotal (Rp)', Detail_Transaksi.keuntungan AS 'Keuntungan (Rp)'
                FROM Detail_Transaksi 
                JOIN Produk ON Produk.id = Detail_Transaksi.id_produk
                WHERE Detail_Transaksi.id_transaksi = {pilih_tr}
            """
            df_detail_tr = pd.read_sql_query(query_detail, conn)
            df_detail_tr.insert(0, 'No.', range(1, 1 + len(df_detail_tr)))
            st.write(f"**Detail Barang pada Transaksi #{pilih_tr}:**")
            st.table(df_detail_tr)

        st.markdown("---")
        st.subheader("⚠️ Produk Stok Hampir Habis (< 10 pcs)")
        df_low = pd.read_sql_query("SELECT nama_produk AS 'Nama Produk', stok AS 'Sisa Stok' FROM Produk WHERE stok < 10 ORDER BY stok ASC", conn)
        
        if not df_low.empty:
            df_low.insert(0, 'No.', range(1, 1 + len(df_low)))
            st.warning("Produk ini perlu segera di-restock!")
            st.dataframe(df_low, use_container_width=True, hide_index=True)
        else:
            st.success("Semua stok produk saat ini masih aman (>= 10 pcs).")

        conn.close()