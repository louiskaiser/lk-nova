"""Shared round-stroke constructions in the default physical proportion.

Normal stroke widths are measured after the family's 0.9 horizontal transform.
Open cubic strokes use fixed-topology Hermite offsets, so their sides retain
the same normal thickness rather than thinning at arbitrary control points.
"""
import math
from functools import lru_cache

K=.5522847498307936
SX=.9

def box(x,y,w,h):return f'M{x} {y}h{w}v{h}h{-w}Z'
def poly(points):return 'M'+'L'.join(f'{x} {y}' for x,y in points)+'Z'

def circle_arc(cx,cy,rx,ry,start,end,n=3):
    segments=[]
    for i in range(n):
        a=start+(end-start)*i/n;b=start+(end-start)*(i+1)/n;k=4/3*math.tan((b-a)/4)
        p=(cx+rx*math.cos(a),cy+ry*math.sin(a));q=(cx+rx*math.cos(b),cy+ry*math.sin(b))
        segments.append((p,(p[0]-k*rx*math.sin(a),p[1]+k*ry*math.cos(a)),(q[0]+k*rx*math.sin(b),q[1]-k*ry*math.cos(b)),q))
    return segments

def straight(a,b):return a,(a[0]+(b[0]-a[0])/3,a[1]+(b[1]-a[1])/3),(a[0]+2*(b[0]-a[0])/3,a[1]+2*(b[1]-a[1])/3),b

def stroke(segments,width,steps=4):
    return _stroke(tuple(tuple(tuple(p) for p in c) for c in segments),width,steps)

@lru_cache(maxsize=2048)
def _stroke(segments,width,steps=4):
    """Two analytical normal-offset sides with tangent-matched cubic joins."""
    physical=[tuple((x*SX,y) for x,y in segment) for segment in segments]
    sides=[]
    for sign in (1,-1):
        curves=[]
        for p0,p1,p2,p3 in physical:
            def evaluate(t):
                u=1-t
                p=tuple(u*u*u*p0[i]+3*u*u*t*p1[i]+3*u*t*t*p2[i]+t*t*t*p3[i] for i in (0,1))
                d=tuple(3*u*u*(p1[i]-p0[i])+6*u*t*(p2[i]-p1[i])+3*t*t*(p3[i]-p2[i]) for i in (0,1))
                dd=tuple(6*u*(p2[i]-2*p1[i]+p0[i])+6*t*(p3[i]-2*p2[i]+p1[i]) for i in (0,1))
                speed=math.hypot(*d)
                if speed<1e-7:raise ValueError('Stationary stroke centreline')
                n=(-d[1]/speed,d[0]/speed);dot=d[0]*dd[0]+d[1]*dd[1]
                dn=(-dd[1]/speed-n[0]*dot/(speed*speed),dd[0]/speed-n[1]*dot/(speed*speed))
                delta=width/2*sign
                if (d[0]*(d[0]+delta*dn[0])+d[1]*(d[1]+delta*dn[1]))<=0:
                    raise ValueError(('Offset fold',p0,p1,p2,p3,width,t))
                return (p[0]+delta*n[0],p[1]+delta*n[1]),(d[0]+delta*dn[0],d[1]+delta*dn[1])
            for j in range(steps):
                a=j/steps;b=(j+1)/steps;p,dp=evaluate(a);q,dq=evaluate(b);dt=(b-a)/3
                curves.append((p,(p[0]+dp[0]*dt,p[1]+dp[1]*dt),(q[0]-dq[0]*dt,q[1]-dq[1]*dt),q))
        sides.append(curves)
    def point(p):return f'{p[0]/SX} {p[1]}'
    left,right=sides
    result='M'+point(left[0][0])
    for p,c1,c2,q in left:result+='C'+point(c1)+' '+point(c2)+' '+point(q)
    result+='L'+point(right[-1][-1])
    for p,c1,c2,q in reversed(right):result+='C'+point(c2)+' '+point(c1)+' '+point(p)
    return result+'Z'

