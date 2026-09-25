"""
Minimal Markdown -> print-ready HTML for MASTER_DATA.md.

Only the subset actually used in that file: ATX headings, pipe tables, fenced
code, blockquotes, bullet and ordered lists, horizontal rules, and inline
**bold** / *italic* / `code` / [text](url). No dependencies.
"""
import html
import re
import sys

CSS = """
@page{size:letter portrait;margin:14mm}
:root{--ink:#14121A;--ink2:#433D48;--slate:#6E6873;--rule:#D9D4D7;--rule2:#F4F1F2;
      --red:#BE1E2D;--redsoft:#FBEEEF;--paper:#fff}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);margin:0 auto;max-width:8.1in;
     padding:26px 30px 60px;
     font:11pt/1.5 "Instrument Sans",-apple-system,Segoe UI,system-ui,sans-serif}
h1{font-size:21pt;line-height:1.12;margin:26px 0 6px;border-bottom:2.5pt solid var(--ink);
   padding-bottom:8px;page-break-before:always;page-break-after:avoid}
h1:first-of-type{page-break-before:auto;margin-top:0}
h2{font-size:15pt;margin:22px 0 5px;color:var(--red);page-break-after:avoid}
h3{font-size:12pt;margin:17px 0 4px;page-break-after:avoid}
p{margin:8px 0}
strong{font-weight:700}
code{font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace;font-size:.88em;
     background:var(--rule2);padding:1px 4px;border-radius:2px}
pre{background:var(--rule2);border-left:2.5pt solid var(--red);padding:10px 13px;
    overflow-x:auto;font-family:"IBM Plex Mono",Consolas,monospace;font-size:8.6pt;
    line-height:1.45;page-break-inside:avoid}
pre code{background:none;padding:0}
blockquote{border-left:2.5pt solid var(--red);background:var(--redsoft);margin:12px 0;
           padding:9px 14px;page-break-inside:avoid}
blockquote p{margin:4px 0}
table{border-collapse:collapse;width:100%;margin:11px 0;font-size:8.6pt;
      page-break-inside:avoid}
th{background:var(--rule2);text-align:left;font-weight:600;padding:5px 7px;
   border-bottom:1pt solid var(--ink);font-size:7.6pt;letter-spacing:.03em;
   text-transform:uppercase;color:var(--slate)}
td{padding:4px 7px;border-bottom:.5pt solid var(--rule);vertical-align:top}
tr:last-child td{border-bottom:none}
ul,ol{margin:8px 0;padding-left:20px}
li{margin:3px 0}
hr{border:none;border-top:1px solid var(--rule);margin:20px 0}
a{color:var(--red)}
@media print{body{padding:0;max-width:none}}
"""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"&lt;(https?://[^&]+)&gt;", r'<a href="\1">\1</a>', s)
    s = s.replace(r"\|", "|")
    return s


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def convert(md):
    out, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % "\n".join(buf))
            continue

        if re.match(r"^\|.*\|\s*$", ln) and i + 1 < len(lines) \
                and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = cells(ln)
            i += 2
            body = []
            while i < len(lines) and re.match(r"^\|.*\|\s*$", lines[i]):
                body.append(cells(lines[i]))
                i += 1
            t = ["<table><thead><tr>"]
            t += ["<th>%s</th>" % inline(h) for h in head]
            t.append("</tr></thead><tbody>")
            for row in body:
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in row) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            lv = min(len(m.group(1)), 3)
            out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv))
            i += 1
            continue

        if re.match(r"^---+\s*$", ln):
            out.append("<hr>")
            i += 1
            continue

        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(buf)))
            continue

        if re.match(r"^\s*[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(inline(re.sub(r"^\s*[-*]\s+", "", lines[i])))
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % b for b in buf))
            continue

        if re.match(r"^\s*\d+\.\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                buf.append(inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % b for b in buf))
            continue

        if ln.strip():
            buf = []
            while i < len(lines) and lines[i].strip() \
                    and not re.match(r"^(\||#{1,6}\s|```|>|---+\s*$|\s*[-*]\s|\s*\d+\.\s)",
                                     lines[i]):
                buf.append(lines[i].strip())
                i += 1
            out.append("<p>%s</p>" % inline(" ".join(buf)))
            continue
        i += 1
    return "\n".join(out)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    md = open(src, encoding="utf-8").read()
    title = md.split("\n")[0].lstrip("# ").strip()
    body = convert(md)
    open(dst, "w", encoding="utf-8").write(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>%s</title>"
        "<link rel='preconnect' href='https://fonts.googleapis.com'>"
        "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?"
        "family=Instrument+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500"
        "&display=swap'>"
        "<style>%s</style></head><body>%s</body></html>"
        % (html.escape(title), CSS, body))
    print("wrote %s" % dst)
