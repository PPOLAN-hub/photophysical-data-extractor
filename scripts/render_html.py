#!/usr/bin/env python3
"""Render a focused, auditable long-lived-emission report from canonical JSON."""
import html
import json
import re
import sys
from pathlib import Path


FIELD_LABELS = {
    "compound": "化合物",
    "host_matrix": "Host/Matrix",
    "doping_ratio": "掺杂比例",
    "sample_state": "样品状态",
    "atmosphere": "气氛",
    "temperature": "温度",
    "excitation": "激发条件",
    "delay": "延迟时间",
    "gate_window": "门控窗口",
    "identity": "样品身份",
    "conditions": "测试条件",
    "emission_assignment": "发光归属",
    "afterglow_color": "余辉颜色",
    "afterglow_visible_time": "可见余辉时间",
    "phi_pl": "Φ<sub>PL</sub>",
    "lambda_f": "λ<sub>F</sub>",
    "tau_f": "τ<sub>F</sub>",
    "phi_f": "Φ<sub>F</sub>",
    "lambda_df": "λ<sub>DF</sub>",
    "tau_df": "τ<sub>DF</sub>",
    "phi_df": "Φ<sub>DF</sub>",
    "lambda_p": "λ<sub>P</sub>",
    "tau_p": "τ<sub>P</sub>",
    "phi_p": "Φ<sub>P</sub>",
    "k_isc": "k<sub>ISC</sub>",
    "k_risc": "k<sub>RISC</sub>",
    "k_rp": "k<sub>P</sub>/k<sub>r,P</sub>",
    "knr_p": "k<sub>nr,P</sub>",
}

PAPER_LABELS = {
    "paper_id": "文献 ID",
    "title": "题目",
    "doi": "DOI",
    "journal_year": "期刊 / 年份",
    "main_pdf_reviewed": "主文已核对",
    "supporting_information_reviewed": "SI 已核对",
    "scope": "抽取范围",
}

METRIC_ORDER = [
    "lambda_f", "tau_f", "phi_f",
    "lambda_df", "tau_df", "phi_df",
    "lambda_p", "tau_p", "phi_p",
    "afterglow_color", "afterglow_visible_time", "phi_pl",
    "k_isc", "k_risc", "k_rp", "knr_p",
]

EVIDENCE_TYPE_LABELS = {
    "direct_text": "正文直接陈述",
    "table_value": "表格数值",
    "figure_estimate": "图中估读",
    "calculated_from_reported_values": "基于原文数值计算",
    "author_assignment": "作者归属",
}


def esc(value):
    return html.escape("" if value is None else str(value))


def raw(field, fallback="未报告"):
    if not isinstance(field, dict) or field.get("status") != "reported":
        return fallback
    value = field.get("raw_value")
    unit = field.get("raw_unit")
    if value is None:
        return fallback
    return (str(value) + (" " + str(unit) if unit else "")).strip()


def scientific_value(value):
    text = esc(value)
    substitutions = [
        (r"tau_p", "τ<sub>P</sub>"),
        (r"lambda_p", "λ<sub>P</sub>"),
        (r"tau_longest", "τ<sub>longest</sub>"),
        (r"tauavg", "τ<sub>avg</sub>"),
        (r"tau([123])", r"τ<sub>\1</sub>"),
        (r"lambda", "λ"),
    ]
    for pattern, replacement in substitutions:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def field_label(name):
    return FIELD_LABELS.get(name, esc(name))


def multi_field_label(value):
    names = [item.strip() for item in str(value or "").split(",") if item.strip()]
    return "、".join(field_label(name) for name in names) or "未标注字段"


def evidence_link(evidence_id):
    if not evidence_id:
        return ""
    safe_id = esc(evidence_id)
    return f" <a class='evidence-link' href='#{safe_id}' title='跳转到证据 {safe_id}'>[{safe_id}]</a>"


