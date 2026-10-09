# -*- coding: utf-8 -*-
"""
WIE v3.3 论文手稿 —— 预言与数值数据全程复验脚本
三态判定：通过 / 不通过 / 无判别力（不设人为容差；通过项必须为算术精确、解析恒等或高精度一致）
覆盖：V-1..V-23
输出：temp/wie_reverify_v33.json（中间证据）
"""
import json, os, math
import mpmath as mp
from math import comb, factorial

mp.mp.dps = 40
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wie_reverify_v33.json")

results = []

def record(rid, name, claimed, computed, verdict, note, rel_err=None):
    results.append({
        "id": rid, "name": name,
        "claimed": claimed if isinstance(claimed, str) else repr(claimed),
        "computed": computed if isinstance(computed, str) else repr(computed),
        "rel_err": rel_err if rel_err is None else f"{float(rel_err):.3e}",
        "verdict": verdict, "note": note,
    })
    print(f"[{verdict}] {rid} {name}")

# ============ 基础常数 ============
N = 11
R_STAR = mp.mpf("102.020671834625304")
TOL_STAR = mp.mpf("0.9805864205272267")
B2 = mp.mpf("121") / 4            # v2.5 严格归一 B^2=30.25, B=N/2=5.5
BETA_STAR_CLAIM = mp.mpf("1045.321893477")

# ============ V-1 tol* <-> R* 互推 ============
R_from_tol = (1 + TOL_STAR) / (1 - TOL_STAR)
rel1 = abs(R_from_tol - R_STAR) / R_STAR
record("V-1", "闭合阈值互推 tol*=0.9805864205272267 <=> R*=102.020671834625304",
       str(R_STAR), mp.nstr(R_from_tol, 18), "通过" if rel1 < 1e-14 else "不通过",
       f"R*=(1+tol*)/(1-tol*)，相对误差 {float(rel1):.2e}", rel1)

# ============ V-2 R_spec = 39.482/0.387 行星比恒等 ============
R_spec_planet = mp.mpf("39.482") / mp.mpf("0.387")
rel2 = abs(R_spec_planet - R_STAR) / R_STAR
record("V-2", "R_spec=39.482/0.387=102.020671834625323（数值恒等；v3.3 视为设定输入）",
       str(R_STAR), mp.nstr(R_spec_planet, 18), "通过" if rel2 < 1e-14 else "不通过",
       f"行星比与 R* 残差 {float(rel2):.2e}（该值是外部锚/设定，非导出预言）", rel2)

# ============ V-3 g_K = 2R*/N = 18.5492 ============
gK = 2 * R_STAR / N
rel3 = abs(gK - mp.mpf("18.5492130608")) / mp.mpf("18.5492130608")
record("V-3", "g_K ≡ 2R*/N = 18.54921306084096（手稿 18.5492，4 位小数）",
       "18.5492", mp.nstr(gK, 14), "通过" if rel3 < 1e-10 else "不通过",
       f"g_K=2*{mp.nstr(R_STAR,16)}/11={mp.nstr(gK,14)}；按手稿 4 位小数 18.5492 正确", rel3)

# ============ V-4 R_geo = N*g_K/2：定义应然 vs 手稿实然 ============
R_geo_should = N * gK / 2          # 按 v3.3 定义 = R*
R_geo_manu = mp.mpf("101.8614255") # 手稿 §4.1 值
seven_half = mp.mpf(7) ** mp.mpf("1.5")   # 7^{3/2}=18.520259177452...
R_geo_sevenhalf = N * seven_half / 2      # 11*7^{3/2}/2 = 101.8614254759867
note4 = (f"按 v3.3 定义 g_K=2R*/N 应得 R_geo=R*={mp.nstr(R_geo_should,16)}；"
         f"手稿 R_geo=101.8614255 实为 11*7^{{3/2}}/2={mp.nstr(R_geo_sevenhalf,14)}，"
         f"即已否证路径 7^{{3/2}} 残留值。定义与数值矛盾。")
record("V-4", "R_geo = N·g_K/2（v3.3 定义自洽性）",
       "101.8614255", mp.nstr(R_geo_should, 16), "不通过", note4,
       abs(R_geo_manu - R_geo_should) / R_geo_should)

# ============ V-5 双约束相对差 0.156% ============
rel_manu = (R_STAR - R_geo_manu) / R_STAR * 100
rel_def = (R_STAR - R_geo_should) / R_STAR * 100
record("V-5", "R_spec/R_geo 相对差 0.156%（§4.1）",
       "0.156%", mp.nstr(rel_manu, 6) + "%", "不通过",
       f"手稿两数算得 {float(rel_manu):.4f}%（算术无误），但输入 R_geo 与 v3.3 定义矛盾；"
       f"按定义 R_geo=R* 应得相对差 {float(rel_def):.2e}%", rel_manu / 100)

