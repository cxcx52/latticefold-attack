"""Literal Definition 4.3 / Definition 4.4 / Pi_batch soundness counterexample.

A fully algebraic small instance.  It verifies the genuine range sumcheck,
CCS endpoint, commitment and *printed reversed-coordinate* target relation.
No lattice-hardness claim is inferred from toy A.  A separate union bound
establishes absent source witnesses with overwhelming probability for a
cryptographic-size family.
"""
from random import Random
q=257; d=2; b=2; k=6; B=b**k; ell=2; n_c=4; m=ell*n_c; nu=3
assert m==1<<nu and B**ell >= q/2 and B<q/2
S=[(u,v) for u in (-1,0,1,2) for v in (-1,0,1,2)]
assert 2*k*4*(b-1)<B
zero=(0,0); one=(1,0)
def add(x,y):return ((x[0]+y[0])%q,(x[1]+y[1])%q)
def sub(x,y):return ((x[0]-y[0])%q,(x[1]-y[1])%q)
def mul(x,y):return ((x[0]*y[0]-x[1]*y[1])%q,(x[0]*y[1]+x[1]*y[0])%q)
def smul(a,x):return ((a*x[0])%q,(a*x[1])%q)
def eq(a,x):return (1-a)*(1-x)+a*x

def gadget(f):
    return tuple(add(f[i*ell],smul(B,f[i*ell+1])) for i in range(n_c))

f=[zero for _ in range(m)]
f[0]=one; f[4]=one
assert gadget(f)==(one,zero,one,zero)
# Public split first part claims x_ccs,1=(0,1); actual first two Gf coords are (1,0).
public_x=zero; public_h=one; source_private=(one,zero)
source_z=(public_x,public_h,*source_private)
assert source_z==(zero,one,one,zero)
# Nontrivial degree-two CCS gate is (first gadget coord)*(second gadget coord)=0.
# M1, M2 each have a nonzero entry on row 0 only.
assert mul(source_z[0],source_z[1])==zero
assert mul(gadget(f)[0],gadget(f)[1])==zero
# Real Ajtai-shaped homomorphism (toy rank/size, no computational security claim).
rng=Random(20261123)
A=[[ (rng.randrange(q),rng.randrange(q)) for _ in range(m)] for _ in range(2)]
def commit(f):
    return tuple(__import__('functools').reduce(add,(mul(a,x) for a,x in zip(row,f)),zero) for row in A)
yprime=commit(f)
# Coefficient transform under roots +/-16: NTT(hat1)=(1,0)
hat1=(129,249)
assert ((hat1[0]+16*hat1[1])%q,(hat1[0]-16*hat1[1])%q)==(1,0)
assert mul(mul(hat1,hat1),hat1)==hat1

def F(xs):  # MLE of the one nonzero split digit coefficient table
    return smul(((1-xs[0])*(1-xs[1]))%q,hat1)
def eq_beta(beta,x):
    r=1
    for a,v in zip(beta,x):r=r*eq(a,v)%q
    return r
def poly_range(x):return mul(mul(x,sub(x,one)),add(x,one))
def g(beta,x,mu):return smul(mu*eq_beta(beta,x)%q,poly_range(F(x)))
for j in range(m):
    bits=tuple((j>>v)&1 for v in range(nu))
    assert poly_range(F(bits))==zero

def honest_round(beta,prefix,x,mu):
    remain=nu-len(prefix)-1
    ans=zero
    for mask in range(1<<remain):
        suffix=tuple((mask>>v)&1 for v in range(remain))
        ans=add(ans,g(beta,tuple(prefix)+(x,)+suffix,mu))
    return ans
# Transcript for all sumcheck challenges (actual ring equations, not only Boolean values).
beta=(7,11,13); r=(21,31,42); mu=33; gamma=19
claim=zero
for j in range(nu):
    h=lambda x:honest_round(beta,r[:j],x,mu)
    assert add(h(0),h(1))==claim,(j,'sumcheck failure')
    claim=h(r[j])
assert claim==g(beta,r,mu)
# Nonlinear CCS endpoint: M1(Gf)=eq(0,r), M2(Gf)=0, hence product zero,
# matching the source-CCS polynomial zero.
eta1=smul((1-r[0])*(1-r[1])*(1-r[2])%q,one)
eta2=zero
assert mul(eta1,eta2)==zero
# The endpoint also uses the true range value and the true transformed MLE.
theta=F(r)
assert claim==smul(mu*eq_beta(beta,r)%q,poly_range(theta))
for rho in S:
    # Zero accumulator inputs; one nonzero split digit.
    fo=[mul(tuple(v%q for v in rho),x) for x in f]
    go=gadget(fo); rr=tuple(v%q for v in rho)
    assert go==(rr,zero,rr,zero),('G product',rho)
    yo=tuple(mul(rr,y) for y in yprime)
    assert commit(fo)==yo
    # Figure 6 public output is xw=(x,h)=(0,rho).
    xw=(zero,rr)
    # Printed Definition 4.3 instead uses z=(w,h,x), where w is the suffix.
    w=go[2:]
    z_target=(*w,xw[1],xw[0])
    assert z_target==go,('target gadget',rho)
    # Independent transformed-MLE check. The verifier's RotSum sends
    # NTT(theta)=(weight,0) to (rho.a*weight,rho.b*weight).
    weight=((1-r[0])*(1-r[1]))%q
    claimed_ntt=(rho[0]*weight%q,rho[1]*weight%q)
    independently_computed_ntt=[0,0]
    for index, ring_element in enumerate(fo):
        bits=tuple((index>>j)&1 for j in range(nu))
        coef=1
        for bit,point in zip(bits,r):coef=coef*eq(point,bit)%q
        for t in range(2):
            independently_computed_ntt[t]=(independently_computed_ntt[t]+coef*ring_element[t])%q
    assert claimed_ntt==tuple(independently_computed_ntt)
    # Independent linearized CCS target channels: both M_j have only row 0.
    row0_weight=((1-r[0])*(1-r[1])*(1-r[2]))%q
    public_u=(mul(rr,eta1),mul(rr,eta2))
    actual_u=(smul(row0_weight,go[0]),smul(row0_weight,go[1]))
    assert public_u==actual_u
    # The source aggregate first two coordinates are (0,1), NOT Gf's (1,0).
    assert gadget(f)[:2]!=(public_x,public_h)
print('PASS: genuine degree-two CCS, all sumcheck rounds, nonlinear endpoint,')
print('      and target relation for all',len(S),'folding challenges.')
print('SOURCE claimed public prefix:',(public_x,public_h))
print('SOURCE actual public prefix: ',gadget(f)[:2])
print('OUTPUT always satisfies literal z=(w,h,x) rather than (x,h,w).')
print('Toy A does not certify absent alternative source opening; use the parameterized union bound.')
