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

渲染器、校验器和批量清单脚本只使用 Python 标准库。PDF 读取依赖记录在 `requirements.txt`；需要补齐时由 Agent 使用已选解释器自动安装：

```powershell
<selected-python> -m pip install -r requirements.txt
```

Agent 应按 `runtime_config.json` 顺序选择解释器，然后自动运行 `scripts/check_environment.py`。本机优先使用 `D:\Tool\Pathon\python.exe`；其他电脑会跳过不存在的机器专用路径并尝试可移植候选。Windows 下不要调用裸 `python`，因为它可能是 Microsoft Store 占位符。不得静默使用 Python 3.8 或更早版本，也不得把环境检查、JSON 校验或 HTML 渲染转交给用户手工执行。

### 安装 Skill

不要要求用户手动克隆私人仓库。使用 skills CLI 安装：

```powershell
npx skills add PPOLAN-hub/photophysical-data-extractor --skill photophysical-data-extractor --agent codex
```

其他 Agent 可将 `codex` 替换为对应标识，例如：

```powershell
npx skills add PPOLAN-hub/photophysical-data-extractor --skill photophysical-data-extractor --agent claude-code
npx skills add PPOLAN-hub/photophysical-data-extractor --skill photophysical-data-extractor --agent kimi-cli
```

私人仓库要求当前 GitHub 账号已经获得访问权限。不要把 Personal Access Token 写入命令、提示词或聊天记录。

Cherry Studio 1.9.12 或更新版本使用界面安装：先从有权限的 GitHub 页面下载 ZIP，再进入 `设置 → 技能 → 从 ZIP 文件安装`，最后在目标 Agent 的技能设置中启用本 Skill。

## 3. 用户调用方式

单篇论文可直接上传正文与 SI 两份文件，不要求重命名或由用户手工配对。只需输入：

```text
PDE
```

也可附加关注点：

```text
PDE，重点核对 77 K 数据和 SI 中的寿命表格。
```

Agent 必须自动识别正文与 SI，并完成抽取、JSON 校验和 HTML 渲染，不得要求用户手工运行校验器或渲染器。

多篇论文按批量命名规则准备后，输入：

```text
PDEmore
```

多篇模式不得按标题或上传顺序猜测配对。

## 4. 批量命名

批量任务支持两种完整编号配对方式，推荐使用 `P01/S01`：

```text
P01.pdf  对应  S01.pdf
P02.pdf  对应  S02.pdf
P03.pdf  对应  S03.pdf

1main.pdf  对应  1SI.pdf
2main.pdf  对应  2SI.pdf
```

`P/main` 表示正文，`S/SI` 表示支持信息。数字必须完全一致，包括前导零；`P01.pdf` 不得与 `S1.pdf` 配对，同一对文件也不得混用两种命名方式。不要按上传顺序、标题或 PDF 元数据猜测。正文缺少 SI 可以继续并标记缺失；孤立 SI、重复正文或重复 SI 必须停止。

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

把自定义内容保存为 `my_report_config.json`：

将配置文件与论文一起交给 Agent，并输入 `PDE`。Agent 会按该配置自动重新生成报告。

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

不要直接修改已有 `report.html`。修改 `report_config.json` 后，让 Agent 自动重新生成报告。

### 自定义配置没有生效

确认配置文件是有效 JSON，并在调用 `PDE` 时把该配置文件与论文一起交给 Agent。未提供自定义配置时，Agent 使用 Skill 根目录的默认 `report_config.json`。

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
- 主表的室温掺杂体系 `#D9001B` 红色、77 K `#0000FF` 蓝色和最佳值样式符合规则；完成渲染后由 Agent 自动运行 `scripts/validate_report_html.py`，用户无需手工检查脚本；
- 低置信度与冲突项进入人工复核；
- Agent 已完成 JSON 校验；
- 报告由当前 JSON 重新渲染，而非手工修改旧 HTML。
