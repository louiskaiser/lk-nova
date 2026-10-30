"""Validate font coverage, metadata, axis behavior and sampled interpolations."""
import itertools, json, math, random, string
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist';QA=ROOT/'qa'
QA.mkdir(exist_ok=True)
font=TTFont(DIST/'LKNova-VF.ttf',checkChecksums=2)
manifest=json.loads((DIST/'font-manifest.json').read_text())
for tag in font.keys():
    if tag!='GlyphOrder':font.getTableData(tag)
cmap=font.getBestCmap();axes=font['fvar'].axes
expected={'wght':900,'wdth':100,'slnt':0,'CNTR':92,'ROND':50,'APER':36,'RLEG':80,'XBAR':76,'MARK':20}
assert {a.axisTag:a.defaultValue for a in axes}==expected
assert all(ord(c) in cmap for c in string.ascii_letters+string.digits+string.punctuation+' ÄÖÜäöüßẞΛΞ⇒')
assert all(cp in cmap for cp in list(range(32,127))+list(range(160,256)))
assert font['OS/2'].fsType==0
assert {'fvar','gvar','STAT','GPOS','GSUB','COLR','CPAL'}.issubset(font.keys())
assert len(cmap)==manifest['encoded_characters']
assert cmap[ord('A')]!=cmap[ord('Λ')] and cmap[ord('E')]!=cmap[ord('Ξ')]

probes={'wght':'H','wdth':'H','slnt':'H','CNTR':'H','ROND':'O','APER':'C','RLEG':'R','XBAR':'A','MARK':'■'}
effects={}
for a in axes:
    drawings=[]
    for value in [a.minValue,a.maxValue]:
        gs=font.getGlyphSet(location={**expected,a.axisTag:value})
        pen=RecordingPen();gs[cmap[ord(probes[a.axisTag])]].draw(pen);drawings.append(pen.value)
    effects[a.axisTag]=drawings[0]!=drawings[1]
assert all(effects.values()),effects

# Rounded cap/foot extrema must stay anchored through the weight animation.
anchor_checks=0
for weight in range(500,951,25):
    gs=font.getGlyphSet(location={**expected,'wght':weight})
    for char in '2S':
        pen=BoundsPen(gs);gs[cmap[ord(char)]].draw(pen)
        assert abs(pen.bounds[3]-707)<1.1,(char,weight,'cap anchor',pen.bounds)
        assert abs(pen.bounds[1]-(-7 if char=='S' else 0))<1.1,(char,weight,'baseline anchor',pen.bounds)
        anchor_checks+=1

assert font['CPAL'].palettes[0][0].red==212
assert font['CPAL'].palettes[0][0].green==0 and font['CPAL'].palettes[0][0].blue==0
assert 'uni25A0' in font['COLR'].ColorLayers
locations=[expected]
for a in axes:
    locations += [{**expected,a.axisTag:a.minValue},{**expected,a.axisTag:a.maxValue}]
locations += [{a.axisTag:a.minValue for a in axes},{a.axisTag:a.maxValue for a in axes}]
random.seed(271)
locations += [{a.axisTag:random.uniform(a.minValue,a.maxValue) for a in axes} for _ in range(12)]
glyphs_checked=0;min_x=min_y=float('inf');max_x=max_y=float('-inf')
for i,loc in enumerate(locations):
    gs=font.getGlyphSet(location=loc)
    for char in manifest['characters']:
        glyph=gs[cmap[ord(char)]];pen=BoundsPen(gs);glyph.draw(pen)
        assert glyph.width>0,(char,loc,glyph.width)
        if pen.bounds:
            x1,y1,x2,y2=pen.bounds
            assert all(math.isfinite(x) and -32768<x<32767 for x in pen.bounds),(char,loc,pen.bounds)
            assert x2>=x1 and y2>=y1
            min_x=min(min_x,x1);min_y=min(min_y,y1);max_x=max(max_x,x2);max_y=max(max_y,y2)
        glyphs_checked+=1
    if i%8==0:print(f'Validated location {i+1}/{len(locations)}',flush=True)

roundtrips=[]
for filename in ['LKNova-VF.woff2','LKNova-Black.ttf','LKNova-Medium.ttf']:
    other=TTFont(DIST/filename,checkChecksums=2)
    assert other.getBestCmap()==cmap
    assert other['OS/2'].fsType==0
    if filename.endswith('woff2'):assert len(other['fvar'].axes)==9
    else:assert 'fvar' not in other and 'gvar' not in other
    roundtrips.append(filename)

result={'family':manifest['family'],'version':manifest['version'],'status':'passed',
        'encoded_characters':len(cmap),'glyphs':font['maxp'].numGlyphs,'axes':len(axes),
        'all_ascii_and_latin1':True,'german_characters':True,'brand_alternates_separate':True,
        'unrestricted_embedding':True,'embedded_red_square':True,'square_size_axis':'MARK','each_axis_changes_outlines':effects,
        'sampled_locations':len(locations),'glyph_instances_checked':glyphs_checked,
        'rounded_cap_and_foot_anchor_checks':anchor_checks,
        'sampled_bounds':[min_x,min_y,max_x,max_y],'binary_roundtrips':roundtrips,
        'scope':'Automated structure, coverage and sampled interpolation checks. Optical proofing is not exhaustive.'}
(QA/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
