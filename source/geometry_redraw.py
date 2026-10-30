"""Second construction: all 52 Latin letters redrawn as a coherent grotesque.

Rectilinear stems, proportional widths, ellipse-derived bowls, horizontal
terminals and tangent-aligned cubic contours. No existing font is read.
Coordinates: cap line 0, x-height 28, baseline 100, descender 127.
"""
import math
import round_geometry as rounded

K=.5522847498307936

def box(x,y,w,h):return f'M{x} {y}h{w}v{h}h{-w}Z'
def polygon(points):return 'M'+'L'.join(f'{x} {y}' for x,y in points)+'Z'
def settings(loc):
    weight=loc['wght'];t=22+(weight-900)*(10/400 if weight<=900 else 2/50)
    return t,t*loc['CNTR']/100,loc['ROND'],loc['APER'],loc['RLEG'],loc['XBAR']

def ellipse(cx,cy,rx,ry,r=50):
    k=K+(50-r)*.006
    return (f'M{cx} {cy-ry}C{cx+k*rx} {cy-ry} {cx+rx} {cy-k*ry} {cx+rx} {cy}'
            f'C{cx+rx} {cy+k*ry} {cx+k*rx} {cy+ry} {cx} {cy+ry}'
            f'C{cx-k*rx} {cy+ry} {cx-rx} {cy+k*ry} {cx-rx} {cy}'
            f'C{cx-rx} {cy-k*ry} {cx-k*rx} {cy-ry} {cx} {cy-ry}Z')

def arc(cx,cy,rx,ry,a,b,n=4):
    point=lambda v:(cx+rx*math.cos(v),cy+ry*math.sin(v))
    curves=[]
    for i in range(n):
        u=a+(b-a)*i/n;v=a+(b-a)*(i+1)/n;p=point(u);q=point(v);k=4/3*math.tan((v-u)/4)
        curves.append(f'C{p[0]-k*rx*math.sin(u)} {p[1]+k*ry*math.cos(u)} '
                      f'{q[0]+k*rx*math.sin(v)} {q[1]-k*ry*math.cos(v)} {q[0]} {q[1]}')
    return point(a),''.join(curves),point(b)

def open_bowl(w,top,bottom,t,h,aperture):
    cy=(top+bottom)/2;rx=w/2;ry=(bottom-top)/2
    cut=max(top+aperture,top+h+3)
    dy=cy-cut
    outer_a=math.asin(dy/ry);inner_a=math.asin(dy/(ry-h))
    start,out,_=arc(rx,cy,rx,ry,-outer_a,-math.tau+outer_a)
    istart,inside,_=arc(rx,cy,rx-t,ry-h,inner_a,math.tau-inner_a)
    return f'M{start[0]} {start[1]}{out}L{istart[0]} {istart[1]}{inside}Z'

def right_bowl(w,cy,bottom,t,h,left=0,cx=None):
    cx=w*.55 if cx is None else cx;rx=w-cx;ry=bottom/2
    outer=(f'M{left} 0H{cx}C{cx+K*rx} 0 {w} {cy-K*ry} {w} {cy}'
           f'C{w} {cy+K*ry} {cx+K*rx} {bottom} {cx} {bottom}H{left}Z')
    hole=(f'M{left+t} {h}H{cx}C{cx+K*(rx-t)} {h} {w-t} {cy-K*(ry-h)} {w-t} {cy}'
          f'C{w-t} {cy+K*(ry-h)} {cx+K*(rx-t)} {bottom-h} {cx} {bottom-h}H{left+t}Z')
    return outer,hole

