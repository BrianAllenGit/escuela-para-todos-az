#!/usr/bin/env python3
"""Builds tools/quotes.json from the pages and PDFs captured in tools/captures/ (see tools/fetch/).

The quoted text is copied from the captures. Nothing is reworded. Only markup is added or removed:
line breaks of the PDF text are joined, running page headers and footers of the PDF are dropped,
footnote numbers become <sup>, bullets become <li>.
tools/verify_quotes.py then proves that every paragraph of every quote is a word for word match of its capture.

Usage: python3 tools/extract_quotes.py
"""
import html as H
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "captures")
OUT = os.path.join(HERE, "quotes.json")
RETRIEVED = "2026-11-27"
E = H.escape


def rd(name):
    with open(os.path.join(CAP, name), encoding="utf-8", errors="replace") as f:
        return f.read()


def flat(s):
    return re.sub(r"\s+", " ", s).strip()


def between(text, start, end):
    a = text.index(start)
    b = text.index(end, a + len(start))
    return text[a:b]


quotes = {}


def add(key, lang, kind, url, title, body, doc_date, year=None):
    quotes[key] = {"lang": lang, "kind": kind, "url": url, "title": title, "html": body, "doc_date": doc_date,
                   "year": year, "retrieved": RETRIEVED}


# 1. U.S. Department of Education page, one sentence (English)
ed = flat(rd("ed_equal.txt"))
s = between(ed, "The U.S. Supreme Court has affirmed", "OCR works to ensure")
add("ed_page_en", "en", "ed",
    "https://www.ed.gov/laws-and-policy/civil-rights-laws/title-vi/title-vi-key-issues/equal-rights-public-education-regardless-of-immigrationcitizenship-status",
    "Equal Rights to Public Education Regardless of Immigration/Citizenship Status", "<p>%s</p>" % E(s.strip()), "Page last reviewed October 2, 2026")

# 2. ED status notice of a different, rescinded letter (English)
rs = flat(rd("ed_rescinded.txt"))
s = between(rs, "This letter has been formally rescinded", "Dear Educators")
add("ed_rescinded_en", "en", "ed",
    "https://www.ed.gov/laws-and-policy/key-policy-letters/dear-colleague-letter-resources-ensuring-equal-access-education-immigrant-students-rescinded",
    "Dear Colleague Letter: Resources for Ensuring Equal Access to Education for Immigrant Students (Rescinded)",
    "<p>%s</p>" % E(s.strip()), "January 8, 2025")

# 3. ED EL Family Tool Kit, "Enrolling your child in school": the first page of the rights section (Spanish and English)
NC_ES = "https://ncela.ed.gov/sites/default/files/2023-04/enrolling-spanish.pdf"
NC_EN = "https://ncela.ed.gov/sites/default/files/legacy/files/family_toolkit/EL-Family-Tool-Kit-Enrolling-Your-Child-in-School.pdf"


def toolkit(txt, start, end, intro_end, foot1, foot2_end, h3):
    t = txt
    block = between(t, start, end)
    head, rest = block.split(intro_end, 1)
    intro = flat(head + intro_end)
    bullets = [flat(b) for b in re.split(r"\n\s*[●•]\s+", "\n" + rest)[1:]]
    out = ["<h3>%s</h3>" % E(h3), "<p>%s</p>" % E(intro.replace(h3, "").strip()), "<ul>"]
    for b in bullets:
        b = re.sub(r"([\.a-zé])([12])$", r"\1<sup>\2</sup>", b) if False else b
        out.append("<li>%s</li>" % E(b))
    out.append("</ul>")
    return out


def tk(lang):
    t = rd("pdf/ncela_enrolling_%s.txt" % lang)
    if lang == "es":
        a = t.index("\nDerechos de la familia y del estudiante\n") + 1
        b = t.index("BORRADOR 12-03-18")  # end of page 1
        page = t[a:b]
        h3 = "Derechos de la familia y del estudiante"
        foot_at = page.index("1 Los estudiantes con visas")
    else:
        a = t.index("\nFamily and Student Rights\n") + 1
        b = t.index("Rev. 12/03/2018")
        page = t[a:b]
        h3 = "Family and Student Rights"
        foot_at = page.index("1 Students with F-1")
    main, foot = page[:foot_at], page[foot_at:]
    lines = main.split("\n", 1)[1]
    parts = re.split(r"\n\s*[●•]\s+", "\n" + lines)
    intro = flat(parts[0])
    bullets = [flat(p) for p in parts[1:]][:5]  # the first five bullets (rights); the two English-learner service bullets are not copied
    # keep only the bullets on page 1 (the page ends after bullet 5); the Spanish and English page 1 both end with the "meaningful communication" bullet
    f1 = flat(foot[foot.index("1 "):foot.index("2 ", 5)])[2:]
    f2 = re.sub(r"\s+\d$", "", flat(foot[foot.index(re.search(r"\n2 (La información|Information)", foot).group(0).strip()):])[2:])
    # strip footnote markers from the end of bullet text: "...gratuita.1" -> sup
    def sup(x):
        return re.sub(r"(?<=[\.\)a-zA-Zé])([12])$", r"<sup>\1</sup>", x) if x[-2:] in ("a.", ".", "") or True else x
    body = ["<h3>%s</h3>" % E(h3), "<p>%s</p>" % E(intro), "<ul>"]
    for x in bullets:
        m = re.search(r"^(.*[\.\)])\s?([12])$", x)
        if m and x.endswith(("gratuita.1", "gratuita.1", "free public education.1")) or (m and re.search(r"(escrito\.|permission\.)\s?2$", x)):
            body.append("<li>%s<sup>%s</sup></li>" % (E(m.group(1)), m.group(2)))
        else:
            body.append("<li>%s</li>" % E(x))
    body.append("</ul>")
    body.append('<p class="fn"><sup>1</sup> %s</p>' % E(f1))
    body.append('<p class="fn"><sup>2</sup> %s</p>' % E(f2))
    return "\n".join(body)


