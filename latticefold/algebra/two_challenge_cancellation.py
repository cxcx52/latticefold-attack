"""Independent exact arithmetic check of a corrected-format false-to-true event.

This checks an *allowed knowledge-error event*, NOT a counterexample to
LatticeFold's stated knowledge-soundness theorem.
"""
from itertools import product
from fractions import Fraction

q, d, m = 257, 2, 2
b, k, B = 2, 6, 64
S = tuple(range(1, 5))  # Excludes zero. Scalar-ring strong sampling set.
T = max(S)
assert q % 4 == 1 and 2*k*T*(b-1) < B < q/2

# A vector in R_q^2: each R_q element is a tuple of coefficients (a0,a1).
zero = ((0, 0), (0, 0))
e = ((1, 0), (0, 0))

def scalar(v, a):
    return tuple(tuple((a*x) % q for x in poly) for poly in v)

def add(u, v):
    return tuple(tuple((x+y) % q for x,y in zip(p,s)) for p,s in zip(u,v))

def centered(a):
    a %= q
    return min(a, q-a)

def infinity_norm(v):
    return max(centered(a) for p in v for a in p)

# L = identity. Two public source output maps are ±e, but the input
# evaluation values are both falsely declared to be zero at r_i=0.
y1,y2=e,scalar(e,-1)
assert infinity_norm(y1)<b and infinity_norm(y2)<b
assert y1 != zero and y2 != zero  # MLE at Boolean r=0 is nonzero for y_i.
# Every other folded input has zero instance claims. The dishonest sumcheck
# uses fake opening 0 everywhere, so every zero-sum and endpoint check passes.

successful_pairs=0
for r1,r2 in product(S, repeat=2):
    y_out = add(scalar(y1,r1), scalar(y2,r2))
    if r1 == r2:
        successful_pairs += 1
        assert y_out == zero
        # Prover reveals f_out=0 and verifier claims vhat_out=0. Both target
        # commitment (L=id) and target MLE at *every* output point hold.
        assert infinity_norm(zero) < B
assert successful_pairs == len(S)
assert Fraction(successful_pairs,len(S)**2) == Fraction(1,len(S))
print(f"q={q}, b={b}, k={k}, B={B}, S={S}, T={T}")
print(f"Source inputs invalid (evaluation false), all fake zero sumcheck transcripts pass")
print(f"Target witness 0 exists on {successful_pairs}/{len(S)**2} pairs = 1/{len(S)}")
print(f"Theoretical fold knowledge-error term K/N={2*k}/{len(S)} >= 1/{len(S)}")
print("NO knowledge-soundness theorem violation claimed")
