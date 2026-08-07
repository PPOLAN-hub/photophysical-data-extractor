# 使用指南

## 1. 这是什么

`photophysical-data-extractor` 是面向有机材料光物理文献的 Agent Skill，覆盖荧光、磷光/RTP、延迟荧光/TADF、余辉及相关速率常数。它负责指导智能体从论文正文和 Supporting Information（SI）中抽取可溯源数据，生成：

- `paper_data.json`：机器可读、可校验的唯一数据源；
- `report.html`：供阅读、比较和人工复核的网页报告；
- 批量任务中的 `batch_manifest.json`、`batch_report.json` 和 `batch_report.html`。

本仓库不是一个仅靠单条 Python 命令即可完成语义抽取的传统程序。论文理解、表格含义判断和证据归属由支持 Agent Skills 的模型完成；配对、校验和 HTML 渲染由确定性脚本完成。

## 2. 环境准备

### 必需环境

- Python 3.9 或更高版本；
- 一个能够读取本地文件、运行 Python 命令并加载 `SKILL.md` 的 Agent；
- 可检索文本的论文 PDF，以及可选的 SI PDF。

渲染器、校验器和批量清单脚本只使用 Python 标准库。为了提高 PDF 文字、页码和表格定位能力，建议在 Agent 使用的同一 Python 环境安装：

```powershell
python -m pip install pypdf PyMuPDF PyYAML
```

### 安装 Skill

Codex 用户可将仓库放入：

```text
%CODEX_HOME%/skills/photophysical-data-extractor/
```

Deep Code/兼容 Agent Skills 的工具可放入用户级目录：

```text
~/.agents/skills/photophysical-data-extractor/
```

或项目级目录：

```text
.deepcode/skills/photophysical-data-extractor/
```

安装后应保留完整的 `SKILL.md`、`scripts/`、`references/` 和 `report_config.json`。

## 3. 单篇文献使用方法

准备正文 PDF 和 SI PDF，然后向 Agent 发出类似指令：

```text
使用 photophysical-data-extractor 抽取这篇有机材料光物理论文及其 SI。
要求生成 paper_data.json 和 report.html，并在渲染前通过校验。
```

Agent 应依次：

1. 核对正文和 SI 是否齐全；
2. 搜索 RTP、TADF、寿命、量子效率、77 K、基质、掺杂比例等候选位置；
3. 按“化合物＋样品＋测试条件”建立独立记录；
4. 为报告值关联证据编号；
5. 生成 KOI、逻辑骨架和一句话创新点；
6. 写入 `paper_data.json`；
7. 校验 JSON；
8. 使用渲染脚本生成 HTML。

手动执行最后两步时，在 Skill 根目录运行：

```powershell
python scripts/validate_extraction.py "路径/paper_data.json"
python scripts/render_html.py "路径/paper_data.json" "路径/report.html"
```

校验失败时不要直接制作 HTML，应先修正 JSON 中缺失的证据编号、非法状态或结构错误。

## 4. 批量文献使用方法

### 推荐命名

正文和 SI 使用完全相同的文献 ID：

```text
P001_Liu_2024_main.pdf
P001_Liu_2024_SI.pdf
P002_Zhang_2025_main.pdf
P002_Zhang_2025_SI.pdf
```

也可使用每篇文章一个文件夹：

```text
P001_Liu_2024/main.pdf
P001_Liu_2024/SI.pdf
```

不要依赖文件顺序或模糊标题自动配对。不要使用含义不明确的 `1.pdf`、`1SI.pdf`；至少写成 `001_main.pdf`、`001_SI.pdf`。

### 构建配对清单

```powershell
python scripts/build_batch_manifest.py "输入文件夹" "batch_manifest.json"
```

发生正文重复、SI 重复、SI 无正文或角色不明确时，脚本会停止。正文没有 SI 可以继续，但输出必须标记 SI 缺失。

### 推荐输出结构

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

逐篇完成并校验后，建立：

```json
{
  "paper_data_files": [
    "P001_Liu_2024/paper_data.json",
    "P002_Zhang_2025/paper_data.json"
  ]
}
```

然后运行：

```powershell
python scripts/render_html.py "outputs/batch_report.json" "outputs/batch_report.html"
```

批量报告中，文章信息默认展开；每篇文章的主数据默认折叠；证据台账与人工复核为第二级折叠。证据编号会自动按文章隔离。

## 5. 修改物理量表头

### 默认行为

渲染器自动读取 Skill 根目录的 `report_config.json`。不修改该文件时，输出与本项目确认的默认报告一致。

以下四列固定显示，不由该配置控制：

- 化合物；
- Host；
- 掺杂比例；
- 类型。

