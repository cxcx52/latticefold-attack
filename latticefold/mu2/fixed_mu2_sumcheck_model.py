#!/usr/bin/env python3
"""Exact finite-field sumcheck of a false b=2 range statement with fixed mu=2.

This is an independent arithmetic model, NOT an execution of Nethermind's Rust verifier.
The three coefficient channels have Boolean tables (5,-4,0) at one row and
zero elsewhere. Their weighted range residual at every Boolean row is zero.
The multilinear-extension range polynomial is nevertheless generally nonzero.
"""
from itertools import product

q = 277
ell = 3
beta = (17, 33, 71)
r = (42, 120, 211)
mu = 2
b = 2

def p2(z):
    return (z*z*z-z)%q

def eq0(x):
    out=1
    for xx in x:out=out*(1-xx)%q
    return out

def eqbeta(x):
    out=1
    for xx, bb in zip(x,beta):out=out*((1-bb)*(1-xx)+bb*xx)%q
    return out

def g(x):
    t=eq0(x)
    return eqbeta(x)*(mu*p2(5*t)+mu*mu*p2(-4*t))%q

def h(prefix,t):
    left=ell-len(prefix)-1
    return sum(g((*prefix,t,*s)) for s in product((0,1),repeat=left))%q

def eval_lagrange_at(points, x):
    acc=0
    for i,(xi,yi) in enumerate(points):
        num=den=1
        for j,(xj,_) in enumerate(points):
            if j==i:continue
            num=num*(x-xj)%q
            den=den*(xi-xj)%q
        acc=(acc+yi*num*pow(den,-1,q))%q
    return acc

assert (mu*p2(5)+mu**2*p2(-4))%q == 0
assert p2(5)!=0 and p2(-4)!=0
initial=sum(g(bits) for bits in product((0,1),repeat=ell))%q
assert initial == 0
assert g((2,3,4)) != 0, 'The sumcheck polynomial is not identically zero'
claim=initial
prefix=()
for i,ri in enumerate(r):
    samples=[(t,h(prefix,t)) for t in range(5)]
    assert (samples[0][1]+samples[1][1])%q==claim
    assert all(eval_lagrange_at(samples,t)==h(prefix,t) for t in (5,10,61))
    claim=eval_lagrange_at(samples,ri)
    prefix=(*prefix,ri)
    print(f'round={i+1} challenge={ri}, h0={samples[0][1]}, h1={samples[1][1]}, h(r)={claim}')
assert claim==g(r)
print('PASS: false per-channel range inputs (+5,-4), fixed mu=2, all 3 honest degree-4 sumcheck rounds and endpoint')
print('P_2(5)=%d, P_2(-4)=%d, weighted Boolean residual=%d' %(p2(5),p2(-4),(mu*p2(5)+mu**2*p2(-4))%q))
print('g(2,3,4)=%d confirms polynomial is not identically zero' %g((2,3,4)))
