# -*- coding: utf-8 -*-
"""Erzeugt Reiseprogramm-Thailand-2027.pdf aus den Reisedaten in index.html.

Etappen, Tagespläne, Klima-, Pack- und Infoblöcke werden direkt aus dem
<script>-Block von index.html gelesen, damit PDF und Website nicht auseinanderlaufen.

    python3 tools/build-pdf.py

Benötigt node (liest die JS-Objekte aus) und Chromium (Druckausgabe).
"""
import io, json, html, os, re, subprocess, sys, tempfile, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
OUT_PDF = os.path.join(ROOT, 'Reiseprogramm-Thailand-2027.pdf')

CHROME = next((p for p in [
    os.environ.get('CHROME_PATH'), '/opt/pw-browsers/chromium',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
] if p and os.path.exists(p)), None)


def extract_data():
    """Liest stops/plans/climate/packing/info per node aus index.html."""
    js = re.findall(r'<script>(.*?)</script>', io.open(SRC, encoding='utf-8').read(), re.S)[-1]
    a = js.index('const stops = [')
    b = js.index('];', a) + 2
    c = js.index('const plans={')
    d = js.index('function planKey', c)
    e = js.index(chr(10) + '}' + chr(10), d) + 3
    out = js[a:b] + chr(10) + js[c:e] + chr(10)
    for name in ('const climate = [', 'const packing = [', 'const info = ['):
        i = js.index(name)
        out += js[i:js.index(chr(10) + '];', i) + 3] + chr(10)
    out += 'console.log(JSON.stringify({stops,plans,climate,packing,info}));'
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(out)
        tmp = f.name
    try:
        return json.loads(subprocess.check_output(['node', tmp]).decode('utf-8'))
    finally:
        os.unlink(tmp)


d = extract_data()
stops, plans, climate, packing, info = d['stops'], d['plans'], d['climate'], d['packing'], d['info']
def plan_key(s):
    sc = s.get('scene')
    if sc == 'beach':   return '7.8925,98.2986|patong'
    if sc == 'islands': return '7.8845,98.3875|oldtown'
    if sc == 'sunset':  return '7.8158,98.3004|sunset'
    return ','.join(str(x) for x in s['loc']) if s.get('loc') else ''

def maps(o):
    u = 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(o.get('q',''))
    if o.get('pid'): u += '&query_place_id=' + o['pid']
    return u

E = html.escape

