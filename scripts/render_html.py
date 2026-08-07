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
        (r"\bphi_?pl\b", "Φ<sub>PL</sub>"),
        (r"\bphi_?df\b", "Φ<sub>DF</sub>"),
        (r"\bphi_?f\b", "Φ<sub>F</sub>"),
        (r"\bphi_?p\b", "Φ<sub>P</sub>"),
        (r"\bΦ_?PL\b", "Φ<sub>PL</sub>"),
        (r"\bΦ_?DF\b", "Φ<sub>DF</sub>"),
        (r"\bΦ_?F\b", "Φ<sub>F</sub>"),
        (r"\bΦ_?P\b", "Φ<sub>P</sub>"),
        (r"\btau_?p\b", "τ<sub>P</sub>"),
        (r"\blambda_?p\b", "λ<sub>P</sub>"),
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
    ("doping_ratio", "掺杂比例", "identity"),
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
    if lower.strip() == "fluorescence":
        return "F"
    return str(value or "—")


def short_host(value):
    text = str(value or "")
    lower = text.lower()
    if "pmma" in lower:
        return "PMMA"
    if "pva" in lower:
        return "PVA"
    if "toluene" in lower or lower.strip() == "tol":
        return "Tol"
    if "acetonitrile" in lower or lower.strip() == "acn":
        return "ACN"
    if "chloroform" in lower or lower.strip() in {"chcl3", "chcl₃"}:
        return "CHCl₃"
    if "methylcyclohexane" in lower:
        return "MeCHX"
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
                unique_numbers = list(dict.fromkeys(numbers))
                if name == "tau_df" or len(unique_numbers) > 3:
                    value = f"{min(numbers):g}–{max(numbers):g} {unit}"
                else:
                    value = "/".join(f"{number:g}" for number in unique_numbers) + f" {unit}"
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


def condition_descriptor(sample):
    identity = sample.get("identity", {})
    conditions = sample.get("conditions", {})
    host_full = raw(identity.get("host_matrix"), "未报告介质")
    host = short_host(host_full)
    ratio = raw(identity.get("doping_ratio"), "")
    state = raw(identity.get("sample_state"), "")
    temperature = raw(conditions.get("temperature"), "")
    atmosphere = raw(conditions.get("atmosphere"), "")
    excitation = raw(conditions.get("excitation"), "")
    parts = []
    if ratio:
        parts.append(ratio)
    if host:
        parts.append(host)
    if state:
        state_lower = state.lower()
        if "solution" in state_lower:
            parts.append("溶液")
        elif "film" in state_lower:
            parts.append("薄膜")
    if "pva" in host_full.lower() and "oxygen" in host_full.lower():
        parts.append("PVA 阻氧层")
    if temperature:
        parts.append(temperature)
    if atmosphere:
        parts.append(atmosphere)
    if excitation:
        parts.append("λex=" + excitation)
    return "；".join(parts) or "条件未完整报告"


def condition_marker(sample, registry, labels):
    description = condition_descriptor(sample)
    if description not in registry:
        index = len(registry)
        marker = chr(ord("a") + index) if index < 26 else f"a{index + 1}"
        registry[description] = marker
        labels.append((marker, description))
    return registry[description]


def doped_matrix_temperature(sample):
    identity = sample.get("identity", {})
    state = raw(identity.get("sample_state"), "").lower()
    host = identity.get("host_matrix")
    ratio = identity.get("doping_ratio")
    if "solution" in state or "溶液" in state:
        return ""
    if not isinstance(host, dict) or host.get("status") != "reported":
        return ""
    if not isinstance(ratio, dict) or ratio.get("status") != "reported":
        return ""
    temperature = raw(sample.get("conditions", {}).get("temperature"), "").lower()
    if temperature == "rt" or "room temperature" in temperature or "室温" in temperature:
        return "rt"
    if re.search(r"\b77\s*k\b", temperature) or "77 k" in temperature:
        return "77k"
    return ""