def round_d(w,top,bottom,t,h):
    """Right bowl with physically circular outer and inner end radii."""
    ry=(bottom-top)/2;rx=ry/SX;cx=w-rx;cy=(top+bottom)/2
    thick=min(h,(bottom-top-9)/2);ri=ry-thick;rix=ri/SX
    outer=(f'M0 {top}H{cx}C{cx+K*rx} {top} {w} {cy-K*ry} {w} {cy}'
           f'C{w} {cy+K*ry} {cx+K*rx} {bottom} {cx} {bottom}H0Z')
    counter=(f'M{t} {top+thick}H{cx}C{cx+K*rix} {top+thick} {cx+rix} {cy-K*ri} {cx+rix} {cy}'
             f'C{cx+rix} {cy+K*ri} {cx+K*rix} {bottom-thick} {cx} {bottom-thick}H{t}Z')
    return outer,counter

def arch(w,top,bottom,t):
    rx=w/2;ry=rx*SX;cx=rx;cy=top+ry;normal=t*SX;ir=ry-normal;ix=rx-t
    d=f'M0 {bottom}V{cy}'
    for p,a,b,q in circle_arc(cx,cy,rx,ry,math.pi,math.tau,6):
        d+=f'C{a[0]} {a[1]} {b[0]} {b[1]} {q[0]} {q[1]}'
    d+=f'V{bottom}H{w-t}V{cy}'
    for p,a,b,q in circle_arc(cx,cy,ix,ir,math.tau,math.pi,6):
        d+=f'C{a[0]} {a[1]} {b[0]} {b[1]} {q[0]} {q[1]}'
    return d+f'V{bottom}Z'

def cup(w,top,bottom,t):
    rx=w/2;ry=rx*SX;cx=rx;cy=bottom-ry;normal=t*SX;ir=ry-normal;ix=rx-t
    return (f'M0 {top}H{t}V{cy}C{t} {cy+K*ir} {cx-K*ix} {bottom-normal} {cx} {bottom-normal}'
            f'C{cx+K*ix} {bottom-normal} {w-t} {cy+K*ir} {w-t} {cy}V{top}H{w}V{cy}'
            f'C{w} {cy+K*ry} {cx+K*rx} {bottom} {cx} {bottom}'
            f'C{cx-K*rx} {bottom} 0 {cy+K*ry} 0 {cy}Z')

def k_outline(t,top):
    """One union outline; diagonal normal widths stay stable with weight."""
    w=100 if top==0 else 85;tip=w-2
    # Anchor both diagonal bands inside the spine, retaining a substantial
    # connection at the light end of the animation.
    nominal=22 if top==0 else 22*.88
    anchor=t-.5*max(0,nominal-t)
    junction=top+(100-top)*.68;m=(junction-top)/(tip-anchor)
    normal=t*SX;dy=normal*math.sqrt(1+(m/SX)**2)
    lower_start=top+(100-top)*.49;n=(100-lower_start)/(w-anchor)
    dy2=normal*math.sqrt(1+(n/SX)**2)
    fork=(junction+m*anchor-100+n*w)/(m+n)
    fy=junction-m*(fork-anchor)
    return poly([(0,0),(t,0),(t,junction-m*(t-anchor)-dy),(tip-dy/m,top),(tip,top),
                 (fork,fy),(w,100),(w-dy2/n,100),(t,lower_start+n*(t-anchor)+dy2),(t,100),(0,100)])

def a_outline(t):
    """One true circular roof, trimmed before it meets the lower bowl."""
    normal=t*SX;cx=41;cy=64.9;radius=36.9;rx=41;ir=radius-normal;ix=ir/SX
    cut=50;neck=55
    start=math.pi+math.asin((cy-cut)/radius)
    outside=circle_arc(cx,cy,rx,radius,start,math.tau,6)
    p=outside[0][0];d=f'M{p[0]} {p[1]}'+arc_commands(outside)
    bowl_r=23;bc=bowl_r/SX;by=78;th=normal*.88;hole_r=bowl_r-th;hole_x=hole_r/SX
    d+=(f'V101H{bc}C{bc-K*bc} 101 0 {by+K*bowl_r} 0 {by}'
        f'C0 {by-K*bowl_r} {bc-K*bc} 55 {bc} 55')
    right_angle=math.asin((neck-cy)/ir)
    left_angle=-math.pi-math.asin((cut-cy)/ir)
    inner=circle_arc(cx,cy,ix,ir,right_angle,left_angle,5)
    d+=f'H{inner[0][0][0]}'+arc_commands(inner)+'Z'
    hole=(f'M{82-t} {by-hole_r}H{bc}C{bc-K*hole_x} {by-hole_r} {bc-hole_x} {by-K*hole_r} {bc-hole_x} {by}'
          f'C{bc-hole_x} {by+K*hole_r} {bc-K*hole_x} {by+hole_r} {bc} {by+hole_r}H{82-t}Z')
    return d+hole

