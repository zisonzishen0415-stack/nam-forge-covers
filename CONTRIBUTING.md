# Contributing a cover

Thanks for sharing! This library only accepts covers you made yourself, or covers that use artwork you have explicit permission to redistribute.

## 1. Share from NAM FORGE (recommended)

In the app's **封面设计** page, click **分享到共享库**. Fill in the cover name, author, license and source, then click **分享**.

- The app packs the design and opens a prefilled GitHub issue.
- Click **Submit new issue** once. No token and no file exports are needed.
- The `Accept shared cover` workflow validates the payload, writes the design JSON + PNG, updates `library.json`, comments on the issue and closes it.

The workflow only handles issues that contain the app-generated `NAMFORGE-COVER` marker. It runs with the repository's own `GITHUB_TOKEN`; no personal token is involved.

## 2. Manual submission (fallback)

Export from the app:

- **导出设计** → `namforge-design-YYYY-MM-DD.json` (the actual design; required)
- **导出封面** → `cover-*.png` (preview; optional but recommended)

Then use the [Submit a cover](https://github.com/zisonzishen0415-stack/nam-forge-covers/issues/new?template=submit-cover.yml) issue form and fill in:

- cover name
- author / credit
- license (CC0-1.0, CC-BY-4.0, CC-BY-SA-4.0 or MIT)
- source / original artwork link, if any
- tags / notes

After the issue is created, **drag the design JSON and PNG into the issue body**. GitHub issue forms cannot attach files directly; attachments in the issue are fine.

## 3. Rights

- Only submit your own artwork, or artwork you have written permission to share.
- If the cover is a 1-bit conversion of someone else's illustration, include the source link and proof of permission in the issue.
- Do not submit Bilibili/Pixiv/other third-party art without permission.
- By submitting, you agree to publish the cover under the license you select.

## 4. Maintainer merge checklist

1. Download the design JSON and PNG from the issue.
2. Check the JSON: it should contain `design.base` (base64 of 8,192 bytes), `design.area`, `design.scale`, text settings and `previewName`.
3. Choose an `id` (lowercase slug, unique) and save:
   - `covers/<id>.json`
   - `covers/<id>.png`
4. Add an entry to `library.json`:
   ```json
   {
     "id": "<id>",
     "name": "<display name>",
     "author": "<author>",
     "license": "<license>",
     "source": "<source or 'original'>",
     "preview": "covers/<id>.png",
     "design": "covers/<id>.json",
     "tags": ["<tag>"],
     "added": "YYYY-MM-DD"
   }
   ```
5. Verify the preview renders and the design imports in NAM FORGE (封面设计 → 导入设计).
6. Commit both files and the updated `library.json`.

## Format notes

- The design JSON is exactly what NAM FORGE's **导出设计** produces; do not rewrite it by hand.
- The cover is 128×64, 1-bit. The editor's base is 8,192 bytes (one byte per pixel) before RLE encoding.
- `library.json` is fetched directly by the library page; keep it valid JSON and use relative paths.
- The app validates imported designs; an invalid or oversized design is rejected.

## License of contributions

The library page code is MIT. Each cover remains under the license selected in its `library.json` entry.
