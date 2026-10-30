"""Export editable cubic SVG glyphs, a geometric proof and a cubic UFO master."""
import json, math, re
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import escape
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.svgLib.path import parse_path
from fontTools.ufoLib import UFOWriter
from build_font import ROOT, DIST, DEFAULT, UNIT, BEARING, outlines, directions, ContourPen, make_glyph, glyph_name

def collect(char):
    parts,width=outlines(char,DEFAULT);collector=ContourPen()
    for part in parts:
        d,matrix=part if isinstance(part,tuple) else (part,(1,0,0,1,0,0))
        parse_path(d,TransformPen(collector,matrix))
    return collector.contours,width

def draw(char,target):
    contours,_=collect(char)
    for contour,reverse in zip(contours,directions(char)):
        pen=ReverseContourPen(target) if reverse else target
        for name,args in contour:getattr(pen,name)(*args)

def svg_path(char):
    pen=SVGPathPen(None);draw(char,pen);return pen.getCommands()

def main():
    manifest=json.loads((DIST/'font-manifest.json').read_text())
    vectors=DIST/'vectors';vectors.mkdir(exist_ok=True)
    for char in manifest['characters']:
        _,width=collect(char);d=svg_path(char)
        scale=1 if char in '■\ue000' else .9
        color='#d40000' if char in '■\ue000' else 'black'
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -30 {width*scale+20} 170">'
             f'<title>LK Nova U+{ord(char):04X} {escape(char)}</title>'
             f'<path fill="{color}" transform="scale({scale} 1)" fill-rule="nonzero" d="{d}"/></svg>')
        (vectors/f'U{ord(char):04X}.svg').write_text(svg)
    selected=['G','K','g','k','a','S','ß','■']
    labels={'G':'G / connected outer contour','K':'K / connected join at light weights','g':'g / lowercase construction','k':'k / connected join at light weights','a':'a / rounded construction','S':'S / rounded construction','ß':'ß / rounded construction','■':'■ / baseline-aligned square'}
    panels=[]
    for i,char in enumerate(selected):
        x=(i%2)*360;y=(i//2)*245;d=svg_path(char)
        guides='<path d="M-6 0H121M-6 100H121"/>'
        if char=='0':guides+='<ellipse cx="44" cy="38.6" rx="44" ry="39.6"/><ellipse cx="44" cy="61.4" rx="44" ry="39.6"/>'
        if char=='2':guides+='<ellipse cx="44" cy="34.9" rx="28.8889" ry="26"/>'
        if char=='3':guides+='<ellipse cx="46" cy="29.45" rx="27" ry="20.55"/><ellipse cx="46" cy="70.55" rx="31" ry="20.55"/>'
        if char=='5':guides+='<ellipse cx="47" cy="71" rx="41" ry="30"/><rect x="5" y="0" width="78" height="19.8"/>'
        if char=='6':guides+='<ellipse cx="46" cy="65" rx="40" ry="36"/><ellipse cx="46" cy="34" rx="29" ry="25.1"/>'
        if char=='8':guides+='<ellipse cx="44" cy="27" rx="35" ry="28"/><ellipse cx="44" cy="71" rx="39" ry="30"/>'
        if char=='a':guides+='<ellipse cx="41" cy="64.9" rx="41" ry="36.9"/><ellipse cx="41" cy="64.9" rx="21.64" ry="19.476"/>'
        if char=='S':
            from round_geometry import round_s_centerline,arc_commands
            n=19.8;x1,y1,x2,y2=13.987367448708273,10.245514677569801,82.13278618995717,90.7544853224302
            cs=[tuple(((x-x1)*(96-n/.9)/(x2-x1)+n/1.8,(y-y1)*(102-n)/(y2-y1)+n/2-1) for x,y in c) for c in round_s_centerline()]
            guides+='<path d="M'+str(cs[0][0][0])+' '+str(cs[0][0][1])+arc_commands(cs)+'"/>'
        if char=='y':guides+='<path d="M76 28L40 106C35 116.833 26 119 12 119M12 28L45.538 94"/>'
        if char=='ß':guides+='<ellipse cx="39.5" cy="30" rx="39.5" ry="31"/><ellipse cx="39.5" cy="30" rx="17.5" ry="13.545"/>'
        if char=='€':guides+='<path d="M-7 37H59M-7 63H53"/>'
        if char=='■':guides+='<rect x="0" y="80" width="20" height="20"/>'
        xfactor=1.55 if char in '■\ue000' else 1.395
        ink='#d40000' if char in '■\ue000' else 'black'
        panels.append(f'<g transform="translate({x} {y})"><text x="24" y="26" font-family="Arial,sans-serif" font-size="12" fill="#595959">{escape(labels[char])}</text><g transform="translate(78 65) scale({xfactor} 1.55)"><path class="ink" d="{d}" fill="{ink}" fill-rule="nonzero"/><g class="guides" fill="none" stroke="#d40000" stroke-width=".45">{guides}</g></g></g>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 980"><title>LK Nova — Geometric construction</title><style>.guides{opacity:.65}.ink{opacity:.85}</style><rect width="720" height="980" fill="white"/>'+''.join(panels)+'</svg>'
    (DIST/'LKNova-Konstruktion.svg').write_text(svg)
    # Native font-editor master with the original cubic points, not the many
    # quadratic approximation points needed by the installable TrueType font.
    ufopath=ROOT/'source/LKNova-BlackMaster.ufo'
    writer=UFOWriter(ufopath,formatVersion=3)
    writer.writeInfo(SimpleNamespace(familyName='LK Nova',styleName='Black',unitsPerEm=1000,ascender=910,descender=-270,xHeight=504,capHeight=700,versionMajor=1,versionMinor=0,copyright='Original Louis Kaiser project outlines, 2026.'))
    glyphset=writer.getGlyphSet()
    for char in manifest['characters']:
        _,advance=make_glyph(char,DEFAULT)
        obj=SimpleNamespace(width=advance,unicodes=[ord(char)],note='Original rectangle/ellipse construction; upright default master.')
        def draw_points(pointpen,c=char):
            sx=1 if c in '■\ue000' else .9
            pen=TransformPen(SegmentToPointPen(pointpen),(UNIT*sx,0,0,-UNIT,BEARING,700))
            draw(c,pen)
        glyphset.writeGlyph(glyph_name(char),obj,draw_points)
    glyphset.writeContents();writer.writeLayerContents()
    writer.writeKerning({(glyph_name(k[0]),glyph_name(k[1])):v for k,v in manifest['kerning_pairs'].items()})
    writer.close()
    print(f'Exported {len(manifest["characters"])} editable SVGs, geometry proof and cubic UFO master.')

if __name__=='__main__':main()
