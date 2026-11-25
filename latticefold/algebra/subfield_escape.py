#!/usr/bin/env python3
"""Exact small-parameter algebra certificate for a CONDITIONAL F_q -> R_q
semantic mismatch. This is NOT an attack on LatticeFold's native R_q-CCS
knowledge soundness theorem: the source statement is true in R_q.
"""
from itertools import product

q, d = 269, 4
b, k, B = 2, 6, 64
m, nc, ell_in = 8, 4, 1
S = tuple(range(1,5))

def add(a,b): return tuple((x+y)%q for x,y in zip(a,b))
def neg(a): return tuple((-x)%q for x in a)
def mul(a,b):
    out=[0]*d
    for i,ai in enumerate(a):
        for j,bj in enumerate(b):
            pos=i+j
            out[pos%d]=(out[pos%d]+(ai*bj if pos<d else -ai*bj))%q
    return tuple(out)
def scalar(n): return (n%q,)+(0,)*(d-1)
zero, one, two = scalar(0), scalar(1), scalar(2)

assert q%8==5
assert pow(2,(q-1)//2,q)==q-1   # 2 not square in F_q
sqrt_two=(0,1,0,q-1)            # X-X^3 in F_q[X]/(X^4+1)
assert mul(sqrt_two,sqrt_two)==two
assert sqrt_two!=scalar(0) and sqrt_two!=scalar(1)

# A conventional signed-opening for a (4 x 8) gadget G = I_4 tensor [1,64].
# Coefficient range is centered in (-q/2, q/2].
zz=(zero, one, sqrt_two, zero)
f=(zero,zero, one,zero, sqrt_two,zero, zero,zero)

def gadget(v):
    return tuple(add(v[2*j],mul(scalar(B),v[2*j+1])) for j in range(4))

def cnorm(a):return max(abs(c if c<q/2 else c-q) for c in a)
assert gadget(f)==zz
assert max(map(cnorm,f))==1 < B < q/2
assert B**(m//nc)>=q/2
T=max(S)
assert 2*k*T*(b-1)<B
assert all((a-c)%q for a,c in product(S,repeat=2) if a!=c)

# CCS: one nontrivial row from the two matrices M_1 selecting private w,
# and M_2 selecting homogenizing 1. Its relation is w^2-2*h=0.
ccs_residual=add(mul(zz[2],zz[2]),neg(mul(two,zz[1])))
assert ccs_residual==zero

# In contrast, the *base-field* target ∃u ∈ F_q: u^2-2=0 is empty.
assert all((u*u-2)%q !=0 for u in range(q))

# A separate CRT/Boolean warning: b(b-1)=0 has a nontrivial ring root.
i=next(z for z in range(q) if z*z%q==q-1)
invi=pow(i,-1,q)
e=(pow(2,-1,q),0,(pow(2,-1,q)*invi)%q,0)
assert mul(e,add(e,neg(one)))==zero
assert e!=zero and e!=one

print('PASS: q=%d (q mod 8 = %d), R=F_q[X]/(X^4+1)'%(q,q%8))
print('Base field: x^2=2 has NO solution (Legendre symbol=-1)')
print('Ring: s=X-X^3 satisfies s^2=2 exactly')
print('CCS witness z=(0,1,s,0) and short gadget opening ||f||∞=1 are valid')
print('Fold parameter numeric check 2*k*T*(b-1)=%d < B=%d'%(2*k*T*(b-1),B))
print('Nontrivial ring idempotent coefficients:',e,'; e(e-1)=0')
print('IMPORTANT: source R_q-CCS instance IS valid; not a theorem 4.1 break')
