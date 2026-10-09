# -*- coding: utf-8 -*-
"""WIE v2.2 · 常曲率球面 Einstein 张量验证（强制化简版）"""
import sympy as sp
import json, os

OUT = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\910CF9D8FBF963F109E2915A63F38F70\workspace\conv_c220e5e084e345aa8edd6702582cebba\output\WIE_V2_常曲率验证_20261009.json"


def sphere_g(N, R, q):
    x = []
    for k in range(N):
        e = R
        for i in range(k):
            e *= sp.sin(q[i])
        e *= sp.cos(q[k])
        x.append(e)
    e = R
    for i in range(N):
        e *= sp.sin(q[i])
    x.append(e)
    return sp.Matrix(N, N, lambda i, j: sp.cancel(
        sp.expand_trig(sum(sp.diff(x[k], q[i]) * sp.diff(x[k], q[j]) for k in range(N + 1)))))


def ricci(g, q):
    n = len(q)
    gi = g.inv()
    G = [[[sp.S.Zero] * n for _ in range(n)] for _ in range(n)]
    for a in range(n):
        for b in range(n):
            for c in range(b, n):
                s = sum(gi[a, d] * (sp.diff(g[d, b], q[c]) + sp.diff(g[d, c], q[b])
                                    - sp.diff(g[b, c], q[d])) for d in range(n))
                G[a][b][c] = sp.cancel(sp.expand_trig(s / 2))
                G[a][c][b] = G[a][b][c]
    Ric = sp.zeros(n, n)
    for b in range(n):
        for d in range(n):
            s = 0
            for a in range(n):
                s += sp.diff(G[a][b][d], q[a]) - sp.diff(G[a][b][a], q[d])
                for e in range(n):
                    s += G[a][a][e] * G[e][b][d] - G[a][d][e] * G[e][b][a]
            Ric[b, d] = s
    return Ric


def clean(e):
    return sp.simplify(sp.trigsimp(sp.expand_trig(sp.cancel(e))))


res = {}
R = sp.symbols('R', positive=True)
for N in (2, 3):
    q = sp.symbols('t0:%d' % N, positive=True)
    g = sphere_g(N, R, q)
    Ric = ricci(g, q)
    diffs = [clean(sp.expand_trig(Ric[i, i]) / sp.expand_trig(g[i, i]) - (N - 1) / R**2) for i in range(N)]
    ok = all(d == 0 for d in diffs)
    # Ricci scalar via trace
    Rs = clean(sum(Ric[i, i] * g.inv()[i, i] for i in range(N)))
    res["S%d" % N] = {"match": bool(ok), "diff": [str(d) for d in diffs],
                      "Ricci_scalar": str(Rs),
                      "Theta_analytic": str(sp.cancel(-(N - 1) * (N - 2) / (2 * R**2)))}
    print("S%d match=%s  Ricci_scalar=%s" % (N, ok, Rs))

N = 11
Th = sp.cancel(-(N - 1) * (N - 2) / (2 * R**2))
res["S11"] = {"Theta": str(Th), "Theta_R1": str(Th.subs(R, 1)), "note": "N=11=1+4+6"}
print("S11  Theta =", Th, " (R=1 ->", Th.subs(R, 1), ")")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("OUT ->", OUT)
