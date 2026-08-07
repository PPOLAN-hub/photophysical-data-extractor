# Photophysical Data Extractor

面向有机材料光物理论文的证据可溯源数据抽取 Agent Skill。它从论文正文与 Supporting Information（SI）中整理荧光、磷光/RTP、延迟荧光/TADF、余辉、光谱、寿命、量子效率、基质与速率常数等数据，生成经过校验的 JSON 和便于比较、复核的 HTML 报告。

本项目的重点不是“尽可能多地填数”，而是让每一个具体数值、测试条件和综合结论都能回到原文中的表格、图、正文或 SI。

## 主要能力

- 支持单篇论文及多篇论文批量处理；
- 严格配对正文与 SI，防止批量任务中串文献；
- 抽取化合物、Host/Matrix、掺杂比例、样品状态和完整测试条件；
- 整理荧光、延迟荧光、磷光及总光致发光数据；
- 保留室温、77 K、溶液、掺杂膜、纯膜、晶体、粉末、聚集态等不同条件；
- 提取论文 KOI、逻辑骨架和一句话创新点；
- 为数值和综合结论建立证据编号；
- 自动校验 JSON 中的结构、状态和证据引用；
- 生成适合阅读、横向比较和人工复核的 HTML；
- 主数据表的物理量列、顺序、名称和表头样式均可配置。

## 工作方式

```text
论文正文 PDF + SI PDF
        ↓
Agent 阅读、判断语义并建立证据
        ↓
paper_data.json（唯一数据源）
        ↓
结构与证据校验
        ↓
report.html（确定性渲染）
```

论文理解、表格含义判断、数据归属和证据选择由支持 Agent Skills 的模型完成；本仓库中的脚本负责批量文件配对、JSON 校验和 HTML 渲染。因此，它不是一个脱离 Agent 后仅运行单条 Python 命令就能完成全部语义抽取的传统 PDF 解析器。

## 抽取范围

| 类别 | 默认关注内容 |
|---|---|
| 样品身份 | 化合物、Host/Matrix、掺杂比例、溶剂、浓度、薄膜/晶体/粉末等状态 |
| 测试条件 | 温度、气氛、激发波长、延迟时间、门控窗口、是否脱氧 |
| 总发光 | ΦPL |
| 荧光 | λF、τF、ΦF |
| 延迟荧光 | λDF、τDF、ΦDF、TADF 归属 |
| 磷光 | λP、τP、ΦP、RTP/低温磷光归属 |
| 动力学 | kISC、kRISC、kP/kr,P、knr,P |
| 论文级信息 | DOI、标题、期刊/年份、KOI、逻辑骨架、一句话创新点 |
| 质量控制 | 证据位置、短原文开头、置信度、冲突和人工复核提醒 |

默认比较表中的“类型”只保留 `RTP`、`TADF`、`RTP/TADF`；两者均不成立时使用兼容字段 `Tranditional-F`。JSON 中仍应保留作者的完整发光归属，不得为了表格简化而丢失原始机制信息。

## 输出文件

单篇论文：

```text
paper_data.json   # 机器可读、可校验的唯一数据源
report.html       # 由 JSON 确定性生成的阅读与复核报告
```

批量任务：

```text
batch_manifest.json  # 正文/SI 配对清单
batch_report.json    # 各论文 JSON 路径清单
batch_report.html    # 合并后的批量报告
```

不要手工修改生成后的 HTML。需要修正数据时，请修改 JSON；需要修改展示时，请修改配置或渲染器，然后重新生成 HTML。

## 环境要求

- Python 3.9 或更高版本；
- 能读取本地文件、运行 Python 并加载 `SKILL.md` 的 Agent；
- 可检索文字的论文 PDF，以及可选的 SI PDF。

校验器、渲染器和批量清单脚本只依赖 Python 标准库。为了提高 PDF 文字、页码和表格定位能力，推荐安装：

```powershell
python -m pip install pypdf PyMuPDF PyYAML
```

扫描版 PDF 或图片型表格可能还需要 OCR 或视觉模型。