def displayed(field):
    if not isinstance(field, dict):
        return "<span class='status muted'>未报告</span>"
    status = field.get("status", "uncertain")
    if status != "reported":
        label = "未报告" if status == "not_reported" else "无法确认"
        return f"<span class='status {esc(status)}'>{label}</span>"
    value = raw(field, "无法确认")
    return scientific_value(value) + evidence_link(field.get("evidence_id"))


def reported_items(mapping, names):
    items = []
    for name in names:
        field = mapping.get(name)
        if isinstance(field, dict) and field.get("status") == "reported":
            items.append((name, field))
    return items


def context_text(field):
    context = field.get("measurement_context") if isinstance(field, dict) else None
    if not isinstance(context, dict) or not context:
        return ""
    labels = {
        "excitation": "激发",
        "emission": "监测",
        "temperature": "温度",
        "atmosphere": "气氛",
        "delay": "延迟",
        "gate_window": "门控",
    }
    parts = [f"{labels.get(key, key)}：{esc(value)}" for key, value in context.items()]
    return "<div class='metric-context'>" + " · ".join(parts) + "</div>"


def condition_title(sample):
    fields = sample.get("fields", {})
    conditions = sample.get("conditions", {})
    assignment = raw(fields.get("emission_assignment"), "未明确归属")
    temperature = raw(conditions.get("temperature"), "")
    atmosphere = raw(conditions.get("atmosphere"), "")
    primary = " · ".join(part for part in (temperature, assignment) if part)
    secondary = atmosphere if atmosphere and atmosphere not in primary else ""
    return primary or "条件未完整报告", secondary


def sample_panel(sample):
    identity = sample.get("identity", {})
    conditions = sample.get("conditions", {})
    fields = sample.get("fields", {})
    title, subtitle = condition_title(sample)
    details = []
    for name in ("host_matrix", "doping_ratio", "sample_state"):
        field = identity.get(name)
        if isinstance(field, dict) and field.get("status") == "reported":
            details.append(f"<span><b>{field_label(name)}：</b>{displayed(field)}</span>")
    for name in ("excitation", "delay", "gate_window"):
        field = conditions.get(name)
        if isinstance(field, dict) and field.get("status") == "reported":
            details.append(f"<span><b>{field_label(name)}：</b>{displayed(field)}</span>")
    metrics = []
    for name, field in reported_items(fields, METRIC_ORDER):
        metrics.append(
            "<div class='metric'>"
            f"<div class='metric-label'>{field_label(name)}</div>"
            f"<div class='metric-value'>{displayed(field)}</div>"
            f"{context_text(field)}"
            "</div>"
        )
    note = sample.get("notes")
    note_html = f"<p class='sample-note'><b>备注：</b>{scientific_value(note)}</p>" if note else ""
    metrics_html = "".join(metrics) if metrics else "<p class='empty'>无已报告的目标参数</p>"
    return (
        "<article class='condition-card'>"
        "<header class='condition-head'>"
        f"<div><span class='row-id'>{esc(sample.get('row_id'))}</span><h4>{esc(title)}</h4>"
        f"<p>{esc(subtitle)}</p></div>"
        "</header>"
        f"<div class='condition-details'>{''.join(details)}</div>"
        f"<div class='metric-grid'>{metrics_html}</div>"
        f"{note_html}"
        "</article>"
    )


TABLE_COLUMNS = [
    ("compound", "化合物", "identity"),
    ("host_matrix", "Host", "identity"),
    ("emission_assignment", "类型", "fields"),
    ("phi_pl", "Φ<sub>PL</sub>", "fields"),
    ("lambda_f", "λ<sub>F</sub>", "fields"),
    ("tau_f", "τ<sub>F</sub>", "fields"),
    ("phi_f", "Φ<sub>F</sub>", "fields"),
    ("lambda_df", "λ<sub>DF</sub>", "fields"),
    ("tau_df", "τ<sub>DF</sub>", "fields"),
    ("lambda_p", "λ<sub>P</sub>", "fields"),
    ("tau_p", "τ<sub>P</sub>", "fields"),
    ("phi_p", "Φ<sub>P</sub>", "fields"),
    ("k_isc", "k<sub>ISC</sub>", "fields"),
    ("k_risc", "k<sub>RISC</sub>", "fields"),
    ("k_rp", "k<sub>P</sub>/k<sub>r,P</sub>", "fields"),
    ("knr_p", "k<sub>nr,P</sub>", "fields"),
]


