# arXiv 跨学科测试论文

这里为 Read2Reproduce 的 PDF 上传、解析和学科分类准备了 10 个真实论文样本，每个可选专业方向各一篇。

| 学科 | arXiv ID | 论文 |
| --- | --- | --- |
| 计算机科学 | [1706.03762](https://arxiv.org/abs/1706.03762) | Attention Is All You Need |
| 物理学 | [1602.03837](https://arxiv.org/abs/1602.03837) | Observation of Gravitational Waves from a Binary Black Hole Merger |
| 数学 | [math/0211159](https://arxiv.org/abs/math/0211159) | The Entropy Formula for the Ricci Flow and Its Geometric Applications |
| 化学 | [1610.08935](https://arxiv.org/abs/1610.08935) | ANI-1: An Extensible Neural Network Potential with DFT Accuracy at Force Field Computational Cost |
| 生物学 | [2311.12143](https://arxiv.org/abs/2311.12143) | Gene Expression in Growing Cells: A Biophysical Primer |
| 医学 | [1908.06687](https://arxiv.org/abs/1908.06687) | Bayesian Models for Survival Data of Clinical Trials |
| 经济学 | [2406.01898](https://arxiv.org/abs/2406.01898) | How Inductive Bias in Machine Learning Aligns with Optimality in Economic Dynamics |
| 社会科学 | [2307.01918](https://arxiv.org/abs/2307.01918) | Computational Reproducibility in Computational Social Science |
| 工程 | [2103.13729](https://arxiv.org/abs/2103.13729) | Digital Twinning of Self-sensing Structures Using the Statistical Finite Element Method |
| 人文学科 | [2211.11861](https://arxiv.org/abs/2211.11861) | A Plea for an Upgrade to the Digital Craft of the Historian and Digital Methodology for Discovering the Past |

PDF 属于本地测试夹具，不纳入 Git。首次获取或需要补齐文件时，在仓库根目录运行：

```bash
./scripts/download_test_papers.sh
```

脚本会跳过已经存在且具有 PDF 文件头的样本。
