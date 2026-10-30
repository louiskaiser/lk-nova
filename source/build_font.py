"""Original LK Nova outlines and nine-axis OpenType build.

Requires fonttools[woff] and brotli. No source font is loaded or traced.
All outlines below are generated from project-owned geometric constructions.
"""
from __future__ import annotations
import itertools, json, math, os, sys, unicodedata, copy
from pathlib import Path
from functools import lru_cache
from array import array

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.basePen import BasePen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.otlLib.builder import buildStatTable
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
UPM, UNIT, BEARING = 1000, 7, 42
AXES = [
    ('wght', 500, 900, 950, 'Weight'),
    ('wdth', 85, 100, 140, 'Width'),
    ('slnt', -12, 0, 0, 'Slant'),
    ('CNTR', 78, 92, 105, 'Horizontal stroke ratio'),
    ('ROND', 25, 50, 50, 'Roundness'),
    ('APER', 26, 36, 42, 'Aperture'),
    ('RLEG', 20, 80, 95, 'R leg'),
    ('XBAR', 57, 76, 76, 'A crossbar'),
    ('MARK',10,20,40,'Brand square size'),
]
DEFAULT = {a[0]: a[2] for a in AXES}

def rr(x, y, w, h, r):
    # Keep tiny straight segments so contour topology stays identical at extrema.
    r = min(r, w/2-.25, h/2-.25)
    k = r*.55228475
    return (f'M{x+r} {y}H{x+w-r}C{x+w-r+k} {y} {x+w} {y+r-k} {x+w} {y+r}'
            f'V{y+h-r}C{x+w} {y+h-r+k} {x+w-r+k} {y+h} {x+w-r} {y+h}'
            f'H{x+r}C{x+r-k} {y+h} {x} {y+h-r+k} {x} {y+h-r}'
            f'V{y+r}C{x} {y+r-k} {x+r-k} {y} {x+r} {y}Z')

def rect(x,y,w,h):
    return f'M{x} {y}h{w}v{h}h{-w}Z'

def ellipse(cx,cy,rx,ry,roundness=50):
    # Four symmetric cubic quarters. At the default the handles use the
    # standard ellipse construction; ROND changes the handle ratio symmetrically.
    k=.5522847498307936+(50-roundness)/25*.20
    return (f'M{cx} {cy-ry}C{cx+k*rx} {cy-ry} {cx+rx} {cy-k*ry} {cx+rx} {cy}'
            f'C{cx+rx} {cy+k*ry} {cx+k*rx} {cy+ry} {cx} {cy+ry}'
            f'C{cx-k*rx} {cy+ry} {cx-rx} {cy+k*ry} {cx-rx} {cy}'
            f'C{cx-rx} {cy-k*ry} {cx-k*rx} {cy-ry} {cx} {cy-ry}Z')

def ellipse_arc(cx,cy,rx,ry,start,end,segments=4):
    """Fixed-count tangent-aligned cubic representation of an ellipse arc."""
    point=lambda a:(cx+rx*math.cos(a),cy+ry*math.sin(a))
    commands=[]
    for i in range(segments):
        a=start+(end-start)*i/segments;b=start+(end-start)*(i+1)/segments
        p=point(a);q=point(b);k=4/3*math.tan((b-a)/4)
        commands.append(f'C{p[0]-k*rx*math.sin(a)} {p[1]+k*ry*math.cos(a)} '
                        f'{q[0]+k*rx*math.sin(b)} {q[1]-k*ry*math.cos(b)} {q[0]} {q[1]}')
    return point(start),''.join(commands),point(end)

def poly(points):
    return 'M'+'L'.join(f'{x} {y}' for x,y in points)+'Z'

def line(x1,y1,x2,y2,width):
    dx,dy=x2-x1,y2-y1
    length=math.hypot(dx,dy)
    nx,ny=-dy/length*width/2,dx/length*width/2
    return poly([(x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny)])

def params(loc):
    w=loc['wght']
    t=22+(w-900)*(10/400 if w<=900 else 2/50)
    return t,t*loc['CNTR']/100,loc['ROND'],loc['APER'],loc['RLEG'],loc['XBAR']

from geometry_redraw import capital, lower, sharp_s
import round_geometry as rounded

def shifted(path,sx=1,sy=1,dx=0,dy=0):
    return (path,(sx,0,0,sy,dx,dy))

def digit(c,loc):
    t,h,r,a,leg,b=params(loc)
    if c in '0123456789':return rounded.round_digit(c,t,h,lambda cx,cy,rx,ry:ellipse(cx,cy,rx,ry,r))
    raise KeyError(c)