def short_assignment(value):
    lower = str(value or "").lower()
    if "fluorescence/phosphorescence" in lower or "dual emission" in lower:
        return "F/RTP"
    if "thermally activated delayed fluorescence" in lower or lower.strip() == "tadf":
        return "TADF"
    if "phosphor" in lower or "rtp" in lower:
        return "RTP"
    if "tadf" in lower:
        return "TADF"
    if "delayed fluorescence" in lower:
        return "DF"
    return str(value or "—")


def short_host(value):
    text = str(value or "")
    lower = text.lower()
    if "pmma" in lower and "pva" in lower:
        return "PMMA/PVA"
    if "pmma" in lower:
        return "PMMA"
    if "pva" in lower:
        return "PVA"
    return text


def table_raw(name, field):
    value = raw(field, "—")
    if name == "emission_assignment":
        return esc(short_assignment(value))
    if name == "host_matrix":
        return esc(short_host(value))
    if name in {"phi_pl", "phi_f", "phi_df", "phi_p"}:
        match = re.search(r"\(([0-9.]+\s*%)\)", value)
        if match:
            value = match.group(1)
    if name in {"tau_f", "tau_df", "tau_p"}:
        preferred = re.search(r"tau(?:_?avg|_?longest)\s*=\s*([0-9.]+)\s*(ns|ms|s)", value, re.IGNORECASE)
        if preferred:
            value = preferred.group(1) + " " + preferred.group(2)
        elif value.lower().count("tau") > 1:
            components = re.findall(r"([0-9.]+)\s*(ns|ms|s)", value, re.IGNORECASE)
            if components and len({unit.lower() for _, unit in components}) == 1:
                numbers = [float(number) for number, _ in components]
                unit = components[0][1]
                value = f"{min(numbers):g}–{max(numbers):g} {unit}"
    if name in {"lambda_f", "lambda_df", "lambda_p"} and ";" in value:
        peaks = re.findall(r"[0-9.]+", value)
        unit = "nm" if "nm" in value.lower() else ""
        if len(peaks) > 1:
            value = f"{peaks[0]}–{peaks[-1]}" + (f" {unit}" if unit else "")
    return scientific_value(value)


def compact_field(field, name=""):
    if not isinstance(field, dict) or field.get("status") != "reported":
        return "<span class='table-empty'>—</span>"
    return table_raw(name, field) + evidence_link(field.get("evidence_id"))


def record_tag(sample):
    row_id = str(sample.get("row_id") or "")
    temperature = raw(sample.get("conditions", {}).get("temperature"), "")
    assignment = raw(sample.get("fields", {}).get("emission_assignment"), "")
    lower = assignment.lower()
    mechanism = "TADF" if "tadf" in lower or "delayed fluorescence" in lower else "RTP" if "phosphor" in lower or "rtp" in lower else ""
    return " · ".join(part for part in (row_id, temperature, mechanism) if part)


def condition_summary(sample):
    identity = sample.get("identity", {})
    conditions = sample.get("conditions", {})
    parts = []
    state = identity.get("sample_state")
    if isinstance(state, dict) and state.get("status") == "reported":
        parts.append(compact_field(state))
    for name in ("temperature", "atmosphere", "excitation", "delay", "gate_window"):
        field = conditions.get(name)
        if isinstance(field, dict) and field.get("status") == "reported":
            parts.append(f"<span class='condition-line'><b>{field_label(name)}：</b>{compact_field(field)}</span>")
    return "<br>".join(parts) if parts else "<span class='table-empty'>—</span>"


