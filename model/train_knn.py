import pandas as pd
import pickle
import sys
import os
import re
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import train_test_split

# Tambahkan folder induk ke sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.parser import extract_ram, extract_processor, extract_gpu

# =====================================================
# 1. LOAD & PRE-PROCESSING
# =====================================================
df = pd.read_csv('dataset/final_dataset.csv')
df.columns = df.columns.str.lower()
print("Kolom dataset:")
print(df.columns)

# =====================================================
# Parsing spesifikasi
# =====================================================
df['ram'] = df['product_name'].apply(extract_ram)
df['processor'] = df['product_name'].apply(extract_processor)
df['gpu'] = df['product_name'].apply(extract_gpu)

# =====================================================
# Deteksi multiple RAM (ambil yang terkecil)
# =====================================================
def get_min_ram(text):
    matches = re.findall(r'(\d+)\s?GB', str(text), re.IGNORECASE)
    if matches:
        return min(map(int, matches))
    return None

df['ram_min'] = df['product_name'].apply(get_min_ram)
mask_multiple = df['ram_min'].notna() & (df['ram_min'] < df['ram'].astype(int))
if mask_multiple.any():
    print(f"\n⚠️ Ditemukan {mask_multiple.sum()} produk dengan multiple RAM mentions. Menggunakan RAM terkecil.")
    df.loc[mask_multiple, 'ram'] = df.loc[mask_multiple, 'ram_min']

# =====================================================
# Debug GPU Apple/MacBook (opsional)
# =====================================================
print("\n🔍 DEBUG: Cek produk Apple/MacBook")
mask_apple = df['product_name'].str.contains('MacBook|Apple', case=False, na=False)
if mask_apple.any():
    print(df.loc[mask_apple, ['product_name', 'gpu']].head(5))
else:
    print("Tidak ada produk Apple/MacBook ditemukan dalam dataset.")

print("\n📊 Distribusi GPU (10 terbanyak):")
print(df['gpu'].value_counts().head(10))

# =====================================================
# Bersihkan harga dan RAM
# =====================================================
df['price'] = df['price'].astype(str).str.replace(r'\D', '', regex=True)
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
df = df.dropna(subset=['price', 'ram']).copy()
df['price'] = df['price'].astype(int)
df['ram'] = df['ram'].astype(int)

# =====================================================
# Encoding kategori
# =====================================================
label_encoder = LabelEncoder()
df['kategori_encoded'] = label_encoder.fit_transform(df['kategori_kebutuhan'])

# =====================================================
# Fitur dan bobot
# =====================================================
features = ['price', 'ram', 'kategori_encoded']
weights = np.array([1.0, 2.0, 1.5])

# =====================================================
# Train-test split
# =====================================================
df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df['kategori_kebutuhan'])

X_train_weighted = df_train[features].values * weights
X_test_weighted = df_test[features].values * weights

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_weighted)
X_test_scaled = scaler.transform(X_test_weighted)

# =====================================================
# Grid search parameter terbaik
# =====================================================
def evaluate_params(n_neigh, metric_type):
    n_neigh_safe = min(n_neigh, len(X_train_scaled))
    knn_temp = NearestNeighbors(n_neighbors=n_neigh_safe, metric=metric_type)
    knn_temp.fit(X_train_scaled)
    distances, indices = knn_temp.kneighbors(X_test_scaled)
    predictions = []
    for i in range(len(indices)):
        neighbor_cats = df_train.iloc[indices[i]]['kategori_encoded'].values
        pred_cat = np.bincount(neighbor_cats).argmax()
        predictions.append(pred_cat)
    query_cats = df_test['kategori_encoded'].values
    accuracy = np.mean(np.array(predictions) == query_cats)
    return accuracy, np.mean(distances)

print("\n--- EKSPERIMEN PARAMETER ---")
best_score = -1
best_params = {}
for metric in ['euclidean', 'manhattan']:
    for k in [3, 5, 7]:
        acc, dist = evaluate_params(k, metric)
        print(f"Metric: {metric:10} | K: {k} | Acc: {acc:.2%} | Avg Dist: {dist:.4f}")
        if acc > best_score:
            best_score = acc
            best_params = {'n_neighbors': k, 'metric': metric}

# =====================================================
# Training final dengan seluruh data
# =====================================================
X_full_weighted = df[features].values * weights
scaler_full = StandardScaler()
X_full_scaled = scaler_full.fit_transform(X_full_weighted)
final_knn = NearestNeighbors(**best_params)
final_knn.fit(X_full_scaled)

# =====================================================
# Simpan model dan artifact
# =====================================================
os.makedirs('model', exist_ok=True)

model_data = {
    'model': final_knn,
    'weights': weights,
    'features': features,
    'best_params': best_params,
    'test_accuracy': best_score
}
with open('model/knn_model.pkl', 'wb') as f:
    pickle.dump(model_data, f)

with open('model/label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)

with open('model/scaler.pkl', 'wb') as f:
    pickle.dump(scaler_full, f)

accuracy_data = {
    'default_accuracy': best_score,
    'default_params': best_params,
    'best_accuracy': best_score,
    'best_params': best_params,
    'n_samples': len(df)
}
with open('model/model_accuracy.pkl', 'wb') as f:
    pickle.dump(accuracy_data, f)

df.to_csv('dataset/cleaned_dataset.csv', index=False)

print(f"\n✅ Selesai!")
print(f"🏆 Parameter terbaik: {best_params}")
print(f"🎯 Akurasi pada data test: {best_score:.2%}")
print(f"📦 Total produk dalam database: {len(df)}")