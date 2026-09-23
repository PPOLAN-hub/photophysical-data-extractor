# 豆包工作安装与提示词

适用于带“工作”模式和“插件 · 技能 · 伙伴”入口的豆包桌面端。普通聊天模式不使用本流程。

## 安装

1. 下载 PDE 的豆包发行附件 `photophysical-data-extractor-doubao-skill-vX.Y.Z.zip`。
2. 可选但推荐：按同名 `.sha256` 文件核对 ZIP 的 SHA-256。
3. 在豆包左上角切换到“工作”。
4. 打开“插件 · 技能 · 伙伴”。
5. 选择“新建”或“上传技能”，上传 ZIP，不要先解压后只选 `SKILL.md`。
6. 安装完成后返回工作对话，通过输入框下方的“技能”选择 `photophysical-data-extractor`。
7. 先运行下面的环境自检和首次输出/Obsidian 配置提示词，再处理论文。

ZIP 根目录必须直接包含 `SKILL.md`，并同时保留 `scripts/`、`references/`、`requirements.txt`、`runtime_config.json` 和 `report_config.json`。GitHub 自动生成的 Source code ZIP 通常多套一层目录，不作为豆包安装包。

## 首次安装后的环境自检提示词

```text
请加载 photophysical-data-extractor 技能。

本次只做 PDE 运行环境检测，不提取论文数据：

1. 完整读取 SKILL.md，以及其中要求的 references/portable-agent-contract.md。
2. 按 runtime_config.json 寻找 Python 3.9 或更高版本。
3. 运行 scripts/check_environment.py。
4. 检查 pypdf、PyMuPDF、PyYAML 和 python-docx。
5. 检查是否具备读取 PDF、写入 JSON/HTML/DOCX 和执行 Python 脚本的权限。
6. 逐项报告解释器、依赖、文件权限和脚本执行结果。

如果脚本不能运行，必须明确输出：
PDE script runtime unavailable

不得把“已经读取 SKILL.md”等同于半自动化 PDE 环境已经可用。
```

## 首次正式使用前的强制输出与 Obsidian 配置提示词

```text
请加载 photophysical-data-extractor 技能并执行首次本地配置。

在开始论文抽取前必须完成以下事项，不得跳过：

1. 让我选择统一保存 JSON、HTML、Word 和任务工作目录的 PDE 输出根目录；
2. 让我选择 Obsidian Vault 根目录，并验证其中存在 .obsidian；
3. 让我选择 Vault 内的 PDE 归档域目录；
4. 让我选择需要读取的归档约定文件；
5. 使用 scripts/configure_archive.py 实测输出根目录和 Vault 归档目录的写权限，并显示四个选定路径；
6. 经我确认后保存本机私有配置，禁止把绝对路径写入公共 Skill 文件；
7. 每次任务先运行 scripts/prepare_output_dir.py，正式文件只能写入它返回的任务目录，中间文件只能进入 _work；
8. 第一次有真实 paper_data.json 时，先运行 archive_report.py --preview；
9. 完整展示 Markdown 与计划写入路径，经我确认后才允许 --yes 写入 Vault。

输出目录、归档配置或归档约定缺失时，不得开始正式 PDE，不得自行选择其他目录、Vault 或模板。Obsidian 只保存归档卡与链接，不复制完整报告。
```

## 单篇论文正式调用提示词

先在同一任务中上传正文 PDF 和可选的 Supporting Information，再输入：

```text
PDE

请使用已安装的 photophysical-data-extractor 技能处理本次上传的论文正文和 SI。

必须先确认统一输出目录和 Obsidian 归档配置有效，运行 prepare_output_dir.py 建立本次任务目录，再执行 PDF 文本索引、页码锚定、表图编号索引以及 DOI 和引用信息抓取。严格执行 references/portable-agent-contract.md，区分所有化合物、基质或溶剂、浓度、样品状态、温度、气氛、激发、延迟、门控、发光机制及实验/计算条件。

不得猜测缺失数据，不得合并或擅自解决冲突值，不得混淆可见余辉时间与磷光寿命、总 PLQY 与磷光量子产率、g_lum 与 g_abs。最终必须完成 JSON 审计与校验、条件子行 HTML、Word、两种格式验证以及 Obsidian Markdown 归档。若任一必需脚本或校验失败，不得声称完整 PDE 流程已经完成。
```

## 仅做诊断而不执行正式 PDE

在正式调用提示词末尾追加：

```text
本次只做诊断，不作为正式 PDE 交付，不写入 Obsidian。请明确列出因此未执行的 HTML、Word 和归档步骤。
```

## 验收标准

豆包能够列出选用的 Python、环境检查结果和归档配置，并实际运行索引、书目信息、审计、JSON 校验、HTML/Word 渲染校验及 Obsidian 归档脚本，才算完成半自动化 PDE。若只能复述 `SKILL.md` 而没有脚本运行证据，只能视为自然语言模式。
