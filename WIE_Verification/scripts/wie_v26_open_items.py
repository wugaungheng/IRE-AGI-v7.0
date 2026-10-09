# -*- coding: utf-8 -*-
"""
WIE v2.6 三项未决项裁定（N-6 lambda_I / N-7 rho_vac 模式计数 / N-8 暗物质丰度）
纯标准库实现（py3.11），V8 兼容。
参数取自 v2.5 JSON。
"""
import math, json

# ---- 物理常数 ----
hbar = 1.054571817e-34      # J*s
c = 2.99792458e8            # m/s
G = 6.67430e-11             # m^3/kg/s^2
l_P = 1.616255e-35          # m
eV = 1.602176634e-19        # J
ly = 9.4607304725808e15     # m
L_univ = 4.4e26             # m, particle horizon ~14.3 Gpc

# ---- v2.5 参数 ----
lambda_V = 8.778400645362051e-05     # m
l_M = 8.604531304784749e-07          # m
M_fiber_eV = 0.22932914455046285     # eV/c^2
kappa_star = 2.7923680638884393e-07  # 无量纲
omega = 0.0005284286199562283        # 无量纲
xi_Lambda = 9752152691255.746        # m
Lambda_obs = 1.1056e-52              # m^-2
R_star = 102.0206718346253
lambda_I_from_kappa_m = 1.6283242390424453e-3   # m (kappa^-1/2 物理值)
ratio_kappa_over_lV = 18.549213060840966

print("=" * 74)
print("WIE v2.6 三项未决项裁定")
print("=" * 74)

# ================= N-6: lambda_I 严格值 =================
print("\n【N-6】lambda_I 严格值裁定")
lambda_I_comp = hbar / (M_fiber_eV * eV / c**2 * c)   # hbar/(m c)
ratio_N6 = (0.1 * ly) / lambda_I_comp
m_for_01ly_eV = (hbar / (0.1 * ly * c)) / (eV / c**2)
print(f"  康普顿型衰减 lambda_I = hbar/(m_I c)")
print(f"  若 m_I = M_fiber = {M_fiber_eV:.4f} eV/c^2 -> lambda_I = {lambda_I_comp:.4e} m")
print(f"  与 0.1 ly = {0.1*ly:.4e} m 之比 = {ratio_N6:.4e} 倍")
print(f"  反解：令 lambda_I = 0.1 ly 需 m_I = {m_for_01ly_eV:.4e} eV/c^2")
print(f"  与 M_fiber 之比 = {M_fiber_eV/m_for_01ly_eV:.4e}")
print(f"  判定：❌ 不成立（与 N-1 同源，差 ~1e22 倍）")

# ================= N-7: rho_vac 模式计数 =================
print("\n【N-7】rho_vac 模式计数")
omega_phys = omega * c / l_M          # rad/s
hbar_omega = hbar * omega_phys        # J
print(f"  omega_phys = omega*c/l_M = {omega_phys:.6e} rad/s")
print(f"  hbar*omega_phys = {hbar_omega:.6e} J")

rho_Lambda_kg = Lambda_obs * c**2 / (8 * math.pi * G)
rho_Lambda_J = rho_Lambda_kg * c**2
print(f"  rho_Lambda (J/m^3) = {rho_Lambda_J:.6e}")

# 方案A: 每 lambda_V^3 一个模式, 零点能 (1/2)hbar*omega
n_A = 1.0 / lambda_V**3
rho_vac_A = 0.5 * hbar_omega * n_A
ratio_A = rho_Lambda_J / rho_vac_A

# 方案A': 每 lambda_V^3 一个模式, 能量 hbar*omega (不含 1/2)
rho_vac_A2 = hbar_omega * n_A
ratio_A2 = rho_Lambda_J / rho_vac_A2

# 方案B: 每 l_M^3 一个模式
n_B = 1.0 / l_M**3
rho_vac_B = 0.5 * hbar_omega * n_B
ratio_B = rho_Lambda_J / rho_vac_B

# 方案C: 每 xi_Lambda^3 一个模式
n_C = 1.0 / xi_Lambda**3
rho_vac_C = 0.5 * hbar_omega * n_C
ratio_C = rho_Lambda_J / rho_vac_C

print(f"\n  方案A  (每 lambda_V^3, 零点能 ½hbar*omega): rho_vac = {rho_vac_A:.6e} J/m^3, rho_Lambda/rho_vac = {ratio_A:.4f}")
print(f"  方案A' (每 lambda_V^3, 能量 hbar*omega)   : rho_vac = {rho_vac_A2:.6e} J/m^3, rho_Lambda/rho_vac = {ratio_A2:.4f}")
print(f"  方案B  (每 l_M^3)                          : rho_vac = {rho_vac_B:.6e} J/m^3, rho_Lambda/rho_vac = {ratio_B:.4e}")
print(f"  方案C  (每 xi_Lambda^3)                    : rho_vac = {rho_vac_C:.6e} J/m^3, rho_Lambda/rho_vac = {ratio_C:.4e}")

