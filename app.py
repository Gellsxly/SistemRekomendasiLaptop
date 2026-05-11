from flask import Flask, render_template, request
import pandas as pd

# Import fungsi rekomendasi
from model.recommendation import recommend_laptop

# Import helper format rupiah
from utils.helper import format_rupiah

app = Flask(__name__)

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
    return render_template('about.html')

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
            error='Budget dan kebutuhan wajib diisi'
        )

    # Validasi budget harus angka
    try:
        budget = int(budget)

    except ValueError:

        return render_template(
            'result.html',
            error='Budget harus berupa angka'
        )

    # Validasi kategori
    valid_kategori = [
        'Gaming',
        'Office',
        'Coding',
        'Editing',
        'Rendering'
    ]

    if kebutuhan not in valid_kategori:

        return render_template(
            'result.html',
            error='Kategori tidak valid'
        )

    # Ambil rekomendasi laptop
    try:

        recommendations_df = recommend_laptop(
            budget,
            kebutuhan
        )

    except Exception as e:

        return render_template(
            'result.html',
            error=f'Gagal mendapatkan rekomendasi: {str(e)}'
        )

    # Jika tidak ada hasil
    if recommendations_df.empty:

        return render_template(
            'result.html',
            message='Tidak ada laptop yang sesuai',
            recommendations=[]
        )

    # Konversi dataframe ke list
    recommendations = []

    for _, row in recommendations_df.iterrows():

        laptop = row.to_dict()

        # Format harga rupiah
        laptop['price'] = format_rupiah(
            laptop['price']
        )

        recommendations.append(laptop)

    # Kirim ke result.html
    return render_template(

        'result.html',

        recommendations=recommendations,

        budget=budget,

        kebutuhan=kebutuhan

    )

# =========================
# RUN FLASK
# =========================

if __name__ == '__main__':
    app.run(debug=True)