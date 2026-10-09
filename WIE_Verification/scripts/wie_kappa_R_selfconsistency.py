# -*- coding: utf-8 -*-
"""
WIE v2.3 · kappa–R 自洽方程求解器  (V8 兼容：纯标准库，Python 3.11，无第三方依赖)

物理/几何背景
-------------
规律空间 K 取半径 R 的常曲率球面 S^N (N=11=1+4+6)。
(1) 几何反解势 (v2.2)：alpha*M - beta*Rc = Theta*g  =>  d_A d_B V = kappa * g_AB
    球面:  Rc_AB = (N-1)/R^2 g_AB ,  Theta = -(N-1)(N-2)/(2R^2)
    =>     kappa(R) = 2[ (Theta - alpha)/alpha + (beta/alpha)(N-1)/R^2 ]
    取归一化 alpha = 1 :
        kappa(R) = 2[ A/R^2 - 1 ] ,   A = (N-1)[ beta - (N-2)/2 ]

(2) 约束自洽 (V(L)=½ kappa |L|^2 的谐振子基态宽度)：
        R^2 = c^2 * N * hbar / sqrt(M kappa)  ==  B / sqrt(kappa) ,  B = c^2 N hbar / sqrt(M)
    =>  kappa = B^2 / R^4

(3) 联立 (1)(2)，令 rho = R^2 :
        rho^2 - A rho + B^2/2 = 0
        rho = [ A ± sqrt(A^2 - 2 B^2) ] / 2          (存在条件: A^2 >= 2 B^2, rho>0)

反解：给定 WIE 已有的闭合阈值半径 R* (v1.0 toll 阈值)，则
        A* = rho* + B^2/(2 rho*) ,   beta* = A*/(N-1) + (N-2)/2
"""
from __future__ import annotations
import json, math, os


def A_of(N: int, beta: float) -> float:
    return (N - 1) * (beta - (N - 2) / 2.0)


def kappa_of_R(N: int, R: float, beta: float, alpha: float = 1.0) -> float:
    """kappa(R) = 2[ (Theta-alpha)/alpha + (beta/alpha)(N-1)/R^2 ], Theta=-(N-1)(N-2)/(2R^2)"""
    Theta = -(N - 1) * (N - 2) / (2.0 * R * R)
    return 2.0 * ((Theta - alpha) / alpha + (beta / alpha) * (N - 1) / (R * R))


def Theta_of_R(N: int, R: float) -> float:
    return -(N - 1) * (N - 2) / (2.0 * R * R)


def solve_branches(N: int, beta: float, B2: float):
    """解 rho^2 - A rho + B^2/2 = 0，返回 [(rho, R, kappa), ...]（rho>0, kappa>0）"""
    A = A_of(N, beta)
    disc = A * A - 2.0 * B2
    if disc < 0:
        return None, A, disc
    sq = math.sqrt(disc)
    out = []
    for rho in ((A + sq) / 2.0, (A - sq) / 2.0):
        if rho <= 0:
            continue
        R = math.sqrt(rho)
        kappa = B2 / (rho * rho)           # = kappa from confinement
        kappa_geo = kappa_of_R(N, R, beta)  # should equal kappa (residual check)
        out.append({"rho": rho, "R": R, "kappa": kappa,
                    "kappa_geo": kappa_geo, "residual": kappa - kappa_geo})
    return out, A, disc


def inverse_beta(N: int, R_star: float, B2: float) -> dict:
    """给定参考半径 R*，反解读出自洽所需的 beta*"""
    rho = R_star * R_star
    A_star = rho + B2 / (2.0 * rho)
    beta_star = A_star / (N - 1) + (N - 2) / 2.0
    kappa_star = B2 / (rho * rho)
    return {"R_star": R_star, "rho_star": rho, "A_star": A_star,
            "beta_star": beta_star, "kappa_star": kappa_star,
            "Theta_star": Theta_of_R(N, R_star),
            "residual": kappa_star - kappa_of_R(N, R_star, beta_star)}


