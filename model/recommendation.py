import pickle
import pandas as pd
import numpy as np
import os

# =====================================================
# 1. LOAD MODEL & METADATA ONE-HOT
# =====================================================
try:
    with open('model/best_model.pkl', 'rb') as f:
        best_model = pickle.load(f)
    print(f"🎯 Loaded best model: {best_model.get('type', 'unknown')} with accuracy {best_model.get('accuracy', 0):.2%}")
except FileNotFoundError:
    raise FileNotFoundError("Wajib menjalankan script training terlebih dahulu agar 'model/best_model.pkl' tersedia.")

# Load Target Label Encoder (Berisi 3 kelas: 'Editing_Rendering', 'Gaming', 'Office_Coding')
with open('model/label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

# Load Dataset Bersih Hasil Training
df = pd.read_csv('dataset/cleaned_dataset.csv')

# Ambil komponen penting dari hasil training
model_type = best_model['type']
scaler = best_model['scaler']
features = best_model['features']
encoded_columns = best_model['encoded_columns']
core_model = best_model['model']
model_accuracy = best_model['accuracy']

# Rekonstruksi database berfitur lengkap untuk perhitungan jarak di runtime
df_encoded_db = pd.get_dummies(df, columns=['processor', 'gpu'], prefix=['proc', 'gpu'], dtype=int)

# Jika ada kolom dummy yang hilang di database saat get_dummies, tambahkan dengan nilai 0
for col in encoded_columns:
    if col not in df_encoded_db.columns:
        df_encoded_db[col] = 0

# Urutkan kolom sesuai struktur fitur training
X_database = df_encoded_db[features].values
X_database_scaled = scaler.transform(X_database)

if model_type == 'weighted_knn':
    weights = np.array(best_model['weights'])
    X_database_scaled = X_database_scaled * weights


# =====================================================
# 2. FUNGSI UTAMA REKOMENDASI
# =====================================================
def recommend_laptop(budget, kebutuhan, ram_user=None):
    """
    Memberikan rekomendasi laptop berdasarkan budget mentah, kebutuhan asli, dan preferensi RAM.
    """
    # -------------------------------------------------
    # A. MAPPING KATEGORI USER KE 3 KELAS BARU
    # -------------------------------------------------
    mapping_kebutuhan = {
        'Office': 'Office_Coding',
        'Coding': 'Office_Coding',
        'Office_Coding': 'Office_Coding',
        'Editing': 'Editing_Rendering',
        'Rendering': 'Editing_Rendering',
        'Editing_Rendering': 'Editing_Rendering',
        'Gaming': 'Gaming'
    }
    
    kebutuhan_mapped = mapping_kebutuhan.get(kebutuhan)
    if not kebutuhan_mapped:
        raise ValueError(f"Kategori '{kebutuhan}' tidak dikenali. Pilih dari: Office, Coding, Editing, Rendering, Gaming")

    # -------------------------------------------------
    # B. TRANSLASI BUDGET MENTAH -> PRICE TIER (BINNING)
    # -------------------------------------------------
    if budget <= 7000000:
        price_tier = 1
    elif budget <= 12000000:
        price_tier = 2
    elif budget <= 20000000:
        price_tier = 3
    else:
        price_tier = 4

    # -------------------------------------------------
    # C. TENTUKAN RAM DEFAULT / USER
    # -------------------------------------------------
    if ram_user is not None:
        ram = int(ram_user)
    else:
        subset_kebutuhan = df[df['kategori_3'] == kebutuhan_mapped]
        ram = int(subset_kebutuhan['ram'].median()) if len(subset_kebutuhan) > 0 else 8

    # -------------------------------------------------
    # D. CARI KARAKTERISTIK PROC & GPU (MODE)
    # -------------------------------------------------
    subset_kebutuhan = df[df['kategori_3'] == kebutuhan_mapped]
    if not subset_kebutuhan.empty:
        mode_proc = subset_kebutuhan['processor'].mode()[0]
        mode_gpu = subset_kebutuhan['gpu'].mode()[0]
    else:
        mode_proc = df['processor'].mode()[0]
        mode_gpu = df['gpu'].mode()[0]

    # -------------------------------------------------
    # E. CONSTRUCT USER VECTOR DENGAN ONE-HOT ALIGNMENT
    # -------------------------------------------------
    user_dict = {'price_tier': price_tier, 'ram': ram}
    
    for col in encoded_columns:
        user_dict[col] = 0
        
    target_proc_col = f"proc_{mode_proc}"
    target_gpu_col = f"gpu_{mode_gpu}"
    
    if target_proc_col in user_dict:
        user_dict[target_proc_col] = 1
    if target_gpu_col in user_dict:
        user_dict[target_gpu_col] = 1

    df_user = pd.DataFrame([user_dict])[features]
    user_vector = df_user.values
    
    user_scaled = scaler.transform(user_vector)

    # -------------------------------------------------
    # F. PROSES REKOMENDASI BERDASARKAN ALGORITMA
    # -------------------------------------------------
    if model_type in ['knn', 'weighted_knn']:
        if model_type == 'weighted_knn':
            user_scaled = user_scaled * weights
        
        distances, indices = core_model.kneighbors(user_scaled)
        
        recommendations = df.iloc[indices[0]].copy()
        recommendations['distance'] = distances[0]
        recommendations['similarity'] = 1 / (1 + distances[0])

    elif model_type == 'random_forest':
        distances = np.linalg.norm(X_database_scaled - user_scaled, axis=1)
        
        df_result = df.copy()
        df_result['distance'] = distances
        df_result['similarity'] = 1 / (1 + distances)
        
        filtered = df_result[df_result['kategori_3'] == kebutuhan_mapped].copy()
        if filtered.empty:
            filtered = df_result.copy()
            
        recommendations = filtered.sort_values('distance', ascending=True)

    else:
        raise ValueError(f"Model type '{model_type}' tidak didukung oleh sistem inference.")

    # -------------------------------------------------
    # G. POST-PROCESSING (PEMBERSIHAN DATA)
    # -------------------------------------------------
    recommendations = recommendations.drop_duplicates(subset=['product_name'], keep='first')
    
    max_budget_tolerance = budget * 1.15
    recommendations = recommendations[recommendations['price'] <= max_budget_tolerance]
    
    if recommendations.empty:
        if model_type in ['knn', 'weighted_knn']:
            recommendations = df.iloc[indices[0]].copy()
            recommendations['distance'] = distances[0]
            recommendations['similarity'] = 1 / (1 + distances[0])
        else:
            recommendations = filtered.sort_values('distance', ascending=True)

    recommendations = recommendations.sort_values(['distance', 'price'], ascending=[True, True])
    recommendations = recommendations.head(5)

    output_cols = ['product_name', 'processor', 'ram', 'gpu', 'price', 
                   'kategori_3', 'distance', 'similarity']
    
    for extra_col in ['product_url', 'shop_name']:
        if extra_col in df.columns:
            output_cols.append(extra_col)
            
    existing_cols = [c for c in output_cols if c in recommendations.columns]
    return recommendations[existing_cols]

def get_model_accuracy():
    return model_accuracy