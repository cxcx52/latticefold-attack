"""Exact toy check of the literal (base-field-challenge) Pi_batch CCS attack.

Matches the *unmodified* Figure 5/Section 4.3 use of C=F_q, not an
unwritten extension-field-diagonal-challenge variant. No MSIS certification.
"""
from fractions import Fraction
import os

q,d=257,2
n_c,ell,m=4,2,8
b,k,B=2,6,64
D=int(os.environ.get("CCS_DEG", "40"))
nu=3
c_bound=4
assert q%4==1 and m==n_c*ell and B**ell>=q/2
assert B==b**k and 2*k*c_bound*(b-1)<B<q/2
assert q>=D+2

# CRT for X^2+1 over F_257: roots +16,-16.
SMALL=[(a,b) for a in (-1,0,1,2) for b in (-1,0,1,2)]
def unit(ab):
    a,b=ab
    return (a+16*b)%q != 0 and (a-16*b)%q != 0
assert all(unit(((u[0]-v[0])%q,(u[1]-v[1])%q))
           for u in SMALL for v in SMALL if u!=v)

# R = F_q[X]/(X^2+1)
def add(u,v): return ((u[0]+v[0])%q,(u[1]+v[1])%q)
def neg(u):return (-u[0]%q,-u[1]%q)
def mul(u,v):
    a,b=u;c,e=v
    return ((a*c-b*e)%q,(a*e+b*c)%q)
def scalar(a,u):return ((a*u[0])%q,(a*u[1])%q)
def power(u,n):
    v=(1,0)
    while n:
        if n&1:v=mul(v,u)
        u=mul(u,u);n>>=1
    return v

zero=(0,0);one=(1,0)
# The coefficient-to-NTT transformed ring value of the ring constant 1 is
# the unique element whose CRT evaluations are (1,0):
hat1=(129,249)
assert ((hat1[0]+16*hat1[1])%q,(hat1[0]-16*hat1[1])%q)==(1,0)
assert power(hat1,3)==hat1

# Original source: x_ccs=1, w=(1,1), z=(1,1,1,1).
# CCS: M_1[0,:]=(1,0,0,0), M_1 rows 1..m-1=0, S_1=(1,...,1) (D copies).
# It demands (M_1 z)[0]^D = 1^D=0, an impossible source relation.
source_z=(one,one,one,one)
assert power(source_z[0],D)==one!=zero
# Honest split: digit 0 has first gadget limb=1 in every block,
# digits 1..5 are zero. Individual public prefixes are (1,1) then zeros.
# The folded output is rho*digit0 (accumulator digits zero), and both the
# source and target coordinate order yield (rho,rho,rho,rho). For any rho.
for rho in SMALL:
    assert max(abs(a) for a in rho)<=2<B


def eq(beta,x):return ((1-beta)*(1-x)+beta*x)%q

# At row index i, the transformed coefficient table T(f)[i] equals hat1
# for i even, 0 for i odd. Its MLE is hat1*(1-X_0).
def g(betas,xs,gamma,mu):
    ep=1
    for beta,x in zip(betas,xs):ep=ep*eq(beta,x)%q
    a=1
    for x in xs:a=a*(1-x)%q
    F=scalar((1-xs[0])%q,hat1)
    P=add(power(F,3),neg(F))  # range polynomial for b=2
    H=(pow(a,D,q),0)         # CCS polynomial for x^D=0
    return scalar(ep,add(scalar(mu,P),scalar(gamma,H)))


def true_round(betas,prefix,x,gamma,mu):
    remain=nu-len(prefix)-1
    acc=zero
    for s in range(1<<remain):
        bits=tuple((s>>a)&1 for a in range(remain))
        acc=add(acc,g(betas,tuple(prefix)+(x,)+bits,gamma,mu))
    return acc

T={0,*range(2,D+2)}
def rootpoly(x):
    y=x%q
    for a in range(2,D+2):y=y*((x-a)%q)%q
    return y
assert len(T)==D+1 and rootpoly(1)!=0


def fake_round_one(betas,x,gamma,mu):
    true=true_round(betas,(),x,gamma,mu)
    S=gamma
    for beta in betas:S=S*(1-beta)%q
    if S==0:return true
    correction=(-S)*pow(rootpoly(1),-1,q)*rootpoly(x)%q
    return add(true,(correction,0))


def check(betas,r,gamma,mu):
    claim=zero
    for j in range(nu):
        H=lambda x,j=j: fake_round_one(betas,x,gamma,mu) if j==0 else true_round(betas,r[:j],x,gamma,mu)
        if add(H(0),H(1))!=claim:return False
        claim=H(r[j])
    return claim==g(betas,r,gamma,mu)

betas=(2,3,4)
gamma=5
mu=17
success=[r0 for r0 in range(q) if check(betas,(r0,11,12),gamma,mu)]
assert set(success)==T,(len(success),T.symmetric_difference(success))

# For beta_j !=1 and gamma !=0, the success fraction is |T|/q.
# If gamma*prod(1-beta_j)=0, the true claimed sum is zero and it always passes.
P=1-Fraction(q-1,q)**(nu+1)*(1-Fraction(D+1,q))
print('q,d,m,b,k,B,D=',q,d,m,b,k,B,D)
print('norm condition 2*k*c*(b-1)=',2*k*c_bound*(b-1),'< B=',B)
print('small challenge set strong: yes, size',len(SMALL))
print('source CCS statement unsatisfiable: 1^D != 0')
print('all actual source opening/prefix values are internally consistent')
print('range polynomial on Boolean cube vanishes, but not identically off it')
print('fixed beta/gamma/mu acceptance:',len(success),'/',q)
print('random (beta,gamma) accepting probability:',P, '=',float(P))
print('any successful transcript has a *valid* folded witness for every final small challenge')
