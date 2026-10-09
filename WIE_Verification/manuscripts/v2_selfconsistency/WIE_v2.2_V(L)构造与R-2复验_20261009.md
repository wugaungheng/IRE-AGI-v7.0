# WIE v2.2 —— V(L) 形式确定与 R-2 复验

**日期**：2026-10-09　**基线**：v2.1 完整稿　**本轮焦点**：未解清单 N-3（V(L) 形式未定）与复验项 R-2

---

## 0. 本轮目标

承接 v2.1 未解清单与复验方案：

1. 澄清 V(L) 并非自由输入，而是被几何自洽约束**反解**；
2. 给出 V(L) 的自洽**不动点方程**；
3. 在"规律空间为常曲率紧致流形"假设下给出**解析解**并数值验证；
4. 更新 R-2 与未解清单状态。

---

## 1. 为什么 V(L) 阻塞 R-2

复验项 R-2 要求规律空间的诱导几何满足 Einstein 型约束

$$G_{AB}\,g^{BC} = \Theta_A^{\ C} = \lambda_N\,\delta_A^C + (\text{纤维曲率项})$$

其中 $G_{AB}=\mathcal R_{AB}-\tfrac12\mathcal R\,g_{AB}$。复验需算 $g_{AB}$、$\mathcal R_{AB}$，二者依赖 $\Psi$；而 $\Psi$ 由含 $V(L)$ 的动力学给出。

$$\boxed{\ V(L)\ \text{未知}\ \Rightarrow\ \Psi\ \text{未知}\ \Rightarrow\ \text{几何未知}\ \Rightarrow\ \text{R-2 无法闭合}\ }$$

这正是 v2.1 把 V(L) 列为 N-3 / 阻塞 R-2、N-4 的原因。

---

## 2. 反解：V(L) 被几何约束唯一确定

### 2.1 两个度量

- **量子度规（规律空间信息度量）**
  $$g_{AB}(L)=\frac{\hbar^2}{2M}\int d^DX\;\langle \partial_A\Psi(L;X)\,|\,\partial_B\Psi(L;X)\rangle$$
- **有效质量度量**（含势的 Hessian，归一化 $\int|\Psi|^2 dX=1$）
  $$M_{AB}=g_{AB}+\tfrac12\,\partial_A\partial_B V$$

### 2.2 反解 V 的 Hessian

将 $\alpha M_{AB}-\beta\,\mathcal R_{AB}=\Theta\,g_{AB}$（$\alpha,\beta$ 为 v2.1 定标常数）代入：

$$\tfrac{\alpha}{2}\,\partial_A\partial_B V=(\Theta-\alpha)\,g_{AB}+\beta\,\mathcal R_{AB}$$

即

$$\boxed{\ \partial_A\partial_B V=\frac{2}{\alpha}\Big[(\Theta-\alpha)\,g_{AB}+\beta\,\mathcal R_{AB}\Big]\equiv H_{AB}[\Psi]\ }$$

**结论**：V(L) 的二阶导（地形曲率）被当前几何 $(g,\mathcal R)$ 完全锁死。

### 2.3 不动点方程

沿测地线积分两次：

$$V(L)=V(0)+\partial_A V(0)\,L^A+\int_0^1(1-t)\,H_{AB}[\Psi_V](L_t)\,L^A L^B\,dt$$

而 $\Psi_V$ 由 $V$ 决定、$H_{AB}$ 由 $\Psi_V$ 决定，故

$$\boxed{\ V=\mathcal T[V]\ }$$

- V 本身只余一个常数项与一个线性项（可被平移/规范吸收）；
- **存在性**：弱场（$\|H\|$ 小）下 $\mathcal T$ 为压缩映射，Banach 不动点给出局部唯一解；强场需 Schauder 不动点。

---

## 3. 常曲率解（解析）

若规律空间取半径 $R$ 的紧致常曲率空间（球面 $S^N$）：

$$\mathcal R_{AB}=\frac{N-1}{R^2}\,g_{AB}$$

则

$$G_{AB}=\mathcal R_{AB}-\tfrac12\mathcal R\,g_{AB}=-\frac{(N-1)(N-2)}{2R^2}\,g_{AB}$$

$$\boxed{\ \Theta=-\frac{(N-1)(N-2)}{2R^2}\,\mathbb I\ }$$

且

$$H_{AB}=\frac{2}{\alpha}\Big[(\Theta-\alpha)+\beta\frac{N-1}{R^2}\Big]g_{AB}\equiv\kappa\,g_{AB}\quad(\kappa\ \text{常数})$$

$$\boxed{\ V(L)=\tfrac12\kappa\,|L|^2+c_1+c_A L^A\ }\quad(\text{谐振子型约束势})$$

**自洽条件**：V 的约束半径 $\sim\kappa^{-1/2}$ 必须与被假设的 $R$ 匹配，给出代数方程

$$R=\mathcal F\big(\kappa(R)\big)$$

（$\kappa$–$R$ 自洽方程，留待下一轮数值求解）

### 3.1 数值验证

对 $S^N$（N=2,3,4,5）符号计算，逐项核对 $\mathrm{Ric}_{ii}/g_{ii}=(N-1)/R^2$，全部通过：

| N | Ric ∝ g | Ricci 标量 | Θ = −(N−1)(N−2)/(2R²) |
|---|---|---|---|
| 2 | ✓ | 2/R² | 0 |
| 3 | ✓ | 6/R² | −1/R² |
| 4 | ✓ | 12/R² | −3/R² |
| 5 | ✓ | 20/R² | −6/R² |
| **11** | 定理 | 110/R² | **−45/R²** |

> 规律空间 $N=11=1+4+6$；$R=1$ 时 $\Theta=-45$。
> 验证脚本：`temp/v2_curvature_check3.py`；结果落盘 `output/WIE_V2_常曲率验证_20261009.json`。

---

## 4. R-2 复验结论

在"规律空间为常曲率紧致流形"假设下：

- 几何约束 $G_{AB}g^{BC}=\Theta_A^{\ C}$ **退化为恒等式**（常曲率 $\Rightarrow$ Einstein 空间）；
- $\Theta$ 的显式解析值给出，R-2 由 ⬜ **升为 ✅（条件性完成）**；
- 反之，若不假设常曲率，R-2 等价于要求 $\Psi$ 被 V(L) 约束到 Einstein 空间上——这正是 §2.3 的不动点方程，二者互为等价表述。

---

## 5. 未解清单更新（v2.1 → v2.2）

| 编号 | 状态 | 说明 |
|---|---|---|
| N-1 λ_I 严格值 | 保留 | 待补 V2.4 的 $\xi_\Psi=\lambda_I$ 判定 |
| ~~N-3 V(L) 形式~~ | **已定** | 常曲率解闭式；一般情形存在性定理待证 |
| N-4 构件数值复验 | **部分解锁** | 可用解析 $\Theta$ 计算 $\lambda_N$ 与 $\Lambda$ 的桥接 |
| N-8（新增） | 待解 | $\kappa$–$R$ 自洽方程 $R=\mathcal F(\kappa(R))$ 的数值解 |

---

## 6. 下一步（二选一）

1. **λ_I 严格值**：收口 V2.4，判定 $\xi_\Psi$ 与 $\lambda_I$ 是否严格相等；
2. **κ–R 自洽方程数值求解**：把 R-2 从"条件性完成"变为"无条件闭合"。

---

*变更：v2.1 → v2.2（V(L) 闭式 + R-2 条件性完成）*