def punctuation(c,loc):
    t,h,r,a,leg,b=params(loc);v=max(9,t*.62);dot=rr(0,100-v,v,v,2)
    if c in '■\ue000':
        size=loc['MARK'];return [rect(0,100-size,size,size)],size
    if c=='?':
        d,w=rounded.question(t);return [d],w
    if c=='#':return [rounded.stroke([rounded.straight((30,0),(14,100))],t*.9)+rounded.stroke([rounded.straight((76,0),(60,100))],t*.9)+rect(0,30,96,t*.9)+rect(0,66,96,t*.9)],96
    if c=='\"':return [rect(0,0,t,27)+rect(t+10,0,t,27)],t*2+10
    if c in ' \u00a0\u2002\u2003\u2007\u2009\u202f':return [],{'\u2002':71.4,'\u2003':142.8,'\u2007':100,'\u2009':22,'\u202f':22}.get(c,40)
    if c=='⇒':
        v=t*.58
        upper_top=50-h*.70-v/2;upper_bottom=upper_top+v
        lower_top=50+h*.70-v/2;lower_bottom=lower_top+v
        tip=96-v*.3
        up=lambda y:65+(y-12)/38*(tip-65)
        down=lambda y:65+(88-y)/38*(tip-65)
        # One union contour: both rectangular shafts meet the chevron exactly.
        return [poly([(65,12),(65+v*.9,12),(112,50),(65+v*.9,88),(65,88),
                      (down(lower_bottom),lower_bottom),(0,lower_bottom),(0,lower_top),
                      (down(lower_top),lower_top),(tip,50),(up(upper_bottom),upper_bottom),
                      (0,upper_bottom),(0,upper_top),(up(upper_top),upper_top)])],112
    if c in '.·•':return [rr(0,100-v if c=='.' else 50-v/2,v,v,v/2 if c=='•' else 1)],v
    if c==',':return [f'M0 {100-v}H{v}V100L1 116H{-v*.2}L{v*.3} 100H0Z'],v
    if c==':':return [rr(0,35,v,v,1)+dot],v
    if c==';':p,w=punctuation(',',loc);return [rr(0,35,v,v,1)+p[0]],w
    if c=='!':return [rect(0,0,v,70)+dot],v
    if c=='?':return [(f'M0 27C2 9 17 0 42 0C70 0 84 9 84 28C84 42 76 49 60 56C51 60 49 63 49 71H{49-v}'
                       f'C{49-v} 55 37 48 51 41C61 36 64 34 64 28C64 {h} 57 {h} 42 {h}C28 {h} 22 24 21 29Z')+rect(49-v,100-v,v,v)],84
    if c in '-–—−\u00ad':
        w={'-':45,'–':75,'—':120,'−':70,'\u00ad':45}[c];return [rect(0,50-h/2,w,h)],w
    if c=='_':return [rect(0,108,85,h*.7)],85
    if c=='¬':return [rect(0,40,80,h)+rect(80-h,40,h,37)],80
    if c=='±':return [rect(0,39-h/2,75,h)+rect(37-h/2,4,h,70)+rect(0,90-h/2,75,h)],75
    if c=='¦':return [rect(0,-8,v,49)+rect(0,63,v,49)],v
    if c=='¯':return [rect(0,-8,64,9)],64
    if c=='¨':return [rect(0,0,14,13)+rect(32,0,14,13)],46
    if c=='¸':return accent('\u0327',40,loc),40
    if c in '¹²³':p,w=digit({'¹':'1','²':'2','³':'3'}[c],loc);return [shifted_path(q,.55,.55,0,0) for q in p],w*.55
    if c in 'ªº':p,w=lower('a' if c=='ª' else 'o',loc);return [shifted_path(q,.55,.55,0,-15) for q in p],w*.55
    if c in '¼½¾':
        first,second={'¼':('1','4'),'½':('1','2'),'¾':('3','4')}[c]
        p,w=digit(first,loc);q,z=digit(second,loc)
        return [shifted_path(z,.45,.5,0,0) for z in p]+[shifted_path(z,.45,.5,56,50) for z in q]+[line(28,100,79,0,v*.6)],105
    if c=='µ':p,w=lower('u',loc);return p+[rect(0,80,t*.88,45)],w
    if c=='¶':return [f'M100 0V100H{100-v}V{h}H{70-v}V100H{70-v*2}V61H45C15 61 0 50 0 30S15 0 45 0Z'],100
    if c=='§':p,w=capital('S',loc);return [shifted(p,.7,.65),shifted(p,.7,.65,0,36)],70
    if c in '†‡':return [rect(32-v/2,0,v,110)+rect(0,28,64,h*.65)+(rect(0,65,64,h*.65) if c=='‡' else '')],64
    if c=='¤':return [rr(15,25,60,60,30)+rr(15+v,25+v,60-v*2,60-v*2,30-v)+line(2,12,23,33,v)+line(67,77,88,98,v)+line(2,98,23,77,v)+line(67,33,88,12,v)],90
    if c in '+=':
        return [rect(0,50-h/2,75,h)+rect(37-h/2,12,h,76) if c=='+' else rect(0,32,75,h)+rect(0,68-h,75,h)],75
    if c in '/\\|':return [line(4,100,53,0,v) if c=='/' else line(4,0,53,100,v) if c=='\\' else rect(0,-8,v,120)],57 if c!='|' else v
    if c in '()[]{}':
        if c=='(':return [f'M40 -8H{40-v}C4 15 0 37 0 50C0 72 9 96 {40-v} 112H40C18 86 {v} 68 {v} 50C{v} 32 18 13 40 -8Z'],40
        if c==')':p,w=punctuation('(',loc);return [shifted(p[0],-1,1,40,0)],40
        if c=='[':return [poly([(0,-8),(38,-8),(38,-8+v),(v,-8+v),(v,112-v),(38,112-v),(38,112),(0,112)])],38
        if c==']':p,w=punctuation('[',loc);return [shifted(p[0],-1,1,38,0)],38
        if c=='{':return [f'M48 -8V{-8+v}C25 {-8+v} 25 6 25 22V35C25 43 20 48 12 50C20 52 25 57 25 65V78C25 94 25 {112-v} 48 {112-v}V112C10 112 10 100 10 79V66C10 58 7 56 0 56V44C7 44 10 42 10 34V21C10 0 10 -8 48 -8Z'],48
        p,w=punctuation('{',loc);return [shifted(p[0],-1,1,48,0)],48
    if c in "'\"‘’‚“”„`´":
        down=c in '‚„';left=c in '‘“';y=90 if down else 0
        q=(f'M0 {y}H{v}V{y+v}L2 {y+v+12}H{-v*.12}L{v*.3} {y+v}H0Z')
        if left:q=f'M{v} {y+v+12}H0V{y+12}L{v-2} {y}H{v+v*.12}L{v*.7} {y+12}H{v}Z'
        if c in '“”„"':return [q,shifted(q,1,1,v+8,0)],2*v+8
        return [q],v
    if c in '<>«»‹›':
        p=line(35,22,0,50,v)+line(0,50,35,78,v)
        if c in '>»›':p=[shifted(p,-1,1,35,0)]
        else:p=[p]
        if c in '«»':p += [shifted(p[0][0],p[0][1][0],1,59,0)] if isinstance(p[0],tuple) else [shifted(p[0],1,1,24,0)]
        return p,59 if c in '«»' else 35
    if c=='^':return [line(0,40,32,0,v)+line(32,0,64,40,v)],64
    if c=='~':return [f'M0 54C17 25 36 66 54 38L66 46C45 78 26 39 12 62Z'],66
    if c=='*':return [line(30,0,30,60,v*.65)+line(4,15,56,45,v*.65)+line(4,45,56,15,v*.65)],60
    if c=='#':return [line(28,0,14,100,v)+line(66,0,52,100,v)+rect(0,28,82,h*.7)+rect(0,66,82,h*.7)],82
    if c=='%':return [rr(0,0,36,38,18)+rr(v*.7,v*.7,36-v*1.4,38-v*1.4,9)+rr(60,62,36,38,18)+rr(60+v*.7,62+v*.7,36-v*1.4,38-v*1.4,9)+line(4,100,92,0,v*.65)],96
    if c=='&':
        return [(f'M95 100H{95-t}L61 85C48 98 37 102 24 100C5 98 -3 87 0 70C2 57 12 49 25 42'
                 f'C14 28 14 16 25 6C36 -4 62 -2 72 10C83 23 73 37 54 47L70 63L81 44H101L84 78Z'
                 f'M40 31C51 26 57 21 53 16C48 12 38 14 36 19C34 23 36 27 40 31Z'
                 f'M38 56C25 63 18 69 22 76C27 84 38 82 48 72Z')],101
    if c=='@':
        return [rr(0,0,125,112,50)+rr(v, v,125-v*2,112-v*2,max(3,50-v))
                +rr(36,30,57,53,24)+rr(36+v,30+v,57-v*2,53-v*2,9)+rect(93-v,30,v,53)],125
    if c in '$€£¥¢':
        if c=='$':p,w=capital('S',loc);return [p,rect(46,-10,v*.6,120)],100
        if c=='€':
            p,w=capital('C',loc);end=54+(a-26)*.5-(t-22)*.2;stroke=h*.65
            return [p,rect(-7,37-stroke/2,end+7,stroke),rect(-7,63-stroke/2,end+1,stroke)],100
        if c=='£':return [f'M10 100V{h+20}C10 5 26 0 52 0C76 0 91 6 94 24H{94-t}C{90-t} {h} 63 {h} 52 {h}C37 {h} {10+t} {h+3} {10+t} {h+20}V{100-h}H95V100Z'+rect(0,50,71,h*.7)],95
        if c=='¥':p,w=capital('Y',loc);return [p,rect(13,58,74,h*.55),rect(13,77,74,h*.55)],100
        p,w=capital('C',loc);return [shifted(p,.75,.75,0,20),rect(33,9,v*.6,103)],75
    if c=='×':return [line(6,18,72,84,v)+line(6,84,72,18,v)],78
    if c=='÷':return [rect(0,50-h/2,75,h)+rr(30,13,v,v,2)+rr(30,77,v,v,2)],75
    if c=='°':return [rr(0,0,43,43,21.5)+rr(v*.7,v*.7,43-v*1.4,43-v*1.4,12)],43
    if c in '©®':
        p,w=capital('C' if c=='©' else 'R',loc)
        return [rr(0,0,110,110,55)+rr(v*.55,v*.55,110-v*1.1,110-v*1.1,55-v*.55),shifted(p,.48,.55,31,27)],110
    if c=='™':
        p,w=capital('T',loc);q,z=capital('M',loc);return [shifted(p,.4,.45),shifted(q,.4,.45,45,0)],93
    if c=='…':return [dot,shifted(dot,1,1,v+10,0),shifted(dot,1,1,2*v+20,0)],3*v+20
    if c in '¡¿':p,w=punctuation('!' if c=='¡' else '?',loc);return [shifted(q,-1,-1,w,100) for q in p],w
    raise KeyError(c)

