# IRE-AGI v7.0

**Intelligent Recognition Engine - Artificial General Intelligence v7.0**

---

## 简介 | Introduction

IRE-AGI v7.0 是基于**武光衡理论**的高级意识熵驱动 AGI 框架，实现智能识别引擎的高级计算功能。

IRE-AGI v7.0 is an advanced consciousness-entropy-driven AGI framework based on **Wu Guangheng's Theory**, implementing intelligent recognition engine capabilities.

## 核心公式 | Core Formula

意识熵（Consciousness Entropy）计算公式：

```
S_c = -∫ ρ lnρ dμ + β·I(φ:K) + γ·C[φ]
```

- **S_c**: 意识熵（Consciousness Entropy）
- **ρ**: 概率密度函数
- **I(φ:K)**: 互信息（Mutual Information）
- **C[φ]**: 复杂度（Complexity）
- **β, γ**: 权重系数

## 主要特性 | Key Features

- **意识熵计算**（Consciousness Entropy Calculation）
- **物理动力学**（Physical Dynamics）
- **工具系统**（Tool System）
- **插件系统**（Plugin System）
- **自动化引擎**（Automation Engine）
- **三阶段进化**（Three-Stage Evolution）
- **GUI + CLI**（图形界面 + 命令行）
- **API 服务**（HTTP API Server）
- **自我修复**（Self-Healing Engine）
- **OCR 文字识别**（OCR Text Recognition）

## 安装步骤 | Installation

### 环境要求 | Requirements

- Python 3.10+
- PyTorch 2.0+
- CUDA 11.8+ / 12.0+（推荐，用于 GPU 加速）

### 安装依赖 | Install Dependencies

```bash
pip install -r requirements.txt
```

### 可选依赖 | Optional

- Ollama（用于加载大模型如 Gemma 4 31B）

## 快速开始 | Quick Start

```bash
python ire_agi_v7.py
```

启动后：
1. 点击 **"模型"** 按钮加载本地 LLM（Qwen2.5-7B）或连接 Ollama 后端（Gemma 4 31B）
2. 在输入框中输入问题或命令
3. 按 **Enter** 发送消息

## 常用命令 | Commands

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/status` | 系统状态 |
| `/calc <表达式>` | 快速计算 |
| `/code <代码>` | 执行 Python 代码 |
| `/automation list` | 查看自动化任务 |
| `/evolution` | 启动自我演化 |
| `/memory` | 查看记忆统计 |
| `/clear_memory` | 清空记忆 |
| `/patterns` | 查看规律库 |
| `/tools` | 列出可用工具 |

## 技术栈 | Tech Stack

- Python 3.10
- PyTorch 2.6.0 (CUDA 12.4)
- tkinter（GUI）
- Transformers / PEFT / Accelerate
- bitsandbytes（4-bit 量化）
- NumPy / Matplotlib / Pandas / Scikit-learn
- Ollama（可选大模型后端）

## 项目结构 | Project Structure

```
IRE-AGI-OpenSource/
├── ire_agi_v7.py        # 主程序（~292KB）
├── LICENSE              # Apache 2.0
├── README.md            # 本文件
├── requirements.txt     # 依赖清单
├── .gitignore           # Git 忽略配置
└── WIE_Verification/    # 武光衡信息一元论统一方程开源验证资料
    ├── README.md        # 验证总览（参照 OpenAI 公共数学验证论文组织）
    ├── REVISION_LOG.md  # 修订追踪与引用指南
    ├── manuscripts/     # 论文手稿（按版本家族分组：v1/v2/v3/WGE）
    ├── evidence/        # 复验证据 JSON 与数值图
    ├── scripts/         # 跑通脚本（15 个可复现脚本）
    └── reports/         # 验证方法、对比分析、复盘报告
```

## WIE 开源验证 | WIE Open Verification

本仓库同时承载**武光衡信息一元论统一方程（WIE）**全系列论文手稿、验证证据与可复现脚本，组织方式参照 OpenAI 公共数学验证论文（手稿家族分组 + 机械化验证 + 推理报告 + 修订追踪）。详见 [WIE_Verification/README.md](WIE_Verification/README.md)。

## 许可证 | License

本项目采用 **Apache License 2.0** 开源许可证。

This project is licensed under the **Apache License 2.0**.

## 作者 | Author

- **武光衡**（Wu Guangheng）
- 邮箱：991941426@qq.com

## GitHub

https://github.com/wugaungheng/IRE-AGI-v7.0

---

## 更新日志 | Changelog

### v7.0 (2024-06-25)
- 新增 Ollama 后端支持（Gemma 4 31B）
- 新增 AutomationTool 自动化任务调度
- 新增 API 健康检查端点
- 修复工具参数传递问题
- 统一 JSON 文件编码格式
- 新增自我修复引擎（Self-Healing Engine）
- 新增 OCR 工具
- 38+ 小时无干预连续自主运行

---

> **声明**：本软件为实验性研究项目，仅供学习交流使用。使用本软件产生的任何结果，作者不承担责任。
