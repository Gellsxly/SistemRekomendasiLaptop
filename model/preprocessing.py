import pandas as pd

# Load dataset
gaming = pd.read_csv('dataset/gaming_laptop.csv')
office = pd.read_csv('dataset/office_laptop.csv')
coding = pd.read_csv('dataset/coding_laptop.csv')
editing = pd.read_csv('dataset/editing_laptop.csv')
rendering = pd.read_csv('dataset/rendering_laptop.csv')

# Tambah kategori
gaming['kategori_kebutuhan'] = 'Gaming'
office['kategori_kebutuhan'] = 'Office'
coding['kategori_kebutuhan'] = 'Coding'
editing['kategori_kebutuhan'] = 'Editing'
rendering['kategori_kebutuhan'] = 'Rendering'

# Gabungkan dataset
df = pd.concat([
    gaming,
    office,
    coding,
    editing,
    rendering
], ignore_index=True)

# Simpan final dataset
df.to_csv('dataset/final_dataset.csv', index=False)

print('Final dataset berhasil dibuat!')