def stacked_entry(sample, value):
    return (
        "<div class='stacked-entry'>"
        f"<span class='condition-tag'>{esc(record_tag(sample))}</span>"
        f"<div>{value}</div>"
        "</div>"
    )


def record_score(sample, name):
    conditions = sample.get("conditions", {})
    temperature = raw(conditions.get("temperature"), "").lower()
    atmosphere = raw(conditions.get("atmosphere"), "").lower()
    assignment = short_assignment(raw(sample.get("fields", {}).get("emission_assignment"), ""))
    score = 0
    if temperature == "rt" or "room" in temperature:
        score += 100
    elif "77" in temperature or "cryogenic" in temperature:
        score -= 100
    elif "ambient" in atmosphere:
        score += 70
    if name in {"lambda_df", "tau_df", "phi_df"} and assignment == "TADF":
        score += 60
    if name in {"lambda_p", "tau_p", "phi_p"} and "RTP" in assignment:
        score += 40
    return score


def primary_field(records, group, name):
    candidates = []
    for sample in records:
        field = sample.get(group, {}).get(name)
        if not isinstance(field, dict) or field.get("status") != "reported":
            continue
        candidates.append((record_score(sample, name), sample, field))
    if not candidates:
        return "<span class='table-empty'>—</span>"
    candidates.sort(key=lambda item: item[0], reverse=True)
    return compact_field(candidates[0][2], name)


def assignment_cell(records):
    values = []
    evidence_ids = []
    for sample in records:
        field = sample.get("fields", {}).get("emission_assignment")
        if not isinstance(field, dict) or field.get("status") != "reported":
            continue
        value = short_assignment(raw(field, ""))
        if value not in values:
            values.append(value)
            if field.get("evidence_id"):
                evidence_ids.append(field.get("evidence_id"))
    if not values:
        return "<span class='table-empty'>—</span>"
    return esc("/".join(values)) + "".join(evidence_link(item) for item in evidence_ids)


def logic_rows(analysis, colspan):
    if not isinstance(analysis, dict) or not analysis:
        return ""
    stages = [item.get("stage") for item in analysis.get("logic_skeleton", []) if isinstance(item, dict) and item.get("stage")]
    logic = " → ".join(stages)
    koi = analysis.get("koi", {})
    mechanism = analysis_text(koi.get("mechanism"))
    result = analysis_text(koi.get("key_result"))
    rows = []
    if logic:
        rows.append(f"<tr class='paper-note-row'><td colspan='{colspan}'><b>逻辑骨架：</b>{esc(logic)}</td></tr>")
    rows.append(f"<tr class='paper-note-row'><td colspan='{colspan}'><b>核心论点：</b>{mechanism}；{result}</td></tr>")
    return "".join(rows)


def data_table(samples, analysis):
    headers = "".join(f"<th>{label}</th>" for _, label, _ in TABLE_COLUMNS)
    grouped = {}
    for sample in samples:
        compound = raw(sample.get("identity", {}).get("compound"), "未命名化合物")
        grouped.setdefault(compound, []).append(sample)
    rows = []
    for compound, records in grouped.items():
        cells = []
        for name, _, group in TABLE_COLUMNS:
            if name == "compound":
                compound_fields = [item.get("identity", {}).get("compound") for item in records]
                evidence_ids = []
                for field in compound_fields:
                    if isinstance(field, dict) and field.get("evidence_id") not in evidence_ids:
                        evidence_ids.append(field.get("evidence_id"))
                value = esc(compound) + (evidence_link(evidence_ids[0]) if evidence_ids else "")
            elif name == "emission_assignment":
                value = assignment_cell(records)
            else:
                value = primary_field(records, group, name)
            cell_class = "compound-cell" if name == "compound" else ""
            cells.append(f"<td class='{cell_class}'>{value}</td>")
        record_ids = ", ".join(str(item.get("row_id")) for item in records)
        rows.append(f"<tr title='条件记录：{esc(record_ids)}'>{''.join(cells)}</tr>")
    innovation = analysis_text(analysis.get("one_sentence_innovation")) if isinstance(analysis, dict) else "未提供"
    colspan = len(TABLE_COLUMNS)
    return (
        "<div class='data-table-wrap'><table class='data-table'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{logic_rows(analysis, colspan)}{''.join(rows)}"
        f"<tr class='innovation-row'><td colspan='{colspan}'><b>创新点：</b>{innovation}</td></tr>"
        "</tbody></table></div>"
    )


