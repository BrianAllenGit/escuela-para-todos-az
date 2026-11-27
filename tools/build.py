#!/usr/bin/env python3
"""Builds index.html, docs/SOURCES.md and docs/NEEDS-NATIVE-READ.md from one place.

Run:  python3 tools/build.py     (after tools/extract_quotes.py when the captures change)
No dependencies. The output files are committed, so the site itself has no build step.
Rule: no legal wording on the page is written by us. Quoted text lives in tools/quotes.json (copied from captured source pages),
everything else is a link or a short navigation label (every Spanish one is listed in docs/NEEDS-NATIVE-READ.md).
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKED = "2026-11-27"
CHECKED_TXT = {"es": "27 de noviembre de 2026", "en": "November 27, 2026"}
SITE_URL = "https://brianallengit.github.io/escuela-para-todos-az/"
NAME = "Escuela para todos · Arizona"
E = html.escape

ED_PAGE = "https://www.ed.gov/laws-and-policy/civil-rights-laws/title-vi/title-vi-key-issues/equal-rights-public-education-regardless-of-immigrationcitizenship-status"
US_GOV = "US government work (17 U.S.C. 105: no copyright in the United States). "

# id -> (url, Spanish label, English label, what we took from it, terms note)
SOURCES = {
    "ed_page": (
        ED_PAGE,
        "Departamento de Educación de EE. UU. (OCR): Derechos iguales a la educación pública sin importar el estatus migratorio (en inglés)",
        "U.S. Department of Education (OCR): Equal Rights to Public Education Regardless of Immigration/Citizenship Status",
        "One sentence quoted word for word. The page also lists the 2014 Dear Colleague letter, its Questions and Answers and its Fact Sheet (page shows \"Page Last Reviewed: October 2, 2026\"). Those PDFs answered 403 to automated requests, so they could not be read from ed.gov.",
        US_GOV + "ed.gov website-policies page returned \"The requested page could not be found\" when read, so ED's own reuse statement was not read.",
    ),
    "ed_rescinded": (
        "https://www.ed.gov/laws-and-policy/key-policy-letters/dear-colleague-letter-resources-ensuring-equal-access-education-immigrant-students-rescinded",
        "Departamento de Educación de EE. UU.: carta del 8 de enero de 2025 (anulada), página histórica (en inglés)",
        "U.S. Department of Education: Dear Colleague Letter of January 8, 2025 (Rescinded), historical page",
        "The status sentence quoted word for word. This is a different letter from the 2014 one; its text is not used.",
        US_GOV,
    ),
    "ncela_es": (
        "https://ncela.ed.gov/sites/default/files/2023-04/enrolling-spanish.pdf",
        "Departamento de Educación de EE. UU. (NCELA): Inscribir a su hijo en la escuela, Paquete de Herramientas para Familias de Estudiantes de Inglés (en español)",
        "U.S. Department of Education (NCELA): Enrolling Your Child in School, English Learner Family Tool Kit (Spanish version)",
        "The \"Derechos de la familia y del estudiante\" section, first five bullets and two footnotes, word for word. Every page of the PDF is stamped \"BORRADOR 12-03-18\" (draft). The two last bullets (English learner services) are not copied.",
        US_GOV + "The PDF carries no copyright notice, only a disclaimer. UNVERIFIED and for a human: ED toolkits are sometimes written by contractors; whether NCELA claims any copyright on this one was not found.",
    ),
    "ncela_en": (
        "https://ncela.ed.gov/sites/default/files/legacy/files/family_toolkit/EL-Family-Tool-Kit-Enrolling-Your-Child-in-School.pdf",
        "Departamento de Educación de EE. UU. (NCELA): Enrolling Your Child in School (versión en inglés)",
        "U.S. Department of Education (NCELA): Enrolling Your Child in School, English Learner Family Tool Kit",
        "The \"Family and Student Rights\" section, first five bullets and two footnotes, word for word (\"Rev. 12/03/2018\"). The two last bullets (English learner services) are not copied.",
        US_GOV + "Same note as the Spanish version.",
    ),
    "qa_eric": (
        "https://files.eric.ed.gov/fulltext/ED596830.pdf",
        "Departamento de Justicia y Departamento de Educación: Preguntas y respuestas sobre los derechos de todos los niños a matricularse en la escuela, revisado el 8 de mayo de 2014 (en inglés; copia en ERIC)",
        "Department of Justice and Department of Education: Information on the Rights of All Children to Enroll in School, Questions and Answers (revised May 8, 2014; copy hosted by ERIC)",
        "Q-1, Q-5, Q-7 and Q-8, each with its answer and its footnote, word for word. The document is a joint DOJ Civil Rights Division and ED Office for Civil Rights and Office of the General Counsel work. ERIC (files.eric.ed.gov) is the Education Department's research library site; this copy is titled as the 2014 Q&A.",
        US_GOV + "justice.gov Legal Policies (read 2026-11-27 at https://www.justice.gov/legalpolicies): \"Unless otherwise indicated, information on Department of Justice websites is in the public domain and may be copied and distributed without permission.\" The original justice.gov addresses no longer serve the file (see below).",
    ),
    "aclu_school": (
        "https://www.acluaz.org/publications/fact-sheet-undocumented-students-families-school/",
        "ACLU de Arizona: Fact Sheet: Undocumented Students & Families in School (en inglés)",
        "ACLU of Arizona: Fact Sheet: Undocumented Students & Families in School",
        "The \"What You Need to Know\" list (4 bullets), word for word. Document date July 20, 2017. The \"Things to Note\" section (ICE sensitive locations policy) is not copied because that policy has changed since 2017. No Spanish version was found: the Spanish address returns the English page.",
        "User Agreement (effective July 1, 2024, saved in tools/captures/terms_acluaz.txt): text may be copied if not for commercial use, without editorial changes, not misleadingly excerpted, with the notice \"Copyright [year] ACLU of Arizona. Originally posted by the ACLU of Arizona at ...\". Shown on the page.",
    ),
    "azleg": (
        "https://www.azleg.gov/ars/15/00821.htm",
        "Legislatura de Arizona: A.R.S. 15-821 (en inglés)",
        "Arizona Legislature: A.R.S. 15-821",
        "Subsection A quoted word for word. The statute says nothing about immigration status; it says schools \"shall admit children\" aged 6 to 21 who reside in the district and meet enrollment requirements. Subsections B to D are not copied.",
        "azleg.gov footer: \"© 2026 Arizona State Legislature. All Rights Reserved\". The text of a state statute is law; same approach as the sibling site conoce-tus-derechos-az (A.R.S. 13-2412). UNVERIFIED and for a human: confirm this approach.",
    ),
    "azag_schools": (
        "https://www.azag.gov/resources-for-schools",
        "Oficina del Fiscal General de Arizona: Recursos para escuelas (en inglés)",
        "Arizona Attorney General: Resources for Schools",
        "Link only. The page (English) says the Attorney General is committed to every Arizona student's right to a free public education regardless of immigration status, and links to the legal authorities (Plyler v. Doe, Title VI, FERPA, McKinney-Vento, A.R.S. 15-821).",
        "Link only. The AG's terms-of-use page was not found (404); no text is copied.",
    ),
    "ocr": (
        "https://ocrcas.ed.gov/",
        "Departamento de Educación de EE. UU.: Sistema de Evaluación de Quejas de la Oficina de Derechos Civiles (formulario, en inglés)",
        "U.S. Department of Education: Office for Civil Rights Complaint Assessment System",
        "Link only. The form was not opened or filled in. The page says the assessment is available only in English and gives free language help at 1-800-USA-LEARN (1-800-872-5327).",
        "Link only.",
    ),
    "ed_file_complaint": (
        "https://www.ed.gov/laws-and-policy/civil-rights-laws/file-complaint",
        "Departamento de Educación de EE. UU.: Cómo presentar una queja ante la Oficina de Derechos Civiles (en inglés)",
        "U.S. Department of Education: How to file a complaint with the Office for Civil Rights",
        "Link only. Explains how to file with ED's Office for Civil Rights.",
        "Link only.",
    ),
    "crt": (
        "https://civilrights.justice.gov/report/",
        "Departamento de Justicia de EE. UU., División de Derechos Civiles: reportar una violación de derechos civiles (en inglés)",
        "U.S. Department of Justice, Civil Rights Division: report a civil rights violation",
        "Link only. The form was not opened or filled in. The Division's page lists \"Discrimination at a school, educational program or service, or related to receiving education\" as a kind of report. No Spanish form was found (civilrights.justice.gov/es returned 404).",
        "Link only.",
    ),
    "azag_civil": (
        "https://www.azag.gov/complaints/civil-rights",
        "Oficina del Fiscal General de Arizona: Cuestionario de admisión de derechos civiles (en inglés)",
        "Arizona Attorney General: Civil Rights Intake Questionnaire",
        "Link only. The form was not opened or filled in. The page says people who believe they are victims of discrimination can submit it and will be contacted for an intake interview; a printable form is offered for mail.",
        "Link only. AG reuse terms not found; no text is copied.",
    ),
    "aclu_page": (
        "https://www.acluaz.org/publications/fact-sheet-undocumented-students-families-school/",
        "ACLU de Arizona: hoja informativa (en inglés)",
        "ACLU of Arizona: fact sheet",
        "See the quoted list above.",
        "See above.",
    ),
}

SPANISH_UI = []  # every Spanish string written for this page, for docs/NEEDS-NATIVE-READ.md

TEXT = {
    "title": "¿Puede mi hijo ir a la escuela pública en Arizona?",
    "title_en": "Can my child go to public school in Arizona?",
    "desc": "¿Puede mi hijo ir a la escuela pública en Arizona? Lee lo que dicen las fuentes oficiales y adónde quejarte. Gratis, sin rastreo. Español e inglés.",
    "desc_en": "Can my child go to public school in Arizona? Read what the official sources say and where to complain. Free, no tracking. Spanish and English.",
    "imgalt": "Escuela para todos, Arizona: ¿puede mi hijo ir a la escuela pública? Can my child go to public school in Arizona?",
}
SPANISH_UI += [TEXT["title"], TEXT["desc"], TEXT["imgalt"]]


def ext(url, label, extra=""):
    return '<a href="%s" rel="noopener noreferrer"%s>%s</a>' % (E(url, quote=True), extra, label)


def sources(lang, ids, level=3):
    head = {"es": "De dónde viene esta información", "en": "Where this information comes from"}[lang]
    chk = {"es": "revisado el", "en": "checked on"}[lang]
    li = []
    for i in ids:
        url, es, en, _f, _t = SOURCES[i]
        li.append('<li>%s <span class="chk">(%s <time datetime="%s">%s</time>)</span></li>'
                  % (ext(url, E(es if lang == "es" else en)), chk, CHECKED, CHECKED_TXT[lang]))
    return '<div class="src"><h%d>%s</h%d><ul>%s</ul></div>' % (level, head, level, "".join(li))


with open(os.path.join(ROOT, "tools", "quotes.json"), encoding="utf-8") as _f:
    QUOTES = json.load(_f)


def quote(lang, key):
    """A passage copied word for word from its source, with the credit its terms require."""
    q = QUOTES[key]
    es = lang == "es"
    link = '<a href="%s" rel="noopener noreferrer">%s</a>' % (E(q["url"], quote=True), E(q["url"]))
    read = ("Leído el %s." if es else "Read on %s.") % CHECKED_TXT[lang]
    en_note = " (en inglés)" if (es and q["lang"] == "en") else ""
    if q["kind"] in ("ed", "doj"):
        who = {"ed": "Departamento de Educación de EE. UU." if es else "U.S. Department of Education",
               "doj": "Departamento de Justicia y Departamento de Educación de EE. UU." if es else "U.S. Department of Justice and U.S. Department of Education"}[q["kind"]]
        label = ("Cita del %s%s, palabra por palabra y sin cambios" if es else "Quoted from the %s%s, word for word and unchanged") % (who, en_note) if es else \
                "Quoted from the %s, word for word and unchanged" % who
        notice = ("Fuente: %s, %s. Documento: %s. Información del gobierno de EE. UU., de dominio público. %s"
                  if es else "Source: %s, %s. Document: %s. U.S. government information, in the public domain. %s") % (E(who), link, E(q["doc_date"]), read)
    elif q["kind"] == "az":
        label = "Cita de la ACLU de Arizona%s, palabra por palabra y sin cambios" % en_note if es else "Quoted from the ACLU of Arizona, word for word and unchanged"
        notice = "Copyright %s ACLU of Arizona. Originally posted by the ACLU of Arizona at %s. %s" % (q["year"], link, read)
    else:
        label = "Cita de la ley de Arizona%s, palabra por palabra y sin cambios" % en_note if es else "Quoted from Arizona law, word for word and unchanged"
        notice = ("Arizona Revised Statutes, %s. Leído en %s el %s." if es else "Arizona Revised Statutes, %s. Read at %s on %s.") % (E(q["doc_date"]), link, CHECKED_TXT[lang]) if True else ""
    if es:
        SPANISH_UI.append(label)
        SPANISH_UI.append("Fuente: ... Documento: ... Información del gobierno de EE. UU., de dominio público. Leído el ... (aviso de crédito)")
    return '<figure class="quote" lang="%s"><p class="qlabel" lang="%s">%s</p><div class="qbody">%s</div><figcaption>%s</figcaption></figure>' % (
        q["lang"], lang, E(label), q["html"], notice)


def btn(url, label, cls="primary", lang_attr=""):
    return '<a class="btn %s" href="%s" rel="noopener noreferrer"%s>%s</a>' % (cls, E(url, quote=True), lang_attr, E(label))


def content(lang):
    es = lang == "es"
    p = lang
    h = []
    A = h.append

    def T(a, b):
        if es:
            SPANISH_UI.append(re.sub(r"<[^>]+>", "", a) if isinstance(a, str) else " | ".join(re.sub(r"<[^>]+>", "", x) for x in a))
        return a if es else b

    def sec(i, title, body, cls=""):
        A('<section class="panel%s" id="%s-%s" tabindex="-1" aria-labelledby="%s-%s-h"><h2 id="%s-%s-h">%s</h2>%s</section>' % (cls, p, i, p, i, p, i, title, body))

    A('<section class="notice" aria-labelledby="%s-imp-h"><h2 id="%s-imp-h">%s</h2><p>%s</p></section>' % (
        p, p, T("Importante", "Important"),
        T("Esta página da <strong>información general</strong> y enlaces a fuentes oficiales. <strong>No es consejo legal</strong> y no puede decirte qué pasará en tu caso. "
          "No guarda ni recoge ningún dato tuyo. Los enlaces te llevan a otros sitios.",
          "This page gives <strong>general information</strong> and links to official sources. <strong>It is not legal advice</strong> and it cannot tell you what will happen in your case. "
          "It does not save or collect any information about you. Links take you to other sites.")))

    # 1 the answer: quoted, not written by us
    ans = "<p>%s</p>%s%s<div class=\"calls no-print\"><button type=\"button\" class=\"btn primary big js-print\">%s</button></div>%s" % (
        T("Esto dice el gobierno federal. Está copiado palabra por palabra.", "This is what the federal government says. It is copied word for word."),
        quote(lang, "toolkit_" + lang),
        quote(lang, "ed_page_en"),
        T("Imprimir la tarjeta (esta sección y los pasos)", "Print the card (this section and the steps)"),
        sources(lang, ["ncela_" + lang, "ed_page"]))
    sec("answer", T("¿Puede mi hijo ir a la escuela pública en Arizona?", "Can my child go to public school in Arizona?"), ans, " card")

    # 2 steps
    steps = [
        (T("<strong>Inscribir a tu hijo:</strong> ve a la escuela o al distrito de tu zona y pregunta qué documentos piden. Puedes llevar esta tarjeta impresa.",
           "<strong>Enroll your child:</strong> go to the school or district in your area and ask which documents they ask for. You can bring this card printed."),
         [btn(SOURCES["ncela_es"][0] if es else SOURCES["ncela_en"][0],
              T("Guía del Departamento de Educación: Inscribir a su hijo en la escuela (PDF)", "Department of Education guide: Enrolling Your Child in School (PDF)"), "primary"),
          btn(SOURCES["azag_schools"][0], T("Fiscal General de Arizona: recursos para escuelas (en inglés)", "Arizona Attorney General: resources for schools"), "secondary")]),
        (T("<strong>Si crees que la escuela pidió papeles que no puede pedir, o no dejó inscribir a tu hijo:</strong> compara con las citas de esta página y presenta una queja. Cada botón abre una página oficial.",
           "<strong>If you think the school asked for papers it may not ask for, or would not let your child enroll:</strong> compare with the quotes on this page and file a complaint. Each button opens an official page."),
         [btn(SOURCES["ocr"][0], T("Queja a la Oficina de Derechos Civiles del Departamento de Educación (en inglés)", "Complaint to the Department of Education Office for Civil Rights"), "primary"),
          btn(SOURCES["crt"][0], T("Reporte a la División de Derechos Civiles del Departamento de Justicia (en inglés)", "Report to the Department of Justice Civil Rights Division"), "primary"),
          btn(SOURCES["azag_civil"][0], T("Cuestionario de derechos civiles del Fiscal General de Arizona (en inglés)", "Arizona Attorney General civil rights questionnaire"), "primary"),
          ]),
    ]
    hint = T("El formulario del Departamento de Educación está solo en inglés. Esa página dice que ofrece ayuda gratis con otros idiomas: 1-800-872-5327 (1-800-USA-LEARN).",
             "The Department of Education form is in English only. That page says it offers free language help: 1-800-872-5327 (1-800-USA-LEARN).")
    body = '<p>%s</p><ol class="steps">%s</ol><p class="hint">%s</p>' % (
        T("Haz esto ahora. Cada botón abre una página oficial.", "Do this now. Each button opens an official page."),
        "".join('<li><p>%s</p><div class="calls">%s</div></li>' % (t, "".join(b)) for t, b in steps), hint)
    sec("steps", T("Qué hacer ahora", "What to do now"), body + sources(lang, ["ncela_" + lang, "azag_schools", "ocr", "ed_file_complaint", "crt", "azag_civil"]), " card")

    # 3 details, quoted (English only in the sources)
    det = "<p>%s</p>%s%s%s%s%s%s" % (
        T("Estos textos oficiales están en inglés. La versión en español de 2014 del Departamento de Justicia ya no abre en sus direcciones, así que no se copia.",
          "These official texts are in English. The Department of Justice's 2014 versions no longer open at their addresses, so those are not copied."),
        quote(lang, "qa1_en"), quote(lang, "qa5_en"), quote(lang, "qa7_en"), quote(lang, "qa8_en"), quote(lang, "aclu_school_en"),
        sources(lang, ["qa_eric", "aclu_school"]))
    sec("details", T("Qué puede pedir la escuela y qué no (en inglés)", "What the school may ask for and what it may not"), det)

    # 4 Arizona law
    sec("law", T("La ley de Arizona", "Arizona law"),
        "<p>%s</p>%s%s" % (
            T("Esto dice la ley de Arizona sobre quién debe ser admitido en las escuelas.", "This is what Arizona law says about who schools must admit."),
            quote(lang, "ars_15_821_a"), sources(lang, ["azleg", "azag_schools"])))

    # 5 how current
    cur = T([
        "Los documentos federales de 2014 (carta, hoja informativa, preguntas y respuestas) siguen en la lista de la página del Departamento de Educación, que dice «Page Last Reviewed: October 2, 2026» (última revisión: 2 de octubre de 2026).",
        "Las copias originales del Departamento de Justicia (justice.gov) ya no abrían en sus direcciones de 2014 cuando se revisaron. Por eso la cita de preguntas y respuestas viene de una copia en files.eric.ed.gov, un sitio del gobierno de EE. UU.",
        "Otra carta del Departamento de Educación, del 8 de enero de 2025, fue anulada. Es una carta distinta de la de 2014 y esta página no usa su texto. Se muestra abajo la frase oficial sobre su estado.",
        "La guía en español del Departamento de Educación tiene la marca «BORRADOR 12-03-18» en cada página. La hoja de la ACLU de Arizona es de 2017.",
        "No revisamos si hubo cambios en las políticas federales después de la fecha de revisión de esta página.",
    ], [
        "The 2014 federal documents (letter, fact sheet, questions and answers) are still listed on the Department of Education page, which says \"Page Last Reviewed: October 2, 2026\".",
        "The Department of Justice's original copies (justice.gov) no longer opened at their 2014 addresses when checked. That is why the questions and answers quote comes from a copy on files.eric.ed.gov, a U.S. government site.",
        "A different Department of Education letter, dated January 8, 2025, was rescinded. It is not the 2014 letter and this page does not use its text. The official sentence about its status is shown below.",
        "The Department of Education's Spanish guide is stamped \"BORRADOR 12-03-18\" (draft) on every page. The ACLU of Arizona sheet is from 2017.",
        "We did not check for federal policy changes after this page's review date.",
    ])
    sec("current", T("Qué tan actuales son estas fuentes", "How current these sources are"),
        '<ul class="list">%s</ul>%s%s' % ("".join("<li>%s</li>" % x for x in cur), quote(lang, "ed_rescinded_en"), sources(lang, ["ed_rescinded", "ed_page", "qa_eric"])))

    # 6 about
    li = T([
        "<strong>No es consejo legal.</strong> Es una página de enlaces y de citas copiadas de fuentes oficiales y de la ACLU de Arizona. No dice qué pasará en tu caso. Habla con un abogado o con una organización de ayuda legal sobre tu situación.",
        "<strong>No recogemos datos.</strong> Esta página no tiene analíticas, anuncios, cookies, formularios ni cuentas, y no guarda nada.",
        "<strong>Los enlaces salen de este sitio.</strong> Los otros sitios tienen sus propias reglas de privacidad. Esta página no abre ni llena ningún formulario por ti.",
        "Cada enlace se revisó el <time datetime=\"%s\">%s</time>. Las citas son del gobierno de EE. UU. (de dominio público), de la Legislatura de Arizona y de la ACLU de Arizona; se copian <strong>palabra por palabra y sin cambios</strong>, con el crédito que cada fuente pide. Los títulos, botones y avisos fuera de un recuadro de cita son de esta página." % (CHECKED, CHECKED_TXT["es"]),
        "Esta página no está afiliada a ninguna de las organizaciones nombradas ni al gobierno.",
        "En un teléfono o computadora compartidos, el historial del navegador puede mostrar que visitaste esta página.",
        "Es gratis y siempre lo será.",
    ], [
        "<strong>This is not legal advice.</strong> It is a page of links and of quotes copied from official sources and the ACLU of Arizona. It does not say what will happen in your case. Talk to a lawyer or a legal aid organization about your situation.",
        "<strong>We collect no data.</strong> This page has no analytics, ads, cookies, forms or accounts, and it saves nothing.",
        "<strong>Links leave this site.</strong> Other sites have their own privacy rules. This page does not open or fill in any form for you.",
        "Every link was checked on <time datetime=\"%s\">%s</time>. The quotes are from the U.S. government (public domain), the Arizona Legislature and the ACLU of Arizona; they are copied <strong>word for word and unchanged</strong>, with the credit each source asks for. Headings, buttons and notices outside a quote box are this page's own." % (CHECKED, CHECKED_TXT["en"]),
        "This page is not affiliated with any of the organizations named or with the government.",
        "On a shared phone or computer, the browser history can show that you visited this page.",
        "It is free and always will be.",
    ])
    sec("about", T("Sobre esta página", "About this page"),
        '<ul class="list">%s</ul><div class="calls no-print"><button type="button" class="btn primary big js-print">%s</button></div>' % (
            "".join("<li>%s</li>" % x for x in li), T("Imprimir la tarjeta", "Print the card")))
    h.insert(1, h.pop(0))  # the answer comes first, the notice right after it
    return "\n".join(h)


def jsonld_graph():
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": SITE_URL + "#org", "name": NAME, "url": SITE_URL, "logo": SITE_URL + "apple-touch-icon.png",
             "description": "Free, ad-free, zero-tracking page in Spanish and English that quotes official U.S. government and Arizona sources on enrolling a child in public school regardless of immigration status, with links to file a complaint."},
            {"@type": "WebSite", "@id": SITE_URL + "#website", "url": SITE_URL, "name": NAME, "description": TEXT["desc"],
             "inLanguage": ["es", "en"], "publisher": {"@id": SITE_URL + "#org"}},
            {"@type": "WebPage", "@id": SITE_URL + "#webpage", "url": SITE_URL, "name": TEXT["title"], "description": TEXT["desc"],
             "inLanguage": ["es", "en"], "isPartOf": {"@id": SITE_URL + "#website"}, "publisher": {"@id": SITE_URL + "#org"},
             "dateModified": CHECKED,
             "primaryImageOfPage": {"@type": "ImageObject", "url": SITE_URL + "og-image.png", "width": 1200, "height": 630},
             "about": {"@type": "Thing", "name": "Enrolling a child in an Arizona public school regardless of immigration status, and where to file a complaint"}},
        ],
    }


def page():
    foot_es = ("Este sitio no tiene analíticas y no guarda nada. Está alojado en GitHub Pages, que puede guardar registros estándar de visitas "
               "que nosotros no podemos ver ni controlar. Nosotros no agregamos nada.")
    foot_en = ("This site has no analytics and saves nothing. It is hosted on GitHub Pages, which may keep standard visit logs "
               "that we cannot see or control. We add nothing.")
    lead_es = "¿Puede mi hijo ir a la escuela pública en Arizona? Lee lo que dicen las fuentes oficiales, palabra por palabra, y adónde ir si la escuela no cumple."
    lead_en = "Can my child go to public school in Arizona? Read what the official sources say, word for word, and where to go if the school does not follow them."
    SPANISH_UI.extend([foot_es, "Ir al contenido", "Escuela para todos", "Escuelas · Arizona", lead_es])
    jsonld = json.dumps(jsonld_graph(), ensure_ascii=False, indent=1).replace("</", "<\\/")
    es_html, en_html = content("es"), content("en")
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{site}">
<link rel="alternate" hreflang="es" href="{site}">
<link rel="alternate" hreflang="en" href="{site}">
<link rel="alternate" hreflang="x-default" href="{site}">
<meta property="og:site_name" content="{name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}og-image.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{imgalt}">
<meta property="og:url" content="{site}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_US">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}og-image.png">
<meta name="twitter:image:alt" content="{imgalt}">
<meta name="theme-color" content="#1d4ed8">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<script type="application/ld+json">{jsonld}</script>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; manifest-src 'self'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<link rel="stylesheet" href="style.css">
<noscript><link rel="stylesheet" href="noscript.css"></noscript>
</head>
<body>
<a class="skip es" href="#main">Ir al contenido</a>
<a class="skip en" href="#main" lang="en">Skip to content</a>
<header class="top">
  <div class="brand">
    <h1 class="es">Escuela para todos <span class="where">Escuelas · Arizona</span></h1>
    <h1 class="en" lang="en">School for all <span class="where">Schools · Arizona</span></h1>
  </div>
  <div class="langs no-print" role="group" aria-label="Idioma / Language">
    <button type="button" id="lang-es" data-lang="es" lang="es" aria-label="ES, Español" aria-pressed="true">ES</button>
    <button type="button" id="lang-en" data-lang="en" lang="en" aria-label="EN, English" aria-pressed="false">EN</button>
  </div>
</header>

<main id="main" tabindex="-1">
<div class="es wrap">
<p class="lead">{lead_es}</p>
{es}
</div>
<div class="en wrap" lang="en">
<p class="lead">{lead_en}</p>
{en}
</div>
</main>

<footer>
  <p class="es">{foot_es}</p>
  <p class="en" lang="en">{foot_en}</p>
  <p>{name} · MIT</p>
</footer>
<script src="app.js"></script>
</body>
</html>
""".format(desc=TEXT["desc"], title=TEXT["title"], imgalt=TEXT["imgalt"], jsonld=jsonld, site=SITE_URL, name=NAME,
           es=es_html, en=en_html, foot_es=foot_es, foot_en=foot_en, lead_es=lead_es, lead_en=lead_en)


