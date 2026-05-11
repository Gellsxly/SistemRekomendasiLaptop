document.getElementById('recommendForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const budget = document.getElementById('budget').value;
  const kebutuhan = document.getElementById('kebutuhan').value;

  if (!budget || !kebutuhan) {
    alert('Harap isi budget dan pilih kebutuhan!');
    return;
  }

  const loadingDiv = document.getElementById('loading');
  const resultDiv = document.getElementById('resultContainer');
  const submitBtn = document.getElementById('submitBtn');

  // Tampilkan loading, disable tombol
  loadingDiv.style.display = 'block';
  submitBtn.disabled = true;
  resultDiv.innerHTML = '';

  try {
    const response = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        budget: parseInt(budget),
        kebutuhan: kebutuhan
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Terjadi kesalahan');
    }

    if (data.status === 'success' && data.recommendations.length > 0) {
      displayRecommendations(data.recommendations);
    } else {
      resultDiv.innerHTML = `<p style="color: #e94560;">⚠️ ${data.message || 'Tidak ada rekomendasi untuk kriteria ini.'}</p>`;
    }
  } catch (error) {
    resultDiv.innerHTML = `<p style="color: red;">❌ Error: ${error.message}</p>`;
  } finally {
    loadingDiv.style.display = 'none';
    submitBtn.disabled = false;
  }
});

function displayRecommendations(laptops) {
  const container = document.getElementById('resultContainer');
  container.innerHTML = '<h3>✨ Rekomendasi Laptop Untukmu:</h3>';

  laptops.forEach(laptop => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <h3>${laptop.product_name}</h3>
      <p><strong>Processor:</strong> ${laptop.processor}</p>
      <p><strong>RAM:</strong> ${laptop.ram} GB</p>
      <p><strong>GPU:</strong> ${laptop.gpu}</p>
      <p><strong>Harga:</strong> ${laptop.price}</p>
      <p><strong>Kategori:</strong> ${laptop.kategori_kebutuhan}</p>
      <p><strong>Toko:</strong> ${laptop.shop_name}</p>
      <a href="${laptop.product_url}" target="_blank">Lihat Produk</a>
    `;
    container.appendChild(card);
  });
}