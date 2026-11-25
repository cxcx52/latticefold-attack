"""Exact scalar checks of p45 Eq(36) versus Figure 7.

Only the native linear CCS channel is tested; other channels are chosen honestly.
Parameters use a fully split ring R_q with q=257, d=2 (X^2+1=(X-16)(X+16)).
The remaining witness/evaluation and range channels are chosen honestly and
cancel from the Boolean sum.  The examples use L=Lw=identity and b=2,
k=6,B=64, small scalar S={1,2,3,4}, with 2k*4*(b-1)=48 < 64.
"""
q=257
S=(1,2,3,4)
qinv2=pow(2,-1,q)

def mmul(M, v):
    return tuple(sum(a*b for a,b in zip(row,v))%q for row in M)

def dot(v,w):
    return sum(a*b for a,b in zip(v,w))%q

def tensor_paper(r):
    return (r%q, (1-r)%q)

def tensor_standard(r):
    return ((1-r)%q, r%q)

def rel_u(M,z,r,tensor=tensor_paper):
    return dot(mmul(M,tensor(r)),z)

def sumcheck_linear_channel(M,z,r):
    # Figure 7: eq(r,x) * (M z)[x], summed over x=0,1
    Mz=mmul(M,z)
    return ((1-r)*Mz[0]+r*Mz[1])%q

def endpoint(M,z,ro):
    Mz=mmul(M,z)
    return ((1-ro)*Mz[0]+ro*Mz[1])%q

# A: tensor-order warning under the USUAL 0-first row convention.
# The source does not explicitly settle how vectors index Boolean rows.
# This example is not a convention-independent refutation.
M_A=((1,0),(0,1))
z_A=(1,0)
r_A=0
u_A=rel_u(M_A,z_A,r_A)
g_A=sumcheck_linear_channel(M_A,z_A,r_A)
assert (u_A,g_A)==(0,1)
# After honest endpoint, output u_o=rho*endpoint(M,z,ro), while the
# target relation Eq(36) demands rel_u(M,rho*z,ro).
for rho in S:
    for ro in range(q):
        observed=rho*endpoint(M_A,z_A,ro)%q
        target=rel_u(M_A, tuple(rho*c%q for c in z_A),ro)
        assert (observed==target)==(ro==qinv2)

# B: convention-independent matrix transpose mismatch. r=1/2 makes the paper and
# standard tensor order identical, yet the two formulas disagree.
M_B=((0,1),(0,0))
z_B=(1,0)
r_B=qinv2
u_B=rel_u(M_B,z_B,r_B)
g_B=sumcheck_linear_channel(M_B,z_B,r_B)
assert (u_B,g_B)==(qinv2,0)
assert rel_u(M_B,z_B,r_B,tensor_standard)==u_B
for rho in S:
    for ro in range(q):
        observed=rho*endpoint(M_B,z_B,ro)%q  # always zero
        target=rel_u(M_B,tuple(rho*c%q for c in z_B),ro)
        assert (observed==target)==(ro==1)

# At the first sumcheck, the honest claimed sum differs from actual sum
# by zeta*(g-u). Since g != u, an honest polynomial passes the Boolean-
# sum check exactly when zeta=0 (one of q equally likely values).
assert all((zeta*(g_A-u_A))%q==0 for zeta in [0])
assert all((zeta*(g_A-u_A))%q!=0 for zeta in range(1,q))
assert all((zeta*(g_B-u_B))%q!=0 for zeta in range(1,q))

print('q =',q,'R_q fully split; S =',S,'||S||op = 4, 2kc(b-1) = 48 < B=64')
print('A (CONDITIONAL ON 0-FIRST ROW ORDER): symmetric M=I, input r=0, paper relation u=',u_A,
      ', Figure 7 actual Boolean sum linear term =',g_A)
print('   output relation holds for exactly 1 of',q,'sumcheck points (ro=1/2)')
print('B: nonsymmetric M, input r=1/2, paper relation u=',u_B,
      ', Figure 7 actual Boolean sum linear term =',g_B)
print('   output relation holds for exactly 1 of',q,'sumcheck points (ro=1)')
print('B is convention-independent; if Figure 7 uses M as printed, honest output holds with probability 1/q^2',
      '=1/',q*q,'under independent uniform zeta and ro in F_q;'
      ' other channels are honest and final rho is nonzero in S.')
