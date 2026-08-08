# Photophysical Data Extractor

面向有机材料光物理与电子结构论文的证据可溯源数据抽取 Skill，简称 **PDE**。除发光光谱、寿命和效率外，默认抽取并显示 HOMO、LUMO、S1、T1 与 ΔEST。

单篇论文上传正文及 Supporting Information（SI）后，输入 `PDE` 即可；多篇论文使用 `PDEmore`。Agent 会自动完成论文读取、数据抽取、证据关联、JSON 校验和 HTML 报告生成；用户不需要手工执行脚本或自行制作 HTML。

## 主要能力

- 支持单篇论文和多篇论文批量抽取；
- 抽取化合物、Host/Matrix、掺杂比例、样品状态和测试条件；
- 整理荧光、磷光/RTP、延迟荧光/TADF、余辉及速率常数；
- 保留室温、77 K、溶液、掺杂膜、纯膜、晶体、粉末及不同气氛条件；
- 提取 DOI、题目、KOI、逻辑骨架和一句话创新点；
- 为具体数值和综合结论建立可跳转证据；
- 自动标记冲突、低置信度项目和需要人工复核的内容；
- 自动生成经过校验的 JSON 和便于比较、溯源的 HTML；
- 支持修改主数据表的物理量列、顺序、名称和表头样式。

## 输出

单篇论文自动生成：

```text
paper_data.json
report.html
```

批量任务还会生成合并报告：

```text
batch_report.json
batch_report.html
```

`paper_data.json` 是唯一数据源，HTML 由当前 JSON 自动生成。不要手工修改 HTML。

## 安装

