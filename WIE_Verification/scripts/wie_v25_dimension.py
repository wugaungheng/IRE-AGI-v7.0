# -*- coding: utf-8 -*-
"""
WIE v2.5 · 量纲自洽化 + 基态宽度 O(1) 系数归一 + lambda_V 定标复核
纯标准库实现（py3.11），与 IRE-AGI_V8_Standalone 无依赖冲突。
"""
import json
import math
from decimal import Decimal, getcontext

getcontext().prec = 60

# ---------------------------------------------------------------- 常数
PI = Decimal("3.14159265358979323846264338327950288419716939937511")
N = 11                      # 规律空间维数 N = 1 + 4 + 6
N1 = Decimal(N - 1)         # 10
N2h = Decimal(N - 2) / 2    # 4.5
R_STAR = Decimal("102.020671834625304")   # v2.4 目标半径
RHO_STAR = R_STAR * R_STAR

HBAR = 1.054571817e-34      # J*s
C = 299792458.0             # m/s
G = 6.67430e-11             # m^3 kg^-1 s^-2
L_P = 1.616255e-35          # m
LY = 9.4607304725808e15     # m
LAMBDA_OBS = 1.1056e-52     # m^-2 (Planck 2018)
EV = 1.602176634e-19        # J


def solve_branch(B2, label):
    """给定 B^2，按 v2.3 二次闭式反解 beta* 并判定闭合。"""
    A = RHO_STAR + B2 / (2 * RHO_STAR)
    beta = A / N1 + N2h
    Delta = A * A - 2 * B2
    s = Delta.sqrt()
    rho_p = (A + s) / 2
    rho_m = (A - s) / 2
    kappa = B2 / (RHO_STAR * RHO_STAR)
    kappa_geo = 2 * (Decimal(-45) / RHO_STAR - 1) + 2 * beta * N1 / RHO_STAR
    resid = RHO_STAR * RHO_STAR - A * RHO_STAR + B2 / 2
    rel = resid / (RHO_STAR * RHO_STAR)
    return {
        "label": label,
        "B2": float(B2),
        "B": float(B2.sqrt()),
        "A_star": float(A),
        "beta_star": float(beta),
        "beta_star_str": f"{beta:.9f}",
        "Delta": float(Delta),
        "rho_plus": float(rho_p),
        "R_plus": float(rho_p.sqrt()),
        "rho_minus": f"{rho_m:.10g}",
        "residual": float(resid),
        "rel_residual": f"{rel:.3e}",
        "kappa_star": float(kappa),
        "kappa_geo": float(kappa_geo),
        "kappa_gap": float(abs(kappa - kappa_geo)),
        "omega": float(kappa.sqrt()),
        "lambda_I_num": float(1 / kappa.sqrt()),
        "R_plus_matches_Rstar": float(abs(rho_p.sqrt() - R_STAR)),
    }


# ---------------------------------------------------------------- 1. O(1) 系数归一
B2_v24 = Decimal(121)                 # B = c^2 N hbar / sqrt(M) = 11
B2_strict = Decimal(121) / Decimal(4)  # 严格谐振子 B_strict = B/2 -> B^2/4 = 30.25

branch_v24 = solve_branch(B2_v24, "v2.4 采用的 O(1) 系数 (=1)")
branch_strict = solve_branch(B2_strict, "v2.5 严格归一 (系数=1/4)")

d_beta = branch_strict["beta_star"] - branch_v24["beta_star"]

# ---------------------------------------------------------------- 2. 物理尺度
xi_Lambda = LAMBDA_OBS ** (-0.25)                     # m，宇宙学尺度 Lambda^{-1/4}
xi_Lambda_ly = xi_Lambda / LY
lambda_V = (8 * math.pi * L_P ** 2 / LAMBDA_OBS) ** 0.25   # m，真空微观尺度
lambda_V_um = lambda_V * 1e6

# v2.1 原文 lambda_V = 28 um 所隐含的 Lambda
lambda_V_v21 = 28e-6
Lambda_implied = 8 * math.pi * L_P ** 2 / lambda_V_v21 ** 4
ratio_Lambda = Lambda_implied / LAMBDA_OBS

# 结构式：lambda_V = (8 pi)^{1/4} * sqrt(l_P * xi_Lambda)
lambda_V_struct = (8 * math.pi) ** 0.25 * math.sqrt(L_P) * xi_Lambda

# ---------------------------------------------------------------- 3. 量纲桥：K 长度单位
# 母作用量第三项 hbar^2/(2M)|d_L Psi|^2  => 自然单位下 K 的长度单位 l_M = hbar/(M c)
# 若令 K 半径 R* 对应真空微观尺度 lambda_V，则 l_M 定标、M 被约束
l_M = lambda_V / float(R_STAR)
M_fiber = HBAR / (C * l_M)            # kg
M_fiber_eV = M_fiber * C * C / EV     # eV/c^2

# 该定标下 lambda_I（若取 kappa^{-1/2}）的物理值
lambda_I_kappa_m = branch_strict["lambda_I_num"] * l_M
lambda_I_kappa_mm = lambda_I_kappa_m * 1e3

# 反比：lambda_I 若取 0.1 光年，则 l_M 应为多少 -> 需要的 M
l_M_ly = 0.1 * LY / branch_strict["lambda_I_num"]
M_ly = HBAR / (C * l_M_ly)
M_ly_eV = M_ly * C * C / EV
ratio_M = M_fiber / M_ly            # 两套定标下的 M 之比