物理量列由 `physical_quantity_columns` 控制。数组顺序就是表头从左到右的顺序。删除某一项即可隐藏该列。

### 支持的物理字段

| 字段 | 含义 |
|---|---|
| `phi_pl` | 总光致发光量子效率 |
| `lambda_f` | 荧光发射位置 |
| `tau_f` | 荧光寿命 |
| `phi_f` | 荧光量子效率 |
| `lambda_df` | 延迟荧光发射位置 |
| `tau_df` | 延迟荧光寿命 |
| `phi_df` | 延迟荧光量子效率 |
| `lambda_p` | 磷光发射位置 |
| `tau_p` | 磷光寿命 |
| `phi_p` | 磷光量子效率 |
| `k_isc` | 系间窜越速率常数 |
| `k_risc` | 反向系间窜越速率常数 |
| `k_rp` | 磷光辐射相关速率常数 |
| `knr_p` | 三重态非辐射速率常数 |

### 修改列顺序或隐藏列

例如，只保留磷光的发射位置、寿命和效率：

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

若要显示默认表头未包含的 `ΦDF`，可加入：

```json
{"field": "phi_df", "parts": [{"symbol": "Φ", "subscript": "DF"}]}
```

### 组合表头

`parts` 按顺序组合表头。`symbol` 会被包装为主物理量符号，`subscript` 为下标；`text` 用于斜杠或其他普通字符。例如：

```json
{
  "field": "k_rp",
  "parts": [
    {"symbol": "k", "subscript": "P"},
    {"text": "/"},
    {"symbol": "k", "subscript": "r,P"}
  ]
}
```

不要在配置中写 HTML；渲染器会对文字进行转义并生成安全的上、下标结构。

### 修改字体样式

`physical_header_style` 支持：

| 键 | 格式 | 默认值 |
|---|---|---|
| `font_family` | 字体名称 | `Times New Roman` |
| `font_size` | `px`、`pt`、`em` 或 `rem` | `14pt` |
| `font_weight` | 100–900 的整数 | `400` |
| `color` | 六位十六进制颜色 | `#233A57` |
| `symbol_italic` | `true`/`false` | `true` |
| `subscript_italic` | `true`/`false` | `false` |

### 使用独立配置而不修改默认文件

把自定义内容保存为 `my_report_config.json`，将其作为第三个参数传入：

```powershell
python scripts/render_html.py "paper_data.json" "report.html" "my_report_config.json"
```

这样适合不同课题组、论文类型或项目分别维护自己的表头。配置文件不存在、字段不受支持、字段重复或样式格式错误时，渲染器会直接报错，不会静默生成错误表格。

## 6. 人工复核重点

优先复核：

- SI 独有数据；
- 由图中估读的数据；
- PLQY 与磷光量子效率可能混淆的值；
- 可见余辉时间与磷光寿命可能混淆的值；
- TADF、普通延迟荧光、激基缔合物或杂质发光归属；
- 正文与 SI 数值冲突；
- 缺少温度、气氛、激发波长或掺杂比例的数据。

点击主表中的 `[Exx]` 会自动展开证据区并定位至对应条目。绿色高亮表示当前跳转目标，不表示更高置信度；置信度以条目右侧标签为准。

## 7. 常见问题

### HTML 修改后没有变化

不要直接修改已有 `report.html`。修改 `report_config.json` 或渲染器后，重新运行 `scripts/render_html.py`。

### 自定义配置没有生效

确认配置文件是有效 JSON，并确认命令中第三个参数指向正确文件。若未提供第三个参数，渲染器只读取 Skill 根目录的默认 `report_config.json`。

### 表头字段存在但整列为空

配置只决定显示哪些列，不会创造论文未报告的数据。确认 `paper_data.json` 的 `samples[*].fields` 中是否存在对应字段且状态为 `reported`。

### PDF 可以打开但抽不到表格

检查 PDF 是否为扫描件或表格是否以图片形式保存。必要时使用 OCR、页面截图或视觉模型；不要把无法读取的内容标为高置信度。

### 一篇文章出现重复化合物行

JSON 中可以有多个条件记录，但 HTML 应按化合物合并为一行。检查化合物名称是否存在大小写、连字符或空格差异，并确认不同论文没有被错误合并。

## 8. 发布前检查清单

- 每个报告值都有有效的证据编号；
- 正文和 SI 覆盖状态真实；
- 室温、77 K、薄膜、溶液和气氛条件没有互相合并；
- 掺杂比例没有被删除；
- 主表的红色、蓝色和最佳值样式符合规则；
- 低置信度与冲突项进入人工复核；
- `validate_extraction.py` 返回成功；
- 报告由当前 JSON 重新渲染，而非手工修改旧 HTML。
