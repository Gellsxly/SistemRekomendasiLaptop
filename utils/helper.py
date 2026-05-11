# Format harga rupiah

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(',', '.')