"""Batch query and pandas DataFrame examples."""

from opentargets import OpenTargetsClient

client = OpenTargetsClient()

# Fetch multiple targets in one API call
targets = client.get_targets(["EGFR", "BRAF", "KRAS", "TP53"])
print("Batch target fetch:")
for t in targets:
    print(f"  {t.approved_symbol:<10} {t.id}")

# Get associations as a DataFrame
df = client.get_target_associations("EGFR", limit=50, as_dataframe=True)
print(f"\nEGFR associations DataFrame shape: {df.shape}")
print(df[["disease_name", "score"]].head(10).to_string())