# 尺度比
ratio_sigma = lambda_I_kappa_m / lambda_V            # kappa^{-1/2} 物理值 / lambda_V
ratio_lambda = xi_Lambda / lambda_V                  # Lambda^{-1/4} / lambda_V

result = {
    "meta": {
        "version": "v2.5",
        "date": "2026-10-09",
        "N": N,
        "alpha": 1,
        "units": "hbar=M=c=1 for K-sector; SI for physical scales",
    },
    "1_O1_normalization": {
        "v24": branch_v24,
        "v25_strict": branch_strict,
        "delta_beta": d_beta,
        "conclusion": "O(1) 系数由 1 归一为 1/4，beta* 仅移 4.4e-4 量级，R-2 闭合结构不变",
    },
    "2_physical_scales_SI": {
        "Lambda_obs_m-2": LAMBDA_OBS,
        "xi_Lambda_m": xi_Lambda,
        "xi_Lambda_ly": xi_Lambda_ly,
        "lambda_V_m": lambda_V,
        "lambda_V_um": lambda_V_um,
        "lambda_V_struct_check_um": lambda_V_struct * 1e6,
        "lambda_V_v21_um": 28.0,
        "Lambda_implied_by_28um_m-2": Lambda_implied,
        "ratio_Lambda_implied_over_obs": ratio_Lambda,
        "lambda_V_corrected_over_v21": lambda_V / lambda_V_v21,
    },
    "3_dimension_bridge": {
        "l_M_m": l_M,
        "M_fiber_kg": M_fiber,
        "M_fiber_eV": M_fiber_eV,
        "lambda_I_from_kappa_mm": lambda_I_kappa_mm,
        "l_M_for_0.1ly_m": l_M_ly,
        "M_for_0.1ly_eV": M_ly_eV,
        "ratio_M_two_calibrations": ratio_M,
        "ratio_kappa_phys_over_lambda_V": ratio_sigma,
        "ratio_xiLambda_over_lambda_V": ratio_lambda,
        "conclusion": "kappa^{-1/2} 物理值 ~1.63 mm，与 lambda_V ~87.8 um 同量级(差 18.6 倍)；若强行令 lambda_I = 0.1 光年，需 M ~ 3.9e-19 eV，与 lambda_V 定标下的 M ~ 0.229 eV 相差 ~5.8e17 倍 -> N-1 等式不成立",
    },
}

with open("WIE_v2.5_量纲自洽化_20261009.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- 控制台摘要
print("=" * 72)
print("WIE v2.5 量纲自洽化 + O(1) 归一")
print("=" * 72)
print("\n[1] 基态宽度 O(1) 系数归一")
print(f"    v2.4:  B^2={branch_v24['B2']:>8.3f}  beta*={branch_v24['beta_star']:.9f}  "
      f"kappa*={branch_v24['kappa_star']:.6e}  rel_res={branch_v24['rel_residual']}")
print(f"    v2.5:  B^2={branch_strict['B2']:>8.3f}  beta*={branch_strict['beta_star']:.9f}  "
      f"kappa*={branch_strict['kappa_star']:.6e}  rel_res={branch_strict['rel_residual']}")
print(f"    Delta beta* = {d_beta:.6e}")
print(f"    R+ 命中 R* 偏差 = {branch_strict['R_plus_matches_Rstar']:.3e}")
print(f"    kappa*-kappa_geo 残差 = {branch_strict['kappa_gap']:.3e}")
print(f"    判别式 Delta = {branch_strict['Delta']:.6e} > 0 -> 两实根, 闭合结构不变")

print("\n[2] 物理尺度复核")
print(f"    Lambda_obs        = {LAMBDA_OBS:.4e} m^-2")
print(f"    xi_Lambda = L^-1/4= {xi_Lambda:.4e} m = {xi_Lambda_ly:.5f} 光年 = {xi_Lambda/1.495978707e11:.1f} AU")
print(f"    lambda_V (自洽)   = {lambda_V:.4e} m = {lambda_V_um:.2f} um")
print(f"    结构式核对        = {lambda_V_struct*1e6:.2f} um  (=(8pi)^1/4 sqrt(l_P) xi_Lambda)")
print(f"    v2.1 取值 28 um   -> 隐含 Lambda = {Lambda_implied:.4e} m^-2")
print(f"    隐含/观测 = {ratio_Lambda:.2f}  -> 28um 与 Lambda_obs 不自洽")

print("\n[3] 量纲桥 l_M = hbar/(M c)")
print(f"    若令 K 半径 R* <-> lambda_V : l_M = {l_M:.4e} m,  M = {M_fiber_eV:.3f} eV/c^2")
print(f"    此时 kappa^-1/2 物理值 = {lambda_I_kappa_mm:.4e} mm")
print(f"    尺度比 lambda_I^kappa / lambda_V = {ratio_sigma:.2f}")
print(f"    若强令 lambda_I = 0.1 光年 : 需 M = {M_ly_eV:.4e} eV/c^2")
print(f"    两套定标的 M 之比 = {ratio_M:.3e} => N-1 等式不成立")
print(f"    参考: xi_Lambda/lambda_V = {ratio_lambda:.3e}")
print(f"\n[4] lambda_I(V3, >=0.1 ly = {0.1*LY:.3e} m) vs xi_Lambda = {xi_Lambda:.3e} m, 相差 {0.1*LY/xi_Lambda:.1f} 倍")
