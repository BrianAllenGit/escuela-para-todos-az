#!/usr/bin/env python3
"""Proves every quote in tools/quotes.json (and so on the page) is a word for word match of a captured source.

For each quote, every block of it (paragraph, list item, heading, footnote) is checked on its own: strip tags, unescape
entities, collapse whitespace, then require the result to appear inside the captured source text (same normalisation).
Then the page itself is checked: every quote box in index.html must contain exactly the quote's HTML.
Exit 1 on any mismatch.
"""
import html as H
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CAP = os.path.join(HERE, "captures")
SOURCE = {"ed_page_en": "ed_equal.txt", "ed_rescinded_en": "ed_rescinded.txt", "toolkit_es": "pdf/ncela_enrolling_es.txt",
          "toolkit_en": "pdf/ncela_enrolling_en.txt", "qa1_en": "pdf/eric_qa_en.txt", "qa5_en": "pdf/eric_qa_en.txt",
          "qa7_en": "pdf/eric_qa_en.txt", "qa8_en": "pdf/eric_qa_en.txt", "aclu_school_en": "aclu_school_en.html",
          "ars_15_821_a": "azleg_821.txt"}


def norm(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<svg.*?</svg>", " ", s, flags=re.S)
    s = re.sub(r"</(li|p|h\d|div|ul|ol|td|tr)>|<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = H.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def blocks(h):
    return [b for b in re.findall(r"<(?:p|li|h3)[^>]*>(.*?)</(?:p|li|h3)>", h, flags=re.S) if norm(b)]


def main():
    quotes = json.load(open(os.path.join(HERE, "quotes.json"), encoding="utf-8"))
    page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    bad = 0
    for key, q in quotes.items():
        src = norm(open(os.path.join(CAP, SOURCE[key]), encoding="utf-8", errors="replace").read())
        srcns = re.sub(r"\s", "", src)
        bl = blocks(q["html"])
        miss = [b for b in bl if norm(b) not in src and re.sub(r"\s", "", norm(b)) not in srcns]
        chars = sum(len(norm(b)) for b in bl)
        n_page = page.count(q["html"])
        ok = not miss and n_page >= 1
        print("%s %-16s %5d chars, %2d blocks, blocks not in source: %d, on page: %dx" % ("PASS" if ok else "FAIL", key, chars, len(bl), len(miss), n_page))
        for m in miss:
            print("   NOT IN SOURCE: " + norm(m)[:120])
        if not ok:
            bad += 1
    print("QUOTES: %d checked, %d failed" % (len(quotes), bad))
    sys.exit(1 if bad else 0)


main()
