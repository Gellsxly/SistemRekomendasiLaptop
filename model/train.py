import pandas as pd
import pickle
import sys
import os
import re
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.parser import extract_ram, extract_processor, extract_gpu

# =====================================================
# 1. LOAD & PRE-PROCESSING (3 KATEGORI BARU)
# =====================================================
df = pd.read_csv('dataset/final_dataset.csv')
df.columns = df.columns.str.lower()

# Parsing spesifikasi menggunakan fungsi parser terbaru (Kebal VRAM & Storage)
print("⏳ Mengekstrak spesifikasi text mining produk...")
df['ram'] = df['product_name'].apply(extract_ram)
df['processor'] = df['product_name'].apply(extract_processor)
df['gpu'] = df['product_name'].apply(extract_gpu)

# Pastikan tipe data angka aman
df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
df['price_tier'] = pd.to_numeric(df['price_tier'], errors='coerce')

# Buang baris kosong yang melibatkan ram ATAU price_tier agar dimensi matriks X konsisten
df = df.dropna(subset=['ram', 'price_tier']).copy()
df['ram'] = df['ram'].astype(int)
df['price_tier'] = df['price_tier'].astype(int)

# Handle missing processor dan gpu
df['processor'] = df['processor'].fillna('Unknown')
df['gpu'] = df['gpu'].fillna('Integrated')

# 🎯 SINKRONISASI: Mapping 5 kategori lama ke 3 kelas utama hasil optimasi
category_mapping = {
    'Gaming': 'Gaming',
    'Office': 'Office_Coding',
    'Coding': 'Office_Coding',
    'Editing': 'Editing_Rendering',
    'Rendering': 'Editing_Rendering'
}
df['kategori_3'] = df['kategori_kebutuhan'].map(category_mapping)

# Encode kategori target 3 kelas
label_encoder = LabelEncoder()
df['kategori_encoded'] = label_encoder.fit_transform(df['kategori_3'])

# =====================================================
# STRATEGI STRUKTUR: ONE-HOT ENCODING (PROCESSOR & GPU)
# =====================================================
unique_processors = sorted(df['processor'].unique())
unique_gpus = sorted(df['gpu'].unique())

df_encoded = pd.get_dummies(df, columns=['processor', 'gpu'], prefix=['proc', 'gpu'], dtype=int)

# Ambil semua kolom baru hasil One-Hot Encoding
encoded_cols = [col for col in df_encoded.columns if col.startswith('proc_') or col.startswith('gpu_')]

# Definisikan fitur baru
features = ['price_tier', 'ram'] + encoded_cols
X = df_encoded[features].values
y = df_encoded['kategori_encoded'].values

print(f"📊 Dataset: {len(df_encoded)} samples, {len(features)} total features")
print(f"🎯 Target classes (3): {list(label_encoder.classes_)}")

# =====================================================
# 2. SPLIT DATA
# =====================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"✓ Train size: {len(X_train)}, Test size: {len(X_test)}")

# =====================================================
# 3. STANDARDISASI
# =====================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print(f"✓ Data standardized successfully.")

# =====================================================
# 4. EVALUATION FUNCTION
# =====================================================
def evaluate_model(y_true, y_pred, model_name):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    print(f"\n{model_name}\n  Accuracy:  {acc:.4f}\n  Precision: {prec:.4f}\n  Recall:    {rec:.4f}\n  F1-Score:  {f1:.4f}")
    return {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}

# =====================================================
# 5. MODEL 1: KNN
# =====================================================
print("\n" + "="*50 + "\nMODEL 1: K-NEAREST NEIGHBORS\n" + "="*50)
best_knn_acc, best_knn_model, best_knn_params = 0, None, {}

for metric in ['euclidean', 'manhattan']:
    for k in [3, 5, 7, 9]:
        knn = KNeighborsClassifier(n_neighbors=k, metric=metric)
        knn.fit(X_train_scaled, y_train)
        acc = accuracy_score(y_test, knn.predict(X_test_scaled))
        print(f"  KNN(k={k}, metric={metric:10s}) -> Accuracy: {acc:.4f}")
        if acc > best_knn_acc:
            best_knn_acc, best_knn_model, best_knn_params = acc, knn, {'n_neighbors': k, 'metric': metric}

y_pred_knn = best_knn_model.predict(X_test_scaled)
best_knn_metrics = evaluate_model(y_test, y_pred_knn, f"🎯 KNN Terbaik (k={best_knn_params['n_neighbors']})")

