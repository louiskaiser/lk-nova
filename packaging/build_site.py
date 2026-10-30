"""Build localized static pages from the English template and locale records."""
from pathlib import Path
import html,json,re
root=Path(__file__).resolve().parents[1]
source=root/'packaging';docs=root/'docs'
locales={p.stem:json.loads(p.read_text()) for p in sorted((source/'locales').glob('*.json'))}
assert all(set(data)==set(locales['en']) for data in locales.values())
template=(source/'site-template.html').read_text()
paths={'en':'index.html','de-DE':'de/index.html','de-CH':'de-CH/index.html','zh-CN':'zh-CN/index.html'}
for locale,path in paths.items():
 values={**locales[locale],'locale':locale,'base':'' if locale=='en' else '../'}
 rendered=re.sub(r'@@([a-z_]+)@@',lambda m:html.escape(str(values[m[1]]),quote=True),template)
 assert '@@' not in rendered
 target=docs/path;target.parent.mkdir(exist_ok=True);target.write_text(rendered)
(docs/'locales.js').write_text('window.LKNovaLocales='+json.dumps(locales,ensure_ascii=False,separators=(',',':'))+';\n')
print('Built English source page and de-DE, de-CH, zh-CN versions.')
# The desktop download uses the same authoritative copy as the website.
for locale,data in locales.items():
 suffix='' if locale=='en' else '.'+('de' if locale=='de-DE' else locale)
 links=' · '.join('<a href="START'+('' if lang=='en' else '.'+('de' if lang=='de-DE' else lang))+'.html">'+label+'</a>' for lang,label in [('en','English'),('de-DE','Deutsch (Deutschland)'),('de-CH','Deutsch (Schweiz)'),('zh-CN','简体中文')])
 sections=''.join('<section><h2>'+html.escape(data[key])+'</h2><p>'+html.escape(data[description])+'</p></section>' for key,description in [('install','install_description'),('settings','settings_description'),('web','web_description'),('license','license_description')])
 guide='<!doctype html><html lang="'+locale+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LK Nova</title><style>@font-face{font-family:Nova;src:url(Web/LKNova-VF.woff2)}*{box-sizing:border-box}body{margin:0;background:white;color:black;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:960px;margin:auto;padding:48px 24px}nav{font-size:13px}a{color:inherit;text-underline-offset:4px}h1{font:900 clamp(64px,15vw,140px)/1.2 Nova,sans-serif;letter-spacing:-.05em;margin:50px 0}h1:after{content:"";display:inline-block;width:.14em;height:.14em;background:#d40000;margin-left:.035em}h2{font-size:26px;font-weight:500;letter-spacing:-.03em}section{border-top:1px solid #bbb;padding:18px 0}p{max-width:750px;color:#595959}nav a:focus-visible{outline:2px solid #d40000;outline-offset:4px}</style></head><body><main><nav>'+links+'</nav><h1>LK NOVA</h1>'+sections+'<a href="LICENSE.txt">'+html.escape(data['read_license'])+' ⇒</a></main></body></html>'
 (source/('START'+suffix+'.html')).write_text(guide)