## 安装

克隆私有仓库：

```powershell
git clone https://github.com/PPOLAN-hub/photophysical-data-extractor.git
```

Codex 用户可将完整仓库放入：

```text
%CODEX_HOME%/skills/photophysical-data-extractor/
```

兼容 Agent Skills 的其他工具可使用用户级目录：

```text
~/.agents/skills/photophysical-data-extractor/
```

或项目级目录：

```text
.deepcode/skills/photophysical-data-extractor/
```

安装后应保留 `SKILL.md`、`scripts/`、`references/`、`agents/` 和 `report_config.json`。

## 单篇论文快速开始

准备正文和 SI，并向 Agent 发出类似请求：

```text
使用 $photophysical-data-extractor 抽取这篇有机材料光物理论文及其 SI。
生成 paper_data.json 和 report.html；保留室温、77 K、溶液与固态条件，并在渲染前完成证据校验。
```

标准流程是：

1. 核对正文和 SI 的覆盖状态；
2. 阅读正文、表格、图注和 SI 中的候选位置；
3. 按“化合物＋样品＋测试条件”建立独立记录；
4. 为每个具体值和论文级综合结论关联证据；
5. 生成 KOI、逻辑骨架和一句话创新点；
6. 写入 `paper_data.json`；
7. 校验 JSON；
8. 从 JSON 渲染 HTML。

手动执行最后两步：

```powershell
python scripts/validate_extraction.py "路径/paper_data.json"
python scripts/render_html.py "路径/paper_data.json" "路径/report.html"
```

校验失败时，应先修复 JSON 中的无效状态、缺失证据或悬空证据编号，不要跳过校验直接制作 HTML。

## 批量处理

### 文件命名

推荐正文与 SI 使用完全相同的文献 ID：

```text
P001_Liu_2024_main.pdf
P001_Liu_2024_SI.pdf
P002_Zhang_2025_main.pdf
P002_Zhang_2025_SI.pdf
```

也可每篇论文单独放入文件夹：

```text
P001_Liu_2024/main.pdf
P001_Liu_2024/SI.pdf
```

不建议使用 `1.pdf`、`1SI.pdf` 这类语义不清的名称。最低限度应使用 `001_main.pdf` 与 `001_SI.pdf`，避免排序变化或文件增删导致错误配对。

### 构建配对清单

```powershell
python scripts/build_batch_manifest.py "输入文件夹" "batch_manifest.json"
```

正文重复、SI 重复、SI 无正文或角色无法判断时，脚本会停止。正文缺少 SI 可以继续，但结果中必须如实标记 SI 未覆盖。

### 推荐输出目录

```text
outputs/
  P001_Liu_2024/
    paper_data.json
    report.html
  P002_Zhang_2025/
    paper_data.json
    report.html
  batch_report.json
  batch_report.html
```

每篇论文校验通过后，创建：

```json
{
  "paper_data_files": [
    "P001_Liu_2024/paper_data.json",
    "P002_Zhang_2025/paper_data.json"
  ]
}
```

再生成合并报告：

```powershell
python scripts/render_html.py "outputs/batch_report.json" "outputs/batch_report.html"
```

批量报告中，文章信息默认展开；每篇文章的主数据区默认折叠；证据台账与人工复核位于主数据区中的第二级折叠。证据 ID 会按文章自动隔离。

## HTML 报告的默认阅读规则

- 每种化合物在主表中只显示一行；不同测试条件通过同一单元格内换行和条件脚注区分；
- Host 和掺杂比例只展示固态掺杂体系，不重复写入溶液条件；
- 掺杂基质、室温条件下的 λP、τP、ΦP 显示为红色；
- 77 K 条件下相应数据使用 `#0000FF` 蓝色；
- 室温掺杂体系中最长的 τP 和最高的 ΦP 加粗并加下划线；
- 77 K 条件下最长的 τP 加粗；
- 一个单元格内的多个数据直接换行；数值、条件上标和 `[Exx]` 证据编号保持同一行；
- `[Exx]` 使用浅灰色，点击后会展开证据区并以浅绿色高亮目标条目；
- 高置信度证据仅显示表号或原文开头几个词；中低置信度、冲突和模糊项进入人工复核。

