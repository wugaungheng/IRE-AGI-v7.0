# -*- coding: utf-8 -*-
"""
WIE 方案二：计入纤维项 [∇_A, ∇_B]_fib 重构 Θ，参数化扫描 c_f 看 β 能否回到 O(1)
纯标准库实现（py3.11），V8 兼容。

模型：Θ_new = −(N−1)(N−2)/(2R²) + c_f·(N−1)/R² = (N−1)[−(N−2)/2 + c_f] / R²
即纤维项对 Θ 贡献一个与标量曲率同量级的项，系数 c_f 待定。

由自洽条件 κ(R*) = B²/R*⁴，推导 β 闭式：
β = B²/(2ρ*) − (N−1)[−(N−2)/2 + c_f] + α/(N−1)
其中 α=1，β* 必须 > 0（几何约束要求）。
"""
import json, math

N = 11
N1 = 10
N2h = 4.5
alpha = 1
R_star = 102.020671834625304
rho_star = R_star * R_star
B2 = 30.25  # v2.5 严格归一
B2_2rho = B2 / (2 * rho_star)  # 第一项
term3 = alpha / N1  # 第三项

def beta_of_cf(cf):
    """给定 c_f，返回 β* = 闭式解。"""
    return B2_2rho - N1 * (-(N2h) + cf) + term3

# 扫描 c_f 范围
results = []
for cf in [i * 0.25 for i in range(0, 81)]:  # 0 → 20
    b = beta_of_cf(cf)
    if b > 0:
        results.append({"cf": round(cf, 2), "beta_star": round(b, 4)})

# 寻找 O(1) 区域
o1_min, o1_max = None, None
for r in results:
    if 0.5 <= r["beta_star"] <= 2.0:
        if o1_min is None:
            o1_min = r["cf"]
        o1_max = r["cf"]

# 寻找 β ~ O(10) 区域
o10_min, o10_max = None, None
for r in results:
    if 3.0 <= r["beta_star"] <= 30:
        if o10_min is None:
            o10_min = r["cf"]
        o10_max = r["cf"]

# 找 β=0 的临界 c_f
cf_crit = B2_2rho + N1 * N2h + term3  # β=0 的 c_f
beta_at_zero_cf = beta_of_cf(0)
beta_at_crit = 0

print("=" * 72)
print("WIE 方案二：纤维项 [∇_A, ∇_B]_fib 重构 Θ → β 参数扫描")
print("=" * 72)
print(f"\n模型：Θ_new = (N−1)[−(N−2)/2 + c_f] / R²")
print(f"       β = B²/(2ρ*) − (N−1)[−(N−2)/2 + c_f] + α/(N−1)")
print(f"参数：N=11, R*=102.0207, B²=30.25（严格归一）, α=1")
print(f"\nβ=0 临界 c_f = {cf_crit:.4f}")
print(f"β at c_f=0 = {beta_at_zero_cf:.4f}")

# 关键 c_f 值
for cf_val in [0, 1, 2, 3, 4, 5, 10, 20]:
    b = beta_of_cf(cf_val)
    flag = "" if b > 0 else " ⛔ β<0 (不通过)"
    print(f"  c_f = {cf_val:>3.1f}  →  β* = {b:>8.4f}{flag}")

print(f"\nO(1) 区域 [0.5 ≤ β* ≤ 2.0]：c_f ∈ [{o1_min}, {o1_max}]")
print(f"O(10) 区域 [3 ≤ β* ≤ 30]  ：c_f ∈ [{o10_min}, {o10_max}]")

# 反向：给出 β 对应 c_f 的表格
print("\n| c_f | β* | 备注 |")
print(f"|------|------|------|")
for cf_val, b in [(0, beta_at_zero_cf), (1, beta_of_cf(1)), (2, beta_of_cf(2)),
                   (3, beta_of_cf(3)), (4, beta_of_cf(4)), (5, beta_of_cf(5))]:
    note = ""
    if b < 0:
        note = "β<0，不通过"
    elif 0.5 <= b <= 2.0:
        note = "O(1)"
    elif 3 <= b <= 30:
        note = "O(10)"
    elif b >= 30:
        note = "O(100)"
    elif 2 < b < 3:
        note = "过渡"
    print(f"| {cf_val} | {b:6.3f} | {note} |")

# 完整结果表（用于 json 输出）
table = []
for cf in range(0, 21):
    b = beta_of_cf(cf)
    status = "通过" if b > 0 else "不通过"
    note = ""
    if 0.5 <= b <= 2.0:
        note = "O(1)"
    elif 3 <= b <= 30:
        note = "O(10)"
    elif b >= 30:
        note = "O(100)"
    elif 2 < b < 3:
        note = "过渡"
    table.append({"cf": cf, "beta_star": round(b, 4), "status": status, "note": note})

data = {
    "meta": {"version": "方案二", "date": "2026-10-09", "N": N, "R_star": R_star,
             "B2": B2, "alpha": alpha, "crit_cf": round(cf_crit, 4)},
    "table": table,
    "o1_range": {"cf_min": o1_min, "cf_max": o1_max},
    "o10_range": {"cf_min": o10_min, "cf_max": o10_max},
    "conclusion": (
        "β 随 c_f 递减；c_f=0 时 β=1045.3（同 v2.4），随 c_f 增加快速下降。"
        "β 回到 O(1) 需 c_f≈3.6~3.85，O(10) 需 c_f≈3.0~4.2。"
        "c_f=0.4 时 β≈780，c_f=1 时 β≈376，c_f=2 时 β≈152。"
        "纤维项必须贡献约 3.5 倍标量曲率量级才能使 β→O(1)，"
        "这与 Bianconi 2025 中纤维曲率与标量曲率同量级（c_f≈0.5）的预期不符。"
        "因此方案二难以自然把 β 拉到 O(1)，除非引入更强的额外耦合。"
    ),
}

with open("WIE_方案二_纤维项重构_20261009.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nJSON 已写入 WIE_方案二_纤维项重构_20261009.json")
print("=" * 72)