需要 Node.js（用于运行 `npx`）及 [skills CLI](https://skills.sh/)。本仓库为私人仓库，当前 GitHub 账号必须具有访问权限。README 不要求、也不提供手动克隆私人仓库的安装方式。

### Claude Code

```powershell
npx skills add PPOLAN-hub/photophysical-data-extractor --skill photophysical-data-extractor --agent claude-code
```

### Codex

```powershell
npx skills add PPOLAN-hub/photophysical-data-extractor --skill photophysical-data-extractor --agent codex
```

### Kimi CLI

```powershell
npx skills add PPOLAN-hub/photophysical-data-extractor --skill photophysical-data-extractor --agent kimi-cli
```

也可以一次安装到多个 Agent：

```powershell
npx skills add PPOLAN-hub/photophysical-data-extractor --skill photophysical-data-extractor --agent claude-code --agent codex --agent kimi-cli
```

不要把 Personal Access Token 写入命令、提示词、聊天记录或仓库。

### Cherry Studio

Cherry Studio 1.9.12 或更新版本支持界面安装，无需命令行。请下载已经打包并测试的专用文件：

[下载 photophysical-data-extractor-skill-v1.3.0.zip](https://github.com/PPOLAN-hub/photophysical-data-extractor/releases/latest/download/photophysical-data-extractor-skill-v1.3.0.zip)

1. 使用有权限的 GitHub 账号下载上述 ZIP；
2. 打开 Cherry Studio 的 `设置 → 技能`；
3. 选择“从 ZIP 文件安装”，并直接选择下载的文件；
4. 打开目标 Agent 的设置，在“技能”中启用 `photophysical-data-extractor`。

ZIP 不需要解压或重新压缩。私人仓库不会出现在公共技能搜索结果中，因此 Cherry Studio 使用本地 ZIP 导入。

## 调用

单篇论文可直接上传正文和 SI 两份文件，文件名不作要求，也不需要用户说明哪份是正文、哪份是 SI。输入：

```text
PDE
```

需要补充要求时，可在同一句中说明，例如：

```text
PDE，重点核对 77 K 数据和 SI 中的寿命表格。
```

Agent 应自行完成数据抽取、验证和 HTML 渲染，只向用户交付最终文件及必要的人工复核提醒。

同时处理多篇论文时，按下一节命名文件并输入：

```text
PDEmore
```

`PDEmore` 启动严格的批量配对；Agent 不会按标题或上传顺序猜测正文与 SI 的对应关系。

## 批量文件命名

批量处理支持两种确定性命名。推荐使用第一种：

```text
# 推荐：P/S 前缀，辨识清楚且排序稳定
P01.pdf  对应  S01.pdf
P02.pdf  对应  S02.pdf
P03.pdf  对应  S03.pdf

# 兼容：main/SI 后缀
1main.pdf  对应  1SI.pdf
2main.pdf  对应  2SI.pdf
```

- `P` 或 `main` 表示论文正文，`S` 或 `SI` 表示该论文的支持信息；
- 编号必须完全一致，包括前导零；
- `P01.pdf` 不能与 `S1.pdf` 配对；
- 同一对文件不能混用两种命名方式；
- 不按上传顺序、论文标题或 PDF 元数据猜测配对关系；
- 正文没有 SI 时可以继续，但报告必须标记 SI 缺失；
- 出现孤立 SI、重复正文或重复 SI 时必须停止并提醒用户。

## 抽取范围

| 类别 | 默认关注内容 |
|---|---|
| 样品身份 | 化合物、Host/Matrix、掺杂比例、溶剂、浓度、薄膜/晶体/粉末等状态 |
| 测试条件 | 温度、气氛、激发波长、延迟时间、门控窗口、是否脱氧 |
| 电子与激发态能级 | HOMO、LUMO、E(S1)、E(T1)、ΔEST；实验值与计算值分行并保留方法 |
| 总发光 | ΦPL |
| 荧光 | λF、τF、ΦF |
| 延迟荧光 | λDF、τDF、ΦDF、TADF 归属 |
| 磷光 | λP、τP、ΦP、RTP/低温磷光归属 |
| 动力学 | kISC、kRISC、kP/kr,P、knr,P |
| 论文信息 | DOI、标题、期刊/年份、KOI、逻辑骨架、一句话创新点 |
| 质量控制 | 证据位置、短原文开头、置信度、冲突和人工复核提醒 |

主数据表中的“类型”默认只保留 `RTP`、`TADF`、`RTP/TADF`；两者均不成立时使用兼容字段 `Tranditional-F`。JSON 仍保留作者给出的完整发光归属。

## 报告显示规则

- 每种化合物在主表中只显示一行；不同测试条件在同一单元格中换行并以脚注区分；
- Host 和掺杂比例只展示固态掺杂体系，不重复写入溶液条件；
- 掺杂基质、室温条件下的 λP、τP、ΦP 显示为 `#D9001B` 红色；`RT (ambient)` 等常见室温写法会被自动识别；
- 77 K 条件下相应数据使用 `#0000FF` 蓝色；
- 室温掺杂体系中最长的 τP 和最高的 ΦP 加粗并加下划线；
- 77 K 条件下最长的 τP 加粗；
- 数值、条件上标和浅灰色 `[Exx]` 证据编号保持同一行；
- 点击 `[Exx]` 会展开证据区，并以浅绿色高亮目标条目；
- 高置信度证据只显示表号或原文开头；中低置信度、冲突和模糊项进入人工复核。

颜色用于帮助比较，不替代测试条件脚注，也不代表证据置信度。

## 自定义物理量表头

默认物理量列位于根目录 `report_config.json`。固定列“化合物、Host、掺杂比例、类型”不受配置控制；其余列可重新排序、删除、增加或改名。

支持字段：

```text
phi_pl, lambda_f, tau_f, phi_f,
lambda_df, tau_df, phi_df,
lambda_p, tau_p, phi_p,
e_homo, e_lumo, e_s1, e_t1, delta_e_st, e_t2,
k_isc, k_risc, k_rp, knr_p
```

示例：

```json
{
  "physical_quantity_columns": [
    {"field": "lambda_p", "parts": [{"symbol": "λ", "subscript": "P"}]},
    {"field": "tau_p", "parts": [{"symbol": "τ", "subscript": "P"}]},
    {"field": "phi_p", "parts": [{"symbol": "Φ", "subscript": "P"}]}
  ],
  "physical_header_style": {
    "font_family": "Times New Roman",
    "font_size": "14pt",
    "font_weight": 400,
    "color": "#233A57",
    "symbol_italic": true,
    "subscript_italic": false
  }
}
```

完整配置说明见 [references/usage-guide.md](references/usage-guide.md)。

## 可靠性原则

- 每个报告值必须关联有效证据；
- 总 PLQY 不得自动等同于磷光量子效率；
- 可见余辉时间不得自动等同于磷光寿命；
- 室温与 77 K、溶液与固态、正文与 SI 数据不得混合；
- 图中估读不能标为高置信度；
- 计算值必须记录公式、输入和输入证据；
- 来源存在歧义或冲突时必须进入人工复核。

## 环境说明

- Python 3.9 或更高版本；解释器候选顺序记录在 `runtime_config.json`；
- Agent 必须能够读取论文文件、写入输出目录并运行 Skill 自带脚本；
- 本机已配置优先使用 `D:\Tool\Pathon\python.exe`（Python 3.13.7）；若其他电脑不存在该路径，会自动尝试 Skill 内 `.venv`、`py -3` 或 `python3`；
- 兼容依赖范围记录在 `requirements.txt`；当前实测环境为 `pypdf 6.10.2`、`PyMuPDF 1.27.2.2`、`PyYAML 6.0.3`；
- Agent 应先运行 `scripts/check_environment.py` 自动检查解释器和依赖，不要求用户手工选择 Python；
- Windows 下不得直接调用裸 `python`，以免命中无功能的 Microsoft Store 占位符；
- 扫描版 PDF 或图片型表格可能需要 OCR 或视觉模型。

无论使用 Codex、Claude、Kimi、DeepSeek 或其他模型，都应保留 JSON 校验、证据链接及中低置信度人工复核。上传论文到云端模型前，请自行核对版权、保密和数据处理政策。

## 进一步阅读

- [抽取与证据政策](references/extraction-policy.md)
- [JSON 数据结构](references/data-schema.md)
- [批量输入规范](references/batch-input.md)
- [HTML 报告样式规则](references/html-report-style.md)
- [配置与故障排查](references/usage-guide.md)