def e_outline(t):
    """Single connected exterior; horizontal bar and closed upper counter."""
    cx=41;cy=64.5;rx=41;ry=36.5;normal=t*SX;ix=rx-t;ir=ry-normal
    bar_y=cy-normal*.4;bar_h=normal*.8;cut=88
    angle=math.asin((cut-cy)/ry)
    outer=circle_arc(cx,cy,rx,ry,angle,math.tau,6)
    d='M'+str(outer[0][0][0])+' '+str(outer[0][0][1])
    for p,a,b,q in outer:d+=f'C{a[0]} {a[1]} {b[0]} {b[1]} {q[0]} {q[1]}'
    d+=f'V{bar_y+bar_h}H{t}'
    # Continue around the lower inner bowl with an exact ellipse arc.
    inner_start=math.pi-math.asin((bar_y+bar_h-cy)/ir)
    x=cx+ix*math.cos(inner_start)
    d=d[:-len(f'H{t}')]+f'H{x}'
    inside=circle_arc(cx,cy,ix,ir,inner_start,angle,5)
    for p,a,b,q in inside:d+=f'C{a[0]} {a[1]} {b[0]} {b[1]} {q[0]} {q[1]}'
    d+='Z'
    # The top counter has a flat bottom on the bar and a smooth round roof.
    y=bar_y;ang=math.asin((y-cy)/ir)
    start=math.pi-ang;end=math.tau+ang
    arc=circle_arc(cx,cy,ix,ir,start,end,6)
    p=arc[0][0];hole=f'M{p[0]} {p[1]}'
    for p,a,b,q in arc:hole+=f'C{a[0]} {a[1]} {b[0]} {b[1]} {q[0]} {q[1]}'
    return d+hole+'Z'

def t_outline(t,h):
    normal=t*SX;radius=25;rx=radius/SX;cx=15+rx;cy=100-radius
    ir=radius-normal;ix=ir/SX
    return (f'M15 8H{15+t}V28H65V{28+h}H{15+t}V{cy}'
            f'C{15+t} {cy+K*ir} {cx-K*ix} {100-normal} {cx} {100-normal}H65V100H{cx}'
            f'C{cx-K*rx} 100 15 {cy+K*radius} 15 {cy}V{28+h}H0V28H15Z')

@lru_cache(maxsize=1)
def round_s_centerline():
    """C2 cubic B-spline, trimmed at its two open terminals."""
    points=[(84,70),(84,43)]
    points += [(48+36*math.cos(math.radians(a)),31+23*math.sin(math.radians(a))) for a in [0,-45,-90,-135,-180,-225]]
    points += [(48+37*math.cos(math.radians(a)),70+23*math.sin(math.radians(a))) for a in [-45,0,45,90,135,180]]
    points += [(11,43),(11,30)]
    curves=[]
    for a,b,c,d in zip(points,points[1:],points[2:],points[3:]):
        curves.append((tuple((a[i]+4*b[i]+c[i])/6 for i in (0,1)),tuple((2*b[i]+c[i])/3 for i in (0,1)),tuple((b[i]+2*c[i])/3 for i in (0,1)),tuple((b[i]+4*c[i]+d[i])/6 for i in (0,1))))
    def split(curve,t):
        def mix(a,b):return tuple((1-t)*a[i]+t*b[i] for i in (0,1))
        a,b,c=mix(curve[0],curve[1]),mix(curve[1],curve[2]),mix(curve[2],curve[3])
        d,e=mix(a,b),mix(b,c);f=mix(d,e)
        return (curve[0],a,d,f),(f,e,c,curve[3])
    def trim(cs,y,front):
        for i in (range(len(cs)) if front else reversed(range(len(cs)))):
            curve=cs[i]
            if curve[0][1]>=y>=curve[3][1]:
                lo,hi=0,1
                for _ in range(50):
                    mid=(lo+hi)/2
                    if split(curve,mid)[0][-1][1]>y:lo=mid
                    else:hi=mid
                a,b=split(curve,(lo+hi)/2)
                return [b]+cs[i+1:] if front else cs[:i]+[a]
        raise ValueError('S terminal outside curve')
    return tuple(trim(trim(curves,30,True),72,False))

