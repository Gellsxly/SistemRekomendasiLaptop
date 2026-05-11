from flask import Flask, render_template, request, jsonify
import pandas as pd

# Import fungsi rekomendasi dari file yang sudah kamu buat
from model.recommendation import recommend_laptop
# Import helper untuk format harga
from utils.helper import format_rupiah

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Endpoint API untuk rekomendasi (bisa diakses via POST atau GET)
@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        # Jika client mengirim JSON
        data = request.get_json()
        budget = data.get('budget')
        kebutuhan = data.get('kebutuhan')
    else:
        # Jika menggunakan query parameter (GET)
        budget = request.args.get('budget')
        kebutuhan = request.args.get('kebutuhan')

    # Validasi input
    if not budget or not kebutuhan:
        return jsonify({'error': 'Parameter budget dan kebutuhan wajib diisi'}), 400

    try:
        budget = int(budget)
    except ValueError:
        return jsonify({'error': 'Budget harus berupa angka'}), 400

    # Daftar kategori yang valid (sesuai dengan label encoder)
    valid_kategori = ['Gaming', 'Office', 'Coding', 'Editing', 'Rendering']
    if kebutuhan not in valid_kategori:
        return jsonify({'error': f'Kategori tidak valid. Pilih salah satu: {valid_kategori}'}), 400

    # Panggil fungsi rekomendasi
    try:
        recommendations_df = recommend_laptop(budget, kebutuhan)
    except Exception as e:
        return jsonify({'error': f'Gagal mendapatkan rekomendasi: {str(e)}'}), 500

    # Jika tidak ada rekomendasi
    if recommendations_df.empty:
        return jsonify({'message': 'Tidak ada laptop yang sesuai dengan budget dan kebutuhan ini'}), 200

    # Konversi DataFrame ke list of dict, dan format harga pakai helper
    result = []
    for _, row in recommendations_df.iterrows():
        item = row.to_dict()
        item['price'] = format_rupiah(item['price'])  # Harga sudah diformat
        result.append(item)

    return jsonify({
        'status': 'success',
        'total': len(result),
        'recommendations': result
    })

if __name__ == '__main__':
    app.run(debug=True)