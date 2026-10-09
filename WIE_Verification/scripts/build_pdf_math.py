# -*- coding: utf-8 -*-
"""LaTeX 公式手稿（Markdown）-> A4 分页 PDF：KaTeX 渲染公式 + Chromium 打印。
用法: python build_pdf_math.py <input.md> <output.pdf>
"""
import base64, json, os, re, subprocess, sys

TEMP = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\910CF9D8FBF963F109E2915A63F38F70\workspace\conv_c220e5e084e345aa8edd6702582cebba\temp"
KATEX_DIR = os.path.join(TEMP, "node_modules", "katex", "dist")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

in_md, out_pdf = sys.argv[1], sys.argv[2]
src = open(in_md, encoding="utf-8").read()

# ---------- 1) 抽取数学片段，替换为占位符 ----------
items = []


def gather(tex, display):
    items.append({"tex": tex.strip(), "display": display})
    return f"\x00MATH{len(items) - 1}\x00"


# display: $$...$$
src = re.sub(r"\$\$(.+?)\$\$", lambda m: gather(m.group(1), True), src, flags=re.S)
# inline: $...$（排除 $$、跨行与表格竖线）
src = re.sub(r"(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)", lambda m: gather(m.group(1), False), src)

# ---------- 2) Markdown -> HTML ----------
import markdown

body = markdown.markdown(
    src,
    extensions=["tables", "fenced_code", "sane_lists", "md_in_html", "attr_list"],
    output_format="html5",
)

# ---------- 3) 调 KaTeX 渲染 ----------
proc = subprocess.run(
    ["node", os.path.join(TEMP, "render_math.js")],
    input=json.dumps({"items": items}, ensure_ascii=False),
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
if proc.returncode != 0:
    print("KATEX FAIL:", proc.stderr[:800]); sys.exit(1)
rendered = json.loads(proc.stdout)
errs = [i for i, h in enumerate(rendered) if "math-error" in h]
print(f"math items: {len(items)}  errors: {len(errs)} {errs[:5]}")

for i, html in enumerate(rendered):
    cls = "mathblock" if items[i]["display"] else "mathinline"
    tag = f'<div class="{cls}"><div class="mathinner">{html}</div></div>' if items[i]["display"] \
        else f'<span class="{cls}">{html}</span>'
    body = body.replace(f"\x00MATH{i}\x00", tag)

# ---------- 4) KaTeX CSS（字体内嵌 base64，离线可打印） ----------
css = open(os.path.join(KATEX_DIR, "katex.min.css"), encoding="utf-8").read()
fontdir = os.path.join(KATEX_DIR, "fonts")


def font_data(name):
    fp = os.path.join(fontdir, name)
    if not os.path.exists(fp):
        base = os.path.splitext(name)[0]
        for ext in (".woff2", ".woff", ".ttf"):
            if os.path.exists(os.path.join(fontdir, base + ext)):
                fp = os.path.join(fontdir, base + ext); break
    mime = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf"}[os.path.splitext(fp)[1]]
    return f"data:{mime};base64," + base64.b64encode(open(fp, "rb").read()).decode()


katex_css = re.sub(r"url\(fonts/([^)]+)\)", lambda m: f"url({font_data(m.group(1))})", css)

CSS = """
@page { size: A4; margin: 19mm 15mm 17mm 15mm; }
html { font-size: 10.5pt; }
body { font-family: "Times New Roman", "Cambria Math", "Segoe UI Symbol",
       "Microsoft YaHei", "SimSun", serif; line-height: 1.65; color: #111;
       margin: 0; text-align: justify; }
h1 { font-size: 19pt; text-align: center; margin: 0 0 6pt; }
h1 + h2 { text-align: center; font-size: 12pt; font-weight: normal; margin: 0 0 12pt;
          padding-bottom: 8pt; border-bottom: 1.2pt solid #333; }
h2 { font-size: 14pt; margin: 15pt 0 8pt; padding-bottom: 3pt;
     border-bottom: .6pt solid #999; page-break-after: avoid; }
h3 { font-size: 12pt; margin: 12pt 0 6pt; page-break-after: avoid; }
h4 { font-size: 11pt; margin: 10pt 0 5pt; page-break-after: avoid; }
p, li { margin: 5pt 0; }
ul, ol { padding-left: 1.6em; margin: 6pt 0; }
hr { border: none; border-top: .6pt solid #bbb; margin: 13pt 0; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; border-left: 2.4pt solid #666;
             background: #f7f7f7; page-break-inside: avoid; }
blockquote p { margin: 3pt 0; }
em { font-style: italic; }
code { font-family: "Consolas", "Cascadia Mono", "Cambria Math", "Segoe UI Symbol",
       "Microsoft YaHei", monospace; font-size: 9.6pt; }
pre { font-family: "Consolas", "Cascadia Mono", "Cambria Math", "Segoe UI Symbol",
      "Microsoft YaHei", monospace; font-size: 9.4pt; line-height: 1.45;
      background: #f6f6f6; border: .6pt solid #ccc; padding: 7pt 9pt; margin: 8pt 0;
      white-space: pre-wrap; word-wrap: break-word; page-break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 9pt 0; font-size: 9.2pt; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th, td { border: .6pt solid #999; padding: 3.5pt 5pt; vertical-align: top;
         text-align: left; word-break: break-word; }
th { background: #ececec; font-weight: bold; }
/* 公式块：禁止跨页截断，超宽自动缩放（见页内脚本） */
.mathblock { margin: 9pt 0; page-break-inside: avoid; }
.mathinner { display: block; }
.mathblock .katex-display { margin: 4pt 0; }
.mathinline { white-space: nowrap; }
.mathinner .katex, .mathinline .katex { font-size: 1.02em; }
""".replace("{KATEX}", katex_css)

AUTOSCALE = """
window.addEventListener('load', function () {
  document.querySelectorAll('.mathblock').forEach(function (b) {
    var inner = b.querySelector('.mathinner');
    if (!inner) return;
    var avail = b.clientWidth;
    var w = inner.scrollWidth;
    if (w > avail + 1) {
      var s = avail / w;
      inner.style.transformOrigin = 'left top';
      inner.style.transform = 'scale(' + s + ')';
      b.style.height = (inner.offsetHeight * s) + 'px';
      b.style.overflow = 'hidden';
    }
  });
});
"""

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>武光衡信息一元论统一方程（WIE v1.0）</title>
<style>{katex_css}</style>
<style>{CSS}</style>
</head>
<body>
{body}
<script>{AUTOSCALE}</script>
</body>
</html>
"""

html_path = os.path.join(TEMP, "wie_manuscript.html")
open(html_path, "w", encoding="utf-8", newline="\n").write(html)
print("HTML ->", html_path, len(html), "chars")

if os.path.exists(out_pdf):
    os.remove(out_pdf)
r = subprocess.run(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
     "--virtual-time-budget=30000", f"--print-to-pdf={out_pdf}",
     "file:///" + html_path.replace("\\", "/")],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
print("chrome rc:", r.returncode)
print((r.stderr or "")[-400:])
print("pdf:", out_pdf, os.path.getsize(out_pdf) if os.path.exists(out_pdf) else "MISSING")
