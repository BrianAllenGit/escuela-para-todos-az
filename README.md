# Escuela para todos · Arizona

"Can my child go to public school in Arizona?" A free, ad-free, zero-tracking, Spanish-first page (Spanish and English) for parents and guardians in Arizona. The answer is not written by us: it is what the U.S. Department of Education, the U.S. Department of Justice, the Arizona Legislature and the ACLU of Arizona say, quoted word for word with credit.

Status: private draft. Not published. Planned address once shipped: https://brianallengit.github.io/escuela-para-todos-az/

## What the page does

One reason to arrive (can my child go to public school, and what may the school ask for?) and one action to leave with (enroll; and if you think the school asked for papers it may not ask for, file a complaint):

1. The quoted answer: the Department of Education family guide (Spanish and English) and one sentence from its Office for Civil Rights page.
2. Steps: enroll (ask the school which documents it asks for), or file a complaint with the ED Office for Civil Rights, the DOJ Civil Rights Division, or the Arizona Attorney General (links only; nothing is submitted for you).
3. Quoted detail (English): four items of the 2014 DOJ and ED Questions and Answers, the ACLU of Arizona "What You Need to Know" list, A.R.S. 15-821(A).
4. How current the sources are (see below).
5. A printable card (the answer and the steps).

## Source status you should know (checked 2026-11-27)

- The ED page still lists the May 8, 2014 Dear Colleague letter, Questions and Answers and Fact Sheet. Those PDFs, and the original justice.gov copies, could not be read by a bot (403, or the old addresses are gone). The letter and fact sheet are therefore NOT quoted; the Q&A is quoted from an ERIC (ed.gov research library) copy.
- A different ED letter (January 8, 2025) was rescinded. The page says so and does not use it.
- The only official Spanish text copied is the ED/NCELA family guide, which is stamped "BORRADOR" (draft).

Details: [docs/SOURCES.md](docs/SOURCES.md).

## No legal wording is written by us

All legal wording is quoted unchanged (`tools/quotes.json`, built from pages and PDFs saved in `tools/captures/`). `python3 tools/verify_quotes.py` proves every block of every quote is a word for word match of its capture and that it is on the page. Everything else is a link or a short navigation label; the Spanish labels are listed in [docs/NEEDS-NATIVE-READ.md](docs/NEEDS-NATIVE-READ.md).

## Privacy promise

- No cookies, no localStorage, no accounts, no forms, no analytics, no ads, no third-party fonts or scripts.
- A strict Content Security Policy blocks every outside request. The page loads only its own HTML, CSS and one small script.
- The language choice lives only in the page address (`?lang=en`).
- Links leave the site. Other sites have their own privacy rules.
- GitHub Pages, the planned host, may keep standard visit logs that the page cannot see or control.

## Accessibility and checks

WCAG 2.2 AA target. Evidence: [docs/DEFINITION-OF-DONE.md](docs/DEFINITION-OF-DONE.md), [docs/screenshots](docs/screenshots), [docs/lighthouse](docs/lighthouse).

## Run it

Open `index.html` in a browser. Nothing to install.

## Change the content

```
python3 tools/extract_quotes.py   # rebuilds tools/quotes.json from tools/captures/
python3 tools/build.py            # rewrites index.html, docs/SOURCES.md, docs/NEEDS-NATIVE-READ.md
python3 tools/verify_quotes.py    # every quote must match its capture
./tools/audit.sh                  # axe, overflow, screenshots (Docker only)
./tools/dod.sh                    # icons, head and JSON-LD validation, keyboard, Lighthouse (Docker only)
```

`tools/fetch/` has the capture script (headless Chromium in Docker; nothing is installed on the host). PDFs in `tools/captures/pdf/` were downloaded with plain `curl` and converted with `pdftotext -layout`. When a link or quote is checked again, update `CHECKED` in `tools/build.py`.

## Deploy to GitHub Pages (only when the owner says so)

1. Make the repository public. 2. Settings, Pages, branch `main`, folder `/ (root)`. 3. If the address changes, update `SITE_URL` in `tools/build.py` and `tools/validate.js`, then rebuild.

MIT License.
