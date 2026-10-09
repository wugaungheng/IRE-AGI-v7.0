# -*- coding: utf-8 -*-
"""
WIE v2.2 · V(L) 自洽性数值验证
验证：规律空间取常曲率球面 S^N 时，几何约束 G_ab g^{bc} = Theta 自动满足，
     且 Theta = -(N-1)(N-2)/(2R^2) I。
方法：sympy 符号计算 S^N (N=2,3) 的 Ricci 张量，核对 Ric_ab = (N-1)/R^2 g_ab，
     再给出 N=11 的解析值。
输出：JSON 到 output，便于台账。
"""
import sympy as sp
import json, os

OUT = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\910CF9D8FBF963F109E2915A63F38F70\workspace\conv_c220e5e084e345aa8edd6702582cebba\output\WIE_V2_常曲率验证_20261009.json"


def sphere_g(N, R, q):
    """标准球坐标参数化 S^N -> R^{N+1}，返回度规 g_ij。"""
    x = []
    for k in range(N):
        expr = R
        for i in range(k):
            expr *= sp.sin(q[i])
        expr *= sp.cos(q[k])
        x.append(expr)
    expr = R
    for i in range(N):
        expr *= sp.sin(q[i])
    x.append(expr)
    return sp.Matrix(N, N, lambda i, j: sp.cancel(
        sum(sp.diff(x[k], q[i]) * sp.diff(x[k], q[j]) for k in range(N + 1))))


def riemann_ricci(g, q):
    n = len(q)
    ginv = g.inv()
    G = [[[sp.S.Zero] * n for _ in range(n)] for _ in range(n)]
    for a in range(n):
        for b in range(n):
            for c in range(b, n):
                s = sum(ginv[a, d] * (sp.diff(g[d, b], q[c]) + sp.diff(g[d, c], q[b])
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
            Ric[b, d] = sp.cancel(s)
    return Ric


results = {"check": "G_ab g^bc = Theta  (常曲率球面 S^N)"}
R = sp.symbols('R', positive=True)

for N in (2, 3):
    q = sp.symbols('t0:%d' % N, positive=True)
    g = sphere_g(N, R, q)
    Ric = riemann_ricci(g, q)
    ratios = [sp.cancel(Ric[i, i] / g[i, i]) for i in range(N)]
    expect = sp.simplify((N - 1) / R**2)
    ok = all(sp.simplify(r - expect) == 0 for r in ratios)
    Rscalar = sp.cancel(sum(Ric[i, i] * g.inv()[i, i] for i in range(N)))
    Tval = sp.cancel(-(N - 1) * (N - 2) / (2 * R**2))
    results[f"S{N}"] = {
        "Ric_ratio": [str(r) for r in ratios],
        "expect_(N-1)/R^2": str(expect),
        "match": bool(ok),
        "Ricci_scalar": str(Rscalar),
        "Theta_(analytic)": str(Tval),
    }

# N=11 解析
N = 11
Theta11 = sp.cancel(-(N - 1) * (N - 2) / (2 * R**2))
results["S11"] = {"Theta_(analytic)": str(Theta11),
                  "Theta_at_R=1": str(Theta11.subs(R, 1)),
                  "note": "规律空间 N=11=1+4+6"}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(json.dumps(results, ensure_ascii=False, indent=2))
print("\nOUT ->", OUT)
