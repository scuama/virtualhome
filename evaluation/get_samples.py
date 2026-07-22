import random
from table3_configs import source_records

all_sources = {category: [r[0] for r in source_records(category)] for category in "GMP"}
random.seed(42)
cross_samples = {}
for category, records in all_sources.items():
    cross_samples[category] = random.sample(records, 5)

for category, samples in cross_samples.items():
    print(f"'{category}': {samples},")