def s_stroke(t,small=False):
    # Preserve the lowercase construction; the capital below uses circular
    # turns and true ellipse arcs for a rounder upper and lower bowl.
    bones=[((82,30),(82,17),(67,9),(48,9)),((48,9),(28,9),(11,17),(11,30)),
           ((11,30),(11,44.7142857143),(27,47),(48,50)),
           ((48,50),(69,53),(84,55.1428571429),(84,72)),
           ((84,72),(84,85),(68,92),(48,92)),((48,92),(29,92),(12,84),(12,71))]
    normal=t*SX
    if not small:
        # Normalize the smooth centreline to the cap/foot extrema. Its inner
        # and outer sides come from the same analytical normal offsets.
        x1,y1,x2,y2=13.987367448708273,10.245514677569801,82.13278618995717,90.7544853224302
        sx=(96-normal/SX)/(x2-x1);sy=(102-normal)/(y2-y1)
        bones=[tuple(((x-x1)*sx+normal/(2*SX),(y-y1)*sy+normal/2-1) for x,y in c) for c in round_s_centerline()]
        return stroke(bones,normal,steps=8),96
    if small:
        # Optical compensation for the compact double curve preserves its
        # round counters without a squeezed inner offset at black weights.
        normal*=.75;sy=(73-normal)/83;dy=28+normal/2-9*sy;sx=(68-normal)/(73*SX)
        dx=normal/(2*SX)-11*sx
        bones=[tuple((x*sx+dx,y*sy+dy) for x,y in c) for c in bones]
    return stroke(bones,normal),68/SX if small else 96

def round_r_shoulder(t):
    w=82;cx=41;cy=28+41*SX;ry=41*SX;inner=ry-t*SX;cut=55
    oa=math.acos((cut-cx)/41);ia=math.acos((cut-cx)/(41-t))
    outside=circle_arc(cx,cy,41,ry,math.pi,math.tau-oa)
    inside=circle_arc(cx,cy,41-t,inner,math.tau-ia,math.pi)
    def end(c):return c[-1][-1]
    p=outside[0][0];d=f'M0 100L{p[0]} {p[1]}'
    for a,b,c,q in outside:d+=f'C{b[0]} {b[1]} {c[0]} {c[1]} {q[0]} {q[1]}'
    p=inside[0][0];d+=f'L{p[0]} {p[1]}'
    for a,b,c,q in inside:d+=f'C{b[0]} {b[1]} {c[0]} {c[1]} {q[0]} {q[1]}'
    return d+'V100Z'+box(0,28,t,cy-28),58

def diagonal_width(w,h,normal):
    height=100-2*h;width=w*SX;a=height*height-normal*normal;b=2*normal*normal*width;c=-normal*normal*(height*height+width*width)
    return (-b+math.sqrt(b*b-4*a*c))/(2*a)/SX

def question(t):
    bones=[((12,26),(12,13),(27,9),(44,9)),((44,9),(64,9),(77,17),(77,29)),
           ((77,29),(77,42),(62,47),(51,55)),((51,55),(45.5,59),(44,63),(44,70))]
    normal=t*SX
    return stroke(bones,normal)+box(44-t/2,100-normal,t,normal),89