def capital(c,loc):
    t,h,r,ap,leg,bar=settings(loc)
    if c=='A':
        # Straight sides and an entirely horizontal crossbar; the counter's
        # sides are parallel to the outside diagonals.
        w=100;side=t*.99;peak=t*.55;xb=max(bar,h+t*1.05+6)
        return (polygon([(0,100),(50-peak,0),(50+peak,0),(100,100),(100-side,100),(100-side-(100-xb)*.34,xb),(side+(100-xb)*.34,xb),(side,100)])
                +polygon([(side+(100-xb+h)*.34,xb-h),(100-side-(100-xb+h)*.34,xb-h),(50,t*1.05)])),w
    if c=='Λ':return polygon([(0,100),(50-t*.55,0),(50+t*.55,0),(100,100),(100-t*.99,100),(50,t*1.05),(t*.99,100)]),100
    if c=='Ξ':return box(0,0,86,h)+box(0,50-h/2,86,h)+box(0,100-h,86,h),86
    if c=='B':
        # A single exterior and two counters sharing exactly one middle bar.
        mid=48;half=h*.45
        # Join the two exterior lobes at the waist; no stacked closing bars.
        cx1=86-(mid+half)/2/.9;cy1=(mid+half)/2
        cy2=(mid-half+100)/2;ry2=(100-mid+half)/2;cx2=90-ry2/.9
        out=(f'M0 0H{cx1}C{cx1+K*(86-cx1)} 0 86 {cy1-K*cy1} 86 {cy1}'
             f'C86 {cy1+K*(mid-cy1)} 77 {mid} 70 {mid}'
             f'C81 {mid} 90 {cy2-K*(cy2-mid)} 90 {cy2}'
             f'C90 {cy2+K*ry2} {cx2+K*(90-cx2)} 100 {cx2} 100H0Z')
        _,hole1=rounded.round_d(86,0,mid+half,t,h*.9)
        _,hole2=rounded.round_d(90,mid-half,100,t,h*.9)
        return out+hole1+hole2,90
    if c=='C':return open_bowl(100,-1,101,t,h,ap+1),100
    if c=='D':
        out,hole=right_bowl(98,50,100,t,h,cx=43)
        return out+hole,98
    if c in 'EF':
        w=86 if c=='E' else 82;mid=77 if c=='E' else 74
        if c=='E':return polygon([(0,0),(w,0),(w,h),(t,h),(t,48-h/2),(mid,48-h/2),(mid,48+h/2),(t,48+h/2),(t,100-h),(w,100-h),(w,100),(0,100)]),w
        return polygon([(0,0),(w,0),(w,h),(t,h),(t,48-h/2),(mid,48-h/2),(mid,48+h/2),(t,48+h/2),(t,100),(0,100)]),w
    if c=='G':
        # One union boundary: the bowl, horizontal bar and descending stem
        # share edges rather than relying on separate overlapping contours.
        w=102;cx=51;cy=50;ry=51;cut=max(-1+ap+1,-1+h+3)
        outer_angle=math.asin((cy-cut)/ry)
        stem_x=w-t;stem_angle=math.acos((stem_x-cx)/cx)
        start,outside,_=arc(cx,cy,cx,ry,-outer_angle,-math.tau+stem_angle,8)
        bar_bottom=49+h*.82
        lower_ry=ry-h
        inner_angle=math.asin((bar_bottom-cy)/lower_ry)
        inner_cut=math.asin((cy-cut)/(ry-h))
        p,inside_lower,_=arc(cx,cy,cx-t,lower_ry,inner_angle,math.pi,4)
        _,inside_upper,_=arc(cx,cy,cx-t,ry-h,math.pi,math.tau-inner_cut,4)
        inside=inside_lower+inside_upper
        d=(f'M{start[0]} {start[1]}{outside}V100H102V49H56V{bar_bottom}'
           f'H{p[0]}{inside}Z')
        return d,w
    if c=='H':return polygon([(0,0),(t,0),(t,49-h/2),(96-t,49-h/2),(96-t,0),(96,0),(96,100),(96-t,100),(96-t,49+h/2),(t,49+h/2),(t,100),(0,100)]),96
    if c=='I':return box(0,0,t,100),t
    if c=='J':
        w=76;cy=68
        return (f'M{w-t} 0H{w}V68C{w} {68+K*33} {38+K*38} 101 38 101C{38-K*38} 101 0 {68+K*33} 0 68H{t}'
                f'C{t} {68+K*(33-h)} {38-K*(38-t)} {101-h} 38 {101-h}'
                f'C{38+K*(38-t)} {101-h} {w-t} {68+K*(33-h)} {w-t} 68Z'),w
    if c=='K':return rounded.k_outline(t,0),100
    if c=='L':return polygon([(0,0),(t,0),(t,100-h),(82,100-h),(82,100),(0,100)]),82
    if c=='M':return polygon([(0,100),(0,0),(t+3,0),(58,100-t*1.55),(113-t,0),(116,0),(116,100),(116-t,100),(116-t,t*1.3),(58+t*.35,100),(58-t*.35,100),(t,t*1.3),(t,100)]),116
    if c=='N':return polygon([(0,100),(0,0),(t+1,0),(96-t,100-t*1.6),(96-t,0),(96,0),(96,100),(96-t-1,100),(t,t*1.6),(t,100)]),96
    if c=='O':return ellipse(51,50,51,51,r)+ellipse(51,50,51-t,51-h,r),102
    if c=='P':
        out,hole=rounded.round_d(86,0,62,t,h*.90)
        return out+hole+box(0,61,t,39),86
    if c=='Q':
        # Both tail sides are parallel offsets of one 45-degree centreline.
        rx=51*.9;ry=51;cx=51*.9;cy=50;ux=uy=math.sqrt(.5);nx=-uy;ny=ux;half=t*.9*.46
        def intersection(offset):
            a=ux*ux/(rx*rx)+uy*uy/(ry*ry)
            b=2*offset*(ux*nx/(rx*rx)+uy*ny/(ry*ry))
            cc=offset*offset*(nx*nx/(rx*rx)+ny*ny/(ry*ry))-1
            distance=(-b+math.sqrt(b*b-4*a*cc))/(2*a)
            x=cx+ux*distance+nx*offset;y=cy+uy*distance+ny*offset
            return math.atan2((y-cy)/ry,(x-cx)/rx)
        a=intersection(-half);b=intersection(half)
        _,first,_=arc(51,50,51,51,0,a,1);root,last,_=arc(51,50,51,51,b,math.pi/2,1)
        end_a=((cx+ux*71-nx*half)/.9,cy+uy*71-ny*half)
        end_b=((cx+ux*71+nx*half)/.9,cy+uy*71+ny*half)
        outer=(f'M51 -1C{51+K*51} -1 102 {50-K*51} 102 50{first}'
               f'L{end_a[0]} {end_a[1]}L{end_b[0]} {end_b[1]}L{root[0]} {root[1]}{last}'
               f'C{51-K*51} 101 0 {50+K*51} 0 50C0 {50-K*51} {51-K*51} -1 51 -1Z')
        return outer+ellipse(51,50,51-t,51-h,r),116
    if c=='R':
        w=88;cy=31;ry=31;rx=ry/.9;cx=w-rx;theta=math.acos((64-cx)/rx)
        _,right,root=arc(cx,cy,rx,ry,0,theta,1);x,y=root
        f=(leg-20)/75;band=t*1.25;end=100
        c1x=x+(end-x)/3+(82-(x+(end-x)/3))*f
        c1y=y+(100-y)/3+(y+1.5-(y+(100-y)/3))*f
        c2x=x+2*(end-x)/3+(89-(x+2*(end-x)/3))*f
        c2y=y+2*(100-y)/3+(86-(y+2*(100-y)/3))*f
        outer=(f'M0 0H{cx}C{cx+K*rx} 0 {w} {cy-K*ry} {w} {cy}{right}'
               f'C{c1x} {c1y} {c2x} {c2y} {end} 100H{end-band}'
               f'C{c2x-band} {c2y} {c1x-band} {c1y} {x-band} {y}H{t}V100H0Z')
        _,hole=rounded.round_d(w,0,62,t,h*.9)
        return outer+hole,100
    if c=='S':return rounded.s_stroke(t)
    if c=='T':return polygon([(0,0),(94,0),(94,h),(47+t/2,h),(47+t/2,100),(47-t/2,100),(47-t/2,h),(0,h)]),94
    if c=='U':return rounded.cup(96,0,101,t),96
    if c=='V':return polygon([(0,0),(t,0),(50,100-t*1.06),(100-t,0),(100,0),(50+t*.58,100),(50-t*.58,100)]),100
    if c=='W':return polygon([(0,0),(t,0),(31,100-t*1.6),(67-t/2,0),(67+t/2,0),(103,100-t*1.6),(134-t,0),(134,0),(103+t*.55,100),(103-t*.55,100),(67,t*1.5),(31+t*.55,100),(31-t*.55,100)]),134
    if c=='X':return polygon([(0,0),(t*1.15,0),(50,50-t*.75),(100-t*1.15,0),(100,0),(50+t*.6,50),(100,100),(100-t*1.15,100),(50,50+t*.75),(t*1.15,100),(0,100),(50-t*.6,50)]),100
    if c=='Y':return polygon([(0,0),(t*1.12,0),(50,58-t*.75),(100-t*1.12,0),(100,0),(50+t/2,61),(50+t/2,100),(50-t/2,100),(50-t/2,61)]),100
    if c=='Z':
        d=rounded.diagonal_width(92,h,t*.9)
        return polygon([(0,0),(92,0),(92,h),(d,100-h),(92,100-h),(92,100),(0,100),(0,100-h),(92-d,h),(0,h)]),92
    raise KeyError(c)

