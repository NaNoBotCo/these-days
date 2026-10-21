# These Days · ช่วงนี้

NaN's answer to "so what are you staying busy with these days?" — Mot Dang, Hongdam, wichaa, paid work for people and bots, minisites drawn with math, and Rotary. English and Thai.

Live: https://nanobotco.github.io/these-days/

- `src/data.json` — every link and every word, English and Thai.
- `tools/build.py` — writes `docs/` and `docs/th/`. Each tile shows its site's own share picture, read from the page's og:image; the two counts (Mot Dang records, NaNoBotCo GitHub Pages sites) are read at build. `--cards` redraws the placeholder share cards.
- `src/cache.json` — last pictures and counts, used when a source does not answer.

```
python3 tools/build.py --cards
```

Text CC BY 4.0, code MIT. Contact: nan@motdang.net