def sharp_s(t):
    """Rounded upper roof; the lower bowl is exactly the 0.810 construction."""
    cx=49;cy=75;rx=37;ry=26;bottom_h=t*SX*.75
    ix=rx-t;ir=ry-bottom_h;right=cx+rx;inner_right=cx+ix
    head_x=39.5;head_y=30;head_rx=39.5;head_ry=31
    inner_rx=head_rx-t;inner_ry=inner_rx*SX*.86
    inner_top=head_y-inner_ry;inner_bottom=head_y+inner_ry;head_right=79-t
    d=(f'M0 100V30C0 {head_y-K*head_ry} {head_x-K*head_rx} -1 {head_x} -1'
       f'C{head_x+K*head_rx} -1 79 {head_y-K*head_ry} 79 30C79 39 73 44 62 49'
       f'C76 52 {right} 61 {right} {cy}'
       f'C{right} {cy+K*ry} {cx+K*rx} 101 {cx} 101H34V{101-bottom_h}H{cx}'
       f'C{cx+K*ix} {101-bottom_h} {inner_right} {cy+K*ir} {inner_right} {cy}'
       f'C{inner_right} {cy-K*ir} {cx+K*ix} {cy-ir} {cx} {cy-ir}H36V{inner_bottom}H{head_x}'
       f'C{head_x+K*inner_rx} {inner_bottom} {head_right} {head_y+K*inner_ry} {head_right} {head_y}'
       f'C{head_right} {head_y-K*inner_ry} {head_x+K*inner_rx} {inner_top} {head_x} {inner_top}'
       f'C{head_x-K*inner_rx} {inner_top} {t} {head_y-K*inner_ry} {t} {head_y}V100Z')
    return d,88

def y_outline(t):
    """Parallel arms and a constant-normal descender; flat x-height cuts."""
    normal=t*SX
    bones=[((40,106),(35,116.8333333333),(26,119),(12,119))]
    d=stroke(bones,normal)
    p,p1=bones[0][:2];dx=(p1[0]-p[0])*SX;dy=p1[1]-p[1];speed=math.hypot(dx,dy)
    nx=-dy/speed;ny=dx/speed
    left=(p[0]+nx*normal/2/SX,p[1]+ny*normal/2)
    right=(p[0]-nx*normal/2/SX,p[1]-ny*normal/2)
    top_left=left[0]+(28-left[1])*(-36/78)
    top_right=right[0]+(28-right[1])*(-36/78)
    first=d.index('C')
    d=f'M{top_left} 28L{left[0]} {left[1]}'+d[first:-1]+f'L{top_right} 28Z'
    slope=.5;band=normal*math.sqrt(1+(slope*SX)**2)/SX
    join_y=94;join_x=76+(join_y-28)*(-36/78)
    left_top=join_x-slope*(join_y-28)-band/2
    arm=poly([(left_top,28),(left_top+band,28),(join_x+band/2,join_y),(join_x-band/2,join_y)])
    return d+arm,88

def arc_commands(segments):
    return ''.join(f'C{a[0]} {a[1]} {b[0]} {b[1]} {q[0]} {q[1]}' for p,a,b,q in segments)

def capsule(w,top,bottom,inset=0):
    radius=w*SX/2;cx=w/2;rx=cx-inset;ry=radius-inset*SX
    upper=top+radius;lower=bottom-radius
    d=f'M{inset} {lower}V{upper}'
    d+=arc_commands(circle_arc(cx,upper,rx,ry,math.pi,math.tau,6))
    d+=f'V{lower}'+arc_commands(circle_arc(cx,lower,rx,ry,0,math.pi,6))
    return d+'Z'

