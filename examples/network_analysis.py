"""Build a simple target–disease network using opentargets-py."""

from collections import defaultdict

from opentargets import OpenTargetsClient

TARGETS = ["EGFR", "BRAF", "KRAS"]
SCORE_THRESHOLD = 0.5

client = OpenTargetsClient()

network: dict[str, list[str]] = defaultdict(list)

for symbol in TARGETS:
    assocs = client.get_target_associations(symbol, limit=10)
    for a in assocs:
        if a.score >= SCORE_THRESHOLD:
            network[symbol].append(a.disease_name)

print("Target → Disease network (score ≥ 0.5):")
for target, diseases in network.items():
    print(f"\n{target}:")
    for d in diseases:
        print(f"  • {d}")
