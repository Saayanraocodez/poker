"""Assemble PROOF_WORKBOOK.pdf: part1.html + part2.html with workbook/fragments.json (gen.py) and
the new-results tables (from today's JSON outputs), rendered with KaTeX and printed by headless Edge.

usage (from the repository root):  python workbook/gen.py && python workbook/build.py
"""
import os, sys, json, re, subprocess, glob
from fractions import Fraction as F
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WB = os.path.join(ROOT, "workbook")
os.chdir(ROOT)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def new_results():
    h = []
    # --- R14 re-read
    A = json.load(open("reread14.json")); B = json.load(open("reread14b.json"))
    lb = np.array([float(F(a["dist_lb"])) for a in A]); ub = np.array([float(F(b["dist_ub"])) for b in B])
    gap = max(F(b["dist_ub"]) - F(a["dist_lb"]) for a, b in zip(A, B))
    ex = np.array([a["expl"] for a in A])
    from collections import Counter
    sup = Counter(c for a in A for c in a["support"])
    h.append("<h3>D.1 R14 re-read: distance of the 150 MCCFR outputs to the complete Nash set</h3>")
    h.append("<table class='t s'><tr><th>quantity</th><th>value</th></tr>"
             "<tr><td>certified lower bound (LP dual, exact) / exact witness (re-verified Nash)</td><td>agree to \\(\\le %.1e\\) for all 150; exactly equal for %d</td></tr>"
             "<tr><td>distance: min / median / max</td><td>%.4f / %.4f / %.4f</td></tr>"
             "<tr><td>outputs farther than 0.01 / 0.02 / 0.05</td><td>%d / %d / %d of 150</td></tr>"
             "<tr><td>exploitability (median) and distance / exploitability (median)</td><td>%.5f; %.1f</td></tr>"
             "<tr><td>coordinates carrying the certificates</td><td>%s</td></tr>"
             "<tr><td>off path (Table 4's windows)</td><td>every output inside every window; in fact at Table 2's values</td></tr></table>"
             % (float(gap), sum(F(b["dist_ub"]) == F(a["dist_lb"]) for a, b in zip(A, B)), lb.min(), np.median(lb), lb.max(),
                (lb > .01).sum(), (lb > .02).sum(), (lb > .05).sum(), np.median(ex), np.median(lb / ex),
                ", ".join("\\(%s_{%s}\\) %d" % (k[0], k[1:], v) for k, v in sup.most_common(6))))
    h.append("<p><b>Reading.</b> R14 called its 99/150 off-family outputs suggestive evidence of equilibria outside the family. Theorems 4–5 settle that question the other way: no output is within 0.0067 of any equilibrium. The failures are <i>on</i> the path of play, where Theorem 4 leaves no room, so Table 4's wider off-path windows rescue none of them. The single largest error, \\(a_{32}\\) (P1 calling P3's bet with the 3), was never checked in R14. The 51 outputs R14 placed <i>inside</i> a sub-family are off the Nash set as well (median distance 0.0285).</p>")
    # --- mixing
    h.append("<h3>D.2 Why: averaging is not closed on the Nash set</h3>")
    rows = [l for l in open("log_mixdemo.txt").read().splitlines() if re.match(r"\s+(0|1|\d+/\d+)\s+0\.", l)]
    h.append("<p>Two exact equilibria, \\(x_A\\) (\\(b_{11}=\\tfrac1{20},b_{21}=\\tfrac15,c_{11}=0\\)) and \\(x_C\\) (\\(b_{11}=\\tfrac15,b_{21}=\\tfrac1{20},c_{11}=\\tfrac12\\)), with the same payoffs \\((-\\tfrac7{240},-\\tfrac1{48},\\tfrac1{20})\\). Their sequence-form mixture, which is what an average over iterations computes:</p>")
    h.append("<table class='t s'><tr><th>\\(\\lambda\\)</th><th>\\(b_{11}\\)</th><th>\\(b_{21}\\)</th><th>\\(c_{11}\\)</th><th>\\(b_{33}\\)</th><th>exploitability (exact)</th><th>distance (certified)</th></tr>")
    for l in rows:
        t = l.split()
        h.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (t[0], t[1], t[2], t[3], t[4], t[5], t[-1]))
    h.append("</table><p>The exploitability is exactly \\(\\lambda(1-\\lambda)/80\\). The mixtures sit \"between sub-families\" (intermediate \\(c_{11}\\), \\(b_{11}\\ne b_{21}\\)) at the same distances and exploitabilities as the MCCFR outputs.</p>")
    # --- long MCCFR
    if os.path.exists("cfrlong_an.json"):
        Z = json.load(open("cfrlong_an.json"))
        h.append("<h3>D.3 ES-MCCFR to \\(10^8\\) iterations (24 seeds): the average stalls off the Nash set</h3>")
        h.append("<table class='t s'><tr><th>iterations</th><th>exploitability (median)</th><th>distance of the running average (median / max)</th><th>\\(a_{32}\\) (median)</th><th>distance of the window's own play (median)</th></tr>")
        for t in ("10000", "100000", "1000000", "10000000", "100000000"):
            run = [z["run"][t] for z in Z]; win = [z["win"][t] for z in Z if t in z["win"]]
            h.append("<tr><td>\\(10^{%d}\\)</td><td>%.1e</td><td>%.4f / %.4f</td><td>%.4f</td><td>%s</td></tr>" % (
                len(t) - 1, np.median([r["expl"] for r in run]), np.median([r["dist"] for r in run]), max(r["dist"] for r in run),
                np.median([r["a32"] for r in run]), "%.4f" % np.median([w["dist"] for w in win]) if win else "–"))
        late = [str(c) for c in sorted(int(k) for k in Z[0]["win"]) if c > 10 ** 6]
        sw = sum(len({z["win"][t]["sub"] for t in late}) > 1 for z in Z)
        bsd = np.median([np.std([z["win"][t]["beta"] for t in late]) for z in Z])
        h.append("</table><p>Between \\(10^7\\) and \\(10^8\\) iterations the running average stops approaching the Nash set. Meanwhile the play itself keeps moving: over the last two decades the nearest sub-family of the window's play changes in %d of 24 seeds, and \\(\\beta\\) varies with standard deviation %.3f within a seed. The average of a wandering sequence of near-equilibria is D.2's mixture.</p>" % (sw, bsd))
    # --- CFR variants
    runs = []
    for fn in sorted(glob.glob("cfrfull_*.json")):
        runs += json.load(open(fn))
    if runs:
        h.append("<h3>D.4 Full-width CFR variants (24 starts each): which equilibrium is selected?</h3>")
        h.append("<table class='t s'><tr><th>variant</th><th>iterations</th><th>exploitability (max)</th><th>distance (median / max)</th><th>nearest sub-family A/B/C</th><th>\\(\\beta\\) mean (range)</th><th>\\(u_1\\), \\(u_3\\) mean</th><th>\\(c_{33}\\) position in window (mean)</th><th>\\(b_{32}\\) mean</th></tr>")
        names = {"cfr": "vanilla CFR", "lcfr": "Linear CFR", "cfrp": "CFR+", "dcfr": "DCFR(1.5,0,2)"}
        for v in ("cfr", "lcfr", "cfrp", "dcfr"):
            rs = [r["final"] for r in runs if r["variant"] == v]
            if not rs: continue
            it = [r["iters"] for r in runs if r["variant"] == v][0]
            b = [r["beta"] for r in rs]; u = np.array([r["u"] for r in rs]); cnt = Counter(r["sub"] for r in rs)
            fr = [r["c33frac"] for r in rs if r["c33frac"] is not None]
            h.append("<tr><td>%s</td><td>%.0e</td><td>%.1e</td><td>%.1e / %.1e</td><td>%d/%d/%d</td><td>%.3f (%.3f–%.3f)</td><td>%.5f, %.5f</td><td>%.2f</td><td>%.3f</td></tr>" % (
                names[v], it, max(r["expl"] for r in rs), np.median([r["dist"] for r in rs]), max(r["dist"] for r in rs),
                cnt["A"], cnt["B"], cnt["C"], np.mean(b), min(b), max(b), u[:, 0].mean(), u[:, 2].mean(), np.mean(fr), np.mean([r["b32"] for r in rs])))
        h.append("</table><p>\\(\\beta=0\\) gives \\(u_1=-\\tfrac1{48}\\approx-0.02083\\), \\(u_3=\\tfrac1{24}\\approx0.04167\\). Every algorithm's choice moves \\(\\kappa\\beta\\) from P1 to P3. The properness point is position \\(\\tfrac13\\) in the \\(c_{33}\\) window, and refinement predicts \\(b_{32}=0\\); no variant respects either.</p>")
    # --- quasi-perfection
    Q = json.load(open("qperf.json"))
    h.append("<h3>D.5 Quasi-perfection does not select \\(\\tfrac{55}{96}\\) (<code>qperf.py</code>)</h3>")
    h.append("<table class='t s'><tr><th>\\(c_{33}\\)</th><th>Nash</th><th>perfect (control)</th><th>quasi-perfect</th></tr>")
    for q in Q:
        f = lambda ok, info: ("certified, \\(s^\\ast=%s\\), rank %d" % (info["s"], info["rank"])) if ok else "undecided at first order (pole)"
        h.append("<tr><td>\\(%s\\)</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (q["c33"].replace("/", "/"), "yes" if q["nash"] else "no",
                 f(q["perfect"], q["perfect_info"]), f(q["quasi"], q["quasi_info"])))
    h.append("</table><p>A symbolic version with \\(c_{33}\\) free certifies <b>every</b> \\(c_{33}\\in(\\tfrac12,\\tfrac{23}{32})\\) for both refinements: one direction \\(\\delta\\), every condition a polynomial in \\(c_{33}\\) signed by exact root isolation, and an \\(8\\times8\\) Jacobian minor with constant determinant \\(-\\tfrac{95}{3439853568}\\) (<code>log_qperf.txt</code>).</p>")
    return "".join(h)


