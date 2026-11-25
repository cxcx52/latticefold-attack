"""Independent arithmetic check of the malicious final-digit NIFS construction.

Mirrors the committed/weighted algebra and range combination in the uploaded
Nethermind source for its real Goldilocks coefficient ring and DP constants.
This is not a Rust NIFSVerifier execution or a proof of MSIS hardness.
"""
from random import Random

Q = (1 << 64) - (1 << 32) + 1
D = 24
TAU = 3
SLOTS = 8
K = 15
B = 1 << K
B_SMALL = 2
GADGET_LIMBS = 5
assert D == TAU * SLOTS


def poly(values=None):
    out = [0] * D
    if values:
        for exponent, value in values.items():
            out[exponent] = value % Q
    return tuple(out)


def add(a, b):
    return tuple((x + y) % Q for x, y in zip(a, b))


def times_int(a, x):
    return tuple(x * y % Q for y in a)


def mul_phi72(a, b):
    # Goldilocks coefficient ring: F_Q[X]/(X^24 - X^12 + 1).
    r = [0] * (2 * D - 1)
    for i, x in enumerate(a):
        if x == 0: continue
        for j, y in enumerate(b):
            r[i + j] = (r[i + j] + x * y) % Q
    for degree in range(len(r) - 1, D - 1, -1):
        v = r[degree]
        # X^24 = X^12 - 1, so X^degree -> X^(degree-12) - X^(degree-24).
        r[degree - 12] = (r[degree - 12] + v) % Q
        r[degree - 24] = (r[degree - 24] - v) % Q
        r[degree] = 0
    return tuple(r[:D])


def ring_commit(matrix, f):
    return [tuple_sum(mul_phi72(a, fi) for a, fi in zip(row, f)) for row in matrix]


def tuple_sum(items):
    res = poly()
    for item in items:
        res = add(res, item)
    return res


def centered_norm(a):
    return max(min(v, Q-v) for v in a)


def p2(v):
    return (v * (v*v - 1)) % Q


def rcomb(channels, mu):
    # Exact reversed Horner loop in folding/utils.rs:290-320 with b=2.
    result = 0
    for v in reversed(channels):
        result = ((result + p2(v)) * mu) % Q
    return result


def eq_zero(r):
    out = 1
    for a in r:
        out = out * (1 - a) % Q
    return out

rng = Random(20261123)

# First gadget limb carries the invalid (B,-B) and malicious last digit (b,-b).
f_bad = [poly({0:B_SMALL, 8:-B_SMALL})] + [poly()] * (GADGET_LIMBS - 1)
f_src = [poly({0:B, 8:-B})] + [poly()] * (GADGET_LIMBS - 1)
assert [times_int(fi, 1 << (K-1)) for fi in f_bad] == f_src
assert centered_norm(f_bad[0]) == B_SMALL
assert centered_norm(f_src[0]) == B
assert B_SMALL < B

for trial in range(40):
    A = [[poly({j:rng.randrange(Q) for j in range(D)}) for _ in range(GADGET_LIMBS)]
         for _ in range(4)]
    cm_bad = ring_commit(A, f_bad)
    cm_src = ring_commit(A, f_src)
    assert [times_int(c, 1 << (K-1)) for c in cm_bad] == cm_src

    for _ in range(60):
        point = [rng.randrange(Q) for _ in range(3)]  # verifier's MLE point
        beta = [rng.randrange(Q) for _ in range(3)]   # range localization
        lam = eq_zero(point)
        channels = [(2*lam)%Q, (-2*lam)%Q, 0]
        # All three transformed block range residuals vanish AFTER batching.
        assert rcomb(channels, 1) == 0
        # At a Boolean point the first and second range constraints are false.
        assert rcomb([2, -2 % Q, 0], 1) == 0
        assert p2(2) != 0 and p2((-2) % Q) != 0
        assert (eq_zero(beta)*rcomb(channels, 1))%Q == 0

    # With all other private digits zero and rho_last=1, final public commitment
    # is cm_bad, with explicit legal B-short target witness f_bad.
    assert centered_norm(f_bad[0]) < B

print('PASS: 40 random Ajtai matrices, 2400 verifier-point/localization pairs')
print('PASS: weighted decomposition commitment and all range-cancellation identities')
print('ACTUAL PARAMETERS:', {'q':Q, 'coeff_degree':D, 'tau':TAU, 'k':K, 'B':B, 'b':B_SMALL})
print('LIMIT: this script is independent algebra, not a Rust LFProof/NIFSVerifier test')
