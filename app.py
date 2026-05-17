from flask import Flask, render_template, request
import pandas as pd

# Import fungsi rekomendasi dan akurasi (langsung dari recommendation)
from model.recommendation import recommend_laptop, get_model_accuracy

# Import helper format rupiah
from utils.helper import format_rupiah

app = Flask(__name__)

# =========================
# LOAD MODEL ACCURACY
# =========================
model_accuracy = None
try:
    model_accuracy = get_model_accuracy()
    print(f"✅ Model accuracy loaded: {model_accuracy:.2%}")
except Exception as e:
    print(f"⚠️ Could not load model accuracy: {e}")

# =========================
# HOME PAGE
# =========================
@app.route('/')
def home():
    return render_template('index.html')

# =========================
# ABOUT PAGE
# =========================
@app.route('/about')
def about():
    return render_template('about.html', model_accuracy=model_accuracy)

# =========================
# RECOMMENDATION RESULT
# =========================
@app.route('/recommend', methods=['POST'])
def recommend():
    # Ambil data dari form
    budget = request.form.get('budget')
    kebutuhan = request.form.get('kebutuhan')

    # Validasi input kosong
    if not budget or not kebutuhan:
        return render_template(
            'result.html',
            error='Budget dan kebutuhan wajib diisi',
            model_accuracy=model_accuracy
        )

    # Validasi budget harus angka
    try:
        budget = int(budget)
    except ValueError:
        return render_template(
            'result.html',
            error='Budget harus berupa angka',
            model_accuracy=model_accuracy
        )

    # Validasi kategori
    valid_kategori = ['Gaming', 'Office', 'Coding', 'Editing', 'Rendering']
    if kebutuhan not in valid_kategori:
        return render_template(
            'result.html',
            error='Kategori tidak valid',
            model_accuracy=model_accuracy
        )

    # Ambil rekomendasi laptop
    try:
        recommendations_df = recommend_laptop(budget, kebutuhan)
    except Exception as e:
        return render_template(
            'result.html',
            error=f'Gagal mendapatkan rekomendasi: {str(e)}',
            model_accuracy=model_accuracy
        )

    # Jika tidak ada hasil
    if recommendations_df.empty:
        return render_template(
            'result.html',
            message='Tidak ada laptop yang sesuai',
            recommendations=[],
            model_accuracy=model_accuracy
        )

    # Konversi dataframe ke list dengan format tambahan
    recommendations = []
    for _, row in recommendations_df.iterrows():
        laptop = row.to_dict()

        # Format harga rupiah
        laptop['price'] = format_rupiah(laptop['price'])

        # Format jarak (distance) menjadi 4 desimal
        if 'distance' in laptop:
            laptop['distance'] = f"{laptop['distance']:.4f}"
        
        # Format similarity menjadi persen dengan 2 desimal
        if 'similarity' in laptop:
            laptop['similarity'] = f"{laptop['similarity']:.2%}"

        recommendations.append(laptop)

    # Kirim ke result.html
    return render_template(
        'result.html',
        recommendations=recommendations,
        budget=budget,
        kebutuhan=kebutuhan,
        model_accuracy=model_accuracy
    )

# =========================
# RUN FLASK
# =========================
if __name__ == '__main__':
    app.run(debug=True)