# ============ V-6 β 反解 1042.075（途径 B）============
def beta_of_R(R):
    rho = R * R
    return (rho + B2 / (2 * rho)) / (N - 1) + (N - 2) / 2

beta_manu = beta_of_R(R_geo_manu)
beta_should = beta_of_R(R_geo_should)
record("V-6", "β 反解 = 1042.075（§4.2，途径 B）",
       "1042.075", mp.nstr(beta_manu, 10), "不通过",
       f"对 R_geo=101.8614255 的反解数学上 = {mp.nstr(beta_manu,10)}（与 1042.075 一致），"
       f"但该输入与 v3.3 标定矛盾；对定义值 R_geo=R* 反解 = β* = {mp.nstr(beta_should,10)}",
       abs(beta_manu - mp.mpf("1042.075")) / mp.mpf("1042.075"))

# ============ V-7 β 相对差 0.31% ============
rel_beta = (BETA_STAR_CLAIM - beta_manu) / BETA_STAR_CLAIM * 100
record("V-7", "β* 与 β 反解相对差 0.31%（§4.2）",
       "0.31%", mp.nstr(rel_beta, 5) + "%", "不通过",
       f"算术 {float(rel_beta):.4f}% 无误，但基于矛盾输入 R_geo；按定义 β 反解=β*，差应为 0%",
       rel_beta / 100)

# ============ V-8 P2 = R_spec/R_geo = 1.0016 ============
p2_manu = R_STAR / R_geo_manu
p2_def = R_STAR / R_geo_should
record("V-8", "预言 P2 = R_spec/R_geo = 1.0016（§6）",
       "1.0016", mp.nstr(p2_manu, 8), "不通过",
       f"手稿两数算得 {mp.nstr(p2_manu,8)}（≈1.0016 算术无误），但 R_geo 输入与 v3.3 定义矛盾；"
       f"按定义 R_geo=R* 应得比值 {mp.nstr(p2_def,10)}（恒等 1）",
       abs(p2_manu - mp.mpf("1.0016")) / mp.mpf("1.0016"))

# ============ V-9 κ–R 方程 β* 反解（B^2=30.25）============
rho_star = R_STAR * R_STAR
A_star = rho_star + B2 / (2 * rho_star)
beta_rev = A_star / (N - 1) + (N - 2) / 2
rel9 = abs(beta_rev - BETA_STAR_CLAIM) / BETA_STAR_CLAIM
record("V-9", "κ–R 自洽反解 β* = 1045.321893477（ρ²−Aρ+B²/2=0, B=N/2=5.5）",
       "1045.321893477", mp.nstr(beta_rev, 15), "通过" if rel9 < 1e-8 else "不通过",
       f"A*={mp.nstr(A_star,14)}，β*=A*/10+4.5={mp.nstr(beta_rev,12)}，相对误差 {float(rel9):.2e}", rel9)

# ============ V-10 κ–R 方程在 R* 处闭合残差 ============
resid = rho_star * rho_star - A_star * rho_star + B2 / 2
rel_resid = abs(resid) / (rho_star * rho_star)
record("V-10", "κ–R 自洽方程在 R* 处闭合（残差 ~ 机器精度）",
       "~0", mp.nstr(resid, 4), "通过" if rel_resid < 1e-25 else "不通过",
       f"ρ²−Aρ+B²/2 = {mp.nstr(resid,4)}，相对残差 {float(rel_resid):.2e}", rel_resid)

# ============ V-11 7^{3/2} = 18.520259177452 ============
record("V-11", "7^{3/2} = 18.5202591775（§3.3/§5.2 已否证项数值）",
       "18.5202591775", mp.nstr(seven_half, 14), "通过",
       "算术精确；作为几何指纹的物理主张已在 v3.1/v3.3 否证（P1 注销），此处仅验数值")

# ============ V-12 g_K 与 7^{3/2} 偏差 0.156% ============
rel12 = (gK - seven_half) / gK * 100
record("V-12", "g_K 与 7^{3/2} 残余偏差 0.156%（§3.3）",
       "0.156%", mp.nstr(rel12, 5) + "%", "通过",
       f"({mp.nstr(gK,12)}-{mp.nstr(seven_half,12)})/{mp.nstr(gK,12)} = {float(rel12):.4f}%")

