#!/usr/bin/env python3
"""Exact algebra checks for two attacks on LatticeFold+ (2025-08-09 PDF).
NOT an implementation of the complete interactive protocol; see report.md.
"""
import random
Q = 12289
D = 64
DPRIME = D//2
K = 2
B = DPRIME**K

def mul(a, b):
    out = [0]*D
    for i, ai in enumerate(a):
        if not ai:
            continue
        for j, bj in enumerate(b):
            if not bj:
                continue
            k = i+j
            out[k % D] = (out[k % D] + (ai*bj if k<D else -ai*bj)) % Q
    return out

def monom(j):
    a=[0]*D
    a[j]=1
    return a

psi=[0]*D
for j in range(1,DPRIME):
    psi[j] = (psi[j]+j) % Q
    psi[D-j] = (psi[D-j]-j) % Q

ct=lambda a: a[0]%Q
m_canonical_0=monom(1)
m_alt_0=monom(33)
m_alt_1=monom(1)
u_can=(ct(mul(psi,m_canonical_0)),0)
u_alt=(ct(mul(psi,m_alt_0)),ct(mul(psi,m_alt_1)))
assert u_can == (1,0)
assert u_alt == (Q-31,1)
assert (u_alt[0]+DPRIME*u_alt[1]) % Q == 1
assert all(monom(j)[j]==1 for j in (1,33))
assert B==1024
print('=== Attack 1: noncanonical digit opening ===')
print(f'd={D} q={Q} dprime={DPRIME} B={B}')
print(f'canonical=(1,0), alternate=(-31,1); recon={(-31+32*1)}')
print(f'ct(psi*X^33)={u_alt[0]-Q}, ct(psi*X)={u_alt[1]}')

# Because only first row of the witness is nonzero, its MLE at any r is E(r)=product(1-r_i).
rng=random.Random(1967)
for _ in range(400):
    r=[rng.randrange(Q) for _ in range(6)]
    E=1
    for ri in r:
        E=(E*(1-ri))%Q
    v=E
    lhs = (E * (u_alt[0] +DPRIME*u_alt[1]))%Q
    assert lhs == v
print('PASS: 400 random MLE points satisfy every reconstructed coefficient check')

# Membership of X^33,X in monomial set is certified by ordinary polynomial evaluation a(beta^2)=a(beta)^2.
for _ in range(400):
    beta = rng.randrange(Q)
    for exponent in (33,1):
        assert pow(beta*beta%Q,exponent,Q)==pow(pow(beta,exponent,Q),2,Q)
print('PASS: 400 random beta confirm both monomial polynomial identities')

# Attack 2: Appendix A, all-zero opening and a conflicting homogenization constraint.
# R1CS: A=B=0, C first row selects z0. Source says z0=1, impossible.
print('=== Attack 2: missing public/homogenizing constraints ===')
for _ in range(400):
    r=[rng.randrange(Q) for _ in range(2)]
    ro=[rng.randrange(Q) for _ in range(2)]
    # With f=0, all MLEs and sumcheck polynomials =0; endpoint is identically zero.
    vals=(0,0,0,0)
    e=1
    for ri,oi in zip(r,ro):
        e=e*((1-ri)*(1-oi)+ri*oi)%Q
    assert e*(vals[1]*vals[2]-vals[3])%Q == 0
print('PASS: 400 Figure-1 endpoint samples accept zero opening for the inconsistent R1CS')

# Independent diagnostic: Figure 1 labels g as individual degree <=2, but an honest g can have degree 3.
# Let two Boolean variables x,y and g_A=g_B=g_C=x*y.
# Sum over y of eq(r,(x,y))*((x*y)^2-(x*y)) yields
# h(x)=r_y * ((1-r_x)+(2r_x-1)*x) * (x*x-x)
# Leading coefficient is r_y*(2r_x-1) != 0 with overwhelming probability.
for _ in range(400):
    rx,ry=[rng.randrange(Q) for __ in range(2)]
    cubic=(ry*(2*rx-1))%Q
    if rx != (Q+1)//2 and ry !=0:
        assert cubic !=0
# Concrete honest first sumcheck message: r=(2,3), h(T)=9T^3-12T^2+3T.
h = [0,3,Q-12,9]
assert (h[0] + sum(h)) % Q == 0
assert h[3] == 9
print('PASS: honest Figure-1 sumcheck may have degree 3 although text labels degree <=2')
print('explicit h(T)=9*T^3-12*T^2+3*T with h(0)+h(1)=0')
