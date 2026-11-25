"""Exact literal-Theorem-4.1 honest-completeness counterexample, 2025-12-15 PDF.

Composition: valid R_cmccs + valid zero R_evalccs -> honest Figure 5,
Figure 6, Figure 7. All public verifier checks pass, but final relation
Eq.(34)-(35) fails except when the one active folding challenge is zero.
Small toy parameters only: no concrete MSIS-hardness claim.
"""
from random import Random
from itertools import product

q, d, b, k, B, nc, ell, m, nu = 257, 2, 2, 6, 64, 4, 2, 8, 3
assert m == 2 ** nu == nc * ell and B ** ell >= q / 2
A_bound = 4
assert 2*k*A_bound*(b-1) < B < q/2

R = lambda a, c=0: (a % q, c % q)
zero, one = R(0), R(1)
add=lambda x,y:R(x[0]+y[0],x[1]+y[1])
neg=lambda x:R(-x[0],-x[1])
sub=lambda x,y:add(x,neg(y))
mul=lambda x,y:R(x[0]*y[0]-x[1]*y[1],x[0]*y[1]+x[1]*y[0])
scale=lambda c,x:R(c*x[0],c*x[1])
S=[R(i,j) for i,j in product((-1,0,1,2),repeat=2)]
for i,a in enumerate(S):
    for b2 in S[i+1:]:
        diff=sub(a,b2)
        assert all((diff[0]+root*diff[1])%q != 0 for root in (16,-16))

inv2=pow(2,-1,q)
inv32=pow(32,-1,q)
hat=lambda a: R((a[0]+a[1])*inv2,(a[0]-a[1])*inv32)
ntt=lambda a:((a[0]+16*a[1])%q,(a[0]-16*a[1])%q)
assert ntt(hat(one)) == (1,0)

def eq(a,x): return ((1-a)*(1-x)+a*x)%q

def mle(elems,x):
    res=zero
    for i,val in enumerate(elems):
        weight=1
        for j,xx in enumerate(x):weight=weight*eq((i>>j)&1,xx)%q
        res=add(res,scale(weight,val))
    return res

def gadget(f):
    return tuple(add(f[ell*j],scale(B,f[ell*j+1])) for j in range(nc))

def ccs(z): return sub(z[0],z[1])

f=[zero]*m; f[0]=one; f[ell]=one
fa=[zero]*m
assert gadget(f)==(one,one,zero,zero)
assert gadget(fa)==(zero,zero,zero,zero)
assert ccs(gadget(f))==zero

rng=Random(20261123)
A=[[R(rng.randrange(q),rng.randrange(q)) for _ in range(m)] for __ in range(2)]

def commit(x):
    ans=[]
    for row in A:
        s=zero
        for a,v in zip(row,x):s=add(s,mul(a,v))
        ans.append(s)
    return tuple(ans)

cm=commit(f)
# Figure 5: true CCS sumcheck, all rows zero; output linearized u = 0.
assert ccs(gadget(f))==zero
# Figure 6: exact signed digit decomposition of f and zero accumulator.
comp_digits=[f]+[[zero]*m for _ in range(k-1)]
acc_digits=[[zero]*m for _ in range(k)]
for digits,original in [(comp_digits,f),(acc_digits,fa)]:
    reconstructed=[zero]*m
    for h,di in enumerate(digits):
        reconstructed=[add(v,scale(2**h,z)) for v,z in zip(reconstructed,di)]
    assert reconstructed==original
    assert all(all(max(abs(z if z<q//2 else z-q) for z in x)<2 for x in di) for di in digits)

# Figure 7: one nonzero evaluation/range channel; the linear CCS channel vanishes.
# Honest MLE at each Boolean row equals either 0 or the map of the coefficient 1.
hat_f=[hat(a) for a in f]
Pb=lambda z:mul(mul(z,sub(z,one)),add(z,one))
for i in range(m):assert Pb(hat_f[i])==zero

for trial in range(20):
    alpha,mu,beta0,beta1,beta2 = (rng.randrange(q) for _ in range(5))
    rr=tuple(rng.randrange(q) for _ in range(nu)) # original input point
    rout=tuple(rng.randrange(q) for _ in range(nu))
    beta=(beta0,beta1,beta2)
    vhat=mle(hat_f,rr)

    def g(x):
        ex, eb=1,1
        for a,xx in zip(rr,x):ex=ex*eq(a,xx)%q
        for a,xx in zip(beta,x):eb=eb*eq(a,xx)%q
        th=mle(hat_f,x)
        return add(scale(alpha*ex,th),scale(mu*eb,Pb(th)))
    claim=scale(alpha,vhat)
    # All honest sumcheck equations h_j(0)+h_j(1)=previous claim.
    for j in range(nu):
        def h(x):
            ans=zero
            for z in range(1 << (nu-j-1)):
                suffix=tuple((z>>r)&1 for r in range(nu-j-1))
                ans=add(ans,g((*rout[:j],x,*suffix)))
            return ans
        assert add(h(0),h(1))==claim
        claim=h(rout[j])
    assert claim==g(rout)
    theta=mle(hat_f,rout)
    assert claim==add(scale(alpha*__import__('functools').reduce(
        lambda acc,v:acc*eq(v[0],v[1])%q,zip(rr,rout),1),theta),
        scale(mu*__import__('functools').reduce(
        lambda acc,v:acc*eq(v[0],v[1])%q,zip(beta,rout),1),Pb(theta)))
    for rho in S:
        # Final public commitment, xw=(x,h), and genuine output witness.
        fo=[mul(rho,a) for a in f]
        gg=gadget(fo)
        assert gg==(rho,rho,zero,zero)
        assert commit(fo)==tuple(mul(rho,a) for a in cm)
        assert ccs(gg)==zero
        assert ccs((zero,zero,rho,rho))==zero # output linearized u matches
        assert ntt(mle([hat(a) for a in fo],rout)) == tuple(
            (a * ntt(theta)[0]) % q for a in rho
        )
        wgt=ntt(theta)[0]
        honest_out_coeff=R(*ntt(mle([hat(a) for a in fo],rout)))
        assert honest_out_coeff==scale(wgt,rho)
        target_z=(zero,zero,rho,rho) # Eq 34: (w,h,x)
        assert (gg==target_z) == (rho==zero)

print('PASS: fully valid source; 20 random full Figure-7 sumchecks,')
print('      Figure-5 CCS polynomial identically zero; all',len(S),'final challenges;')
print('      commitments/CCS/MLE/target checked.')
print('Original literal accumulated relation accepts only 1/16 of honest final witnesses.')