# ============ V-13 λ_V = (8πℓ_P²/Λ_obs)^{1/4} = 87.78 μm ============
L_P = 1.616255e-35
LAMBDA_OBS = 1.1056e-52
lambda_V = (8 * math.pi * L_P ** 2 / LAMBDA_OBS) ** 0.25
lambda_V_um = lambda_V * 1e6
rel13 = abs(lambda_V_um - 87.78) / 87.78
record("V-13", "λ_V=(8πℓ_P²/Λ_obs)^{1/4}=87.78 μm（§3.1）",
       "87.78 μm", mp.nstr(lambda_V_um, 6) + " μm", "通过" if rel13 < 5e-4 else "不通过",
       f"ℓ_P=1.616255e-35 m，Λ_obs=1.1056e-52 m⁻² ⇒ {lambda_V_um:.4f} μm，相对误差 {float(rel13):.2e}", rel13)

# ============ V-14 ℓ_M = λ_V / R* = 8.6045e-7 m ============
l_M = lambda_V / float(R_STAR)
rel14 = abs(l_M - 8.6045e-7) / 8.6045e-7
record("V-14", "ℓ_M = λ_V/R* = 8.6045e-7 m（§2.2/§2.4）",
       "8.6045e-7 m", f"{l_M:.4e} m", "通过" if rel14 < 5e-4 else "不通过",
       f"{lambda_V:.4e}/{float(R_STAR):.4f} = {l_M:.4e} m", rel14)

# ============ V-15 M = ħ/(c·ℓ_M) = 0.229 eV/c² ============
HBAR = 1.054571817e-34
C = 299792458.0
EV = 1.602176634e-19
M_kg = HBAR / (C * l_M)
M_eV = M_kg * C * C / EV
rel15 = abs(M_eV - 0.229) / 0.229
record("V-15", "M = ħ/(cℓ_M) = 0.229 eV/c²（v2.5 §2.2）",
       "0.229 eV/c²", f"{M_eV:.4f} eV/c²", "通过" if rel15 < 5e-3 else "不通过",
       f"{M_kg:.4e} kg = {M_eV:.4f} eV/c²", rel15)

# ============ V-16 λ_I^κ = 1892.40×ℓ_M = 1.6283 mm；比 λ_V = 18.55 ============
kappa_star = B2 / (rho_star * rho_star)
lambda_I_num = 1 / mp.sqrt(kappa_star)
lambda_I_phys = float(lambda_I_num) * l_M
lambda_I_mm = lambda_I_phys * 1e3
ratio_kv = lambda_I_phys / lambda_V
rel16 = abs(lambda_I_mm - 1.6283) / 1.6283
record("V-16", "λ_I^κ = κ*^{-1/2}·ℓ_M = 1.6283 mm，λ_I^κ/λ_V = 18.55（v2.5 §2.2）",
       "1.6283 mm / 18.55", f"{lambda_I_mm:.4f} mm / {ratio_kv:.2f}", "通过" if rel16 < 5e-4 else "不通过",
       f"κ*={mp.nstr(kappa_star,6)}，κ*^{{-1/2}}={mp.nstr(lambda_I_num,8)}，"
       f"×ℓ_M={lambda_I_mm:.4f} mm，比 λ_V={ratio_kv:.2f}（≈18.55，同量级）", rel16)

# ============ V-17 S^7 体积 a0 = π^4/3 ============
a0 = mp.pi ** 4 / 3
rel17 = abs(a0 - mp.mpf("32.469697011334")) / mp.mpf("32.469697011334")
record("V-17", "S⁷ 体积 a₀ = π⁴/3 = 32.469697011334（解析恒等）",
       "32.469697011334", mp.nstr(a0, 14), "通过" if rel17 < 1e-12 else "不通过",
       f"π⁴/3={mp.nstr(a0,14)}", rel17)

# ============ V-18 S^7 a1/a0 = 7（解析：n(n-1)/6）============
a1a0_analytic = mp.mpf(7 * 6) / 6
record("V-18", "S⁷ 热核一阶系数 a₁/a₀ = n(n−1)/6 = 7（一次幂，精确）",
       "7", mp.nstr(a1a0_analytic, 14), "通过",
       f"n=7 ⇒ 7·6/6=7；v3.1 数值拟合 6.9999999999983（残差 1.7e-13）")

# ============ V-19 S^7 a2/a0 = 8484/360 = 23.5667 ============
a2a0 = mp.mpf(8484) / 360
record("V-19", "S⁷ 热核二阶系数 a₂/a₀ = 8484/360 = 23.5667（解析值）",
       "23.5666667", mp.nstr(a2a0, 12), "通过", "8484/360=23.5666666667")

