"""Refresh public assets from the released font and original vector geometry."""
from pathlib import Path
import shutil,sys,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
assets=root/'docs/assets';assets.mkdir(parents=True,exist_ok=True)
(root/'dist/LKNova-BrandSquare.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>LK Nova Brand Square</title><rect width="20" height="20" fill="#d40000"/></svg>\n')
for name in ['LKNova-VF.woff2','LICENSE.txt','font-manifest.json']:
 shutil.copy2(root/'dist'/name,assets/name)
for cp,char in [('004F','O'),('004B','K'),('0061','a')]:
 svg=ET.fromstring((root/f'dist/vectors/U{cp}.svg').read_text())
 view=svg.attrib['viewBox'];path=svg.find('{http://www.w3.org/2000/svg}path')
 guides='<path d="M-9 0H130M-9 100H130"/>'
 if char=='O':guides+='<ellipse cx="51" cy="50" rx="51" ry="51"/><ellipse cx="51" cy="50" rx="29" ry="30.76"/><path d="M51 -15V115M-8 50H115"/>'
 if char=='K':guides+='<path d="M0 -15V115M22 -15V115M22 68L98 0M22 49L100 100"/>'
 if char=='a':guides+='<path d="M-9 28H110"/><ellipse cx="41" cy="64.9" rx="41" ry="36.9"/><ellipse cx="41" cy="64.9" rx="21.64" ry="19.476"/>'
 result='<svg xmlns="http://www.w3.org/2000/svg" viewBox="'+view+'"><title>LK Nova '+char+' — Original outline and construction guides</title><g transform="scale(.9 1)"><path d="'+path.attrib['d']+'" fill="black" fill-rule="nonzero"/><g fill="none" stroke="#d40000" stroke-width=".35" opacity=".8">'+guides+'</g></g></svg>'
 (assets/f'construction-{char}.svg').write_text(result)
for p in assets.glob('U*.svg'):p.unlink()
print('Updated public font, license, manifest and three original construction diagrams.')
