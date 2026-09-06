"""Build the bundled CJK font subsets.

The full Chiron Sung HK variable font is 82 MB, far too heavy to commit.
This script collects every CJK character that lunar_python 1.4.8 can
possibly emit (by scanning the installed package source) plus everything
in generate.py, then subsets the fonts to exactly that set. Rerun only
when lunar_python is upgraded or new literal text is added to the
renderer.

The universe includes the traditional forms produced by the OpenCC s2t
and s2hk tables, since the renderer converts everything to traditional
Chinese at run time.

Usage:
    pip install fonttools opencc-python-reimplemented lunar_python==1.4.8
    python3 subset_fonts.py /path/to/ChironSungHKVF.ttf /path/to/NotoSansSC.ttf

Sources:
    Chiron Sung HK: https://github.com/chiron-fonts/chiron-sung-hk (OFL)
    Noto Sans SC:   https://github.com/google/fonts (OFL)
"""

import sys
from pathlib import Path

import lunar_python
from fontTools import subset

HERE = Path(__file__).resolve().parent


def cjk_universe():
    from opencc import OpenCC

    converters = [OpenCC("s2t"), OpenCC("s2hk")]
    chars = set()
    pkg = Path(lunar_python.__file__).parent
    for src in list(pkg.rglob("*.py")) + [HERE / "generate.py"]:
        raw = src.read_text(encoding="utf-8")
        for text in [raw] + [cc.convert(raw) for cc in converters]:
            for ch in text:
                if ord(ch) >= 0x2E80:
                    chars.add(ch)
    return chars


def subset_font(src, dest, chars):
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    font = subset.load_font(str(src), opts)
    ss = subset.Subsetter(opts)
    ss.populate(text="".join(chars) + "".join(chr(c) for c in range(0x20, 0x7F)))
    ss.subset(font)
    subset.save_font(font, str(dest), opts)
    print(f"{dest.name}: {dest.stat().st_size / 1e6:.2f} MB, {len(chars)} CJK chars")


def main():
    chiron_src, noto_src = sys.argv[1], sys.argv[2]
    chars = cjk_universe()
    subset_font(chiron_src, HERE / "fonts" / "ChironSungHK.ttf", chars)
    subset_font(noto_src, HERE / "fonts" / "NotoSansSC.ttf", chars)


if __name__ == "__main__":
    main()