def move(path,sx=1,sy=1,dx=0,dy=0):return path,(sx,0,0,sy,dx,dy)

def lower(c,loc):
    T,H,r,ap,leg,bar=settings(loc);t=T*.88;h=H*.88;w=82;cx=w/2;cy=64.5;ry=36.5
    ring=ellipse(cx,cy,cx,ry,r)+ellipse(cx,cy,cx-t,ry-h,r)
    if c=='a':
        return [rounded.a_outline(t)],82
    if c in 'bdpq':
        stemx=0 if c in 'bp' else w-t;top=0 if c in 'bd' else 28;bottom=100 if c in 'bd' else 127
        return [ring+box(stemx,top,t,bottom-top)],w
    if c=='o':return [ring],w
    if c=='c':return [open_bowl(w,28,101,t,h,ap*.65)],w
    if c=='e':
        return [rounded.e_outline(t)],w
    if c=='f':
        radius=27;cx=43;cy=27;normal=t*.9;ir=radius-normal;ix=ir/.9
        head=(f'M13 100V27C13 {cy-K*radius} {cx-K*30} 0 {cx} 0H61V{normal}H{cx}'
              f'C{cx-K*ix} {normal} {13+t} {cy-K*ir} {13+t} 27V100Z')
        return [head+box(0,28,61,normal)],61
    if c=='g':
        normal=t*.9;radius=41*.9-normal/2;center_y=128-41*.9;right=w-t/2
        bones=[rounded.straight((right,28),(right,center_y))]
        bones+=rounded.circle_arc(41,center_y,radius/.9,radius,0,math.radians(145))
        return [ring+rounded.stroke(bones,normal)],w
    if c in 'hn':
        top=0 if c=='h' else 28
        return [rounded.arch(w,28,100,t)+box(0,top,t,28+w*.9/2-top)],w
    if c=='i':return [box(0,0,t,h)+box(0,28,t,72)],t
    if c=='j':return [box(25,0,t,h)+f'M25 28H{25+t}V99C{25+t} 119 35 128 14 128H0V{128-h}H11C22 {128-h} 25 110 25 98Z'],25+t
    if c=='k':return [rounded.k_outline(t,28)],85
    if c=='l':return [box(0,0,t,100)],t
    if c=='m':
        first=rounded.arch(w,28,100,t);offset=w-t
        return [first+box(0,28,t,w*.9/2),move(first,1,1,offset,0)],w+offset
    if c=='r':
        p,width=rounded.round_r_shoulder(t);return [p],width
    if c=='s':
        p,width=rounded.s_stroke(T,small=True);return [p],width
    if c=='t':return [rounded.t_outline(t,h)],65
    if c=='u':return [rounded.cup(w,28,101,t)],w
    if c in 'vwxz':
        p,width=capital(c.upper(),loc);return [move(p,.82,.72,0,28)],width*.82
    if c=='y':return [rounded.y_outline(t)[0]],88
    raise KeyError(c)

def sharp_s(loc,capital_form=False):
    return rounded.sharp_s(settings(loc)[0])
