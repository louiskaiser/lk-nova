# LK Nova

Variable display typeface for headlines and branding. Nine axes, 280 encoded characters and six static weights. Free for personal and commercial use under the included permission.

[Deutsch](README.de.md)

## Use

- Open `docs/index.html` for the product page and specimen.
- Install `dist/LKNova-VF.ttf` for variable applications. For other applications, use the six static weights instead.
- For websites, keep `dist/font.css` beside `dist/LKNova-VF.woff2` and use the `lk-display` class.
- Brand settings: weight 900, width 100, upright, tracking −0.05 em. Use a separate text face for long passages and interfaces.

The square ■ sits on the baseline; MARK controls its size. Automatic red requires color-font support. `dist/LKNova-BrandSquare.svg` is the vector alternative. Λ and Ξ are separate characters for LOUIS KΛISΞR.

## Languages

English is the maintained source. German (Germany), German (Switzerland) and Simplified Chinese are translated versions. The first visit follows the supported device language, with English as fallback. The language menu sets an explicit preference. An explicit `?lang=en` opens English. Chinese interface text uses system fallback fonts; LK Nova itself does not include Chinese glyphs.

Edit `packaging/site-template.html` and `packaging/locales/en.json`. Keep the translated locale files in sync, then run `python3 packaging/build_site.py`. This generates the static pages, interface translations and localized desktop guides. Do not maintain generated HTML separately.

## Build

Python 3.10 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r source/requirements.txt
.venv/bin/python source/build_font.py
.venv/bin/python source/export_vectors.py
.venv/bin/python source/validate_font.py
.venv/bin/python source/validate_geometry.py
.venv/bin/python source/validate_vectors.py
.venv/bin/python packaging/prepare_assets.py
.venv/bin/python packaging/build_site.py
.venv/bin/python packaging/package.py
```

The release preserves the approved 0.900 outline and variation tables. The font is constructed from original geometric sources; no third-party font outlines are included. Helvetica Neue was a visual reference.

## Files

- `dist/`: variable TTF/WOFF2, six static TTF weights, CSS, vectors, manifest and license.
- `source/`: original geometry, font build, validation and editable UFO master.
- `packaging/`: English source template, translations, download guides and packaging scripts.
- `docs/`: generated product presentation, interface script and downloads.
- `qa/`: font and presentation checks.
- `PUBLISHING.md`: GitHub Pages and Releases instructions.

See `LICENSE.txt` for use, embedding, modification and redistribution permissions. The font permission does not grant rights to the LOUIS KΛISΞR brand.