CSS = r"""
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
:root { --ink:#1b1b1b; --muted:#555; --rule:#ccc; --accent:#1f4e79; --bg:#ffffff; }
body { font-family: Georgia, 'Times New Roman', serif; color: var(--ink); background: var(--bg); font-size: 10.5pt; line-height: 1.42; }
h1 { color: var(--accent); font-size: 22pt; margin: 0 0 6pt; }
h1.part { page-break-before: always; font-size: 18pt; border-bottom: 2px solid var(--accent); padding-bottom: 4pt; }
h2 { color: var(--accent); font-size: 14pt; margin: 16pt 0 6pt; border-bottom: 1px solid var(--rule); padding-bottom: 2pt; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; }
section { page-break-before: always; }
section.cover { page-break-before: auto; }
.sub { font-size: 13pt; color: var(--muted); margin-top: 0; }
.meta { color: var(--muted); font-size: 9.5pt; }
.box { border: 1px solid var(--rule); background: #f6f8fb; padding: 6pt 10pt; border-radius: 4px; }
.prop { border-left: 3px solid var(--accent); padding-left: 8pt; }
.warn { border-left: 3px solid #b5651d; padding-left: 8pt; background: #fdf6ef; }
.ex { border: 1px dashed #888; padding: 4pt 10pt; margin: 10pt 0; background: #fafafa; }
table { border-collapse: collapse; margin: 6pt 0; page-break-inside: auto; }
tr { page-break-inside: avoid; }
table.t td, table.t th, table.ledger td, table.ledger th { border: 1px solid var(--rule); padding: 2pt 5pt; vertical-align: top; }
table.t th, table.ledger th { background: #eef2f7; font-weight: bold; }
table.s { font-size: 9pt; }
table.ledger { width: 100%; font-size: 8.8pt; }
table.ledger td:first-child { font-size: 12pt; text-align: center; }
.two { display: flex; gap: 10pt; }
.two table { flex: 1; }
.tag { display: inline-block; font-size: 7.5pt; font-weight: bold; padding: 0 3pt; border-radius: 3px; color: #fff; }
.tag.P { background: #2e7d32; } .tag.E { background: #1f4e79; } .tag.G { background: #b5651d; } .tag.O { background: #8e2430; }
.small { font-size: 9pt; }
.dpoly { font-size: 8.4pt; margin: 3pt 0; text-align: left; }
.dpoly .katex-display { margin: 2pt 0; text-align: left; }
.dpoly .katex-display > .katex { text-align: left; white-space: normal; }
.allD .katex { font-size: 1em; }
code { font-size: 9pt; }
dl.ans dt { font-weight: bold; float: left; width: 3em; }
dl.ans dd { margin-left: 3.5em; margin-bottom: 4pt; }
ol.toc li { margin: 1pt 0; }
.katex-display { overflow: visible !important; }
.katex-display > .katex { max-width: 100%; }
table.t td .katex, table.ledger td .katex { white-space: normal; }
"""