add("toolkit_es", "es", "ed", NC_ES, "Inscribir a su hijo en la escuela", tk("es"), "Borrador 12-03-18")
add("toolkit_en", "en", "ed", NC_EN, "Enrolling Your Child in School", tk("en"), "Rev. 12/03/2018")

# 4. Joint DOJ and ED Questions and Answers, revised May 8, 2014 (English, ERIC copy of the ED document)
QA = "https://files.eric.ed.gov/fulltext/ED596830.pdf"
QA_TITLE = "Information on the Rights of All Children to Enroll in School: Questions and Answers for States, School Districts and Parents"
qa = rd("pdf/eric_qa_en.txt")
qa = re.sub(r"\n\s*Revised as of May 8, 2014\s*", "\n\n", qa)
qa = re.sub(r"\n\s*Page \d+ . Questions and Answers: School Enrollment Procedures\s*", "\n\n", qa)


def qa_quote(n, nxt, fn_start=None, fn_end=None):
    block = between(qa, "Q - %d." % n, nxt)
    fn = None
    if fn_start:  # a footnote printed at the bottom of its page: take it from the text and cut it out of the block
        m = re.search(fn_start, qa, flags=re.S)
        fn = flat(m.group(0))
        block = block.replace(m.group(0), "")
    paras = [flat(p) for p in re.split(r"\n\s*\n", block) if flat(p)]
    first = paras[0]
    out = []
    m = re.match(r"^(Q - \d+\.)\s(.*?)\s(A\s?-\s?\d+\.)\s(.*)$", first, flags=re.S)
    if m:
        out.append("<p><strong>%s %s</strong></p>" % (E(m.group(1)), E(m.group(2))))
        out.append("<p>%s %s</p>" % (E(m.group(3)), E(m.group(4))))
    else:
        out.append("<p><strong>%s</strong></p>" % E(first))
    for p in paras[1:]:
        out.append("<p>%s</p>" % E(p))
    if fn:
        out.append('<p class="fn">%s</p>' % E(fn))
    return out


for n, nxt, fs, fe, key in [(1, "Q - 2.", r"\n3\s+For purposes of this guidance.*?law\.", None, "qa1_en"), (5, "Q - 6.", None, None, "qa5_en"),
                            (7, "Q - 8.", r"\n5\s+Similarly, a school district.*?number\.", None, "qa7_en"), (8, "Q - 9.", None, None, "qa8_en")]:
    parts = qa_quote(n, nxt, fs, fe)
    add(key, "en", "doj", QA, QA_TITLE, "\n".join(parts), "Revised as of May 8, 2014")

# 5. ACLU of Arizona fact sheet, "What You Need to Know" list (English)
AZ = "https://www.acluaz.org/publications/fact-sheet-undocumented-students-families-school/"
h = rd("aclu_school_en.html")
i = h.index("What You Need to Know")
j = h.index("<ul>", i)
k = h.index("</ul>", j) + 5
ul = h[j:k]
ul = re.sub(r">\s+<", "><", ul)
ul = ul.replace("<li>", "\n<li>").replace("</ul>", "\n</ul>")
add("aclu_school_en", "en", "az", AZ, "Fact Sheet: Undocumented Students & Families in School", "<h3>What You Need to Know</h3>\n" + ul.strip(), "July 20, 2017", "2017")

# 6. A.R.S. 15-821, subsection A (English)
st = rd("azleg_821.txt")
a = st.index("A. Unless otherwise")
b = st.index("B. If a preschool")
add("ars_15_821_a", "en", "az_leg", "https://www.azleg.gov/ars/15/00821.htm", "15-821. Admission of children; required age",
    "<h3>15-821. Admission of children; required age</h3>\n<p>%s</p>" % E(flat(st[a:b])), "Subsection A")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(quotes, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("wrote", OUT, len(quotes), "quotes")
