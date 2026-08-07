#!/usr/bin/env python3
"""Render a focused, auditable long-lived-emission report from canonical JSON."""
import html
import json
import re
import sys
from collections import OrderedDict
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


def compound_sections(samples):
    grouped = OrderedDict()
    for sample in samples:
        compound = raw(sample.get("identity", {}).get("compound"), "未命名化合物")
        grouped.setdefault(compound, []).append(sample)
    sections = []
    for compound, records in grouped.items():
        hosts = []
        ratios = []
        for record in records:
            host = raw(record.get("identity", {}).get("host_matrix"), "")
            ratio = raw(record.get("identity", {}).get("doping_ratio"), "")
            if host and host not in hosts:
                hosts.append(host)
            if ratio and ratio not in ratios:
                ratios.append(ratio)
        row_ids = " ".join(f"<span class='row-chip'>{esc(item.get('row_id'))}</span>" for item in records)
        meta = " · ".join(part for part in (" / ".join(hosts), " / ".join(ratios)) if part)
        sections.append(
            "<section class='compound-card'>"
            "<header class='compound-head'>"
            f"<div><h3>{esc(compound)}</h3><p>{esc(meta)}</p></div>"
            f"<div class='row-chips'>{row_ids}</div>"
            "</header>"
            f"<div class='condition-grid'>{''.join(sample_panel(item) for item in records)}</div>"
            "</section>"
        )
    return "".join(sections), len(grouped)


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
    compounds_html, compound_count = compound_sections(samples)
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
.compound-card{{background:#fff;border:1px solid var(--line);border-radius:12px;margin-bottom:16px;overflow:hidden;box-shadow:0 4px 14px rgba(24,34,53,.035)}}
.compound-head{{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:17px 20px;border-bottom:1px solid var(--line);background:#fbfcfe}}
.compound-head h3{{margin:0;font-size:21px}}.compound-head p{{margin:2px 0 0;color:var(--muted)}}
.row-chips{{display:flex;flex-wrap:wrap;gap:5px;justify-content:flex-end}}
.condition-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px;padding:16px}}
.condition-card{{border:1px solid var(--line);border-radius:9px;overflow:hidden;background:#fff}}
.condition-head{{padding:12px 14px;background:var(--soft);border-bottom:1px solid var(--line)}}
.condition-head h4{{display:inline;margin:0 0 0 7px;font-size:16px}}.condition-head p{{margin:2px 0 0;color:var(--muted)}}
.row-id{{display:inline-block;color:var(--blue);font:700 11px/1.2 ui-monospace,SFMono-Regular,Consolas,monospace}}
.condition-details{{display:flex;flex-wrap:wrap;gap:7px 14px;padding:11px 14px;border-bottom:1px solid #edf0f4;color:#475569;font-size:12px}}
.metric-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;padding:12px}}
.metric{{min-width:0;border:1px solid #e2e8f0;border-radius:7px;padding:9px 10px;background:#fff}}
.metric-label{{color:#526070;font-weight:700;font-size:12px}}
.metric-value{{margin-top:2px;font-size:14px;font-weight:650;overflow-wrap:anywhere}}
.metric-context{{margin-top:5px;color:var(--muted);font-size:11px;line-height:1.4}}
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
@media(max-width:820px){{.page{{width:min(100% - 18px,1440px)}}.summary{{grid-template-columns:repeat(2,1fr)}}.paper-grid{{grid-template-columns:1fr}}.compound-head{{align-items:flex-start;flex-direction:column}}.row-chips{{justify-content:flex-start}}.metric-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media print{{body{{background:#fff}}.page{{width:100%;margin:0}}.hero,.compound-card,.summary-card{{box-shadow:none}}details.ledger{{break-before:page}}}}
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
    <div class="section-title"><h2>主数据表</h2><p>按化合物归组；不同温度、气氛与发光机制保留为独立条件</p></div>
    {compounds_html}
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
