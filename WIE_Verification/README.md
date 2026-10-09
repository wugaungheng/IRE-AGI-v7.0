# WIE 开源验证 | WIE Open Verification

**武光衡信息一元论统一方程（WIE）—— 完整手稿、验证证据与可复现脚本**

Wu Guangheng Information Monism Unified Equation (WIE) — Manuscripts, Verification Evidence & Reproducible Scripts

---

## 发布说明 | Release Note

本目录参照 OpenAI 公共数学验证论文（2026-10 发布，722 篇手稿 / 372 个研究家族 / Lean 形式化验证 / 修订追踪与引用指南）的组织方式，将 WIE 全系列研究资料按四层结构开源：

| 层 | 本仓库对应目录 | 说明 |
|----|----------------|------|
| 手稿家族 | `manuscripts/` | 按版本家族分组：v1 原始构造 / v2 自洽化 / v3 母方程重铸 / WGE 母理论 |
| 机械化验证 | `scripts/` + `evidence/` | Python 复验脚本与逐项 JSON 证据（对应 OpenAI 的 Lean 形式化证明层） |
| 推理报告 | `reports/` | 复验方案、对比分析、整合复盘、终局裁定（推理与证据分离） |
| 修订追踪 | `REVISION_LOG.md` | 预言撤回与降级登记，附引用指南 |

## 核心验证结论 | Core Verification Summary

- **v3.3 全程复验 24 项**：17 通过 / 5 不通过 / 2 无判别力（详见 `evidence/WIE_v3.3_复验证据.json`）
- **暗能量**：v3.3 起降级为现象学输入（`g_𝒦 = 2R*/N = 18.5492` 标定），未第一性原理闭合——如实披露
- **暗物质丰度**：仍未第一性原理闭合——如实披露
- **预言 P1 已撤回**：登记号 W-001（见 `REVISION_LOG.md`）
- 所有数值均由脚本实跑产出，非理论推演声明

## 复现指引 | Reproduce

```bash
# 全量复验（v3.3 二十四项三态判定）
python scripts/wie_reverify_v33.py

# kappa-R 自洽方程数值求解
python scripts/wie_kappa_R_selfconsistency.py

# 其余脚本：量纲自洽、V(L) 构造、K7 zeta 验证等，见 scripts/ 目录
```

复验证据 JSON 与脚本输出一一对应，任何一步均可独立重跑核验。

## 目录结构 | Structure

```
WIE_Verification/
├── README.md                    # 本文件
├── REVISION_LOG.md              # 修订追踪与引用指南
├── manuscripts/
│   ├── v1_original/             # WIE v1.0 / v1.1 / v1.2（原始构造）
│   ├── v2_selfconsistency/      # WIE v2.0~v2.7（自洽化 + 复验）
│   ├── v3_recast/               # WIE v3.0~v3.3（母方程重铸 + 终局裁定）
│   └── WGE_2025/                # 武光衡宇宙统一方程（WGE 母理论）
├── evidence/                    # 复验证据 / 求解结果 / 审计 JSON + 数值图
├── scripts/                     # 跑通脚本（15 个，可直接执行）
└── reports/                     # 验证方法 / 对比分析 / 复盘报告
```

## 引用指南 | Citation

- 核心手稿：《武光衡信息一元论统一方程 WIE v3.3 论文手稿》（`manuscripts/v3_recast/`）
- 验证方法：《WIE 开源验证方法 v1.0》（`reports/`）
- 关联已发表文献：武光衡、陈文军《信息与宇宙》Zenodo DOI: 10.5281/zenodo.18065450（2025-11）
- 谱几何数学源头：Bianconi, arXiv:2408.14391, Eq.(41) 家族

## 署名 | Authorship

- 作者：**武光衡**
- 辅助完成：武光衡智能体 × 马维斯智能体