def comparison_value(name, field):
    rendered = html.unescape(re.sub(r"<[^>]+>", "", table_raw(name, field)))
    if name == "tau_p":
        numbers = [float(item) for item in re.findall(r"[0-9.]+", rendered)]
        units = re.findall(r"\b(ns|ms|s)\b", rendered, re.IGNORECASE)
        if not numbers or not units:
            return None
        scale = {"ns": 1e-9, "ms": 1e-3, "s": 1.0}[units[-1].lower()]
        return max(numbers) * scale
    match = re.search(r"([0-9.]+)\s*(ns|ms|s|%)?", rendered, re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    return value


def doped_maxima(samples):
    maxima = {
        "rt": {"tau_p": None, "phi_p": None},
        "77k": {"tau_p": None},
    }
    for sample in samples:
        temperature_kind = doped_matrix_temperature(sample)
        if temperature_kind not in maxima:
            continue
        for name in maxima[temperature_kind]:
            field = sample.get("fields", {}).get(name)
            if not isinstance(field, dict) or field.get("status") != "reported":
                continue
            value = comparison_value(name, field)
            current = maxima[temperature_kind][name]
            if value is not None and (current is None or value > current):
                maxima[temperature_kind][name] = value
    return maxima


def all_condition_field(records, group, name, registry, labels, maxima):
    entries = []
    seen = set()
    for sample in records:
        field = sample.get(group, {}).get(name)
        if not isinstance(field, dict) or field.get("status") != "reported":
            continue
        marker = condition_marker(sample, registry, labels)
        value = table_raw(name, field)
        key = (re.sub(r"<[^>]+>", "", value), marker)
        if key in seen:
            continue
        seen.add(key)
        temperature_kind = doped_matrix_temperature(sample)
        classes = []
        numeric_value = comparison_value(name, field)
        if name in {"lambda_p", "tau_p", "phi_p"} and temperature_kind == "rt":
            classes.append("doped-rt-phosphor")
            rt_maximum = maxima["rt"].get(name)
            if name == "tau_p" and numeric_value is not None and rt_maximum is not None and abs(numeric_value - rt_maximum) <= max(abs(rt_maximum) * 1e-9, 1e-12):
                classes.append("best-lifetime")
            elif name == "phi_p" and numeric_value is not None and rt_maximum is not None and abs(numeric_value - rt_maximum) <= max(abs(rt_maximum) * 1e-9, 1e-12):
                classes.append("best-efficiency")
        elif name in {"lambda_p", "tau_p", "phi_p"} and temperature_kind == "77k":
            classes.append("doped-77k-phosphor")
            k77_maximum = maxima["77k"].get(name)
            if name == "tau_p" and numeric_value is not None and k77_maximum is not None and abs(numeric_value - k77_maximum) <= max(abs(k77_maximum) * 1e-9, 1e-12):
                classes.append("best-77k-lifetime")
        if classes:
            value = f"<span class='{' '.join(classes)}'>{value}</span>"
        entries.append(value + evidence_link(field.get("evidence_id")) + f"<sup class='condition-ref'>[{marker}]</sup>")
    if not entries:
        return "<span class='table-empty'>—</span>"
    return "<span class='condition-values'>" + " / ".join(entries) + "</span>"


def formulation_field(records, name):
    """Render the doped/solid formulation once; solution media belong in metric footnotes."""
    entries = []
    seen = set()
    for sample in records:
        identity = sample.get("identity", {})
        sample_state = raw(identity.get("sample_state"), "").lower()
        if "solution" in sample_state or "溶液" in sample_state:
            continue
        field = identity.get(name)
        if not isinstance(field, dict) or field.get("status") != "reported":
            continue
        value = table_raw(name, field)
        key = re.sub(r"<[^>]+>", "", value)
        if key in seen:
            continue
        seen.add(key)
        entries.append(value + evidence_link(field.get("evidence_id")))
    if not entries:
        return "<span class='table-empty'>—</span>"
    return " / ".join(entries)


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
    condition_registry = {}
    condition_labels = []
    maxima = doped_maxima(samples)
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
            elif name in {"host_matrix", "doping_ratio"}:
                value = formulation_field(records, name)
            else:
                value = all_condition_field(records, group, name, condition_registry, condition_labels, maxima)
            cell_class = "compound-cell" if name == "compound" else ""
            cells.append(f"<td class='{cell_class}'>{value}</td>")
        record_ids = ", ".join(str(item.get("row_id")) for item in records)
        rows.append(f"<tr title='条件记录：{esc(record_ids)}'>{''.join(cells)}</tr>")
    innovation = analysis_text(analysis.get("one_sentence_innovation")) if isinstance(analysis, dict) else "未提供"
    colspan = len(TABLE_COLUMNS)
    footnotes = "".join(
        f"<div><sup>[{esc(marker)}]</sup> {esc(description)}</div>"
        for marker, description in condition_labels
    ) or "<div>未生成条件脚注</div>"
    return (
        "<div class='data-table-wrap'><table class='data-table'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{logic_rows(analysis, colspan)}{''.join(rows)}"
        f"<tr class='condition-footnotes'><td colspan='{colspan}'><b>条件脚注：</b>{footnotes}</td></tr>"
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


def quote_prefix(value, word_limit=10, char_limit=46):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    words = text.split(" ")
    if len(words) > 1:
        prefix = " ".join(words[:word_limit])
        return prefix + ("…" if len(words) > word_limit else "")
    return text[:char_limit] + ("…" if len(text) > char_limit else "")


def table_source_label(location):
    matches = re.findall(r"\bTables?\s+[A-Za-z]?[0-9]+(?:\s*[–-]\s*[A-Za-z]?[0-9]+)?", str(location or ""), re.IGNORECASE)
    return "、".join(dict.fromkeys(matches)) or "所列表格"


def evidence_cards(ledger):
    cards = []
    for evidence in ledger:
        evidence_id = evidence.get("evidence_id")
        note = evidence.get("manual_check_note")
        quote = evidence.get("quote")
        confidence = str(evidence.get("confidence") or "").lower()
        evidence_type = evidence.get("type")
        if confidence == "high" and evidence_type == "table_value":
            extracted_html = ""
            quote_html = f"<p class='source-cue'><b>表格证据：</b>来自 {esc(table_source_label(evidence.get('location')))}</p>"
            note_html = ""
        elif confidence == "high":
            extracted_html = ""
            prefix = quote_prefix(quote)
            quote_html = (
                f"<blockquote class='compact-quote'><span>原文开头</span>“{esc(prefix)}”</blockquote>"
                if prefix else "<blockquote class='missing-quote'>未提供原文开头</blockquote>"
            )
            note_html = ""
        else:
            extracted_html = f"<p class='extracted'><b>抽取值：</b>{scientific_value(evidence.get('extracted_value'))}</p>"
            quote_html = (
                f"<blockquote><span>原文短引</span>“{esc(quote)}”</blockquote>"
                if quote else "<blockquote class='missing-quote'>未提供原文短引</blockquote>"
            )
            review_note = note or "该证据置信度不足，请对照原文人工复核。"
            note_html = f"<p class='evidence-note'><b>需人工复核：</b>{scientific_value(review_note)}</p>"
        cards.append(
            f"<article class='evidence-card' id='{esc(evidence_id)}'>"
            "<header>"
            f"<div><span class='evidence-id'>{esc(evidence_id)}</span>"
            f"<span class='evidence-row'>{esc(evidence.get('row_id'))}</span></div>"
            f"{confidence_badge(evidence.get('confidence'))}"
            "</header>"
            f"<h4>{multi_field_label(evidence.get('field_name'))}</h4>"
            f"{extracted_html}"
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
    review_html = "".join(f"<li>{scientific_value(item)}</li>" for item in review_items) or "<li>未列出需人工复核项目</li>"
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
.condition-ref{{margin-left:2px;color:#7a4d00;font-size:9px;font-weight:800}}.condition-values{{white-space:normal}}
.doped-rt-phosphor{{color:#c5162e}}.doped-77k-phosphor{{color:#245fc7}}
.best-lifetime{{font-weight:850;text-decoration:underline;text-underline-offset:2px}}
.best-efficiency{{font-weight:850;text-decoration:underline;text-underline-offset:2px}}
.best-77k-lifetime{{font-weight:850}}
.condition-footnotes td{{text-align:left;max-width:none;padding:12px 16px;background:#fffdf7;color:#5f5335;line-height:1.55}}
.condition-footnotes div{{display:inline;margin-right:18px}}.condition-footnotes sup{{color:#7a4d00;font-weight:800}}
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
.source-cue{{color:#344d6b;background:#f1f6fb;padding:7px 9px;border-radius:5px}}.compact-quote{{padding:7px 9px}}
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
    <div class="section-title"><h2>主数据表</h2><p>每种化合物一行；RT/77 K、薄膜/溶液等条件以脚注区分</p></div>
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
