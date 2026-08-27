# Derivation Trace

`EQUATION_CARDS.json` 是公式权威源，自动展开结果见 `DERIVATION.md`。每张卡都包含论文位置、推导、参数来源、代码引用和独立检查。

核心路径为：

```text
paper/supplement equations
  -> Laurent hopping or analytic potential
  -> explicit finite geometry / momentum path
  -> independent numerical arrays
  -> invariant and convergence checks
  -> frozen hashes
  -> render-only figures
```

主文与补充材料分别由 EQC001–006 和 EQC007–011 覆盖。无法从论文唯一确定的量（S5 选态能量、S7 正标量语义与 N=935 离散几何）不会被补写进公式卡，而是进入 `PAPER_REVIEW.md` 的证伪队列。