def accent(mark,width,loc,upper=True):
    t,h,r,a,leg,b=params(loc);v=9;cx=width/2;y=-22 if upper else 6
    if mark=='\u0308':return [rect(cx-23,y,14,13)+rect(cx+9,y,14,13)]
    if mark=='\u0301':return [poly([(cx-15,y+14),(cx+1,y),(cx+21,y),(cx+1,y+14)])]
    if mark=='\u030b':return [poly([(cx-29,y+14),(cx-13,y),(cx+3,y),(cx-13,y+14)])+poly([(cx-3,y+14),(cx+13,y),(cx+29,y),(cx+13,y+14)])]
    if mark=='\u0300':return [poly([(cx-21,y),(cx-1,y),(cx+15,y+14),(cx-1,y+14)])]
    if mark=='\u0302':return [poly([(cx-27,y+14),(cx-9,y),(cx+9,y),(cx+27,y+14),(cx+9,y+14),(cx,y+7),(cx-9,y+14)])]
    if mark=='\u030c':return [poly([(cx-27,y),(cx-9,y),(cx,y+7),(cx+9,y),(cx+27,y),(cx+9,y+14),(cx-9,y+14)])]
    if mark=='\u0303':return [f'M{cx-28} {y+10}C{cx-13} {y-7} {cx+2} {y+17} {cx+18} {y}L{cx+27} {y+7}C{cx+10} {y+25} {cx-6} {y} {cx-20} {y+17}Z']
    if mark=='\u030a':return [rr(cx-14,y-6,28,25,12)+rr(cx-6,y,12,13,5)]
    if mark=='\u0327':return [f'M{cx-4} 98H{cx+8}L{cx+1} 108C{cx+24} 108 {cx+24} 130 {cx} 130H{cx-15}V121H{cx-2}C{cx+10} 121 {cx+10} 115 {cx-6} 115H{cx-10}Z']
    if mark=='\u0304':return [rect(cx-24,y+5,48,9)]
    if mark=='\u0306':return [f'M{cx-24} {y}H{cx-13}Q{cx} {y+14} {cx+13} {y}H{cx+24}Q{cx} {y+32} {cx-24} {y}Z']
    if mark=='\u0307':return [rect(cx-7,y,14,13)]
    if mark=='\u0328':return [f'M{cx+15} 98H{cx+27}Q{cx+3} 119 {cx+24} 120V130Q{cx-15} 127 {cx+15} 98Z']
    raise KeyError(mark)

