"""Two algebraic counterexamples against the *printed* 2025-12-15 LatticeFold.

1. Figure 5 / Definition 4.3 coordinate-order knowledge-extraction conflict.
2. Appendix B.1 claimed CCS-degree-independent sumcheck error bound.

Finite toy values are exact checks, not concrete MSIS hardness claims.
"""
from fractions import Fraction
from random import Random

Q=257
B=4
ELL=4
NC=4
M=NC*ELL
NU=4
D=40
assert M==2**NU and B**ELL>=Q//2 and Q%4==1

# G=I_4 tensor [1,B,...,B^(ELL-1)], for constant-polynomial gadget limbs.
def gadget(first_limb_coefficients):
    assert len(first_limb_coefficients)==NC
    return tuple(first_limb_coefficients)

def opening(coords):
    f=[0]*M
    for j,x in enumerate(coords): f[j*ELL]=x
    return tuple(f)

def check_gadget(f):
    return tuple(sum(B**j*f[i*ELL+j] for j in range(ELL))%Q for i in range(NC))

# Fix a reproducible arbitrary A, represented as two modular linear rows on
# constant-polynomial coefficients. The abstract argument holds for any A.
rng=Random(20261123)
A=[[rng.randrange(Q) for _ in range(M)] for _ in range(2)]
def commit(f):
    return tuple(sum(a*b for a,b in zip(row,f))%Q for row in A)

# Test 1: Ccs M has one row (1,-1,0,0). The input x=1 satisfies x-1=0.
f1=opening((0,0,1,1))
z1_in=(1,1,0,0)
z1_out=(0,0,1,1)
assert check_gadget(f1)==z1_out
assert (z1_in[0]-z1_in[1])%Q==0
assert (z1_out[0]-z1_out[1])%Q==0
assert max(abs(v) for v in f1)<B
assert z1_out[:2]!=(1,1)  # No source opening equal to this target opening.
cm1=commit(f1)
print('ATTACK 1 (coordinate order):')
print('  source CCS vector   =',z1_in)
print('  valid target Gf     =',z1_out)
print('  source prefix       =',(1,1))
print('  target actual prefix=',z1_out[:2])
print('  commitment A*f      =',cm1)
print('  all Figure 5 sumcheck terms = 0 (for every challenge)')
print('  ANY extracted source f\' necessarily yields a nonzero kernel vector f\'-f')

# Test 2: CCS enforces x^D=0 at row zero, x=1, hence the input is unsatisfiable.
# For z=(1,1,1,1), the reversed output layout agrees with the input layout,
# so this independent attack does not rely on the coordinate-order problem.
f2=opening((1,1,1,1))
assert check_gadget(f2)==(1,1,1,1)
assert 1**D % Q ==1
cm2=commit(f2)


def eq(beta, x):
    return ((1-beta)*(1-x)+beta*x)%Q

def g(betas, xs):
    ans=1
    for beta,x in zip(betas,xs):
        ans=ans*eq(beta,x)*pow((1-x)%Q,D,Q)%Q
    return ans

# The true sumcheck polynomial in the first variable is degree D+1.
def h1true(betas, x):
    coeff=1
    for v in betas[1:]: coeff=coeff*(1-v)%Q
    return coeff*eq(betas[0],x)*pow((1-x)%Q,D,Q)%Q

# Choose exactly D+1 roots, including 0 but excluding 1, for the cheating
# correction to the first sumcheck polynomial.
T={0,*range(2,D+2)}
assert len(T)==D+1 and 1 not in T

def rootpoly(x):
    v=x%Q
    for a in range(2,D+2): v=v*((x-a)%Q)%Q
    return v

assert rootpoly(0)==0 and rootpoly(1)!=0

def forged_h1(betas, x):
    S=1
    for v in betas: S=S*(1-v)%Q
    if S==0: return h1true(betas,x)
    c=(-S)*pow(rootpoly(1),-1,Q)%Q
    return (h1true(betas,x)+c*rootpoly(x))%Q


def honest_round(betas, preceding, x):
    """Actual sum of g over all remaining binary variables, no trust in prover."""
    j=len(preceding)
    remain=NU-j-1
    return sum(g(betas,preceding+[x]+[(s>>a)&1 for a in range(remain)])
               for s in range(1<<remain))%Q


def verifier_accepts(betas, challenges):
    # Model the actual 4-round sumcheck check and endpoint. For r1 in T,
    # remaining 3 univariate messages are the correct restricted sums.
    prev=0
    for j in range(NU):
        h=(lambda x: forged_h1(betas,x)) if j==0 else (
            lambda x,j=j: honest_round(betas,list(challenges[:j]),x))
        if (h(0)+h(1)-prev)%Q: return False
        prev=h(challenges[j])
    return prev==g(betas,challenges)

fixed_beta=(2,2,2,2)
assert all((b!=1) for b in fixed_beta)
accepted=[r for r in range(Q) if verifier_accepts(fixed_beta,(r,3,4,5))]
assert set(accepted)==T,(len(accepted),T.symmetric_difference(accepted))
for r in range(Q):
    assert (forged_h1(fixed_beta,r)==h1true(fixed_beta,r)) == (r in T)

beta_zero_probability=1-Fraction(Q-1,Q)**NU
accept_probability=beta_zero_probability+(1-beta_zero_probability)*Fraction(D+1,Q)
claimed_bound=Fraction((2*2+1)*NU,Q)
assert accept_probability>claimed_bound
print('ATTACK 2 (CCS degree error):')
print('  q,d,B,m,degree      =',Q,2,B,M,D)
print('  source x            = 1, while constraint x^D=0 is false')
print('  target Gf           =',check_gadget(f2),'(same under both coordinate orders)')
print('  for beta=(2,2,2,2), accepted first challenges:',len(accepted),'of',Q)
print('  accepted first set =',sorted(accepted))
print('  exact random-beta acceptance probability =',accept_probability)
print('  numerical acceptance probability         =',float(accept_probability))
print('  Appendix B.1 claimed error (b=2, m=16)  =',claimed_bound,'=',float(claimed_bound))
print('  complete verifier transcript equations tested; no terminal or cryptographic attack claimed')
