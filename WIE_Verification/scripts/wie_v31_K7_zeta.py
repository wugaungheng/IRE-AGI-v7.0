# -*- coding: utf-8 -*-
"""
WIE v3.1 —— K7 (=S^7) 谱 zeta 函数严格验证脚本
目的：验证 v3.0 的断言 g_K = (N-4)^{3/2} = 7^{3/2} = 18.5203 是否由 K7 谱几何导出。
结论（本脚本可复现）：
  - 热核系数 a1/a0 = 7 精确（= dim K7，一次幂）
  - 但 a_k/a_0 与 zeta_op(s) 中不存在 18.55（或 sqrt7）
  - 故 3/2 次幂无谱几何来源，N-7 残差 0.156% 属数值巧合
输出：全部关键数值（供报告引用）
"""
import mpmath as mp
from math import comb, factorial
mp.mp.dps = 35

# ---------- 0. S^7 谱数据 ----------
# 拉普拉斯谱: lambda_l = l(l+6), l=0,1,2,...
# 简并: d_l = C(l+5,5) * (l+3)/3   （等价 (2l+6)(l+1)(l+2)(l+3)(l+4)(l+5)/720）
def d_l(l):
    return comb(l + 5, 5) * (l + 3) // 3

def check_degeneracy():
    for l in range(6):
        a = d_l(l)
        b = (2 * l + 6) * factorial(l + 5) // (factorial(l) * 720)
        assert a == b, (l, a, b)
    print("[校验] d_l 两种表达式一致: d_0..d_5 =", [d_l(l) for l in range(6)])

# ---------- 1. 热核 K(t)= sum d_l e^{-lambda_l t} = (4pi t)^{-7/2} sum a_k t^k ----------
def K(t):
    s = mp.mpf(0); l = 0
    while True:
        term = mp.mpf(d_l(l)) * mp.e ** (-mp.mpf(l * (l + 6)) * t)
        s += term
        if l > 50 and term < mp.mpf('1e-45'):
            break
        l += 1
        if l > 3000:
            break
    return s

def fit_weyl(nterms=5):
    pts = [mp.mpf('1.5e-4') * (mp.mpf('1.15') ** i) for i in range(8)]
    rows, bv = [], []
    for t in pts:
        rows.append([t ** k for k in range(nterms)])
        bv.append(K(t) * ((4 * mp.pi * t) ** mp.mpf('3.5')))
    ak = mp.lu_solve(mp.matrix(rows), mp.matrix(bv))
    return ak

# ---------- 2. zeta 正规化: 负变元用 Abel-Plana ----------
def d7c(z):  # 解析延拓用的 d_l
    return (2 * z + 6) * (z + 1) * (z + 2) * (z + 3) * (z + 4) * (z + 5) / 720

def zeta_neg(s, dps=25):
    mp.mp.dps = dps
    def h(u):
        u = mp.mpf(u); y = u * u; z = 1j * float(y)
        imf = d7c(z) * (z * (z + 6)) ** (-s)
        imf = imf.imag
        den = mp.e ** (2 * mp.pi * y) - 1
        if den < mp.mpf('1e-18'):
            den = 2 * mp.pi * y
        return -2 * mp.mpf(imf) / den * (2 * u)
    return mp.quad(h, [0, 0.1, 0.3, 0.7, 1.5, 3, 6, 8])

def zeta_pos(s, L=200000):
    tot = mp.mpf(0); l = 1
    while l < L:
        t = mp.mpf(d_l(l)) * mp.mpf(l * (l + 6)) ** (-s)
        tot += t
        if t < mp.mpf('1e-40') and l > 1000:
            break
        l += 1
    return tot

# ---------- 主流程 ----------
if __name__ == '__main__':
    check_degeneracy()

    ak = fit_weyl()
    print("\n[热核 Weyl 系数] (S^7)")
    for k in range(5):
        print("  a%d/a0 = %-18s" % (k, mp.nstr(ak[k] / ak[0], 14)))
    print("  a0 = Vol(S^7) = pi^4/3 =", mp.nstr(mp.pi ** 4 / 3, 14))
    print("  理论: a1/a0 = 7 ; a2/a0 = 8484/360 =", mp.nstr(mp.mpf(8484) / 360, 14))

    print("\n[谱 zeta 值] (S^7)")
    print("  zeta_op(0)    =", mp.nstr(sum(mp.mpf([1, 157, 949, 4, 13, 1, 1][k]) /
          mp.mpf([1, 60, 360, 3, 36, 20, 360][k]) * mp.zeta(-k) for k in range(7)), 14),
          "  (= -99/140 = %s)" % mp.nstr(mp.mpf(-99) / 140, 14))
    for s in [-0.5, -1.5, -2.5]:
        print("  zeta_op(%+.1f) = %s" % (s, mp.nstr(zeta_neg(s), 14)))
    for s in [4, 5]:
        print("  zeta_op(%d)    = %s" % (s, mp.nstr(zeta_pos(s), 14)))

    # ---------- 3. 与目标比对 ----------
    print("\n[与目标 18.5492127 比对]")
    target = mp.mpf('18.5492127')
    for nm, v in [("7^(3/2)", mp.mpf(7) ** mp.mpf('1.5')),
                  ("a2/a0", mp.mpf(8484) / 360),
                  ("a1/a0", mp.mpf(7)),
                  ("a0*(4/7) [事后拟合]", (mp.pi ** 4 / 3) * mp.mpf(4) / 7)]:
        print("  %-22s = %-12s 偏差 %+.4f%%" % (nm, mp.nstr(v, 12), (v - target) / target * 100))

    # ---------- 4. R* 身份核验 ----------
    r_min, r_max = mp.mpf('0.387'), mp.mpf('39.482')   # 水星 / 冥王星 半长轴 (AU)
    R = r_max / r_min
    tol = (r_max - r_min) / (r_max + r_min)
    print("\n[R* 身份核验]")
    print("  R* = r_max/r_min = 39.482/0.387 =", mp.nstr(R, 18))
    print("  tol* = 39.095/39.869 =", mp.nstr(tol, 18))
    print("  与 v2.3/v3.0 记录值 102.0206718346253 / 0.9805864205272267 一致 ->",
          abs(R - mp.mpf('102.0206718346253')) < mp.mpf('1e-10'))
    print("  2R*/N = 2R*/11 =", mp.nstr(2 * R / 11, 12), " (v3.0 的 18.5492131)")
    print("  R_geo = N*(N-4)^{3/2}/2 = 11*7^1.5/2 =", mp.nstr(11 * mp.mpf(7) ** mp.mpf('1.5') / 2, 12),
          " 相对差 %.4f%%" % ((11 * mp.mpf(7) ** mp.mpf('1.5') / 2 - R) / R * 100))
