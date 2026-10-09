
import json, math, os, datetime
EVID = {}

# ---- 常量（SI） ----
G   = 6.67430e-11
a0  = 1.2e-10          # MOND 加速度标度（galaxy_simulation_tool.py 默认）
HBAR= 1.054571817e-34
c   = 299792458.0
LAM_DEFAULT = 1.0e20   # WGE: WUGUANGHENG_LAMBDA_GRID[0] 单位=米（长度）

# ---- 维度向量 (L, M, T) ----
DIM = {
 "r":(1,0,0), "M":(0,1,0), "T":(0,0,1),
 "v":(1,0,-1), "a":(1,0,-2), "L_ang":(2,1,-1),   # 角动量量纲
 "G":(3,-1,-2), "a0":(1,0,-2), "hbar":(2,1,-1), "c":(1,0,-1),
 "lam_wge":(1,0,0),          # WGE λ：长度（米）-> Compton 波长
 "lam_gal":(1,0,0),          # 占位，下面用代数算
}
def mul(*terms):
    # terms: (dimtuple, power)
    v=[0,0,0]
    for d,p in terms:
        for i in range(3): v[i]+=d[i]*p
    return tuple(v)

# V^4 = G*M*a0*lam_gal  ->  [lam_gal] = [V^4]/([G][M][a0])
dim_lam_gal = mul((DIM["v"],4),(DIM["G"],-1),(DIM["M"],-1),(DIM["a0"],-1))
dim_lam_wge = DIM["lam_wge"]
audit = {
 "lam_wge_dim": dim_lam_wge,          # WGE 侧 λ
 "lam_gal_dim": dim_lam_gal,           # 星系反演式给出的 λ
 "lam_wge_is_length": dim_lam_wge==(1,0,0),
 "lam_gal_is_dimensionless": dim_lam_gal==(0,0,0),
 "lam_gal_equals_lam_wge_dim": dim_lam_gal==dim_lam_wge,
}

# ---- MOND 恒等式：若 a0 = V^4/(G M) 成立，则 lam_gal == 1（与数据无关） ----
# 数值示例（文献量级，NGC 3198；仅示 O(1)，非 SPARC 导入）
V = 1.50e5        # m/s  (~150 km/s)
Mb= 3.0e10*1.989e30   # kg (~3e10 Msun)
lam_gal_num = V**4/(G*Mb*a0)
mond_ratio  = lam_gal_num   # 同一表达式

# ---- K-4 Compton 桥（唯一量纲自洽的 λ<->质量 关系） ----
m_eff_from_lam = HBAR/(c*LAM_DEFAULT)          # λ=1e20m -> m
lam_from_electron = HBAR/(9.1093837015e-31*c)  # 电子质量 -> λ
k4 = {
 "relation": "lam = hbar/(m*c);  m_eff = hbar/(c*lam)",
 "m_eff_at_lam_1e20kg": m_eff_from_lam,
 "lam_from_m_electron_m": lam_from_electron,
 "orders_apart_vs_1e20m": math.log10(LAM_DEFAULT/lam_from_electron),
}

# ---- 幂次权重 w = p_lambda + p_c 对既有外部口径 ----
w_table = [
 ("r",0,0),("M",0,0),("v",0,0),("T",0,0),("a",0,0),("L_ang",0,0),
 ("lam_gal=V^4/(GMa0)",1,0),   # 该式把 λ 定义出来 -> p_lambda=1（R50 登记）
 ("lam_K4=hbar/(mc)",-1,0),
]
w_rows=[{"observable":n,"p_lambda":pl,"p_c":pc,"w":pl+pc,"w_nonzero":(pl+pc)!=0} for n,pl,pc in w_table]

# ---- “20 个数量级”的成因核对：是否恰为 log10(lambda_default) ----
orders_artifact = math.log10(LAM_DEFAULT)   # = 20

EVID={
 "round":"R59","date":"2026-10-09",
 "purpose":"对‘PRED-A1 外部锚’候选通道做量纲通道门审计（gate audit），判定方案一/二/三是否结构性可通",
 "constants":{"G":G,"a0_mond":a0,"hbar":HBAR,"c":c,"lambda_default_m":LAM_DEFAULT},
 "dimensional_audit":audit,
 "mond_identity":{
   "statement":"V^4 = G*M*a0*lam_gal  ⇒  lam_gal = V^4/(G*M*a0)；若 MOND 关系 a0=V^4/(G*M) 成立，则 lam_gal ≡ 1（与任何数据无关）",
   "numeric_example":{"note":"文献量级示例（NGC 3198 量级：V≈150 km/s, M_bary≈3e10 Msun）；非 SPARC 导入，仅示 O(1)",
                      "V_ms":V,"M_kg":Mb,"lam_gal":lam_gal_num},
   "conclusion":"lam_gal 是无量纲 MOND 偏差比（≈1），不是长度；与 WGE λ（长度, 1e20 m）量纲不同，不能充当其外部锚"
 },
 "k4_compton_bridge":k4,
 "gauge_weight_table":w_rows,
 "orders_artifact_check":{
   "R50_reported_orders_apart":20,
   "log10_lambda_default":orders_artifact,
   "is_unit_artifact": abs(orders_artifact-20)<1e-9
 },
 "verdict":{
   "scheme1_T_based": "结构性封闭：w 只计 p_lambda+p_c，T 读数 p_lambda=p_c=0 ⇒ w=0，与数据精度无关（EA-4 已实测 w=0）；提高 Gaia/JPL 精度不可能改变幂次零",
   "scheme2_M_based": "结构性封闭：纯质量读数 w=0",
   "scheme3_G_combos": "结构性封闭：G 不入 λ/c 幂律 ⇒ w=0",
   "only_w_nonzero_candidate_lam_gal": "量纲自洽性否决：该式给出的 lam_gal 无量纲(≡1)，非 WGE 长度 λ ⇒ 不能锚定 λ_default；R50 所记‘相差 ~20 个数量级’恰等于 log10(1e20)，属单位记账伪差",
   "k4_compton_route": "量纲自洽但数值否决：λ=1e20 m 对应 m_eff≈3.5e-63 kg（不可测）；反之电子级实测质量给 λ≈3.9e-13 m，与 1e20 m 相差 ~32.4 个数量级",
   "net": "在现行 WGE 表述（λ 为长度、且 K-4 桥取康普顿口径）下，不存在量纲自洽且数值可达的外部观测量可承载 λ 的绝对标度 ⇒ PRED-A1 不是‘待收集数据’问题，而是表述层缺口",
   "not_a_breakthrough":True
 },
 "scope_limits":[
   "本判定仅覆盖项目现行公式集（galaxy_simulation_tool.py 的 V^4=GMa0λ 与 dynamics.py 的康普顿桥）；新增量纲耦合可另开通道",
   "未改动任何源码；未写入项目目录；示例数值为文献量级，非观测导入",
   "未闭合项一律不得写成已完成"
 ]
}
out=os.path.join(r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\910CF9D8FBF963F109E2915A63F38F70\workspace\conv_c220e5e084e345aa8edd6702582cebba\output","R60_结构门审计_20261009.json")
json.dump(EVID,open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("WROTE",out)
print(json.dumps(audit,ensure_ascii=False))
print("lam_gal(num)=",lam_gal_num)
print("m_eff@1e20m=",m_eff_from_lam,"kg;  lam@m_e=",lam_from_electron,"m; orders=",k4["orders_apart_vs_1e20m"])
print("w_table:",[(r["observable"],r["w"]) for r in w_rows])
