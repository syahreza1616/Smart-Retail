# -*- coding: utf-8 -*-
"""
Commit 4 — Modul Transaksi
Deskripsi:
- Menu transaksi penjualan (kasir)
- Menampilkan daftar produk & pencarian stok
- Input ID produk & jumlah barang
- Validasi stok & kalkulasi subtotal
- Opsi tambah barang ke keranjang
- Hitung total belanja, pembayaran, dan kembalian
- Update/pengurangan stok otomatis di database SQLite
- Pencetakan struk belanja & penyimpanan Detail_Transaksi
"""

import sqlite3
from datetime import datetime


def lihat_produk():
    """Menampilkan daftar produk beserta harga dan stok saat ini."""
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


def transaksi_penjualan():
    """Fungsi utama untuk memproses transaksi penjualan kasir."""
    keranjang = []

    while True:
        lihat_produk()

        try:
            id_produk = int(input("\nMasukkan ID produk : "))
            jumlah = int(input("Jumlah pembelian : "))
        except ValueError:
            print("Input harus berupa angka.")
            continue

        if jumlah <= 0:
            print("Jumlah harus lebih dari 0.")
            continue

        conn = sqlite3.connect("smart_retail.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, nama_produk, harga_jual, stok FROM Produk WHERE id = ?",
            (id_produk,),
        )
        produk = cursor.fetchone()
        conn.close()

        if produk is None:
            print("Produk tidak ditemukan.")
            continue

        id_barang, nama, harga, stok = produk

        # Hitung akumulasi barang jika sudah ada di keranjang
        jumlah_lama = 0
        for item in keranjang:
            if item[0] == id_barang:
                jumlah_lama = item[2]

        # Validasi kecukupan stok
        if jumlah + jumlah_lama > stok:
            print("Stok tidak mencukupi.")
            print(f"Stok tersedia : {stok}")
            continue

        subtotal = harga * jumlah
        ada = False

        # Perbarui jumlah dan subtotal jika produk sudah ada di keranjang
        for item in keranjang:
            if item[0] == id_barang:
                item[2] += jumlah
                item[3] += subtotal
                ada = True
                break

        if not ada:
            keranjang.append([id_barang, nama, jumlah, subtotal, harga])

        print(f"Produk '{nama}' berhasil ditambahkan ke keranjang.")

        tambah = input("Tambah barang lain? (Y/T) : ")
        if tambah.upper() != "Y":
            break

    if not keranjang:
        print("Keranjang belanja masih kosong.")
        return

    # --- STRUK BELANJA & KETENTUAN BAYAR ---
    print("\n" + "=" * 55)
    print("                STRUK BELANJA TOKO                ")
    print("=" * 55)

    total = 0
    for item in keranjang:
        id_barang, nama, jumlah, subtotal, harga = item
        print(f"{nama:<25} | {jumlah:>2} x Rp{harga:<8,} = Rp{subtotal:,}")
        total += subtotal

    print("-" * 55)
    print(f"TOTAL BELANJA : Rp{total:,}")
    print("-" * 55)

    # Input Nominal Pembayaran
    while True:
        try:
            bayar = int(input("Uang bayar    : Rp"))
        except ValueError:
            print("Uang bayar harus berupa angka.")
            continue

        if bayar < total:
            print("Uang pembayaran kurang.")
        else:
            break

    kembalian = bayar - total
    print(f"KEMBALIAN     : Rp{kembalian:,}")
    print("=" * 55)

    # --- SIMPAN TRANSAKSI DAN UPDATE STOK BARANG ---
    conn = sqlite3.connect("smart_retail.db")
    cursor = conn.cursor()

    tanggal = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # 1. Simpan Header Transaksi
    cursor.execute(
        "INSERT INTO Transaksi (tanggal, total_bayar) VALUES (?, ?)",
        (tanggal, total),
    )
    id_transaksi = cursor.lastrowid

    # 2. Simpan Detail Transaksi dan Kurangi Stok Produk di DB
    for item in keranjang:
        id_barang, nama, jumlah, subtotal, harga = item

        cursor.execute(
            "INSERT INTO Detail_Transaksi (id_transaksi, id_produk, jumlah, subtotal) VALUES (?, ?, ?, ?)",
            (id_transaksi, id_barang, jumlah, subtotal),
        )

        cursor.execute(
            "UPDATE Produk SET stok = stok - ? WHERE id = ?",
            (jumlah, id_barang),
        )

    conn.commit()
    conn.close()

    print("-" * 55)
    print("Transaksi berhasil disimpan.")
    print("Nomor transaksi :", id_transaksi)


def menu_transaksi():
    """Menu antarmuka untuk Modul Transaksi."""
    while True:
        print("\n===== MODUL TRANSAKSI Penjualan =====")
        print("1. Transaksi Penjualan")
        print("2. Lihat Daftar Produk")
        print("3. Keluar Modul Transaksi")

        pilihan = input("Pilih menu : ")

        if pilihan == "1":
            transaksi_penjualan()
        elif pilihan == "2":
            lihat_produk()
        elif pilihan == "3":
            print("Keluar dari Modul Transaksi.")
            break
        else:
            print("Pilihan tidak tersedia.")


if __name__ == "__main__":
    menu_transaksi()