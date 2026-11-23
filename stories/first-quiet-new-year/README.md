# The first quiet New Year?

Data from [`analysis/fireworks-air`](../../analysis/fireworks-air/). On 3 January 2027:

```bash
gh workflow run fetch -f name=fireworks        # adds the 2026/27 week (API, unvalidated)
git clone -b raw-fireworks --depth 1 https://github.com/jawdat-rana/unexpected-signals.git /tmp/raw-fireworks
python analysis/fireworks-air/prepare.py /tmp/raw-fireworks
```

Then fill the ⟨…⟩ marks in `story.md` and empty `open` in `story.toml`.
