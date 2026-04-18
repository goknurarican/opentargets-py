"""Basic usage examples for opentargets-py."""

from opentargets import OpenTargetsClient

client = OpenTargetsClient()

# --- Target ---
target = client.get_target("EGFR")
print(f"Target: {target.approved_symbol} ({target.id})")
print(f"Name:   {target.approved_name}")
print(f"Type:   {target.biotype}")

# --- Associations ---
associations = client.get_target_associations("EGFR", limit=5)
print(f"\nTop {len(associations)} diseases associated with EGFR:")
for a in associations:
    print(f"  {a.disease_name:<40} score={a.score:.3f}")

# --- Drugs ---
drugs = client.get_target_drugs("EGFR")
print(f"\nDrugs targeting EGFR ({len(drugs)} total):")
for d in drugs[:5]:
    print(f"  {d.name:<25} phase={d.max_clinical_trial_phase}")

# --- Disease ---
disease = client.get_disease("EFO_0003060")
print(f"\nDisease: {disease.name}")
print(f"Areas:   {', '.join(disease.therapeutic_areas)}")

# --- Drug ---
drug = client.get_drug("CHEMBL939")
print(f"\nDrug: {drug.name} ({drug.id})")
print(f"Type: {drug.drug_type}")
print(f"MOA:  {drug.mechanism_of_action}")

# --- Search ---
results = client.search("lung cancer", entity_type="disease", limit=3)
print("\nSearch results for 'lung cancer':")
for r in results:
    print(f"  [{r.entity_type}] {r.name} ({r.id})")
