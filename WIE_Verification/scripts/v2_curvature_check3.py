# -*- coding: utf-8 -*-
"""WIE v2.2 · 球面 Einstein 张量验证（对角度规版 + 数值抽查）"""
import sympy as sp
import json, os, random, math

OUT = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\910CF9D8FBF963F109E2915A63F38F70\workspace\conv_c220e5e084e345aa8edd6702582cebba\output\WIE_V2_常曲率验证_20261009.json"


def sphere_g_diag(N, R, q):
    """S^N 标准角坐标：对角度规 g_ii = R^2 * prod_{j<i} sin^2(theta_j)"""
    g = sp.zeros(N, N)
    for i in range(N):
        e = R**2
        for j in range(i):
            e *= sp.sin(q[j])**2
        g[i, i] = e
    return g


def ricci(g, q):
    n = len(q)
    gi = g.inv()
    G = [[[sp.S.Zero] * n for _ in range(n)] for _ in range(n)]
    for a in range(n):
        for b in range(n):
            for c in range(b, n):
                s = sum(gi[a, d] * (sp.diff(g[d, b], q[c]) + sp.diff(g[d, c], q[b])
                                    - sp.diff(g[b, c], q[d])) for d in range(n))
                G[a][b][c] = sp.cancel(s / 2)
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


res = {"method": "球面对角度规 g_ii=R^2*prod sin^2(theta_j)；核对 Ric_ii/g_ii=(N-1)/R^2"}
R = sp.symbols('R', positive=True)

for N in (2, 3, 4, 5):
    q = sp.symbols('t0:%d' % N, positive=True)
    g = sphere_g_diag(N, R, q)
    Ric = ricci(g, q)
    ok_all = True
    for i in range(N):
        diff = sp.simplify(sp.trigsimp(sp.expand_trig(Ric[i, i] / g[i, i] - (N - 1) / R**2)))
        if diff != 0:
            ok_all = False
        # 数值抽查
        vals = {R: 1.0}
        for k, s in enumerate(q):
            vals[s] = random.uniform(0.2, 1.2)
        num = float(diff.subs(vals)) if diff != 0 else 0.0
        if abs(num) > 1e-9:
            ok_all = False
    Rs = sp.simplify(sum(Ric[i, i] * g.inv()[i, i] for i in range(N)))
    res["S%d" % N] = {"Ric_proportional_to_g": bool(ok_all),
                      "Ricci_scalar": str(Rs),
                      "Theta_analytic": str(sp.cancel(-(N - 1) * (N - 2) / (2 * R**2)))}
    print("S%d  Ric∝g=%s  Ricci_scalar=%s  Theta=%s" % (
        N, ok_all, Rs, sp.cancel(-(N - 1) * (N - 2) / (2 * R**2))))

N = 11
Th = sp.cancel(-(N - 1) * (N - 2) / (2 * R**2))
res["S11"] = {"Theta": str(Th), "Theta_R1": str(Th.subs(R, 1)), "note": "规律空间 N=11=1+4+6"}
print("S11 Theta =", Th, "| R=1 ->", Th.subs(R, 1))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("OUT ->", OUT)
