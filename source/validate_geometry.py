"""Check the new master: smooth cubic joins, equal Xi bars and connected arrow."""
import math,json,string
from pathlib import Path
from export_vectors import collect
from build_font import DEFAULT,capital,outlines,ContourPen
from fontTools.svgLib.path import parse_path

root=Path(__file__).resolve().parents[1]
(root/'qa/geometry-validation.json').write_text(json.dumps({'status':'running'})+'\n')

intentional={('B',70.0,48.0),('R',64.0,60.536)}
smooth=0;corners=[]
for char in string.ascii_letters:
    contours,_=collect(char)
    for contour in contours:
        previous=at=None
        for operation,args in contour:
            if operation=='curveTo':
                if previous is not None:
                    a=(at[0]-previous[0],at[1]-previous[1]);b=(args[0][0]-at[0],args[0][1]-at[1]);length=math.hypot(*a)*math.hypot(*b)
                    if length:
                        angle=math.degrees(math.acos(max(-1,min(1,(a[0]*b[0]+a[1]*b[1])/length))))
                        if angle>.1:
                            assert any(char==c and abs(at[0]-x)<.01 and abs(at[1]-y)<.02 for c,x,y in intentional),(char,at,angle)
                            corners.append({'glyph':char,'position':at,'angle':angle,'reason':'Intentional concave branch between letter strokes; not a smooth bowl join.'})
                        else:smooth+=1
                previous=args[-2];at=args[-1]
            else:
                previous=None
                if args:at=args[-1]

d,width=capital('Ξ',DEFAULT);pen=ContourPen();parse_path(d,pen)
rects=[]
for contour in pen.contours:
    points=[a[-1] for op,a in contour if a];xs=[p[0] for p in points];ys=[p[1] for p in points]
    rects.append((max(xs)-min(xs),max(ys)-min(ys)))
assert len(rects)==3 and all(abs(w-86)<1e-6 and abs(h-20.24)<1e-6 for w,h in rects)
arrow,_=outlines('⇒',DEFAULT);pen=ContourPen();parse_path(arrow[0],pen)
assert len(pen.contours)==1
result={'status':'passed','redrawn_latin_letters':52,'tangent_aligned_consecutive_cubic_joins':smooth,'intentional_concave_branches':corners,'xi_bar_dimensions':rects,'double_arrow_contours':1,'scope':'The upright default cubic master. Straight-to-curve terminals and stroke intersections are intentional corners; this does not certify optical quality.'}

# Densely sample the analytical normal offsets independently of the four
# drawing subsegments, to detect folds between the drawing sample points.
import round_geometry as rounded
from geometry_redraw import lower, sharp_s
from build_font import params,ellipse
original_stroke=rounded.stroke
checks=0
def dense_stroke(segments,width,steps=4):
    global checks
    rounded._stroke(tuple(tuple(tuple(p) for p in curve) for curve in segments),width,32)
    checks+=1
    return original_stroke(segments,width,steps)
rounded.stroke=dense_stroke
for weight in [500,900,925,950]:
    loc={**DEFAULT,'wght':weight};t=params(loc)[0]
    capital('S',loc)
    for c in 'aefghmnrsuy':lower(c,loc)
    for c in '1235689':rounded.round_digit(c,t,t*.92,ellipse)
    rounded.question(t);sharp_s(loc)
rounded.stroke=original_stroke
result['dense_stroke_checks']=checks
result['dense_stroke_weights']=[500,900,925,950]
result['dense_normal_offsets_without_folds']=True
print('Dense stroke checks:',checks)

# A single connected outline is required for sharp s, not touching components.
for weight in [500,700,900,950]:
    parts,_=outlines('ß',{**DEFAULT,'wght':weight});p=ContourPen();parse_path(parts[0],p)
    assert len(p.contours)==1
result['sharp_s_single_contour']=True
# Cubic spline joins match signed curvature, including the waist.
curves=rounded.round_s_centerline()
def curvature(c,end):
    c=[(x*.9,y) for x,y in c]
    if end:d=(3*(c[3][0]-c[2][0]),3*(c[3][1]-c[2][1]));dd=(6*(c[3][0]-2*c[2][0]+c[1][0]),6*(c[3][1]-2*c[2][1]+c[1][1]))
    else:d=(3*(c[1][0]-c[0][0]),3*(c[1][1]-c[0][1]));dd=(6*(c[2][0]-2*c[1][0]+c[0][0]),6*(c[2][1]-2*c[1][1]+c[0][1]))
    return (d[0]*dd[1]-d[1]*dd[0])/math.hypot(*d)**3
errors=[abs(curvature(a,True)-curvature(b,False)) for a,b in zip(curves,curves[1:])]
assert max(errors)<1e-9,errors
result['S_centerline_curvature_continuity_max_error']=max(errors)


# Connected outlines and strengthened spine joins across the weight range.
connected=[]
for weight in [500,600,700,800,900,950]:
    for cntr in [78,92,105]:
        for aperture in [26,36,42]:
            loc={**DEFAULT,'wght':weight,'CNTR':cntr,'APER':aperture}
            for char in 'GKk':
                parts,_=outlines(char,loc);collector=ContourPen()
                assert len(parts)==1,(char,loc)
                parse_path(parts[0],collector);assert len(collector.contours)==1,(char,loc)
                connected.append((char,weight,cntr,aperture))
result['single_contour_G_K_k_checks']=len(connected)
join_heights=[]
for weight in [500,600,700,800,900,950]:
    for char,top in [('K',0),('k',28)]:
        loc={**DEFAULT,'wght':weight};t=params(loc)[0]*(1 if char=='K' else .88)
        d=rounded.k_outline(t,top);collector=ContourPen();parse_path(d,collector)
        pts=[args[-1] for op,args in collector.contours[0] if args]
        height=pts[8][1]-pts[2][1];assert height>=t,(char,weight,height,t)
        join_heights.append({'glyph':char,'weight':weight,'spine_connection_height':height,'stem_width':t})
result['K_k_join_heights']=join_heights
(root/'qa/geometry-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