def analysis_text(item):
    if isinstance(item, str):
        return esc(item)
    if not isinstance(item, dict):
        return "未提供"
    links = "".join(evidence_link(eid) for eid in item.get("evidence_ids", []))
    return scientific_value(item.get("text", "未提供")) + links


def article_analysis_panel(analysis):
    if not isinstance(analysis, dict) or not analysis:
        return "<div class='analysis-missing'>尚未抽取文章级 KOI、创新点与逻辑骨架。</div>"
    koi_labels = {
        "research_problem": "研究问题",
        "knowledge_gap": "关键缺口",
        "design_strategy": "设计策略",
        "mechanism": "作用机制",
        "key_result": "关键结果",
        "application": "应用落点",
        "boundary": "边界与限制",
    }
    koi = analysis.get("koi", {})
    koi_html = "".join(
        f"<div class='koi-item'><dt>{esc(koi_labels.get(key, key))}</dt><dd>{analysis_text(value)}</dd></div>"
        for key, value in koi.items()
    )
    innovation = analysis_text(analysis.get("one_sentence_innovation"))
    stages = []
    for index, stage in enumerate(analysis.get("logic_skeleton", []), start=1):
        label = stage.get("stage", f"步骤 {index}") if isinstance(stage, dict) else f"步骤 {index}"
        stages.append(
            f"<li><span>{index}</span><div><b>{esc(label)}</b><p>{analysis_text(stage)}</p></div></li>"
        )
    logic_html = "".join(stages) or "<li class='analysis-missing'>未提供逻辑骨架</li>"
    return (
        f"<div class='innovation'><b>一句话创新点</b><p>{innovation}</p></div>"
        f"<dl class='koi-grid'>{koi_html}</dl>"
        f"<ol class='logic-chain'>{logic_html}</ol>"
    )


def confidence_badge(value):
    labels = {"high": "高置信度", "medium": "中置信度", "low": "低置信度"}
    key = str(value or "").lower()
    return f"<span class='confidence {esc(key)}'>{labels.get(key, esc(value))}</span>"


def evidence_cards(ledger):
    cards = []
    for evidence in ledger:
        evidence_id = evidence.get("evidence_id")
        note = evidence.get("manual_check_note")
        quote = evidence.get("quote")
        note_html = f"<p class='evidence-note'><b>复核提示：</b>{scientific_value(note)}</p>" if note else ""
        quote_html = (
            f"<blockquote><span>原文短引</span>“{esc(quote)}”</blockquote>"
            if quote else "<blockquote class='missing-quote'>未提供原文短引</blockquote>"
        )
        cards.append(
            f"<article class='evidence-card' id='{esc(evidence_id)}'>"
            "<header>"
            f"<div><span class='evidence-id'>{esc(evidence_id)}</span>"
            f"<span class='evidence-row'>{esc(evidence.get('row_id'))}</span></div>"
            f"{confidence_badge(evidence.get('confidence'))}"
            "</header>"
            f"<h4>{multi_field_label(evidence.get('field_name'))}</h4>"
            f"<p class='extracted'><b>抽取值：</b>{scientific_value(evidence.get('extracted_value'))}</p>"
            f"<p class='location'><b>位置：</b>{esc(evidence.get('location'))}</p>"
            f"{quote_html}{note_html}"
            f"<footer>{esc(EVIDENCE_TYPE_LABELS.get(evidence.get('type'), evidence.get('type')))}</footer>"
            "</article>"
        )
    return "".join(cards)