CSS = u"""
@page { size: A4; margin: 15mm 14mm 16mm 14mm; }
@page :first { margin-top: 0; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin:0; font-family:"Noto Sans","DejaVu Sans",Helvetica,Arial,sans-serif;
       font-size:9.6pt; line-height:1.45; color:#22303a; }
h1,h2,h3 { font-family:Georgia,"Noto Serif",serif; margin:0; font-weight:600; }
a { color:#0d7377; text-decoration:none; }

/* ---------- Titelkopf ---------- */
.cover { background:linear-gradient(160deg,#0d7377 0%,#12898b 45%,#1aa3a0 100%);
         color:#fff; padding:26mm 14mm 14mm; margin:0 -14mm 9mm; position:relative; overflow:hidden; }
.cover:after { content:""; position:absolute; left:0; right:0; bottom:-1px; height:12mm;
               background:radial-gradient(ellipse 60% 100% at 50% 100%, #fbf7f0 50%, transparent 51%); }
.cover-eyebrow { font-size:8pt; letter-spacing:.28em; text-transform:uppercase; opacity:.85; }
.cover h1 { font-size:30pt; line-height:1.05; margin:5mm 0 3mm; }
.cover h1 em { font-style:italic; color:#ffd9a0; }
.cover-dates { font-size:11pt; opacity:.95; }
.facts { display:flex; gap:9mm; margin-top:7mm; }
.fact .n { font-size:17pt; font-family:Georgia,serif; color:#ffd9a0; line-height:1; }
.fact .l { font-size:7.2pt; letter-spacing:.18em; text-transform:uppercase; opacity:.85; margin-top:1.5mm; }

/* ---------- Abschnitte ---------- */
section { margin-bottom:7mm; }
.sec-label { font-size:7.2pt; letter-spacing:.24em; text-transform:uppercase; color:#e8794a; font-weight:700; }
.sec-title { font-size:14pt; margin:1mm 0 3.5mm; }

/* ---------- Übersichtstabelle ---------- */
table.ov { width:100%; border-collapse:collapse; font-size:8.8pt; }
table.ov th { text-align:left; font-size:7pt; letter-spacing:.14em; text-transform:uppercase;
              color:#6b7a83; font-weight:700; border-bottom:1.2pt solid #0d7377; padding:0 2mm 1.6mm 0; }
table.ov td { padding:2.1mm 2mm 2.1mm 0; border-bottom:.5pt solid #e6ded1; vertical-align:top; }
table.ov tr:last-child td { border-bottom:none; }
table.ov td.d { white-space:nowrap; color:#0d7377; font-weight:600; }
table.ov td.n { white-space:nowrap; text-align:center; }
.st-name { font-weight:600; }
.st-sub { color:#6b7a83; font-size:8pt; }

/* ---------- Etappenkarten ---------- */
.stage { border:.6pt solid #e0d6c6; border-radius:3mm; padding:4mm 4.5mm; margin-bottom:4.5mm;
         background:#fffdf9; break-inside:avoid; page-break-inside:avoid; }
.stage-head { display:flex; align-items:baseline; gap:3mm; border-bottom:.8pt solid #f0e7d8;
              padding-bottom:2.2mm; margin-bottom:3mm; }
.stage-emoji { font-size:14pt; line-height:1; }
.stage-days { font-size:7.2pt; letter-spacing:.16em; text-transform:uppercase; color:#e8794a; font-weight:700; }
.stage-name { font-family:Georgia,serif; font-size:12.5pt; font-weight:600; }
.stage-nights { margin-left:auto; font-size:8pt; color:#0d7377; font-weight:600; white-space:nowrap; }
.note { background:#fdf3e9; border-left:2.2pt solid #e8794a; padding:2mm 3mm; border-radius:0 2mm 2mm 0;
        font-size:8.6pt; margin-bottom:3mm; }
.cols { display:flex; gap:6mm; }
.col { flex:1; min-width:0; }
.lbl { font-size:7pt; letter-spacing:.16em; text-transform:uppercase; color:#0d7377;
       font-weight:700; margin-bottom:1.6mm; }
.dp { display:flex; gap:2.5mm; font-size:8.5pt; padding:1.1mm 0; border-bottom:.4pt dotted #e6ded1; }
.dp:last-child { border-bottom:none; }
.dp .dpd { flex:0 0 30mm; color:#0d7377; font-weight:600; }
ul.acts { margin:0; padding-left:4mm; font-size:8.5pt; }
ul.acts li { margin-bottom:1.2mm; }
.hotel { font-size:8.6pt; padding:1.2mm 0; border-bottom:.4pt dotted #e6ded1; }
.hotel:last-child { border-bottom:none; }
.hotel .hn { font-weight:600; }
.rating { display:inline-block; background:#0d7377; color:#fff; border-radius:2mm;
          padding:.3mm 1.4mm; font-size:7pt; margin-left:1.5mm; vertical-align:1px; }
.booked { display:inline-block; background:#e8794a; color:#fff; border-radius:2mm;
          padding:.3mm 1.4mm; font-size:7pt; margin-left:1.5mm; vertical-align:1px; }
.transfer { margin-top:3mm; padding-top:2.2mm; border-top:.8pt solid #f0e7d8;
            font-size:8.5pt; color:#3c4c56; }
.transfer b { color:#0d7377; }

/* ---------- Transportzeile solo ---------- */
.leg { display:flex; gap:3mm; align-items:baseline; font-size:9pt; padding:2.5mm 4.5mm;
       background:#eef7f6; border-radius:2.5mm; margin-bottom:4.5mm; break-inside:avoid; }
.leg .lg-days { font-size:7.2pt; letter-spacing:.16em; text-transform:uppercase;
                color:#e8794a; font-weight:700; white-space:nowrap; }

/* ---------- Klima / Packliste / Info ---------- */
.grid4 { display:flex; gap:4mm; }
.clim { flex:1; border:.6pt solid #e0d6c6; border-radius:2.5mm; padding:3mm; background:#fffdf9; }
.clim h3 { font-size:9.5pt; margin-bottom:1.8mm; }
.clim div { font-size:8.2pt; padding:.5mm 0; }
.packcols { column-count:2; column-gap:7mm; }
.packbox { break-inside:avoid; margin-bottom:4mm; }
.packbox h3 { font-size:10pt; margin-bottom:1.5mm; }
.packbox ul { margin:0; padding-left:4mm; font-size:8.4pt; }
.packbox li { margin-bottom:.8mm; }
.ibox { border:.6pt solid #e0d6c6; border-left:2.2pt solid #0d7377; border-radius:0 2.5mm 2.5mm 0;
        padding:3mm 3.5mm; margin-bottom:3mm; background:#fffdf9; break-inside:avoid; }
.ibox.good { border-left-color:#3fa34d; }
.ibox.warn { border-left-color:#e8794a; }
.ibox h3 { font-size:10pt; margin-bottom:1.5mm; }
.ibox ul { margin:0; padding-left:4mm; font-size:8.4pt; }
.ibox li { margin-bottom:1mm; }
.tag { display:inline-block; border-radius:2mm; padding:.3mm 1.6mm; font-size:7pt;
       font-weight:700; margin-right:1mm; background:#e6ded1; color:#3c4c56; }
.tag.green { background:#dcf0de; color:#28632f; }
.tag.amber { background:#fdf0dc; color:#93571c; }
.tag.red   { background:#fadedd; color:#8f2b25; }
.foot { margin-top:6mm; padding-top:2.5mm; border-top:.6pt solid #e0d6c6;
        font-size:7.6pt; color:#6b7a83; text-align:center; }
.pb { page-break-before: always; }
"""

