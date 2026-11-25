"""Exact algebraic PoC: unsafe scalar aggregation of extension range checks.
This is NOT a counterexample to independently batched/vector-valued checks.
"""
q, d = 277, 4
b, k, B = 2, 6, 64
# q=5 mod 8, X^4+1 splits as two irreducible quadratics over F_q.
assert q % 8 == 5
zeta = next(z for z in range(q) if (z*z+1)%q==0)
assert zeta > 0
zinverse = pow(zeta, -1, q)

def add(a, c): return tuple((x+y)%q for x,y in zip(a,c))
def neg(a): return tuple((-x)%q for x in a)
def mul(a,c):
    out=[0]*d
    for i,x in enumerate(a):
      for j,y in enumerate(c):
        t=i+j
        out[t%d]=(out[t%d]+(1 if t<d else -1)*x*y)%q
    return tuple(out)
def num(z): return (z%q,0,0,0)
def P2(x): return add(mul(mul(x,x),x),neg(x))
zero=num(0)
# E=2*CRT-idempotent for X^2-zeta, i.e. phi(E)=(2,0).
E=(1,0,zinverse,0)
def eval_mod_quad(a,z):
    # Evaluate a in F_q[X]/(X^2-z), return coefficients of 1,X.
    return ((a[0]+z*a[2])%q, (a[1]+z*a[3])%q)
assert eval_mod_quad(E,zeta)==(2,0)
assert eval_mod_quad(E,(-zeta)%q)==(0,0)
assert P2(E)!=zero, 'individual range check must fail'
assert add(P2(E),P2(neg(E)))==zero
# The *original* f has coefficient size 2 (invalid for norm<2).
f=(2,0,q-2,0)
assert max(min(x,q-x) for x in f)==b
S=(0,1,2)  # scalar strong set, exact toy only
T=max(S)
assert 2*k*T*(b-1)<B<q/2
for rho in S:
    folded=mul(num(rho),f)
    norm=max(min(x,q-x) for x in folded)
    assert norm<B
print('q=',q,'d=',d,'zeta=',zeta,'CRT block E=',E)
print('P2(E)=',P2(E),'P2(-E)=',P2(neg(E)))
print('Range errors nonzero individually; scalar sum vanishes identically.')
print('All',len(S),'last challenges yield target norm <B, hence false-to-true succeeds with probability 1.')
print('Repaired vector / independent block batching is NOT attacked.')
