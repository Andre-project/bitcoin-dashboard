from data_collectors.price_data import load_from_csv
import pandas as pd

print("=== TEST COMPLET ===")
df = load_from_csv()

if df is not None:
    print(f"✅ Données chargées: {len(df)} lignes")
    print(f"Index type: {type(df.index)}")
    print(f"Colonnes AVANT reset: {df.columns.tolist()}")
    
    # Simule le fix
    df_reset = df.reset_index()
    print(f"Colonnes APRÈS reset: {df_reset.columns.tolist()}")
    
    # Simule la conversion en dict
    data_dict = df_reset.to_dict('records')
    print(f"Premier record: {data_dict[0]}")
    print(f"Clés du dict: {list(data_dict[0].keys())}")
else:
    print("❌ Aucune donnée")