def nights_of(s):
    n = s.get('note','')
    import re
    m = re.match(r'^(\d+)\s+N', n)
    if m: return m.group(1) + ' Nächte'
    return ''

parts = []
parts.append(u'<div class="cover">')
parts.append(u'<div class="cover-eyebrow">Zürich · Phuket · Chiang Mai · Bangkok · Koh Yao Noi</div>')
parts.append(u'<h1>Dreissig Tage <em>Thailand</em></h1>')
parts.append(u'<div class="cover-dates">3. Januar &ndash; 1. Februar 2027 &nbsp;·&nbsp; Reiseprogramm für zwei</div>')
parts.append(u'<div class="facts">'
    u'<div class="fact"><div class="n">30</div><div class="l">Tage</div></div>'
    u'<div class="fact"><div class="n">5</div><div class="l">Regionen</div></div>'
    u'<div class="fact"><div class="n">28</div><div class="l">Hotelnächte</div></div>'
    u'<div class="fact"><div class="n">1</div><div class="l">Nachtzug</div></div>'
    u'<div class="fact"><div class="n">3</div><div class="l">Flüge</div></div>'
    u'</div>')
parts.append(u'</div>')

# ---- Übersicht ----
parts.append(u'<section><div class="sec-label">Auf einen Blick</div><h2 class="sec-title">Die Route</h2>')
parts.append(u'<table class="ov"><thead><tr><th style="width:34mm">Datum</th><th>Etappe</th>'
             u'<th style="width:20mm">Nächte</th><th style="width:52mm">Unterkunft</th></tr></thead><tbody>')
for s in stops:
    days = s['days']
    date = days.split('·')[-1].strip() if '·' in days else days
    tag  = days.split('·')[0].strip()
    if s.get('transport'):
        parts.append(u'<tr><td class="d">%s</td><td><span class="st-name">%s</span><div class="st-sub">%s</div></td>'
                     u'<td class="n">–</td><td class="st-sub">–</td></tr>'
                     % (E(date), E(s['name']), E(s.get('tline',''))))
        continue
    hot = s.get('hotels') or []
    hname = E(hot[0]['n'].replace(' · gebucht','')) if hot else '–'
    if hot and 'gebucht' in hot[0]['n']: hname += u' <span class="booked">gebucht</span>'
    elif len(hot) > 1: hname += u'<div class="st-sub">+%d Alternative%s</div>' % (len(hot)-1, '' if len(hot)==2 else 'n')
    parts.append(u'<tr><td class="d">%s<div class="st-sub">%s</div></td>'
                 u'<td><span class="st-name">%s</span></td><td class="n">%s</td><td>%s</td></tr>'
                 % (E(date), E(tag), E(s['name']), E(nights_of(s).replace(' Nächte','') or '–'), hname))
parts.append(u'</tbody></table></section>')