def round_digit(c,t,h,ellipse):
    normal=t*SX
    if c=='0':return [capsule(88,-1,101)+capsule(88,-1,101,t)],88
    if c=='1':
        rise=22/33;delta=normal*math.sqrt(1+(rise/SX)**2)
        return [poly([(7,22),(40,0),(40+t,0),(40+t,100),(40,100),(40,delta),(7,22+delta)])],40+t
    if c=='2':
        angle=.92;cx=44;cy=25+normal/2;radius=26
        bones=circle_arc(cx,cy,radius/SX,radius,math.pi,math.tau+angle,9)
        x,y=bones[-1][-1];base=100-normal
        ax=x-normal/2*math.cos(angle)/SX;ay=y-normal/2*math.sin(angle)
        bx=x+normal/2*math.cos(angle)/SX;by=y+normal/2*math.sin(angle)
        left=ax-(base-ay)*math.tan(angle)/SX
        right=bx-(base-by)*math.tan(angle)/SX
        head,tail=stroke(bones,normal).split('L',1)
        # Continue both sides directly into the foot, rather than putting
        # a separate rectangle underneath the diagonal.
        d=head+f'L{left} {base}V100H87V{base}H{right}L'+tail
        return [d],89
    if c=='3':
        # Two true elliptical sweeps sharing the same central bar.
        ry=25.5-normal/4;upper_y=24.5+normal/4;lower_y=75.5-normal/4
        upper=circle_arc(46,upper_y,38-t/2,ry,math.pi,math.tau+math.pi/2,9)
        upper.append(straight((46,50),(34,50)))
        lower=[straight((34,50),(46,50))]
        lower+=circle_arc(46,lower_y,42-t/2,ry,-math.pi/2,math.pi,9)
        return [stroke(upper,normal)+stroke(lower,normal)],92
    if c=='4':
        slope=64/54;dy=normal*math.sqrt(1+(slope/SX)**2);dx=dy/slope
        out=poly([(54,0),(54+t,0),(54+t,64),(96,64),(96,64+normal),(54+t,64+normal),(54+t,100),(54,100),(54,64+normal),(0,64+normal),(0,64)])
        hole=poly([(dx,64),(54,64),(54,dy)])
        return [out+hole],96
    if c=='5':
        # The vertical meets a horizontal shoulder before the rounded bowl.
        cx=47;cy=71;rx=41;ry=30;ir=ry-normal*.82;ix=rx-t
        d=f'M5 0H83V{normal}H{5+t}V41H{cx}'
        d+=arc_commands(circle_arc(cx,cy,rx,ry,-math.pi/2,math.pi,9))
        d+=f'H{cx-ix}'+arc_commands(circle_arc(cx,cy,ix,ir,math.pi,-math.pi/2,9))
        d+='H5Z'
        return [d],90
    if c in '69':
        # Circular bowl and circular shoulder share the same left tangent.
        cx=46;cy=65;rx=40;ry=36
        ring=ellipse(cx,cy,rx,ry)+ellipse(cx,cy,rx-t,ry-normal)
        shoulder=[straight((6+t/2,65),(6+t/2,34))]
        shoulder+=circle_arc(46,34,40-t/2,35-normal/2,math.pi,math.tau-.4,8)
        d=ring+stroke(shoulder,normal)
        return ([d] if c=='6' else [(d,(-1,0,0,-1,92,100))]),92
    if c=='8':
        cx=44;theta=.7;k=.15
        up=circle_arc(cx,27,35,28,-math.pi/2,theta,5)
        low=circle_arc(cx,71,39,30,-theta,math.pi+theta,8)
        last=circle_arc(cx,27,35,28,math.pi-theta,3*math.pi/2,5)
        p=up[-1][-1];q=low[0][0]
        c1=(p[0]-k*35*math.sin(theta),p[1]+k*28*math.cos(theta))
        c2=(q[0]-k*39*math.sin(theta),q[1]-k*30*math.cos(theta))
        d='M44 -1'+arc_commands(up)+f'C{c1[0]} {c1[1]} {c2[0]} {c2[1]} {q[0]} {q[1]}'+arc_commands(low)
        p=low[-1][-1];q=last[0][0]
        c1=(p[0]+k*39*math.sin(theta),p[1]-k*30*math.cos(theta))
        c2=(q[0]+k*35*math.sin(theta),q[1]+k*28*math.cos(theta))
        d+=f'C{c1[0]} {c1[1]} {c2[0]} {c2[1]} {q[0]} {q[1]}'+arc_commands(last)+'Z'
        d+=ellipse(44,27,35-t,28-normal*.82)+ellipse(44,71,39-t,30-normal*.82)
        return [d],83
    if c=='7':
        # A rectangular top and one parallel diagonal, with a flat baseline.
        slope=(100-normal)/57;dx=normal*math.sqrt(1+(slope/SX)**2)/slope
        return [poly([(0,0),(96,0),(96,normal),(39,100),(39-dx,100),(96-dx,normal),(0,normal)])],96
    raise KeyError(c)
