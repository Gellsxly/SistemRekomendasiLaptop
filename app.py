from flask import Flask, render_template, request
import pandas as pd

from model.recommendation import recommend_laptop, get_model_accuracy
from utils.helper import format_rupiah

app = Flask(__name__)

# Load model accuracy dan type
model_accuracy = None
model_type = None

try:
    model_accuracy = get_model_accuracy()
    print(f"✅ Model accuracy loaded: {model_accuracy:.2%}")
except Exception as e:
    print(f"⚠️ Could not load model accuracy: {e}")

# Load model type
try:
    import pickle
    with open('model/best_model.pkl', 'rb') as f:
        best_model = pickle.load(f)
        model_type = best_model.get('type', 'unknown')
        
        # Mapping nama algoritma untuk display yang lebih user-friendly
        model_type_display = {
            'knn': 'K-Nearest Neighbors (KNN)',
            'random_forest': 'Random Forest',
            'weighted_knn': 'Weighted K-Nearest Neighbors (WKNN)'
        }
        model_type = model_type_display.get(model_type, model_type)
        print(f"✅ Model type loaded: {model_type}")
except Exception as e:
    print(f"⚠️ Could not load model type: {e}")

# Mapping dari 5 kategori input ke 3 kategori trained
kategori_mapping = {
    'Gaming': 'Gaming',
    'Office': 'Office_Coding',
    'Coding': 'Office_Coding',
    'Editing': 'Editing_Rendering',
    'Rendering': 'Editing_Rendering'
}
valid_kategori_5 = list(kategori_mapping.keys())

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html', model_accuracy=model_accuracy, model_type=model_type)

@app.route('/recommend', methods=['POST'])
def recommend():
    # Inisialisasi variabel default
    budget = None
    kebutuhan_5 = None
    ram_user = None

    # Ambil data form
    budget_raw = request.form.get('budget')
    kebutuhan_5 = request.form.get('kebutuhan')
    ram_user = request.form.get('ram')

    # Validasi input kosong
    if not budget_raw or not kebutuhan_5:
        return render_template(
            'result.html',
            error='Budget dan kebutuhan wajib diisi',
            budget=budget_raw,
            kebutuhan=kebutuhan_5,
            model_accuracy=model_accuracy,
            model_type=model_type
        )

    # Validasi budget
    try:
        budget = int(budget_raw)
        if budget <= 0:
            raise ValueError
    except ValueError:
        return render_template(
            'result.html',
            error='Budget harus berupa angka bulat positif',
            budget=budget_raw,
            kebutuhan=kebutuhan_5,
            model_accuracy=model_accuracy,
            model_type=model_type
        )

    # Validasi RAM jika diinput
    if ram_user:
        try:
            ram_user = int(ram_user)
            if ram_user <= 0:
                raise ValueError
        except ValueError:
            return render_template(
                'result.html',
                error='RAM harus berupa angka bulat positif',
                budget=budget,
                kebutuhan=kebutuhan_5,
                model_accuracy=model_accuracy,
                model_type=model_type
            )

    # Validasi kategori
    if kebutuhan_5 not in valid_kategori_5:
        return render_template(
            'result.html',
            error=f'Kategori "{kebutuhan_5}" tidak valid. Pilih: {", ".join(valid_kategori_5)}',
            budget=budget,
            kebutuhan=kebutuhan_5,
            model_accuracy=model_accuracy,
            model_type=model_type
        )

    # Mapping ke 3 kelas
    kebutuhan_mapped = kategori_mapping[kebutuhan_5]

    # Dapatkan rekomendasi
    try:
        recommendations_df = recommend_laptop(budget, kebutuhan_mapped, ram_user=ram_user)
    except Exception as e:
        return render_template(
            'result.html',
            error=f'Gagal mendapatkan rekomendasi: {str(e)}',
            budget=budget,
            kebutuhan=kebutuhan_5,
            model_accuracy=model_accuracy,
            model_type=model_type
        )

    if recommendations_df is None or recommendations_df.empty:
        return render_template(
            'result.html',
            message='Tidak ada laptop yang sesuai dengan budget dan kriteria Anda.',
            recommendations=[],
            budget=budget,
            kebutuhan=kebutuhan_5,
            model_accuracy=model_accuracy,
            model_type=model_type
        )

    # Proses rekomendasi
    recommendations = []
    for _, row in recommendations_df.iterrows():
        laptop = row.to_dict()
        laptop['price'] = format_rupiah(laptop['price'])
        if 'distance' in laptop:
            laptop['distance'] = f"{laptop['distance']:.4f}"
        if 'similarity' in laptop:
            if isinstance(laptop['similarity'], (int, float)):
                laptop['similarity'] = f"{laptop['similarity']:.2%}"
            else:
                laptop['similarity'] = str(laptop['similarity'])
        recommendations.append(laptop)

    return render_template(
        'result.html',
        recommendations=recommendations,
        budget=budget,
        kebutuhan=kebutuhan_5,
        model_accuracy=model_accuracy,
        model_type=model_type
    )

if __name__ == '__main__':
    app.run(debug=True)