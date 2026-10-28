# NAM FORGE COVERS

Shared 128×64 cover library for [NAM FORGE](https://zisonzishen0415-stack.github.io/nam-forge/).

- **Browse / download**: <https://zisonzishen0415-stack.github.io/nam-forge-covers/>
- **Submit a cover**: <https://github.com/zisonzishen0415-stack/nam-forge-covers/issues/new?template=submit-cover.yml>
- **Main app**: <https://zisonzishen0415-stack.github.io/nam-forge/>

## How to use a cover

1. Open the library page and pick a cover.
2. Download its **design JSON** (`covers/<id>.json`).
3. In NAM FORGE go to **封面设计 → 导入设计** and select the JSON.
4. The cover is now in the editor; save it to **MY COVERS** if you want to reuse it.

The PNG is a preview only; the JSON is the actual design.

## How to submit

1. In NAM FORGE, design the cover and export:
   - **导出设计** → `namforge-design-*.json`
   - **导出封面** → `cover-*.png`
2. Open a [new submission issue](https://github.com/zisonzishen0415-stack/nam-forge-covers/issues/new?template=submit-cover.yml) and fill in name, author, license and source.
3. After creating the issue, **drag both files into the issue** (GitHub issue forms cannot attach files directly).
4. The maintainer reviews it and adds it to `covers/` + `library.json`.

Only submit covers you made or have explicit permission to share. Third-party artwork without permission will not be merged.

## Format

`library.json`:

```json
{
  "format": 1,
  "updated": "2026-10-28",
  "covers": [
    {
      "id": "example-text-light",
      "name": "Plain text · light",
      "author": "NAM FORGE",
      "license": "MIT",
      "source": "built-in preset (text-light)",
      "preview": "covers/example-text-light.png",
      "design": "covers/example-text-light.json",
      "tags": ["text", "minimal"],
      "added": "2026-10-28"
    }
  ]
}
```

- `covers/<id>.json` is the file exported by **导出设计** (NAM FORGE design JSON; the 8,192-byte 1-bit base is base64-encoded).
- `covers/<id>.png` is a preview image; any size is fine.
- `id` is a lowercase slug, unique in the library.
- `license` is the license granted for that cover entry.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full submission and merge checklist.

## License

- The page/library code is MIT (see [LICENSE](LICENSE)).
- Each cover is published under the license listed in its `library.json` entry.
- The example cover is the built-in NAM FORGE text-light preset, MIT.

## Credits

- [NAM FORGE](https://github.com/zisonzishen0415-stack/nam-forge) — the cover editor and ZDL workbench.
- NAMLite engine / ZDL format: [themanro/ZoomMultistompZDL](https://github.com/themanro/ZoomMultistompZDL) (MIT).
- Palette inspiration: Zoom G1on (amber LCD, blue knobs, gray-black panel). Not affiliated with Zoom Corporation.