def paper_information(paper):
    rows = []
    for key, value in paper.items():
        if isinstance(value, bool):
            rendered = "是" if value else "否"
        elif isinstance(value, list):
            rendered = "、".join(str(item) for item in value)
        else:
            rendered = str(value)
        rows.append(
            f"<div class='paper-item'><dt>{esc(PAPER_LABELS.get(key, key))}</dt>"
            f"<dd>{esc(rendered)}</dd></div>"
        )
    return "".join(rows)


def main(source_text: str, output_text: str) -> None:
    source = Path(source_text)
    data = json.loads(source.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    ledger = data.get("evidence_ledger", [])
    paper = data.get("paper", {})
    analysis = data.get("article_analysis", {})
    table_html = data_table(samples, analysis)
    compound_count = len({raw(item.get("identity", {}).get("compound"), "") for item in samples})
    review_items = data.get("manual_review", [])
    review_html = "".join(f"<li>{esc(item)}</li>" for item in review_items) or "<li>未列出需人工复核项目</li>"
    title = paper.get("title") or "纯有机长寿命发光证据化抽取报告"
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root{{--ink:#182235;--muted:#64748b;--line:#dce3ec;--soft:#f5f7fa;--blue:#2357a5;--blue-soft:#edf4ff;--green:#18794e;--green-soft:#e9f7ef;--amber:#9a6700;--amber-soft:#fff4d6;--red:#b42318;--red-soft:#fff0ee}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:#f3f6f9;color:var(--ink);font:14px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif}}
a{{color:var(--blue)}}
.page{{width:min(1440px,calc(100% - 32px));margin:24px auto 56px}}
.hero{{background:#fff;border:1px solid var(--line);border-top:5px solid var(--blue);border-radius:12px;padding:28px 30px;box-shadow:0 8px 24px rgba(24,34,53,.06)}}
.eyebrow{{margin:0 0 6px;color:var(--blue);font-weight:700;letter-spacing:.08em}}
h1{{max-width:1100px;margin:0;font-size:clamp(25px,3vw,38px);line-height:1.25}}
.hero-meta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}}
.hero-meta span,.row-chip{{border:1px solid #cad8ec;background:var(--blue-soft);color:#234a82;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:650}}
.summary{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:18px 0}}
.summary-card{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px}}
.summary-card strong{{display:block;font-size:26px;line-height:1.1;color:var(--blue)}}
.summary-card span{{color:var(--muted)}}
.section{{margin-top:22px}}
.section-title{{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:10px}}
.section-title h2{{margin:0;font-size:22px}}
.section-title p{{margin:0;color:var(--muted)}}
.paper-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 24px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 20px}}
.paper-item{{display:grid;grid-template-columns:125px 1fr;gap:12px;padding:10px 0;border-bottom:1px solid #edf0f4}}
.paper-item dt{{font-weight:700;color:#475569}}.paper-item dd{{margin:0}}
.innovation{{background:#fff;border:1px solid var(--line);border-left:5px solid var(--blue);border-radius:10px;padding:16px 20px;margin-bottom:12px}}
.innovation>b{{color:var(--blue);font-size:13px}}.innovation p{{margin:5px 0 0;font-size:16px;font-weight:650}}
.koi-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:0}}
.koi-item{{background:#fff;padding:13px 16px}}.koi-item dt{{color:#526070;font-weight:750;font-size:12px}}.koi-item dd{{margin:3px 0 0}}
.logic-chain{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;list-style:none;padding:0;margin:12px 0 0}}
.logic-chain li{{display:flex;gap:10px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:12px}}
.logic-chain li>span{{display:grid;place-items:center;flex:0 0 25px;height:25px;border-radius:50%;background:var(--blue);color:#fff;font-weight:750}}
.logic-chain b{{font-size:13px}}.logic-chain p{{margin:3px 0 0;color:#435168;font-size:12px}}
.analysis-missing{{background:#fff;border:1px dashed var(--line);padding:16px;color:var(--muted)}}
.data-table-wrap{{overflow:auto;background:#fff;border:1px solid #bdc8d6;border-radius:8px;box-shadow:0 4px 14px rgba(24,34,53,.035)}}
.data-table{{border-collapse:separate;border-spacing:0;min-width:1680px;width:100%;font-size:12px;line-height:1.45}}
.data-table th,.data-table td{{padding:10px 9px;border-right:1px solid #d6dee8;border-bottom:1px solid #d6dee8;text-align:center;vertical-align:middle;min-width:88px;max-width:230px;overflow-wrap:anywhere}}
.data-table thead th{{position:sticky;top:0;z-index:3;background:#edf3fa;color:#233a57;font-weight:800;white-space:nowrap}}
.data-table tr:last-child>*{{border-bottom:0}}.data-table tr>*:last-child{{border-right:0}}
.data-table tbody tr:nth-child(even) td,.data-table tbody tr:nth-child(even) th{{background:#fafbfd}}
.data-table tbody tr:hover td,.data-table tbody tr:hover th{{background:#f1f7ff}}
.data-table .compound-cell{{position:sticky;left:0;z-index:2;min-width:130px;background:#fff;font-size:14px;font-weight:800;color:#172b4d}}
.data-table thead th:first-child{{left:0;z-index:5}}
.paper-note-row td,.innovation-row td{{text-align:left;padding:13px 16px;white-space:normal;max-width:none;background:#fff}}
.paper-note-row td{{color:#334155}}.paper-note-row b{{color:#172b4d}}
.innovation-row td{{border-top:2px solid #9fb2c8;background:#fbfcfe;font-size:13px}}.innovation-row b{{color:var(--blue)}}
.condition-line{{display:block;margin-top:4px;color:#526070}}.table-empty{{color:#a4adba}}
.stacked-entry{{padding:7px 0;border-bottom:1px dashed #d8e0ea}}.stacked-entry:first-child{{padding-top:0}}.stacked-entry:last-child{{padding-bottom:0;border-bottom:0}}
.condition-tag{{display:inline-block;margin-bottom:4px;padding:2px 6px;border-radius:999px;background:#e9f1fb;color:#2c5687;font-size:10px;font-weight:800;white-space:nowrap}}
.record-chip{{display:block;margin:3px auto;padding:2px 5px;border-radius:4px;background:#edf4ff;width:max-content}}
.evidence-link{{font-size:10px;text-decoration:none;font-weight:700;white-space:nowrap}}
.sample-note{{margin:0;padding:10px 14px;border-top:1px solid #edf0f4;background:#fffdf7;color:#675c3c;font-size:12px}}
.status{{display:inline-block;border-radius:4px;padding:1px 5px;font-size:11px;font-weight:650}}.not_reported,.muted{{background:#eef1f4;color:#687385}}.uncertain{{background:var(--amber-soft);color:var(--amber)}}
details.ledger{{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
details.ledger>summary{{cursor:pointer;list-style:none;padding:15px 18px;font-weight:750;font-size:16px;background:#fbfcfe}}
details.ledger>summary::-webkit-details-marker{{display:none}}
.evidence-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px;padding:14px;border-top:1px solid var(--line)}}
.evidence-card{{border:1px solid var(--line);border-radius:8px;padding:13px;background:#fff;scroll-margin-top:20px}}
.evidence-card:target{{outline:3px solid #9dc1ff;background:#f7fbff}}
.evidence-card header{{display:flex;justify-content:space-between;align-items:center;gap:10px}}
.evidence-id{{font:750 12px/1 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--blue)}}
.evidence-row{{margin-left:7px;color:var(--muted);font-size:11px}}
.confidence{{border-radius:999px;padding:2px 8px;font-size:11px;font-weight:750}}.confidence.high{{background:var(--green-soft);color:var(--green)}}.confidence.medium{{background:var(--amber-soft);color:var(--amber)}}.confidence.low{{background:var(--red-soft);color:var(--red)}}
.evidence-card h4{{margin:9px 0 5px;font-size:15px}}.evidence-card p{{margin:4px 0}}
.location{{color:#435168}}blockquote{{margin:9px 0 6px;padding:9px 11px;border-left:3px solid #84a9df;background:#f6f9fd;color:#334155}}
blockquote span{{display:block;margin-bottom:2px;color:var(--blue);font-size:11px;font-weight:750}}
.evidence-note{{color:#725e28;background:#fff9e9;padding:7px 9px;border-radius:5px}}
.evidence-card footer{{margin-top:8px;color:var(--muted);font:11px ui-monospace,SFMono-Regular,Consolas,monospace}}
.review{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--amber);border-radius:9px;padding:13px 18px}}
.review li{{margin:6px 0}}
.empty{{color:var(--muted)}}
sub{{font-size:.72em;line-height:0}}
@media(max-width:820px){{.page{{width:min(100% - 18px,1440px)}}.summary{{grid-template-columns:repeat(2,1fr)}}.paper-grid,.koi-grid{{grid-template-columns:1fr}}}}
@media print{{body{{background:#fff}}.page{{width:100%;margin:0}}.hero,.summary-card{{box-shadow:none}}details.ledger{{break-before:page}}}}
</style>
</head>
<body>
<main class="page">
  <header class="hero">
    <p class="eyebrow">PURE-ORGANIC LONG-LIVED EMISSION · EVIDENCE REPORT</p>
    <h1>{esc(title)}</h1>
    <div class="hero-meta"><span>{esc(paper.get('doi', 'DOI 未报告'))}</span><span>{esc(paper.get('journal_year', '期刊信息未报告'))}</span><span>数据源：冻结 JSON</span></div>
  </header>
  <section class="summary" aria-label="抽取总览">
    <div class="summary-card"><strong>{compound_count}</strong><span>种化合物</span></div>
    <div class="summary-card"><strong>{len(samples)}</strong><span>组独立测量条件</span></div>
    <div class="summary-card"><strong>{len(ledger)}</strong><span>条可追溯证据</span></div>
    <div class="summary-card"><strong>{len(review_items)}</strong><span>项人工复核提醒</span></div>
  </section>
  <section class="section">
    <div class="section-title"><h2>论文基本信息</h2><p>主文与 Supporting Information 覆盖状态</p></div>
    <dl class="paper-grid">{paper_information(paper)}</dl>
  </section>
  <section class="section">
    <div class="section-title"><h2>主数据表</h2><p>每种化合物一行；主表优先显示室温核心数据，全部条件仍保留在 JSON 与证据台账</p></div>
    {table_html}
  </section>
  <section class="section">
    <div class="section-title"><h2>证据台账</h2><p>点击参数后的证据编号可跳转至对应原文短引</p></div>
    <details class="ledger" open><summary>展开 / 收起全部证据（{len(ledger)} 条）</summary><div class="evidence-grid">{evidence_cards(ledger)}</div></details>
  </section>
  <section class="section">
    <div class="section-title"><h2>需人工复核</h2><p>冲突、定义差异与 SI-only 数据</p></div>
    <div class="review"><ul>{review_html}</ul></div>
  </section>
</main>
</body>
</html>"""
    Path(output_text).write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render_html.py paper_data.json report.html")
    main(sys.argv[1], sys.argv[2])