def outlines(c,loc):
    if 'A'<=c<='Z' or c in 'ΛΞ':p,w=capital(c,loc);return [p],w
    if 'a'<=c<='z':return lower(c,loc)
    if c.isascii() and c.isdigit():return digit(c,loc)
    nfd=unicodedata.normalize('NFD',c)
    if len(nfd)>1 and nfd[0].isascii() and nfd[0].isalpha():
        p,w=outlines(nfd[0],loc)
        for mark in nfd[1:]:p+=accent(mark,w,loc,nfd[0].isupper())
        return p,w
    if c in 'ÆæŒœ':
        upper=c.isupper();left='A' if c in 'Ææ' else 'O';right='E'
        p,w=outlines(left if upper else left.lower(),loc);q,z=outlines(right if upper else right.lower(),loc)
        return p+[shifted_path(v,1,1,w-13,0) for v in q],w+z-13
    if c in 'Øø':
        p,w=outlines('O' if c=='Ø' else 'o',loc);t=params(loc)[0]
        return p+[line(3,100,w-3,0 if c=='Ø' else 28,t*.55)],w
    if c in 'ÐðĐđ':
        p,w=outlines('D' if c in 'ÐĐ' else 'd',loc);h=params(loc)[1]
        return p+[rect(-10,46 if c in 'ÐĐ' else 12,57,h*.65)],w
    if c in 'Þþ':
        p,w=capital('P',loc);return [shifted(p,1,.75,0,18),rect(0,0,params(loc)[0],100 if c=='Þ' else 125)],w
    if c in 'ßẞ':
        p,w=sharp_s(loc,c=='ẞ');return [p],w
    if c in 'Łł':p,w=outlines('L' if c=='Ł' else 'l',loc);return p+[line(-5,65,w*.8,35,params(loc)[1]*.6)],w
    if c=='ı':t=params(loc)[0]*.88;return [rect(0,28,t,72)],t
    if c=='ĸ':return lower('k',loc)
    return punctuation(c,loc)

