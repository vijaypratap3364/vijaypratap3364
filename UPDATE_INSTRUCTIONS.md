# Apply this redesign

Copy this package over the existing `vijaypratap3364` profile repository, then run:

```bash
python -m pip install -r requirements.txt
python scripts/generate_lunabot.py
python -m unittest discover -s tests -v

git add .
git commit -m "feat: separate Lunabot profile sections"
git pull --rebase origin main
git push origin main
```

The workflow will update all three generated assets daily:

- `assets/mission-telemetry.png`
- `assets/lunabot.gif`
- `assets/mission-output.png`
