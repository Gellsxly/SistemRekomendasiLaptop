import pickle
import pandas as pd

# =========================
# LOAD MODEL
# =========================
with open('model/knn_model.pkl', 'rb') as file:
    knn = pickle.load(file)

# =========================
# LOAD ENCODER
# =========================
with open('model/label_encoder.pkl', 'rb') as file:
    label_encoder = pickle.load(file)

# =========================
# LOAD SCALER (PENTING!)
# =========================
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

    # Input user (fitur: budget, ram, kategori_encoded)
    user_input = [[budget, ram, kategori_encoded]]

    # NORMALISASI input user dengan scaler yang sama
    user_input_scaled = scaler.transform(user_input)

    # Cari tetangga terdekat (gunakan data yang sudah di-scale)
    distances, indices = knn.kneighbors(user_input_scaled)

    # Ambil rekomendasi
    recommendations = df.iloc[indices[0]].copy()

    # Filter duplikat: urutkan harga termurah, lalu RAM terbesar
    recommendations = recommendations.sort_values(
        ['price', 'ram'], ascending=[True, False]
    )
    recommendations = recommendations.drop_duplicates(
        subset=['product_name'], keep='first'
    )

    # Ambil 5 laptop terbaik
    recommendations = recommendations.head(5)

    # Kolom output
    output_cols = ['product_name', 'processor', 'ram', 'gpu', 'price', 'kategori_kebutuhan']
    if 'product_url' in df.columns:
        output_cols.append('product_url')
    if 'shop_name' in df.columns:
        output_cols.append('shop_name')

    return recommendations[output_cols]