def shifted_path(part,sx,sy,dx,dy):
    if isinstance(part,tuple):
        p,m=part;a,b,c,d,e,f=m
        return p,(a*sx,b*sy,c*sx,d*sy,e*sx+dx,f*sy+dy)
    return shifted(part,sx,sy,dx,dy)

class FixedQuadraticPen(BasePen):
    """Fixed topology cubic-to-quadratic conversion across every master."""
    def __init__(self,out):super().__init__(None);self.out=out
    def _moveTo(self,p):self.out.moveTo(p)
    def _lineTo(self,p):self.out.lineTo(p)
    def _qCurveToOne(self,p1,p2):self.out.qCurveTo(p1,p2)
    def _curveToOne(self,p1,p2,p3):
        p0=self._getCurrentPoint()
        def at(t):
            u=1-t
            return tuple(u*u*u*p0[i]+3*u*u*t*p1[i]+3*u*t*t*p2[i]+t*t*t*p3[i] for i in (0,1))
        def derivative(t):
            u=1-t
            return tuple(3*u*u*(p1[i]-p0[i])+6*u*t*(p2[i]-p1[i])+3*t*t*(p3[i]-p2[i]) for i in (0,1))
        for k in range(6):
            a,b=k/6,(k+1)/6;q0,q3=at(a),at(b);da,db=derivative(a),derivative(b)
            q1=tuple(q0[i]+da[i]/18 for i in (0,1));q2=tuple(q3[i]-db[i]/18 for i in (0,1))
            q=tuple((3*q1[i]-q0[i]+3*q2[i]-q3[i])/4 for i in (0,1))
            self.out.qCurveTo(q,q3)
    def _closePath(self):self.out.closePath()
    def _endPath(self):self.out.endPath()

class ContourPen(BasePen):
    def __init__(self):super().__init__(None);self.contours=[];self.current=[]
    def _moveTo(self,p):self.current=[('moveTo',(p,))]
    def _lineTo(self,p):self.current.append(('lineTo',(p,)))
    def _qCurveToOne(self,p1,p2):self.current.append(('qCurveTo',(p1,p2)))
    def _curveToOne(self,p1,p2,p3):self.current.append(('curveTo',(p1,p2,p3)))
    def _closePath(self):self.current.append(('closePath',()));self.contours.append(self.current);self.current=[]
    def _endPath(self):self._closePath()

def inside(pt,points):
    x,y=pt;result=False
    for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]):
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:result=not result
    return result