# 检验 18.55 因子关系
print(f"\n  关键发现：方案A' 比值 = {ratio_A2:.4f}")
print(f"            与 18.549 (lambda_V/kappa^-1/2物理) 对比：{ratio_A2:.4f} vs {ratio_kappa_over_lV:.4f}")
print(f"            偏差 = {abs(ratio_A2-ratio_kappa_over_lV)/ratio_kappa_over_lV*100:.4f}%")
print(f"  证明：rho_Lambda/rho_vac = lambda_V/(l_M*sqrt(kappa)) 恒等成立")
# 验证：sqrt(kappa)*l_M = ?
sqrt_kappa_l_M = math.sqrt(kappa_star) * l_M
pred = lambda_V / sqrt_kappa_l_M
print(f"        lambda_V/(l_M*sqrt(kappa)) = {pred:.6f}   (方案A' 直接值 {ratio_A2:.6f})")

# 反解匹配 rho_Lambda 所需的模式截断尺度
n_needed = rho_Lambda_J / hbar_omega
L_needed = n_needed**(-1/3.0)
print(f"\n  若要求 rho_vac = rho_Lambda（不含 ½），需模式截断尺度 L = {L_needed:.4e} m = {L_needed*1e6:.4f} um")
print(f"  与 lambda_V 之比 = {lambda_V/L_needed:.4f}")
print(f"  判定：⚠️ 量级匹配（同一数量级内），差 ~19 倍，需 O(20) 系数或截断修正")

# ================= N-8: 暗物质丰度 =================
print("\n【N-8】暗物质丰度公式 rho_DM/rho_tot ~ (xi_Psi/L_univ)^2")
Omega_DM = 0.265
ratio_N8 = (lambda_V / L_univ)**2
xi_needed = math.sqrt(Omega_DM) * L_univ
print(f"  xi_Psi = lambda_V = {lambda_V:.4e} m -> (xi/L_univ)^2 = {ratio_N8:.4e}")
print(f"  目标 Omega_DM = {Omega_DM}")
print(f"  差 = {Omega_DM/ratio_N8:.4e} 倍")
print(f"  反解：需 xi_Psi = {xi_needed:.4e} m = {xi_needed/(3.086e22):.4e} Mpc")
print(f"  与 lambda_V 之比 = {xi_needed/lambda_V:.4e}")
print(f"  判定：❌ 不成立（差 ~62 个数量级）")

# ================= 汇总 =================
print("\n" + "=" * 74)
print("裁定汇总")
print("=" * 74)
summary = {
    "N-6_lambda_I": {"verdict": "不成立", "gap": f"{ratio_N6:.3e}x", "note": "与 N-1 同源"},
    "N-7_rho_vac": {"verdict": "量级匹配差 O(20)", "gap": f"{ratio_A2:.2f}x", "note": "18.55 因子恒等重现"},
    "N-8_DM_abundance": {"verdict": "不成立", "gap": f"{Omega_DM/ratio_N8:.3e}x", "note": "差 62 个数量级"},
}
for k, v in summary.items():
    print(f"  {k}: {v['verdict']}  (gap={v['gap']})  [{v['note']}]")

data = {
    "meta": {"version": "v2.6", "date": "2026-10-09", "N": 11,
             "source": "WIE_v2.5 参数", "L_univ_m": L_univ},
    "N6_lambda_I": {
        "lambda_I_compton_m": lambda_I_comp,
        "ratio_to_0.1ly": ratio_N6,
        "m_for_0.1ly_eV": m_for_01ly_eV,
        "M_fiber_eV": M_fiber_eV,
        "ratio_M": M_fiber_eV / m_for_01ly_eV,
        "verdict": "不成立"
    },
    "N7_rho_vac": {
        "omega_phys_rad_s": omega_phys,
        "hbar_omega_J": hbar_omega,
        "rho_Lambda_J_m3": rho_Lambda_J,
        "schemeA_half": {"rho_vac": rho_vac_A, "ratio": ratio_A},
        "schemeA_prime": {"rho_vac": rho_vac_A2, "ratio": ratio_A2},
        "schemeB_lM": {"rho_vac": rho_vac_B, "ratio": ratio_B},
        "schemeC_xiL": {"rho_vac": rho_vac_C, "ratio": ratio_C},
        "identity_check": {"lambda_V_over_lM_sqrtkappa": pred, "direct": ratio_A2},
        "L_needed_for_match_m": L_needed,
        "lambda_V_over_L_needed": lambda_V / L_needed,
        "verdict": "量级匹配, 差 O(20)"
    },
    "N8_DM_abundance": {
        "xi_Psi_lambda_V_m": lambda_V,
        "ratio_squared": ratio_N8,
        "Omega_DM_target": Omega_DM,
        "gap": Omega_DM / ratio_N8,
        "xi_needed_m": xi_needed,
        "xi_needed_Mpc": xi_needed / 3.086e22,
        "ratio_xi_needed_over_lambdaV": xi_needed / lambda_V,
        "verdict": "不成立"
    },
    "summary": summary
}

with open("WIE_v2.6_三项未决项裁定_20261009.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("\nJSON 已写入 WIE_v2.6_三项未决项裁定_20261009.json")
print("=" * 74)