# ---- Etappen ----
parts.append(u'<section class="pb"><div class="sec-label">Tag für Tag</div><h2 class="sec-title">Die Etappen im Detail</h2>')
for s in stops:
    if s.get('transport'):
        parts.append(u'<div class="leg"><span class="lg-days">%s</span><span>%s <b>%s</b></span></div>'
                     % (E(s['days']), s['emoji'], E(s.get('tline',''))))
        continue
    p = [u'<div class="stage">']
    p.append(u'<div class="stage-head"><span class="stage-emoji">%s</span>'
             u'<div><div class="stage-days">%s</div><div class="stage-name">%s</div></div>'
             u'%s</div>'
             % (s['emoji'], E(s['days']), E(s['name']),
                (u'<div class="stage-nights">%s</div>' % E(nights_of(s))) if nights_of(s) else ''))
    if s.get('note'):
        p.append(u'<div class="note">%s</div>' % E(s['note']))
    pk = plan_key(s)
    left = u''
    if plans.get(pk):
        left = u'<div class="lbl">Tag für Tag</div>' + u''.join(
            u'<div class="dp"><span class="dpd">%s</span><span>%s</span></div>' % (E(a), E(b))
            for a, b in plans[pk])
    right = u''
    if s.get('hotels'):
        right += u'<div class="lbl">Unterkunft</div>'
        for h in s['hotels']:
            nm = h['n']
            badge = u''
            if ' · gebucht' in nm:
                nm = nm.replace(' · gebucht',''); badge = u'<span class="booked">gebucht</span>'
            elif h.get('r'):
                badge = u'<span class="rating">★ %s</span>' % E(h['r'])
            right += u'<div class="hotel"><span class="hn">%s</span>%s</div>' % (E(nm), badge)
    if s.get('acts'):
        right += u'<div class="lbl" style="margin-top:3mm">Unternehmungen</div><ul class="acts">' + \
                 u''.join(u'<li>%s</li>' % E(a['t']) for a in s['acts']) + u'</ul>'
    if left and right:
        p.append(u'<div class="cols"><div class="col">%s</div><div class="col">%s</div></div>' % (left, right))
    else:
        p.append(left + right)
    if s.get('tline'):
        p.append(u'<div class="transfer">→ <b>Weiter:</b> %s</div>' % E(s['tline']))
    p.append(u'</div>')
    parts.append(u''.join(p))
parts.append(u'</section>')

# ---- Klima ----
parts.append(u'<section class="pb"><div class="sec-label">Wetter im Januar</div>'
             u'<h2 class="sec-title">Klima unterwegs</h2><div class="grid4">')
for c in climate:
    rows = u''.join(u'<div>%s&nbsp; %s</div>' % (r[0], E(r[1])) for r in c['rows'])
    parts.append(u'<div class="clim"><h3>%s</h3>%s</div>' % (E(c['region']), rows))
parts.append(u'</div></section>')

# ---- Packliste ----
parts.append(u'<section><div class="sec-label">Vorbereitung</div><h2 class="sec-title">Packliste</h2><div class="packcols">')
for b in packing:
    parts.append(u'<div class="packbox"><h3>%s %s</h3><ul>%s</ul></div>'
                 % (b.get('icon',''), E(b['title']),
                    u''.join(u'<li>%s</li>' % it for it in b['items'])))
parts.append(u'</div></section>')

# ---- Gut zu wissen ----
parts.append(u'<section class="pb"><div class="sec-label">Gut zu wissen</div>'
             u'<h2 class="sec-title">Gesundheit, Einreise & Sicherheit</h2>')
for b in info:
    cls = (u' ' + b['type']) if b.get('type') else u''
    parts.append(u'<div class="ibox%s"><h3>%s %s</h3><ul>%s</ul></div>'
                 % (cls, b.get('emoji',''), E(b['title']),
                    u''.join(u'<li>%s</li>' % it for it in b['items'])))
parts.append(u'</section>')

parts.append(u'<div class="foot">Reiseprogramm Thailand · 3. Januar – 1. Februar 2027 · '
             u'Stand 29.08.2026 · Angaben zu Einreise & Gesundheit vor Abreise auf eda.admin.ch prüfen</div>')

doc = (u'<!doctype html><html lang="de"><head><meta charset="utf-8">'
       u'<title>Reiseprogramm Thailand 2027</title><style>%s</style></head><body>%s</body></html>'
       % (CSS, u''.join(parts)))


if CHROME is None:
    sys.exit('Kein Chromium gefunden — CHROME_PATH setzen.')

with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
    f.write(doc)
    page = f.name
try:
    subprocess.check_call([CHROME, '--headless', '--disable-gpu', '--no-sandbox',
                           '--no-pdf-header-footer', '--virtual-time-budget=6000',
                           '--print-to-pdf=' + OUT_PDF, 'file://' + page],
                          stderr=subprocess.DEVNULL)
finally:
    os.unlink(page)
print('geschrieben:', OUT_PDF, os.path.getsize(OUT_PDF), 'Bytes')