@lru_cache(maxsize=None)
def directions(char):
    parts,w=outlines(char,DEFAULT);collector=ContourPen()
    for part in parts:
        path,m=part if isinstance(part,tuple) else (part,(1,0,0,1,0,0))
        parse_path(path,TransformPen(RoundingPen(collector,roundFunc=lambda x:round(x,6)),m))
    polygons=[]
    # Flatten just for containment; drawing retains quadratic curves.
    for contour in collector.contours:
        pen=TTGlyphPen(None,outputImpliedClosingLine=True);q=FixedQuadraticPen(pen)
        for name,args in contour:getattr(q,name)(*args)
        g=pen.glyph();polygons.append(list(g.coordinates))
    rev=[]
    for i,points in enumerate(polygons):
        depth=sum(all(inside(p,q) for p in points[::max(1,len(points)//8)]) for j,q in enumerate(polygons) if j!=i)
        area=sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]))
        # SVG y-down clockwise becomes TrueType clockwise after y inversion.
        desired_positive=depth%2==0
        rev.append((area>0)!=desired_positive)
    return rev

def make_glyph(char,loc):
    from fontTools.pens.reverseContourPen import ReverseContourPen
    parts,w=outlines(char,loc);collector=ContourPen()
    for part in parts:
        path,m=part if isinstance(part,tuple) else (part,(1,0,0,1,0,0))
        parse_path(path,TransformPen(RoundingPen(collector,roundFunc=lambda x:round(x,6)),m))
    pen=TTGlyphPen(None,outputImpliedClosingLine=True);sx=.90*loc['wdth']/100;skew=math.tan(-loc['slnt']*math.pi/180)
    transform=(UNIT*sx,0,-UNIT*skew,-UNIT,BEARING+100*UNIT*skew,700)
    if char in '■\ue000':sx=1;skew=0
    transform=(UNIT*sx,0,-UNIT*skew,-UNIT,BEARING+100*UNIT*skew,700)
    assert len(collector.contours)==len(directions(char)),(char,loc,'contour count')
    for contour,reverse in zip(collector.contours,directions(char)):
        target=TransformPen(FixedQuadraticPen(pen),transform)
        if reverse:target=ReverseContourPen(target)
        for name,args in contour:getattr(target,name)(*args)
    glyph=pen.glyph()
    if glyph.numberOfContours and len(glyph.flags):glyph.flags[0]|=0x40
    advance=round(w*sx*UNIT+BEARING*2)
    if char in '■\ue000':advance=round(w*UNIT+BEARING+52)
    return glyph,advance

def dependencies(char):
    if char in '■\ue000':return ['MARK']
    base=unicodedata.normalize('NFD',char)[0]
    axes=['wght','wdth','slnt','CNTR']
    if base in 'AÆ':axes+=['XBAR']
    if base in 'OoQqUuabcdeghmnopq0689@©®ÆæŒœØø':axes+=['ROND']
    if base in 'CcGgEe€¢':axes+=['ROND','APER']
    if base=='R' or char=='®':axes+=['RLEG']
    return [axis[0] for axis in AXES if axis[0] in axes]

def glyph_name(c):return 'uni%04X'%ord(c)

def build():
    DIST.mkdir(parents=True,exist_ok=True)
    # All printable ASCII, Latin-1, and commonly used Western European extras.
    chars=[chr(i) for i in range(32,127)]+[chr(i) for i in range(160,256)]
    chars+=list('ĀāĂăĄąĆćČčĎďĐđĒēĖėĘęĚěĞğİıŁłŃńŇňŌōŐőŒœŔŕŘřŚśŠšŤťŪūŮůŰűŲųŹźŻżŽžŸẞΛΞ⇒■\ue000€‘’‚“”„–—−…•™†‡\u2002\u2003\u2007\u2009\u202f')
    chars=sorted(set(chars),key=ord)
    # Explicitly omit unsupported Latin-1 spacing symbols from the chosen coverage.
    unsupported=[];supported=[]
    for c in chars:
        try:outlines(c,DEFAULT);supported.append(c)
        except KeyError:unsupported.append(c)
    chars=supported
    names=['.notdef']+[glyph_name(c) for c in chars]
    glyphs={};metrics={};variations={}
    ndpen=TTGlyphPen(None)
    for points in [[(50,0),(50,700),(420,700),(420,0)],[(100,50),(370,50),(370,650),(100,650)]]:
        ndpen.moveTo(points[0])
        for p in points[1:]:ndpen.lineTo(p)
        ndpen.closePath()
    glyphs['.notdef']=ndpen.glyph();metrics['.notdef']=(470,50);variations['.notdef']=[]
    axisinfo={a[0]:a for a in AXES}
    for index,char in enumerate(chars):
        name=glyph_name(char);base,advance=make_glyph(char,DEFAULT)
        glyphs[name]=base;metrics[name]=(advance,round(base.xMin if hasattr(base,'xMin') else BEARING))
        base.recalcBounds(None)
        metrics[name]=(advance,base.xMin if base.numberOfContours else 0)
        coords=list(base.coordinates) if base.numberOfContours else []
        deps=dependencies(char)
        levels=[]
        for tag in deps:
            _,lo,df,hi,_=axisinfo[tag]
            levels.append(([(-1,lo)] if lo<df else [])+[(0,df)]+([(1,hi)] if hi>df else []))
        nodes=list(itertools.product(*levels))
        nodes.sort(key=lambda n:sum(v[0]!=0 for v in n))
        cached={};deltas={};tuples=[]
        zero=(0,)*len(deps)
        cached[zero]=coords+[(0,0),(advance,0),(0,0),(0,0)]
        for node in nodes:
            key=tuple(n[0] for n in node)
            if key==zero:continue
            loc={**DEFAULT,**{tag:n[1] for tag,n in zip(deps,node)}}
            g,aw=make_glyph(char,loc)
            target=list(g.coordinates) if g.numberOfContours else []
            if len(target)!=len(coords) or (g.numberOfContours and list(g.endPtsOfContours)!=list(base.endPtsOfContours)):
                raise ValueError(('Incompatible master',char,loc))
            if g.numberOfContours and [f&1 for f in g.flags]!=[f&1 for f in base.flags]:
                raise ValueError(('Incompatible on/off-curve point types',char,loc))
            target+= [(0,0),(aw,0),(0,0),(0,0)]
            delta=[[p[0]-q[0],p[1]-q[1]] for p,q in zip(target,cached[zero])]
            active=[i for i,k in enumerate(key) if k]
            for count in range(1,len(active)):
                for subset in itertools.combinations(active,count):
                    subkey=tuple(key[i] if i in subset else 0 for i in range(len(deps)))
                    sd=deltas.get(subkey)
                    if sd:
                        for p,d in zip(delta,sd):p[0]-=d[0];p[1]-=d[1]
            delta=[tuple(d) for d in delta]
            # Preserve exact rounded interpolation, including one-unit interactions.
            if any(x or y for x,y in delta):
                deltas[key]=delta
                support={tag:((-1,-1,0) if k<0 else (0,1,1)) for tag,k in zip(deps,key) if k}
                tuples.append(TupleVariation(support,delta))
        variations[name]=tuples
        if index%25==0:print(f'{index+1}/{len(chars)} glyphs: {char!r}',flush=True)
    color_layer='brandmark.red'
    names.append(color_layer);glyphs[color_layer]=copy.deepcopy(glyphs[glyph_name('■')]);metrics[color_layer]=metrics[glyph_name('■')];variations[color_layer]=copy.deepcopy(variations[glyph_name('■')])
    fb=FontBuilder(UPM,isTTF=True)
    fb.setupGlyphOrder(names);fb.setupCharacterMap({ord(c):glyph_name(c) for c in chars})
    fb.setupGlyf(glyphs);fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=910,descent=-270,lineGap=0)
    fb.setupNameTable({'familyName':'LK Nova','styleName':'Black','uniqueFontIdentifier':'LKNova-1.000-original',
                      'fullName':'LK Nova Variable','psName':'LKNova-Variable','version':'Version 1.000',
                      'copyright':'Copyright 2026 Louis Kaiser. Original project outlines.',
                      'licenseDescription':'Unrestricted personal and commercial use, modification, embedding and redistribution. No royalties or attribution required. See LICENSE.txt.'})
    fb.setupOS2(version=4,sTypoAscender=910,sTypoDescender=-270,sTypoLineGap=0,usWinAscent=1000,usWinDescent=350,
                sxHeight=504,sCapHeight=700,usWeightClass=900,usWidthClass=5,fsType=0,fsSelection=0xA0)
    fb.setupPost(keepGlyphNames=True)
    fb.setupMaxp()
    # The geometric variable outlines have no hint program. Request smooth
    # rasterization without grid-fitting thin animated joins.
    from fontTools.ttLib import newTable
    fb.font['gasp']=newTable('gasp');fb.font['gasp'].version=1
    fb.font['gasp'].gaspRange={65535:0x000A}
    fb.setupFvar(AXES,[{'location':{**DEFAULT,'wght':weight},'stylename':style} for style,weight in [('Medium',500),('SemiBold',600),('Bold',700),('ExtraBold',800),('Black',900),('UltraBlack',950)]]+[
                      {'location':{**DEFAULT,'wdth':140},'stylename':'Black Wide'},
                      {'location':{**DEFAULT,'slnt':-12},'stylename':'Black Slanted'}])
    fb.setupGvar(variations)
    fb.setupCOLR({glyph_name(c):[(color_layer,0)] for c in '■\ue000'},version=0)
    fb.setupCPAL([[(212/255,0,0,1)]],paletteLabels=['Louis Kaiser Red'],paletteEntryLabels=['Brand square'])
    style_axes=[]
    for i,a in enumerate(AXES):
        values=[]
        for value in sorted(set(a[1:4]) | ({600,700,800} if a[0]=='wght' else set())):
            name=({500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black',950:'UltraBlack'}[value] if a[0]=='wght' else ('Default' if value==a[2] else f'{a[4]} {value}'))
            values.append({'value':value,'name':name,'flags':2 if value==a[2] else 0})
        style_axes.append({'tag':a[0],'name':a[4],'ordering':i,'values':values})
    buildStatTable(fb.font,style_axes,elidedFallbackName='Black')
    pairs={'AV':-22,'AW':-16,'AY':-22,'AT':-12,'TA':-18,'VA':-22,'WA':-16,'YA':-22,'LT':-12,'LY':-18,'To':-14,'Ta':-14,'Yo':-16,'Te':-12,'FA':-14,'PA':-10}
    fea='languagesystem DFLT dflt; languagesystem latn dflt; feature kern {\n'
    fea+='\n'.join(f'pos {glyph_name(p[0])} {glyph_name(p[1])} {v};' for p,v in pairs.items())+'\n} kern;'
    fea+='\nfeature dlig {\n'
    for sequence in ['[LK]','[lk]']:
        fea+='sub '+' '.join(glyph_name(c) for c in sequence)+' by '+glyph_name('■')+';\n'
    fea+='} dlig;'
    addOpenTypeFeaturesFromString(fb.font,fea)
    fb.font['head'].fontRevision=1.0
    fb.font['head'].macStyle=1
    path=DIST/'LKNova-VF.ttf';fb.save(path)
    font=TTFont(path);font.flavor='woff2';font.save(DIST/'LKNova-VF.woff2')
    for name,loc in [(style,{**DEFAULT,'wght':weight}) for style,weight in [('Medium',500),('SemiBold',600),('Bold',700),('ExtraBold',800),('Black',900),('UltraBlack',950)]]:
        instance=instantiateVariableFont(TTFont(path),loc,inplace=False,updateFontNames=True)
        
        legacy_family='LK Nova' if name=='Bold' else 'LK Nova '+name
        legacy_style='Bold' if name=='Bold' else 'Regular'
        for nid,value in {1:legacy_family,2:legacy_style,3:'LKNova-'+name+'-1.000',4:'LK Nova '+name,6:'LKNova-'+name,16:'LK Nova',17:name}.items():
            instance['name'].setName(value,nid,3,1,0x409)
            instance['name'].setName(value,nid,1,0,0)
        instance['OS/2'].usWeightClass=int(loc['wght'])
        instance['OS/2'].fsSelection=(0x20 if name=='Bold' else 0x40)|0x80
        instance['head'].macStyle=1 if name=='Bold' else 0
        instance.save(DIST/f'LKNova-{name}.ttf')
    manifest={'family':'LK Nova','version':'1.000','stage':'User-approved design; publication release 1.0.',
              'axes':[{'tag':a[0],'min':a[1],'default':a[2],'max':a[3],'name':a[4]} for a in AXES],
              'glyph_count':len(names),'encoded_characters':len(chars),'characters':''.join(chars),
              'omitted_optional_symbols':''.join(unsupported),'units_per_em':UPM,'cap_height':700,'x_height':504,
              'source':'Original generated outlines in source/geometry_redraw.py and source/build_font.py; no Helvetica or other font outlines used.',
              'baseline_reference':{'stroke':22,'width':90,'contrast':92,'roundness':50,'aperture':36,'leg':80,'crossbar':76,'tracking':0},
              'kerning_pairs':pairs,'embedding_restrictions':0,'tracking_em':-0.05,'brand_square':{'characters':['■','\ue000'],'optional_ligatures':['[LK]','[lk]'],'feature':'dlig','color':'#D40000','format':'COLR v0 / CPAL','size_font_units':140,'baseline_y':0,'square_at_every_setting':True,'size_axis':'MARK','unaffected_by_other_axes':True}}
    (DIST/'font-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'built':str(path),'characters':len(chars),'optional_omissions':unsupported},ensure_ascii=False),flush=True)

if __name__=='__main__':build()
