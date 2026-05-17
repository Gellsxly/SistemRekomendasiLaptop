import pickle
import pandas as pd
import numpy as np

# =========================
# LOAD MODEL (dictionary)
# =========================
with open('model/knn_model.pkl', 'rb') as file:
    model_data = pickle.load(file)

knn = model_data['model']
weights = model_data['weights']           # [1.0, 2.0, 1.5]
best_params = model_data['best_params']
model_accuracy = model_data['test_accuracy']

# =========================
# LOAD ENCODER & SCALER
# =========================
with open('model/label_encoder.pkl', 'rb') as file:
    label_encoder = pickle.load(file)

with open('model/scaler.pkl', 'rb') as file:
    scaler = pickle.load(file)

# =========================
# LOAD DATASET
# =========================
df = pd.read_csv('dataset/cleaned_dataset.csv')

# =========================
# RECOMMENDATION FUNCTION
# =========================
def recommend_laptop(budget, kebutuhan, ram_user=None):
    """
    Rekomendasi laptop berdasarkan budget dan kebutuhan.
    Urutan yang benar: weight → scale (sama seperti training)
    """
    # Validasi kategori
    if kebutuhan not in label_encoder.classes_:
        raise ValueError(f"Kategori '{kebutuhan}' tidak dikenali. Pilih dari: {list(label_encoder.classes_)}")

    # Tentukan RAM
    if ram_user is not None:
        ram = ram_user
    else:
        subset = df[df['kategori_kebutuhan'] == kebutuhan]
        if len(subset) > 0:
            ram = int(subset['ram'].median())
        else:
            ram = 8

    # Encode kategori
    kategori_encoded = label_encoder.transform([kebutuhan])[0]

    # Input user (fitur: price, ram, kategori_encoded)
    user_input = np.array([[budget, ram, kategori_encoded]])

    # 1. Terapkan weighting (sama seperti training) – SEBELUM scaling
    user_input_weighted = user_input * weights

    # 2. Normalisasi dengan scaler yang sudah dilatih pada weighted training data
    user_input_scaled = scaler.transform(user_input_weighted)

    # 3. Cari tetangga terdekat
    distances, indices = knn.kneighbors(user_input_scaled)

    # Ambil rekomendasi
    recommendations = df.iloc[indices[0]].copy()

    # Tambahkan distance dan similarity
    recommendations['distance'] = distances[0]
    recommendations['similarity'] = 1 / (1 + distances[0])

    # Filter duplikat: urutkan jarak → harga termurah
    recommendations = recommendations.sort_values(
        ['distance', 'price'], ascending=[True, True]
    )
    recommendations = recommendations.drop_duplicates(
        subset=['product_name'], keep='first'
    )
    recommendations = recommendations.head(5)

    # Kolom output
    output_cols = ['product_name', 'processor', 'ram', 'gpu', 'price',
                   'kategori_kebutuhan', 'distance', 'similarity']
    if 'product_url' in df.columns:
        output_cols.append('product_url')
    if 'shop_name' in df.columns:
        output_cols.append('shop_name')

    return recommendations[output_cols]

# =========================
# Ambil akurasi model (opsional)
# =========================
def get_model_accuracy():
    return model_accuracy