def sources_md():
    out = ["# Sources", "",
           "Every external fact and quote on the site, with the page it was read on and the terms that allow (or do not allow) using it.",
           "All pages were read on %s. This file is generated by `tools/build.py`; edit the lists there." % CHECKED, "",
           "Rule: no legal wording on the page is written by us. It is either quoted word for word (`tools/quotes.json`, proven by `tools/verify_quotes.py` against `tools/captures/`) or it is a link.", "",
           "## Source pages", "", "| # | Source | URL | What the page uses | Terms |", "|---|---|---|---|---|"]
    for n, (k, (url, _es, en, facts, terms)) in enumerate(SOURCES.items(), 1):
        if k == "aclu_page":
            continue
        out.append("| %d | %s | %s | %s | %s |" % (n, en, url, facts, terms.replace("|", "/")))
    out += ["", "## Quotes (10 records)", "",
            "| Key | Source | Shown in |", "|---|---|---|",
            "| toolkit_es | ED/NCELA, Inscribir a su hijo en la escuela, Derechos de la familia y del estudiante (first 5 bullets, 2 footnotes) | Spanish view |",
            "| toolkit_en | ED/NCELA, Enrolling Your Child in School, Family and Student Rights (first 5 bullets, 2 footnotes) | English view |",
            "| ed_page_en | ED OCR page, one sentence | both views |",
            "| qa1_en, qa5_en, qa7_en, qa8_en | DOJ/ED Questions and Answers (May 8, 2014), Q-1, Q-5, Q-7, Q-8 (ERIC copy) | both views |",
            "| aclu_school_en | ACLU of Arizona fact sheet (2017), \"What You Need to Know\" | both views |",
            "| ars_15_821_a | A.R.S. 15-821, subsection A | both views |",
            "| ed_rescinded_en | ED status sentence for the rescinded January 8, 2025 letter | both views |",
            "", "## Federal documents: current status (read 2026-11-27)", "",
            "- The ED OCR page (\"Equal Rights to Public Education Regardless of Immigration/Citizenship Status\", \"Page Last Reviewed: October 2, 2026\") still lists, under May 8, 2014: the \"Dear Colleague\" letter on School Enrollment Procedures, the Questions and Answers, and the Fact Sheet. Nothing on that page says they were withdrawn or archived.",
            "- Those three PDFs (ed.gov, `.../ocr/letters/colleague-201405.pdf`, `.../ocr/docs/qa-201405.pdf`, `.../ocr/docs/dcl-factsheet-201405.pdf`) and the justice.gov copies (`justice.gov/media/1161421/dl`, `justice.gov/crt/page/file/1425316/dl`) answered HTTP 403 to automated requests. No workaround was used. So the Dear Colleague letter and the Fact Sheet are linked from the ED page only through the page; they are NOT quoted.",
            "- The DOJ addresses of 2014 (`justice.gov/crt/about/edu/documents/plylerletter.pdf`, `plylerfact.pdf`, `plylerqa.pdf` and the `...spanish.pdf` versions, listed on https://www.justice.gov/usao-nj/civil-rights-enforcement/public-education) redirect to the justice.gov home page or answer 404. DOJ no longer serves them there.",
            "- The Questions and Answers (English) are quoted from files.eric.ed.gov/fulltext/ED596830.pdf, a copy on an Education Department research site, which returned the PDF. It says \"Revised as of May 8, 2014\".",
            "- A different letter, the Secretary's \"Dear Colleague Letter: Resources for Ensuring Equal Access to Education for Immigrant Students\" (January 8, 2025), is marked \"formally rescinded ... historical purposes only\". Its text points readers to the 2014 Questions and Answers, but this page does not use it.",
            "- Spanish: the only official Spanish text that could be copied is the ED/NCELA family guide (stamped BORRADOR, draft). The Spanish versions of the 2014 letter, fact sheet and Q&A could not be opened.",
            "", "## Looked for and left out", "",
            "- 2014 Dear Colleague letter and Fact Sheet in English and Spanish: not readable (see above). A human could open them in a browser from the ED page and, if they are still current, add them as quotes.",
            "- ACLU of Arizona \"Things to Note\" (ICE sensitive-locations policy, 2017): not copied because that policy has changed since.",
            "- ACLU of Arizona Spanish version: the Spanish address returns the English page.",
            "- MALDEF 2020 warning to two Arizona districts: not used (a human could link it; its terms were not read).",
            "- Arizona Attorney General text: only linked (its terms page was not found).",
            "- A.R.S. 15-821 subsections B to D (preschool, kindergarten age, guardianship): not relevant to the one action, not copied.",
            "- School district enrollment pages (for example Phoenix-area districts): none linked, because their documents lists were not read.",
            "", "## Notes for the reviewer", "",
            "- Spanish headings, buttons and notices written for this page were produced by an AI and need a native-speaker read: see NEEDS-NATIVE-READ.md. The quoted Spanish is the Department of Education's own.",
            "- The page never says \"yes\" in our own words. The answer is the quoted federal sentence and the quoted rights list.",
            "- The statute (A.R.S. 15-821) says nothing about immigration status; the page does not claim it does.",
            ""]
    return "\n".join(out)