颜色用于帮助阅读，不替代测试条件脚注，也不代表证据置信度。

## 自定义主表物理量

默认物理量列定义在根目录的 `report_config.json` 中。固定列“化合物、Host、掺杂比例、类型”不受该配置控制；其余物理量可重新排序、删除、增加或改名。

例如只显示磷光发射位置、寿命和效率：

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

当前支持的字段：

```text
phi_pl, lambda_f, tau_f, phi_f,
lambda_df, tau_df, phi_df,
lambda_p, tau_p, phi_p,
k_isc, k_risc, k_rp, knr_p
```

若希望保留默认配置，可新建自己的配置文件，并作为第三个参数传入：

```powershell
python scripts/render_html.py "paper_data.json" "report.html" "my_report_config.json"
```

配置不存在、字段不受支持、字段重复或样式值非法时，渲染器会明确报错，避免静默生成错误表格。完整说明见 [references/usage-guide.md](references/usage-guide.md)。

## 证据与可靠性原则

- 每个报告值必须引用 `evidence_ledger` 中存在的证据 ID；
- 表格值优先记录表号和单元格线索，不在台账中机械复写整行数据；
- 高置信度正文证据只保留便于检索的短原文开头；
- 图中估读不能标为高置信度，并应明确说明是估读；
- 计算值必须记录公式、输入和输入证据；
- `not_reported` 只在检索过相关正文/SI 后使用；
- 证据存在歧义或冲突时使用 `uncertain` 并加入人工复核；
- 总 PLQY 不得自动等同于磷光量子效率；
- 可见余辉时间不得自动等同于磷光寿命；
- 正文与 SI、室温与 77 K、溶液与固态数据不得混合。

## 与不同模型配合

本仓库遵循 Agent Skill 的文件组织方式。只要模型或 Agent 能完整读取 `SKILL.md`、访问论文文件并运行脚本，就可以使用本工作流，包括 Codex、DeepSeek 或其他兼容 Agent Skills 的环境。

不同模型的论文理解、表格识别和长上下文能力会影响抽取质量。建议无论使用何种模型，都保留 JSON 校验、证据链接和中低置信度人工复核，不要只依据最终 HTML 判断真实性。将论文上传到云端模型前，请自行核对版权、保密和数据处理政策。

## 项目结构

```text
photophysical-data-extractor/
├─ SKILL.md                         # Agent 的主工作流与硬性规则
├─ README.md                        # 项目说明
├─ report_config.json               # 默认物理量表头配置
├─ agents/
│  └─ openai.yaml                   # UI 名称和默认调用提示
├─ scripts/
│  ├─ build_batch_manifest.py       # 正文/SI 批量配对
│  ├─ validate_extraction.py        # JSON 与证据校验
│  └─ render_html.py                # JSON → HTML
└─ references/
   ├─ extraction-policy.md          # 数据判断与证据政策
   ├─ data-schema.md                # JSON 字段规范
   ├─ batch-input.md                # 批量输入规范
   ├─ html-report-style.md          # HTML 展示规则
   └─ usage-guide.md                # 详细使用与配置指南
```

## 进一步阅读

- [详细使用指南](references/usage-guide.md)
- [抽取与证据政策](references/extraction-policy.md)
- [JSON 数据结构](references/data-schema.md)
- [批量输入规范](references/batch-input.md)
- [HTML 报告样式规则](references/html-report-style.md)

## 已知边界

- 扫描件、复杂跨页表格和图片型 SI 可能需要 OCR 或视觉检查；
- 作者未明确区分的发光机制不能由模型强行归类；
- 图中读数、由公式计算的数据和跨来源冲突必须保留不确定性；
- 本项目提供研究整理与复核工具，不替代研究者对原文、实验条件和物理意义的最终判断。
