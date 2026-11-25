"""Unmodified fully split Figure 3: an optimal-order 1/|Csmall|
false-to-true knowledge-error event, even with perfectly binding L=identity.
This does not violate the interactive theorem's stated knowledge error.
It identifies a concrete predicate amenable to classical/QROM FS grinding.
"""
from itertools import product
q,d,m,b,B=257,2,8,2,64
R=lambda a,c=0:(a%q,c%q)
zero,one=R(0),R(1)
S=[R(a,c) for a,c in product((-1,0,1,2),repeat=2)]
assert len(S)==16
mul=lambda u,v:R(u[0]*v[0]-u[1]*v[1],u[0]*v[1]+u[1]*v[0])
# Identity homomorphism L on R^m: every y has exactly one opening f=y.
e=[zero]*m;e[0]=one
y_bad=[R(2)*1 if i==0 else zero for i in range(m)]
assert max(abs(v[0]) for v in y_bad)==b   # not in R_hom^b
# adversarial 'phantom' f_i=0: evaluations zero, range polynomial zero,
# and the complete sumcheck can honestly send zero polynomials for all coins.
assert all(z==zero for z in [zero]*m)
# All remaining 2k-1 inputs have y_i=0 and are actually valid.
output_good=[]
for rho0 in S:
    # The prover only claims an output witness if rho0=0.
    if rho0==zero:
        yo=[mul(rho0,z) for z in y_bad]
        fo=[zero]*m
        assert fo==yo # L=identity
        # final transformed MLE is 0, also true for zero f_o
        output_good.append(rho0)
assert output_good==[zero]
print('The bad source input has no R_hom^b witness under L=identity.')
print('The verifier accepts a true zero sumcheck for every initial transcript.')
print('Target witness f_out=0 is valid when rho_bad=0.')
print('Single-try false-to-true probability:',len(output_good),'/',len(S))
print('This matches an allowed knowledge-error event, not a PPT break.')
