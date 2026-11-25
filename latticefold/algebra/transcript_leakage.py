"""Exact witness-reconstruction from public multilinear evaluations.
Algebraic privacy demonstration only; this is NOT a soundness forgery.
"""
import random
q, nu = 277, 3
m = 2 ** nu
rng = random.Random(20261123)

def weight(u, r):
    w=1
    for j in range(nu):
        w = w * (r[j] if ((u >> j)&1) else (1-r[j])) % q
    return w

def solve(a, b):
    n=len(b)
    A=[[(a[i][j]%q) for j in range(n)] + [b[i]%q] for i in range(n)]
    for col in range(n):
        piv=next((t for t in range(col,n) if A[t][col]%q),None)
        if piv is None: return None
        A[col],A[piv]=A[piv],A[col]
        z=pow(A[col][col],-1,q)
        A[col]=[(x*z)%q for x in A[col]]
        for i in range(n):
            if i!=col:
                v=A[i][col]
                A[i]=[(x-v*y)%q for x,y in zip(A[i],A[col])]
    return [row[-1] for row in A]

# One secret vector under the same public instance; its public evaluation
# values are observed in m independent, correctly executed sessions.
f=[(5 + 29*i + 3*i*i)%q for i in range(m)]
for attempt in range(100):
    points=[tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m)]
    M=[[weight(u,r) for u in range(m)] for r in points]
    vhat=[sum(a*x for a,x in zip(row,f))%q for row in M]
    recovered=solve(M,vhat)
    if recovered is not None: break
assert recovered==f
print('m=',m,'q=',q,'interpolation queries=',m)
print('secret witness:',f)
print('recovered exactly from m public evaluations:',recovered)
print('sampled points:',points)
print('This applies slotwise to NTT/CRT-transformed witness tables, whose map is invertible.')
print('This is a transcript privacy disclosure, not a false-to-true RoK attack.')
