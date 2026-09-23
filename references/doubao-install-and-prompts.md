# 豆包工作安装与提示词

适用于带“工作”模式和“插件 · 技能 · 伙伴”入口的豆包桌面端。普通聊天模式不使用本流程。

## 安装

1. 下载 PDE 的豆包发行附件 `photophysical-data-extractor-doubao-skill-vX.Y.Z.zip`。
2. 可选但推荐：按同名 `.sha256` 文件核对 ZIP 的 SHA-256。
3. 在豆包左上角切换到“工作”。
4. 打开“插件 · 技能 · 伙伴”。
5. 选择“新建”或“上传技能”，上传 ZIP，不要先解压后只选 `SKILL.md`。
6. 安装完成后返回工作对话，通过输入框下方的“技能”选择 `photophysical-data-extractor`。
7. 先运行下面的环境自检提示词，再处理论文。

ZIP 根目录必须直接包含 `SKILL.md`，并同时保留 `scripts/`、`references/`、`requirements.txt`、`runtime_config.json` 和 `report_config.json`。GitHub 自动生成的 Source code ZIP 通常多套一层目录，不作为豆包安装包。

## 首次安装后的环境自检提示词

```text
请加载 photophysical-data-extractor 技能。

本次只做 PDE 运行环境检测，不提取论文数据：

1. 完整读取 SKILL.md，以及其中要求的 references/portable-agent-contract.md。
2. 按 runtime_config.json 寻找 Python 3.9 或更高版本。
3. 运行 scripts/check_environment.py。
4. 检查 pypdf、PyMuPDF 和 PyYAML。
5. 检查是否具备读取 PDF、写入 JSON/HTML 和执行 Python 脚本的权限。
6. 逐项报告解释器、依赖、文件权限和脚本执行结果。

如果脚本不能运行，必须明确输出：
PDE script runtime unavailable

不得把“已经读取 SKILL.md”等同于半自动化 PDE 环境已经可用。
```

## 单篇论文正式调用提示词

先在同一任务中上传正文 PDF 和可选的 Supporting Information，再输入：

```text
PDE

请使用已安装的 photophysical-data-extractor 技能处理本次上传的论文正文和 SI。

必须先执行 PDF 文本索引、页码锚定、表图编号索引以及 DOI 和引用信息抓取，再进行语义数据提取。严格执行 references/portable-agent-contract.md，区分所有化合物、基质或溶剂、浓度、样品状态、温度、气氛、激发、延迟、门控、发光机制及实验/计算条件。

不得猜测缺失数据，不得合并或擅自解决冲突值，不得混淆可见余辉时间与磷光寿命、总 PLQY 与磷光量子产率、g_lum 与 g_abs。最终必须运行 scripts/audit_extraction.py 和 scripts/validate_extraction.py。若任一必需脚本或校验失败，不得声称完整 PDE 流程已经完成。
```

## 仅在对话中输出结果

在正式调用提示词末尾追加：

```text
本次仅在对话中输出提取结果，不交付 HTML 文件；但仍须完成索引、审计和 JSON 结构校验。
```

## 验收标准

豆包能够列出选用的 Python、环境检查结果，并实际运行 `index_sources.py`、`fetch_bibliography.py`、`audit_extraction.py` 和 `validate_extraction.py`，才算完成半自动化 PDE。若只能复述 `SKILL.md` 而没有脚本运行证据，只能视为自然语言模式。
