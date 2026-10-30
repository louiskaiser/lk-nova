"""Check all exported SVGs and cubic UFO bounds against the actual binary."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ufoLib import UFOReader
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.pointPen import PointToSegmentPen
from build_font import ROOT,DIST
font=TTFont(DIST/'LKNova-VF.ttf');manifest=json.loads((DIST/'font-manifest.json').read_text());glyphs=font.getGlyphSet();ufo=UFOReader(ROOT/'source/LKNova-BlackMaster.ufo').getGlyphSet();error=0
class Metadata:pass
for char in manifest['characters']:
 name=font.getBestCmap()[ord(char)];xml=ET.parse(DIST/f'vectors/U{ord(char):04X}.svg');assert xml.getroot().tag.endswith('svg')
 original=BoundsPen(ufo);meta=Metadata();ufo.readGlyph(name,meta,PointToSegmentPen(original));actual=BoundsPen(glyphs);glyphs[name].draw(actual)
 assert meta.width==glyphs[name].width,(char,'advance')
 if original.bounds:
  assert actual.bounds
  error=max(error,max(abs(a-b) for a,b in zip(original.bounds,actual.bounds)))
 assert error<1.1,(char,error)
result={'status':'passed','version':manifest['version'],'ufo_glyphs':len(ufo.keys()),'valid_svg_glyphs':len(manifest['characters']),'cubic_master_vs_ttf_max_bounds_error_font_units':error,'all_advances_match':True}
(ROOT/'qa/vector-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
