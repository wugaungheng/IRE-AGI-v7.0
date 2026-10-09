# -*- coding: utf-8 -*-
"""WIE v3.0 母方程重铸 —— 关键数值关系复现脚本（仅用 math 标准库）
验证：18.55 = 2R*/N = R*/B = f^3，且 f ~= sqrt(N-4) = sqrt(7)
"""
import math

hb = 1.054571817e-34; c = 2.99792458e8; G = 6.67430e-11
lP = math.sqrt(hb*G/c**3); Lobs = 1.1056e-52
eV = 1.602176634e-19
N = 11; B = 5.5; B2 = 30.25
R = 102.020671834625304
kap = B2/R**4; om = math.sqrt(kap)
M = 0.2293*eV/c**2; lM = hb/(M*c)
lamV = (8*math.pi*lP**2/Lobs)**0.25
rhoL = Lobs*c**4/(8*math.pi*G)
rhov = hb*om*c/(lM*lamV**3)

Lcl = (hb*om*c/(lM*rhoL))**(1/3)          # 直接闭合所需模式单元
f = lamV/Lcl

print("rhoL/rhov      =", rhoL/rhov)
print("2R/N = R/B     =", 2*R/N, "=", R/B)
print("f = lamV/Lcl   =", f, "   f^3 =", f**3)
print("f^2            =", f*f, "   (vs 7)")
print("f/sqrt(N-4)-1  =", (f/math.sqrt(N-4)-1)*100, "%")
print("g=(N-4)^1.5    =", (N-4)**1.5, " vs 2R/N =", 2*R/N,
      " diff =", ((N-4)**1.5/(2*R/N)-1)*100, "%")
Rn = N*(N-4)**1.5/2
print("R_geo          =", Rn, "  R_spec =", R, "  diff =", (Rn/R-1)*100, "%")
rho = Rn**2; A = rho + B2/(2*rho)
print("beta from R_geo=", A/(N-1)+(N-2)/2, " (v2.4 tuned 1045.321893477)")
