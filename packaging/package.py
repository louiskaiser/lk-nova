"""Package the approved release for end users and font editors."""
from pathlib import Path
import hashlib,zipfile
root=Path(__file__).resolve().parents[1]
output=root/'docs/downloads';output.mkdir(exist_ok=True)
def create(name,items):
 with zipfile.ZipFile(output/name,'w',zipfile.ZIP_DEFLATED) as z:
  for src,dst in items:z.write(src,'LK-Nova-1.0/'+dst)
 with zipfile.ZipFile(output/name) as z:assert z.testzip() is None
items=[(root/'packaging/START.html','START.html'),(root/'LICENSE.txt','LICENSE.txt'),(root/'CHANGELOG.md','CHANGELOG.md'),(root/'dist/font-manifest.json','font-manifest.json'),(root/'dist/LKNova-VF.ttf','Desktop/Variable/LKNova-VF.ttf'),(root/'dist/LKNova-VF.woff2','Web/LKNova-VF.woff2'),(root/'dist/font.css','Web/font.css'),(root/'dist/LKNova-BrandSquare.svg','Brand/LKNova-BrandSquare.svg')]
items += [(p,'Desktop/Static/'+p.name) for p in sorted((root/'dist').glob('LKNova-*.ttf')) if p.name!='LKNova-VF.ttf']
items += [(p,p.name) for p in sorted((root/'packaging').glob('START.*.html'))]
create('LK-Nova-1.0.zip',items)
items=[(root/'README.md','README.md'),(root/'LICENSE.txt','LICENSE.txt'),(root/'dist/font-manifest.json','dist/font-manifest.json')]
items += [(root/name,name) for name in ['README.de.md','PUBLISHING.md','CHANGELOG.md','docs/app.js','docs/style.css']]
for folder in ['source','dist/vectors','packaging']:
 items +=[(p,str(p.relative_to(root))) for p in sorted((root/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
create('LK-Nova-1.0-Source.zip',items)
checks=[]
for p in sorted(output.glob('*.zip')):checks.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)
(output/'SHA256SUMS.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks))

# Repository-ready publication bundle, including the localized pages.
import json
archive=root.parent/'LK-Nova-1.0-Publication.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or any(part in p.parts for part in ['__pycache__','output']) or p.name in ['.DS_Store','package-validation.json'] or p.suffix=='.pyc':continue
  z.write(p,'LK-Nova-1.0/'+str(p.relative_to(root)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 report={'status':'passed','archive':archive.name,'file_count':len(z.namelist()),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'zip_integrity':'passed'}
(root/'qa/package-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