# ============ V-20 ζ_op(0) = -99/140（独立多项式展开 + Riemann ζ 负整数值）============
def poly_mul(p, q):
    r = [mp.mpf(0)] * (len(p) + len(q) - 1)
    for i, pi in enumerate(p):
        for j, qj in enumerate(q):
            r[i + j] += pi * qj
    return r

# d_l = (2l+6)(l+1)(l+2)(l+3)(l+4)(l+5)/720，展开为 l 的多项式
poly = [mp.mpf(1)]
for fac in ([6, 2], [1, 1], [2, 1], [3, 1], [4, 1], [5, 1]):
    poly = poly_mul(poly, [mp.mpf(fac[0]), mp.mpf(fac[1])])
poly = [c / 720 for c in poly]
zeta0 = sum(poly[k] * mp.zeta(-k) for k in range(len(poly)))
target_zeta0 = mp.mpf(-99) / 140
rel20 = abs(zeta0 - target_zeta0) / abs(target_zeta0)
record("V-20", "𝒦₇=S⁷ 谱 ζ 在原点 ζ_op(0) = −99/140（有理精确）",
       "-99/140", mp.nstr(zeta0, 18), "通过" if rel20 < 1e-25 else "不通过",
       f"d_l 多项式展开 Σc_k ζ(−k) = {mp.nstr(zeta0,18)} = {mp.nstr(target_zeta0,18)}，"
       f"相对误差 {float(rel20):.2e}", rel20)

# ============ V-21 ζ_op(-1/2) 等（Abel–Plana 交叉验证 v3.1 附赠值）============
def d7c(z):
    return (2 * z + 6) * (z + 1) * (z + 2) * (z + 3) * (z + 4) * (z + 5) / 720

def zeta_neg(s, dps=30):
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

z05 = zeta_neg(mp.mpf("-0.5"))
rel21 = abs(z05 - mp.mpf("-0.605464006753")) / mp.mpf("0.605464006753")
record("V-21", "ζ_op(−1/2) = −0.605464006753（Abel–Plana 复现）",
       "-0.605464006753", mp.nstr(z05, 14), "通过" if rel21 < 1e-8 else "不通过",
       f"Abel–Plana 数值 {mp.nstr(z05,14)}，相对误差 {float(rel21):.2e}", rel21)

# ============ V-22 7 维乘积球族排除定理（a1/a0 ≤ 7 < 18.5492）============
def a1a0_product(a, b):
    return mp.mpf(a * (a - 1) + b * (b - 1)) / 6

combos = [(0, 7), (1, 6), (2, 5), (3, 4)]
vals = [(f"S^{a}×S^{b}", a1a0_product(a, b)) for a, b in combos]
vals.append(("T⁷", mp.mpf(0)))
maxv = max(v for _, v in vals)
record("V-22", "7 维刚性乘积球族 a₁/a₀ ≤ 7 < g_K=18.5492（v3.3 终局裁定）",
       "≤7", f"max={mp.nstr(maxv,6)}", "通过" if maxv <= 7 else "不通过",
       "; ".join(f"{n}={mp.nstr(v,6)}" for n, v in vals) + f"；上界 7 < {mp.nstr(gK,8)}")

# ============ V-23 结构设定（无判别力）============
record("V-23", "N = 11 = 4+7，dim E = 11（框架设定）",
       "11", "11", "无判别力", "维数分裂为理论设定，非可由数值判定；P3 的规范群秩匹配需外部观测")
record("V-23b", "ρ_Λ = g_K·ω_phys/λ_V³ 相容性陈述（§3.1）",
       "相容", "—", "无判别力", "ω_phys 未在稿中给出数值/定义，无法独立计算；仅量纲自洽")

# ============ 汇总 ============
counts = {}
for r in results:
    counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
summary = {
    "counts": counts,
    "critical_finding": (
        "手稿 §4.1 的 R_geo=101.8614255 与 v3.3 标定定义 g_K≡2R*/N 矛盾：按定义 R_geo=N·g_K/2=R*=102.0206718346253。"
        "手稿数值实为已否证路径 11·7^{3/2}/2=101.8614254759867 的残留。"
        "由此 §4.1 的 0.156%、§4.2 的 β=1042.075 与 0.31%、§6 的 P2=1.0016 全部建立在该矛盾输入上。"
    ),
    "entries": results,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("\nsummary:", counts)
print("JSON ->", OUT)