# =====================================================
# 6. MODEL 2: RANDOM FOREST
# =====================================================
print("\n" + "="*50 + "\nMODEL 2: RANDOM FOREST\n" + "="*50)
best_rf_acc, best_rf_model, best_rf_params = 0, None, {}

for n_est in [50, 100, 200]:
    for max_d in [5, 10, 15, None]:
        rf = RandomForestClassifier(n_estimators=n_est, max_depth=max_d, random_state=42, n_jobs=-1)
        rf.fit(X_train_scaled, y_train)
        acc = accuracy_score(y_test, rf.predict(X_test_scaled))
        print(f"  RF(n_est={n_est:3d}, max_depth={str(max_d):4s}) -> Accuracy: {acc:.4f}")
        if acc > best_rf_acc:
            best_rf_acc, best_rf_model, best_rf_params = acc, rf, {'n_estimators': n_est, 'max_depth': max_d}

y_pred_rf = best_rf_model.predict(X_test_scaled)
best_rf_metrics = evaluate_model(y_test, y_pred_rf, f"🎯 RF Terbaik (n_est={best_rf_params['n_estimators']})")

# =====================================================
# 7. MODEL 3: WEIGHTED KNN
# =====================================================
print("\n" + "="*50 + "\nMODEL 3: WEIGHTED KNN\n" + "="*50)
weights = np.ones(X_train_scaled.shape[1])
weights[0] = 1.5  # price_tier
weights[1] = 2.0  # ram

X_train_weighted = X_train_scaled * weights
X_test_weighted = X_test_scaled * weights

best_wknn_acc, best_wknn_model, best_wknn_params = 0, None, {}
for metric in ['euclidean', 'manhattan']:
    for k in [3, 5, 7, 9]:
        wknn = KNeighborsClassifier(n_neighbors=k, metric=metric)
        wknn.fit(X_train_weighted, y_train)
        acc = accuracy_score(y_test, wknn.predict(X_test_weighted))
        print(f"  WKNN(k={k}, metric={metric:10s}) -> Accuracy: {acc:.4f}")
        if acc > best_wknn_acc:
            best_wknn_acc, best_wknn_model, best_wknn_params = acc, wknn, {'n_neighbors': k, 'metric': metric}

y_pred_wknn = best_wknn_model.predict(X_test_weighted)
best_wknn_metrics = evaluate_model(y_test, y_pred_wknn, f"🎯 Weighted KNN Terbaik")

# =====================================================
# 8. PERBANDINGAN FINAL & SIMPAN
# =====================================================
comparison = {
    'KNN': {'accuracy': best_knn_acc, 'metrics': best_knn_metrics, 'model': best_knn_model, 'params': best_knn_params, 'type': 'knn'},
    'Random Forest': {'accuracy': best_rf_acc, 'metrics': best_rf_metrics, 'model': best_rf_model, 'params': best_rf_params, 'type': 'random_forest'},
    'Weighted KNN': {'accuracy': best_wknn_acc, 'metrics': best_wknn_metrics, 'model': best_wknn_model, 'params': best_wknn_params, 'type': 'weighted_knn', 'weights': weights.tolist()} # 🎯 FIX: Ditranslasikan ke .tolist() agar aman di-pickle
}

sorted_models = sorted(comparison.items(), key=lambda x: x[1]['accuracy'], reverse=True)
best_model_name, best_model_info = sorted_models[0][0], sorted_models[0][1]

print(f"\n🏆 MODEL TERBAIK: {best_model_name} (Accuracy: {best_model_info['accuracy']:.4f})")

os.makedirs('model', exist_ok=True)
best_model_data = {
    'model': best_model_info['model'],
    'type': best_model_info['type'],
    'scaler': scaler,
    'features': features,
    'encoded_columns': encoded_cols,
    'unique_processors': unique_processors,
    'unique_gpus': unique_gpus,
    'accuracy': best_model_info['accuracy']
}
if 'weights' in best_model_info:
    best_model_data['weights'] = best_model_info['weights']

with open('model/best_model.pkl', 'wb') as f:
    pickle.dump(best_model_data, f)
with open('model/label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)

# Simpan dataset hasil pembersihan final (menyertakan kolom kategori_3 hasil mapping baru)
df.to_csv('dataset/cleaned_dataset.csv', index=False)
print("✅ Semua komponen model dan log One-Hot metadata berhasil disimpan (3 Kategori)!")