def native_md():
    seen, rows = set(), []
    for s in SPANISH_UI:
        s = html.unescape(re.sub(r"\s+", " ", s)).strip()
        if s and s not in seen:
            seen.add(s)
            rows.append(s)
    out = ["# Spanish text written for this page (needs a native-speaker read)", "",
           "Generated by `tools/build.py`. Every Spanish string below was written by an AI, not copied from a source. The quoted Spanish (Department of Education guide) is not listed here because it is copied unchanged.",
           "Questions for the reader: natural for Mexican and Central American Spanish readers in Arizona? Is \"Fiscal General\" the right term for the Arizona Attorney General's office? Is \"queja\" the right word for filing a complaint? Does any phrase sound like legal advice or promise a result? Is \"Oficina de Derechos Civiles\" understood?", "",
           "Also written by us, in `app.js`: the ES page title and description (same strings as the first two items below).", ""]
    out += ["%d. %s" % (i, r) for i, r in enumerate(rows, 1)]
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    out = page()
    assert chr(0x2014) not in out, "em dash found"
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
    md = sources_md()
    nm = native_md()
    assert chr(0x2014) not in md + nm
    open(os.path.join(ROOT, "docs", "SOURCES.md"), "w", encoding="utf-8").write(md)
    open(os.path.join(ROOT, "docs", "NEEDS-NATIVE-READ.md"), "w", encoding="utf-8").write(nm)
    t, d = TEXT["title"], TEXT["desc"]
    print("built index.html (%d bytes); title %d chars, desc %d chars; en title %d, en desc %d" % (len(out), len(t), len(d), len(TEXT["title_en"]), len(TEXT["desc_en"])))
