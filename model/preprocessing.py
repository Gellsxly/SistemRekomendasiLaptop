import pandas as pd
import numpy as np
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.parser import extract_ram, extract_processor, extract_gpu

# Load dataset
gaming = pd.read_csv('dataset/gaming_laptop.csv')
office = pd.read_csv('dataset/office_laptop.csv')
coding = pd.read_csv('dataset/coding_laptop.csv')
editing = pd.read_csv('dataset/editing_laptop.csv')
rendering = pd.read_csv('dataset/rendering_laptop.csv')

# =====================================================
# STRATEGI A: MEREDUKSI AMBIGUITAS DENGAN MERGE KATEGORI
# =====================================================
gaming['kategori_kebutuhan'] = 'Gaming'
office['kategori_kebutuhan'] = 'Office_Coding'
coding['kategori_kebutuhan'] = 'Office_Coding'
editing['kategori_kebutuhan'] = 'Editing_Rendering'
rendering['kategori_kebutuhan'] = 'Editing_Rendering'

# Gabungkan dataset
df = pd.concat([
    gaming,
    office,
    coding,
    editing,
    rendering
], ignore_index=True)

df.columns = df.columns.str.lower()

# Pastikan kolom required ada, jika tidak ada maka isi dengan nilai default
required_cols = ['product_name', 'price', 'kategori_kebutuhan']
for col in required_cols:
    if col not in df.columns:
        if col == 'product_name':
            df['product_name'] = 'Unknown Product'
        elif col == 'price':
            df['price'] = 0
        elif col == 'kategori_kebutuhan':
            df['kategori_kebutuhan'] = 'Gaming'

# =====================================================
# PARSING SPESIFIKASI DARI PRODUCT_NAME
# =====================================================
df['ram'] = df['product_name'].apply(extract_ram)
df['processor'] = df['product_name'].apply(extract_processor)
df['gpu'] = df['product_name'].apply(extract_gpu)

# Deteksi multiple RAM (ambil terkecil)
def get_min_ram(text):
    matches = re.findall(r'(\d+)\s?GB', str(text), re.IGNORECASE)
    if matches:
        return min(map(int, matches))
    return None

df['ram_min'] = df['product_name'].apply(get_min_ram)
mask_multiple = df['ram_min'].notna() & (df['ram_min'] < df['ram'].astype(str).str.extract('(\d+)', expand=False).astype(float, errors='ignore'))
if mask_multiple.any():
    df.loc[mask_multiple, 'ram'] = df.loc[mask_multiple, 'ram_min']

# Clean harga terlebih dahulu agar binning akurat
df['price'] = df['price'].astype(str).str.replace(r'\D', '', regex=True)
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df = df.dropna(subset=['price']).copy()
df['price'] = df['price'].astype(int)

# Konversi RAM ke integer
df['ram'] = pd.to_numeric(df['ram'], errors='coerce').astype('Int64')

# =====================================================
# STRATEGI STRUKTUR: BINNING HARGA (ORDINAL SCALING)
# =====================================================
price_bins = [0, 7000000, 12000000, 20000000, np.inf]
price_labels = [1, 2, 3, 4]

df['price_tier'] = pd.cut(df['price'], bins=price_bins, labels=price_labels).astype(int)

# =====================================================
# PEMBERSIHAN DATA
# =====================================================
# Buang baris dengan RAM atau price_tier kosong
df = df.dropna(subset=['ram', 'price_tier']).copy()
df['ram'] = df['ram'].astype(int)
df['price_tier'] = df['price_tier'].astype(int)

# Handle missing processor dan gpu
df['processor'] = df['processor'].fillna('Unknown')
df['gpu'] = df['gpu'].fillna('Integrated')

# Pastikan ada kolom product_url dan shop_name untuk inference
if 'product_url' not in df.columns:
    df['product_url'] = ''
if 'shop_name' not in df.columns:
    df['shop_name'] = ''

# Simpan final dataset
os.makedirs('dataset', exist_ok=True)
df.to_csv('dataset/final_dataset.csv', index=False)

print('✅ Final dataset dengan Penggabungan Kategori & Price Binning berhasil dibuat!')
print(f"📊 Distribusi kategori baru:\n{df['kategori_kebutuhan'].value_counts()}")
print(f"📊 Jumlah samples: {len(df)}")
print(f"📊 Kolom tersedia: {list(df.columns)}")