def main():
    N = 11
    # 归一化单位：hbar = M = c = 1  => B = N, B2 = N^2
    hbar = M = c = 1.0
    B = c * c * N * hbar / math.sqrt(M)
    B2 = B * B

    out = {"model": "WIE v2.3 kappa-R self-consistency (S^N, alpha=1)",
           "N": N, "units": "hbar=M=c=1", "B": B, "B2": B2,
           "equation": "rho^2 - A rho + B^2/2 = 0,  rho=R^2",
           "A_def": "A=(N-1)(beta-(N-2)/2)"}

    # 存在性阈值
    beta_c = (N - 2) / 2.0 + math.sqrt(2.0 * B2) / (N - 1)
    out["existence"] = {"A_crit": math.sqrt(2.0 * B2),
                        "beta_min_ge": beta_c,
                        "beta_max_le": (N - 2) / 2.0 - math.sqrt(2.0 * B2) / (N - 1),
                        "note": "需 |A|>=sqrt(2 B^2)"}

    # beta 扫描
    scan = []
    for beta in [0.0, 2.944, 3.0, 4.5, 6.0, 6.056, 8.0, 12.0, 50.0]:
        br, A, disc = solve_branches(N, beta, B2)
        if br is None:
            scan.append({"beta": beta, "A": A, "exists": False, "disc": disc})
        else:
            scan.append({"beta": beta, "A": A, "exists": True, "disc": disc,
                         "branches": [{"R": b["R"], "R2": b["rho"], "kappa": b["kappa"],
                                       "kappa_geo": b["kappa_geo"], "residual": b["residual"]}
                                      for b in br]})
    out["scan"] = scan

    # 由 WIE v1.0 闭合阈值 R* 反解读 beta*
    R_star = (1 + 0.9805864205272267) / (1 - 0.9805864205272267)  # tol*=(R-1)/(R+1)
    inv = inverse_beta(N, R_star, B2)
    out["inverse_from_tol"] = inv
    out["inverse_from_tol"]["R_from_tol_recheck"] = \
        (1 + 0.9805864205272267) / (1 - 0.9805864205272267)

    # 闭合阈值半径处的直接几何量
    out["geometry_at_R_star"] = {
        "R_star": R_star, "R_star2": R_star * R_star,
        "Theta": Theta_of_R(N, R_star),
        "lambda_N(assume fiber=0)": Theta_of_R(N, R_star)}

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "WIE_v2.3_kappaR_结果_20261009.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 控制台摘要（精简）
    print("N=%d  B=%g  B2=%g" % (N, B, B2))
    print("existence: |A| >= %.6f  => beta >= %.6f  or beta <= %.6f"
          % (math.sqrt(2 * B2), out["existence"]["beta_min_ge"], out["existence"]["beta_max_le"]))
    print("R* (from WIE tol*) = %.15f" % R_star)
    print("beta* required      = %.9f" % inv["beta_star"])
    print("kappa* = %.6e   residual = %.3e" % (inv["kappa_star"], inv["residual"]))
    print("Theta(R*) = %.9e" % out["geometry_at_R_star"]["Theta"])
    print("--- beta scan ---")
    for s in scan:
        if s["exists"]:
            rs = ", ".join("R=%.6f(k=%.4g,res=%.2e)" % (b["R"], b["kappa"], b["residual"]) for b in s["branches"])
            print("beta=%-7g A=%-9.4f -> %s" % (s["beta"], s["A"], rs))
        else:
            print("beta=%-7g A=%-9.4f -> NO SOLUTION (disc=%.4f)" % (s["beta"], s["A"], s["disc"]))
    print("OUT ->", os.path.join(OUT_DIR, "WIE_v2.3_kappaR_结果_20261009.json"))


OUT_DIR = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\910CF9D8FBF963F109E2915A63F38F70\workspace\conv_c220e5e084e345aa8edd6702582cebba\output"

if __name__ == "__main__":
    main()
