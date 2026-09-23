#!/usr/bin/env python3
"""Preview or write a deterministic PDE Markdown card into an Obsidian vault."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

from archive_common import load_config, require_under_output_root, write_json_atomic
import render_html


BEGIN_SINGLE = "<!-- PDE:SLOT:BEGIN -->"
END_SINGLE = "<!-- PDE:SLOT:END -->"
BEGIN_BATCH = "<!-- PDE:BATCH:BEGIN -->"
END_BATCH = "<!-- PDE:BATCH:END -->"
NUMERIC_PRIORITY = ("tau_p", "afterglow_visible_time", "phi_p", "phi_pl")
FIELD_SYMBOLS = {
    "tau_p": "τ_P",
    "afterglow_visible_time": "余辉",
    "phi_p": "Φ_P",
    "phi_pl": "Φ_PL",
    "lambda_p": "λ_P",
}


def write_text_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_json", type=Path)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--archive-config", type=Path)
    parser.add_argument("--topic", default="PDE批次")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--yes", action="store_true")
    return parser.parse_args()


def clean_inline(value, limit):
    text = re.sub(r"\s+", " ", str(value or "未提供")).strip()
    text = text.replace("|", "／")
    return text if len(text) <= limit else text[: max(1, limit - 1)] + "…"


def analysis_value(value, limit=25):
    if isinstance(value, dict):
        value = value.get("text")
    return clean_inline(value, limit)


def review_text(item, limit=40):
    if isinstance(item, dict):
        value = item.get("issue") or item.get("detail") or json.dumps(item, ensure_ascii=False)
    else:
        value = item
    return clean_inline(value or "无", limit)


def numeric_value(field):
    if not isinstance(field, dict) or field.get("status") != "reported":
        return None
    raw_value = str(field.get("raw_value") or "")
    numbers = [float(item) for item in re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", raw_value)]
    if not numbers:
        return None
    value = max(numbers)
    unit = str(field.get("raw_unit") or "").strip()
    combined = (raw_value + " " + unit).lower()
    if re.search(r"\bms\b", combined):
        return value / 1000.0, "s"
    if re.search(r"\bmin\b", combined):
        return value * 60.0, "s"
    if "%" in combined or unit == "%":
        return value, "%"
    if re.search(r"\bs\b", combined):
        return value, "s"
    return value, unit


def format_number(value):
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def best_metric(data):
    for field_name in NUMERIC_PRIORITY:
        candidates = []
        for sample in data.get("samples", []):
            field = sample.get("fields", {}).get(field_name)
            parsed = numeric_value(field)
            if parsed:
                candidates.append((parsed[0], parsed[1], sample, field))
        if candidates:
            value, unit, sample, field = max(candidates, key=lambda item: item[0])
            return {
                "field": field_name,
                "symbol": FIELD_SYMBOLS[field_name],
                "value": value,
                "unit": unit,
                "sample": render_html.raw(sample.get("identity", {}).get("compound"), "未命名样品"),
                "evidence_id": field.get("evidence_id") or "未关联",
                "display": f"**{FIELD_SYMBOLS[field_name]} {format_number(value)} {unit}**".replace("  ", " "),
            }
    return None


def field_display(sample, field_name):
    field = sample.get("fields", {}).get(field_name)
    parsed = numeric_value(field)
    if not parsed:
        return "—"
    value, unit = parsed
    return f"**{format_number(value)} {unit}**".replace("  ", " ")


def tags_for(data):
    text = " ".join(
        str(sample.get("fields", {}).get("emission_assignment", {}).get("raw_value") or "")
        for sample in data.get("samples", [])
    ).lower()
    tags = ["PDE", "报告"]
    if "rtp" in text or "phosphor" in text or "磷光" in text:
        tags.append("RTP")
    if "tadf" in text or "delayed fluorescence" in text or "延迟荧光" in text:
        tags.append("TADF")
    if any(sample.get("fields", {}).get("g_lum", {}).get("status") == "reported" for sample in data.get("samples", [])):
        tags.append("CPL")
    return tags


def file_link(path: Path, label):
    path = path.expanduser().resolve()
    if not path.is_file():
        return f"{label}（⚠️ 产物缺失：`{path}`）"
    return f"[{label}]({path.as_uri()})"


def yaml_string(value):
    return json.dumps(str(value or ""), ensure_ascii=False)


def title_short(data):
    paper = data.get("paper", {})
    title = str(paper.get("title_short_cn") or paper.get("title") or "未命名论文")
    title = re.sub(r'[\\/:*?"<>|]', "", title).strip(" .")
    return clean_inline(title, 20)


def render_single(data, source, html, docx, model, convention_hash):
    paper = data.get("paper", {})
    paper_id = str(paper.get("paper_id") or "P1")
    analysis = data.get("article_analysis", {})
    innovation = analysis_value(analysis.get("one_sentence_innovation"), 25)
    koi = analysis.get("koi", {}) if isinstance(analysis, dict) else {}
    mechanism = analysis_value(koi.get("mechanism") if isinstance(koi, dict) else None, 60)
    review = data.get("manual_review", [])
    best = best_metric(data)
    strongest = best["display"] + f"（{clean_inline(best['sample'], 18)}，{best['evidence_id']}）" if best else "—（未找到可比较数值）"
    doubt = review_text(review[0], 25) if review else "无已列复核项"
    highlight = strongest if best else "—"
    authors = paper.get("authors", [])
    if not isinstance(authors, list):
        authors = [authors] if authors else []
    rows = []
    for sample in data.get("samples", []):
        compound = clean_inline(render_html.raw(sample.get("identity", {}).get("compound"), "未命名样品"), 30)
        rows.append(
            f"| {compound} | {field_display(sample, 'tau_p')} | {field_display(sample, 'phi_p')} | {field_display(sample, 'lambda_p')} |"
        )
    if not rows:
        rows.append("| — | — | — | — |")
    tags = ", ".join(tags_for(data))
    journal = paper.get("journal") or paper.get("journal_year") or "未报告"
    year = paper.get("year") or "未报告"
    main = paper.get("main_pdf_reviewed", "未报告")
    si = paper.get("supporting_information_reviewed", "未报告")
    return f'''---
title: {yaml_string(paper.get("title") or "未报告")}
doi: {yaml_string(paper.get("doi") or "未报告")}
journal: {yaml_string(journal)}
year: {yaml_string(year)}
authors: {json.dumps(authors, ensure_ascii=False)}
skill: photophysical-data-extractor
paper_id: {yaml_string(paper_id)}
export_date: {date.today().isoformat()}
model: {yaml_string(model)}
tags: [{tags}]
archive_convention_sha256: {convention_hash}
---

{BEGIN_SINGLE}
# ⛛️ {paper_id} · {title_short(data)}

> ⛛️ PDE 单篇抽取 · 执行模型 {model} · {date.today().isoformat()}
> 📊 **{len(data.get("samples", []))}** 个样品 · **{len(data.get("evidence_ledger", []))}** 条证据 · 待人工复核 **{len(review)}** 项

## 🎯 30 秒版（ADHD 速览）

- **一句话**：{innovation}
- **最强证据**：{strongest}
- **最大亮点**：{clean_inline(highlight, 25)}
- **最大疑点**：{doubt}
- **待核项**：**{len(review)}** 项需人工核对

## 🔢 关键数据

> ⏱ 只看加粗数值即可；每行对应一个样品/测量条件。

| 样品 | τ_P | Φ_P | λ_P |
|---|---:|---:|---:|
{chr(10).join(rows)}

## 📄 报告文件（点开才读）

- 📄 {file_link(html, "打开 HTML 报告")} · 📝 {file_link(docx, "打开 Word 报告")} · 🗂️ {file_link(source, "paper_data.json")}

## 📎 论文信息与溯源

| 项目 | 内容 |
|---|---|
| 期刊·年 | {clean_inline(journal, 35)} · {year} |
| DOI | {paper.get("doi") or "未报告"} |
| 作者 | {clean_inline("、".join(map(str, authors)), 40)} |
| 机理 | {mechanism} |
| 证据 | {len(data.get("evidence_ledger", []))} 条（主文={main} / SI={si}） |

{END_SINGLE}

---
*由 photophysical-data-extractor（PDE）生成 · 执行模型 {model} · 报告归档于 Obsidian Vault*
'''


def paper_sort_key(data):
    paper_id = str(data.get("paper", {}).get("paper_id") or "")
    match = re.search(r"\d+", paper_id)
    return (int(match.group()) if match else 10**9, paper_id)


def render_batch(documents, source, html, docx, model, topic, convention_hash):
    documents = sorted(documents, key=paper_sort_key)
    rows = []
    review_rows = []
    best_items = []
    paper_ids = []
    for data in documents:
        paper = data.get("paper", {})
        paper_id = str(paper.get("paper_id") or "未编号")
        paper_ids.append(paper_id)
        best = best_metric(data)
        if best:
            best_items.append((best["value"], paper_id, best["display"]))
        innovation = analysis_value(data.get("article_analysis", {}).get("one_sentence_innovation"), 40)
        journal = clean_inline(paper.get("journal") or paper.get("journal_year") or "未报告", 24)
        year = paper.get("year") or "未报告"
        review = data.get("manual_review", [])
        href = html.expanduser().resolve().as_uri() + "#" + quote(paper_id)
        rows.append(
            f"| [`{paper_id}`]({href}) | {best['display'] if best else '—'} | {innovation} | {journal} · {year} | {'⚠️ ' + str(len(review)) if review else '—'} |"
        )
        if review:
            review_rows.append(f"| [`{paper_id}`]({href}) | {review_text(review[0], 30)} | 人工复核列表 |")
    best_items.sort(reverse=True)
    highlight_id, highlight_reason = (best_items[0][1], best_items[0][2] + "，全批最高") if best_items else ("—", "未找到可比较数值")
    review_missing = sum(1 for data in documents if best_metric(data) is None)
    review_total = sum(len(data.get("manual_review", [])) for data in documents)
    return f'''---
title: {yaml_string(f"PDE {date.today().isoformat()} 批次（{topic}）批量抽取报告")}
skill: photophysical-data-extractor
paper_id: {yaml_string(date.today().isoformat() + "-batch")}
export_date: {date.today().isoformat()}
model: {yaml_string(model)}
tags: [PDE, 报告]
papers: {json.dumps(paper_ids, ensure_ascii=False)}
source: {yaml_string(str(source.resolve().parent))}
archive_convention_sha256: {convention_hash}
---

{BEGIN_BATCH}
# ⛛️ {date.today().isoformat()} 批次 · PDE 批量抽取报告

> ⛛️ PDE 批量抽取 · 执行模型 {model} · {date.today().isoformat()}
> 📊 共 **{len(documents)}** 篇：成功 **{len(documents)}** · 失败 **0** · 关键数字待核 **{review_missing}** 篇
> 📌 最值得先看：**{highlight_id}** —— {highlight_reason}

## 🎯 30 秒版（ADHD 速览）

- **一句话**：完成 {len(documents)} 篇证据化光物理抽取
- **最强证据**：{highlight_reason}
- **最大亮点**：数据均可回溯证据编号
- **最大疑点**：共 {review_total} 项人工复核提醒
- **待核项**：**{review_missing}** 篇缺少关键数字

## 📄 报告文件（点开才读）

- 📄 {file_link(html, "批量 HTML 报告")} · 📝 {file_link(docx, "批量 Word 报告")} · 🗂️ {file_link(source, "batch_report.json")}

## 📊 论文清单

> ⏱ 扫一遍约 2 分钟，只看「关键数字」列即可。

| 序号 | 关键数字 | 一句话创新 | 期刊·年 | 复核 |
|---|---:|---|---|---:|
{chr(10).join(rows)}

## ⚠️ 需人工复核（{review_total} 项）

> ⏱ 只需看 ⚠️ 行。

| 序号 | 复核点 | 线索 |
|---|---|---|
{chr(10).join(review_rows) if review_rows else '| — | 无已列复核项 | — |'}

{END_BATCH}

---
*由 photophysical-data-extractor（PDE）生成 · 执行模型 {model} · 报告归档于 Obsidian Vault*
'''


def safe_name(value):
    return re.sub(r'[\\/:*?"<>|]', "", str(value)).strip(" .") or "PDE报告"


def replace_stable_block(existing, rendered, begin, end):
    if begin not in existing or end not in existing:
        return None
    new_block = rendered[rendered.index(begin) : rendered.index(end) + len(end)]
    return existing[: existing.index(begin)] + new_block + existing[existing.index(end) + len(end) :]


def update_index(index_path, folder_name, count, label, begin, end):
    row = f"| **{folder_name}** | {count} | {label} | [[{folder_name}/{folder_name}|报告]] |"
    if not index_path.exists():
        source = f"---\ntitle: PDE 光物提取索引\ntags: [PDE, 索引]\n---\n\n# ⛛️ PDE 光物提取索引\n\n{begin}\n| 批次 | 篇数 | 说明 | 导航 |\n|---|---:|---|---|\n{row}\n{end}\n"
        write_text_lf(index_path, source)
        return
    source = index_path.read_text(encoding="utf-8")
    if begin not in source or end not in source:
        with index_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"\n## 追加登记\n\n{row}\n")
        return
    block = source[source.index(begin) + len(begin) : source.index(end)]
    existing_rows = [line for line in block.splitlines() if line.startswith("|") and f"[[{folder_name}/" not in line]
    headers = existing_rows[:2] if len(existing_rows) >= 2 else ["| 批次 | 篇数 | 说明 | 导航 |", "|---|---:|---|---|"]
    data_rows = existing_rows[2:] if len(existing_rows) >= 2 else []
    new_block = "\n" + "\n".join(headers + [row] + data_rows) + "\n"
    updated = source[: source.index(begin) + len(begin)] + new_block + source[source.index(end) :]
    write_text_lf(index_path, updated)


def main():
    args = parse_args()
    config_path, config = load_config(args.archive_config)
    source = require_under_output_root(args.source_json, config)
    documents = render_html.load_documents(source)
    if not documents:
        raise ValueError("No paper data found in input JSON")
    html = require_under_output_root(args.html, config)
    docx = require_under_output_root(args.docx, config)
    batch = len(documents) > 1
    if batch:
        folder_name = safe_name(f"{date.today().isoformat()}_{args.topic}")
        markdown = render_batch(documents, source, html, docx, args.model, args.topic, config["convention_sha256"])
        begin, end = BEGIN_BATCH, END_BATCH
        label = f"PDE 批量抽取 {len(documents)} 篇"
    else:
        paper_id = str(documents[0].get("paper", {}).get("paper_id") or "P1")
        folder_name = safe_name(f"{paper_id}-{title_short(documents[0])}")
        markdown = render_single(documents[0], source, html, docx, args.model, config["convention_sha256"])
        begin, end = BEGIN_SINGLE, END_SINGLE
        label = clean_inline(documents[0].get("paper", {}).get("title") or "PDE 单篇报告", 35)
    vault = Path(config["vault_root"])
    archive_root = vault / config["archive_dir"]
    target_dir = archive_root / folder_name
    target = target_dir / f"{folder_name}.md"
    index_path = archive_root / config.get("index", {}).get("file", "_索引.md")
    print(f"[archive] output_root={config['output_root']}")
    print(f"[archive] vault={vault} dir={config['archive_dir']} convention={config['convention_path']}")
    print(f"[archive] target={target}")
    print(f"[archive] index={index_path}")
    print(markdown)
    if args.preview:
        print("[archive] preview only; no vault files were written")
        return
    if not args.yes:
        raise SystemExit("Archive write requires a completed real-data preview and --yes confirmation.")
    target_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        stable = replace_stable_block(existing, markdown, begin, end)
        if stable is not None:
            markdown = stable
        else:
            backup_dir = archive_root / config.get("conflict", {}).get("backup_dir", "_历史")
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.move(str(target), str(backup_dir / f"{stamp}_{target.name}"))
    write_text_lf(target, markdown)
    update_index(
        index_path,
        folder_name,
        len(documents),
        label,
        config.get("index", {}).get("begin", "<!-- PDE:INDEX:BEGIN -->"),
        config.get("index", {}).get("end", "<!-- PDE:INDEX:END -->"),
    )
    if not config.get("preview_confirmed"):
        config["preview_confirmed"] = True
        config["preview_confirmed_at"] = datetime.now().isoformat()
        write_json_atomic(config_path, config)
    print(f"[archive] written={target}")


if __name__ == "__main__":
    main()
