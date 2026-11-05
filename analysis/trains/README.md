# Train disruptions

An investigation of what goes wrong on the Dutch rail network, when it happens and where,
using [Rijden de Treinen's open disruption data](https://www.rijdendetreinen.nl/en/open-data/disruptions)
(CC BY 4.0, 2011 to 2025).

Step 1 is a profile of the raw data:

```bash
python analysis/trains/profile.py
```

Caveats from the source: only disruptions NS communicated are included, and
NS changed systems in 2017, so timing comparisons start in 2017.
