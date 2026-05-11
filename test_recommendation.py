from model.recommendation import recommend_laptop

# Test recommendation

hasil = recommend_laptop(
    15000000,
    'Gaming'
)

print(hasil)