KATEX = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
"""


def main():
    frag = json.load(open(os.path.join(WB, "fragments.json")))
    frag["newresults"] = new_results()
    body = open(os.path.join(WB, "part1.html"), encoding="utf-8").read() + open(os.path.join(WB, "part2.html"), encoding="utf-8").read()
    missing = set(re.findall(r"\{\{(\w+)\}\}", body)) - set(frag)
    assert not missing, missing
    body = re.sub(r"\{\{(\w+)\}\}", lambda m: frag[m.group(1)], body)
    html = ("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>Proof Workbook</title>%s<style>%s</style></head><body>%s"
            "<script>renderMathInElement(document.body,{delimiters:[{left:'\\\\[',right:'\\\\]',display:true},{left:'\\\\(',right:'\\\\)',display:false}],throwOnError:false});</script>"
            "</body></html>") % (KATEX, CSS, body)
    out_html = os.path.join(WB, "workbook.html")
    open(out_html, "w", encoding="utf-8").write(html)
    pdf = os.path.join(ROOT, "PROOF_WORKBOOK.pdf")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=30000",
                    "--print-to-pdf=" + pdf, out_html], check=False, capture_output=True)
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf)
    print("written %s: %d pages" % (pdf, len(doc)))


if __name__ == "__main__":
    main()
