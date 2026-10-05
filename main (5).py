# -*- coding: utf-8 -*-
"""
Commit 5 — Laporan Penjualan & Menu Admin
Deskripsi:
- Menu Navigasi Khusus Admin
- Fitur Rekapitulasi Data Transaksi (Melihat Riwayat Transaksi)
- Laporan Penjualan (Total Omzet, Total Transaksi, Produk Terlaris, dan Peringatan Stok Kritis)
- Integrasi Manajemen Produk (Kelola Produk & Hapus Produk)
"""

import sqlite3


def lihat_produk():
    """Menampilkan daftar produk beserta stok dan harganya."""
    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, nama_produk, harga_jual, stok FROM Produk ORDER BY id")
    data = cursor.fetchall()
    conn.close()

    print("\n===== DAFTAR PRODUK =====")
    print("-" * 65)
    print(f"{'ID':<5}{'Nama Produk':<30}{'Harga Jual':<15}{'Stok':<10}")
    print("-" * 65)

    for produk in data:
        print(f"{produk[0]:<5}{produk[1]:<30}Rp{produk[2]:<13}{produk[3]:<10}")

    print("-" * 65)


def lihat_transaksi():
    """Menampilkan riwayat seluruh transaksi yang telah terjadi."""
    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, tanggal, total_bayar FROM Transaksi ORDER BY id DESC"
    )

    data = cursor.fetchall()
    conn.close()

    print("\n===== DATA TRANSAKSI =====")
    print("-" * 60)
    print(f"{'ID':<8}{'Tanggal':<25}{'Total':<15}")
    print("-" * 60)

    if data:
        for transaksi in data:
            print(f"{transaksi[0]:<8}{transaksi[1]:<25}Rp{transaksi[2]:,}")
    else:
        print("Belum ada transaksi.")

    print("-" * 60)


def laporan_penjualan():
    """Menghasilkan statistik penjualan, produk terlaris, dan peringatan stok."""
    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()

    # Hitung total transaksi dan total omzet
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(total_bayar), 0)
        FROM Transaksi
    """)
    jumlah_transaksi, total_penjualan = cursor.fetchone()

    # Cari produk paling banyak terjual
    cursor.execute("""
        SELECT Produk.nama_produk, SUM(Detail_Transaksi.jumlah)
        FROM Detail_Transaksi 
        JOIN Produk ON Produk.id = Detail_Transaksi.id_produk
        GROUP BY Detail_Transaksi.id_produk 
        ORDER BY SUM(Detail_Transaksi.jumlah) DESC
        LIMIT 1
    """)
    produk_terlaris = cursor.fetchone()

    # Peringatan stok kritis (kurang dari 10 pcs)
    cursor.execute("""
        SELECT nama_produk, stok 
        FROM Produk 
        WHERE stok < 10
        ORDER BY stok ASC
    """)
    stok_hampir_habis = cursor.fetchall()
    conn.close()

    print("\n===== LAPORAN PENJUALAN =====")
    print("Total transaksi :", jumlah_transaksi)
    print(f"Total penjualan : Rp{total_penjualan:,}")

    print("\nProduk terlaris :")
    if produk_terlaris:
        print(f"-> {produk_terlaris[0]} - Terjual {produk_terlaris[1]} pcs")
    else:
        print("Belum ada penjualan.")

    print("\nProduk dengan stok kurang dari 10 :")
    if stok_hampir_habis:
        for produk in stok_hampir_habis:
            print(f"⚠️ {produk[0]} ({produk[1]} pcs)")
    else:
        print("✅ Tidak ada produk dengan stok kurang dari 10.")


def hapus_produk():
    """Fungsi untuk menghapus produk dari database (Fitur Khusus Admin)."""
    lihat_produk()

    try:
        id_produk = int(input("\nMasukkan ID produk yang ingin dihapus : "))
    except ValueError:
        print("ID harus berupa angka.")
        return

    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()

    cursor.execute("SELECT nama_produk FROM Produk WHERE id = ?", (id_produk,))
    produk = cursor.fetchone()

    if produk is None:
        print("Produk tidak ditemukan.")
        conn.close()
        return

    yakin = input(f"Yakin hapus '{produk[0]}'? (Y/T) : ")

    if yakin.upper() == "Y":
        cursor.execute("DELETE FROM Produk WHERE id = ?", (id_produk,))
        conn.commit()
        print("Produk berhasil dihapus.")
    else:
        print("Penghapusan dibatalkan.")

    conn.close()


def menu_admin():
    """Menu antarmuka khusus Role Admin."""
    while True:
        print("\n===== MENU ADMIN =====")
        print("1. Lihat Transaksi")
        print("2. Melihat Laporan Penjualan")
        print("3. Hapus Produk")
        print("4. Keluar / Logout")

        pilihan = input("Pilih menu : ")

        if pilihan == "1":
            lihat_transaksi()
        elif pilihan == "2":
            laporan_penjualan()
        elif pilihan == "3":
            hapus_produk()
        elif pilihan == "4":
            print("Keluar dari Menu Admin.")
            break
        else:
            print("Pilihan tidak tersedia.")


if __name__ == "__main__":
    menu_admin()