#!/usr/bin/env python3
"""Render an auditable RTP extraction report from canonical JSON."""
import html
import json
import sys
from pathlib import Path


def esc(value):
    return html.escape("" if value is None else str(value))


def displayed(field):
    status = field.get("status", "uncertain")
    if status != "reported":
        return f"<mark class='{esc(status)}'>{esc('未报告' if status == 'not_reported' else '无法确认')}</mark>"
    raw = esc(field.get("raw_value"))
    unit = esc(field.get("raw_unit"))
    return f"{raw} {unit} <a href='#{esc(field.get('evidence_id'))}'>[{esc(field.get('evidence_id'))}]</a>"


def main(source_text: str, output_text: str) -> None:
    source = Path(source_text)
    data = json.loads(source.read_text(encoding="utf-8"))
    columns = ["afterglow_color", "afterglow_visible_time", "phi_pl", "lambda_f", "tau_f", "phi_f", "lambda_df", "tau_df", "phi_df", "lambda_p", "tau_p", "phi_p", "k_isc", "k_risc", "k_rp", "knr_p"]
    headers = ["余辉颜色", "余辉时间", "ΦPL", "λF", "τF", "ΦF", "λDF", "τDF", "ΦDF", "λP", "τP", "ΦP", "kISC", "kRISC", "kP/krP", "knr,P"]
    rows = []
    for sample in data.get("samples", []):
        identity, conditions, fields = sample.get("identity", {}), sample.get("conditions", {}), sample.get("fields", {})
        fixed = [identity.get("compound"), identity.get("host_matrix"), identity.get("doping_ratio"), identity.get("sample_state"), conditions.get("atmosphere"), conditions.get("temperature"), conditions.get("excitation"), conditions.get("delay"), conditions.get("gate_window")]
        cells = [f"<td>{esc(sample.get('row_id') or '未报告')}</td>"] + [f"<td>{displayed(x if isinstance(x, dict) else {'status':'not_reported'})}</td>" for x in fixed] + [f"<td>{displayed(fields.get(c, {'status':'not_reported'}))}</td>" for c in columns]
        rows.append("<tr>" + "".join(cells) + "</tr>")
    evidence_rows = []
    for e in data.get("evidence_ledger", []):
        values = [e.get(k) for k in ("evidence_id", "row_id", "field_name", "extracted_value", "location", "quote", "type", "confidence", "manual_check_note")]
        evidence_rows.append("<tr id='"+esc(e.get("evidence_id"))+"'>"+"".join(f"<td>{esc(v)}</td>" for v in values)+"</tr>")
    paper = data.get("paper", {})
    review = "".join(f"<li>{esc(x)}</li>" for x in data.get("manual_review", [])) or "<li>未列出</li>"
    json_blob = html.escape(source.read_text(encoding="utf-8"))
    doc = """<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'><title>RTP 证据化抽取报告</title><style>body{font:14px system-ui;margin:2rem;color:#172033}h1,h2{margin-top:1.7rem}.wrap{overflow-x:auto;border:1px solid #d8dee9}table{border-collapse:collapse;min-width:1400px;width:100%}th,td{border:1px solid #d8dee9;padding:.5rem;text-align:left;vertical-align:top}th{background:#f6f8fa;white-space:nowrap}.high{color:#166534}.medium{color:#9a6700}.low{color:#b42318}mark{padding:.1rem .35rem;border-radius:.2rem}.not_reported{background:#e5e7eb}.uncertain{background:#fef3c7}pre{white-space:pre-wrap;background:#f6f8fa;padding:1rem}details{margin-top:1rem}</style></head><body><h1>RTP 证据化抽取报告</h1><h2>论文基本信息</h2><dl>"""+"".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k,v in paper.items())+"""</dl><h2>主数据表</h2><div class='wrap'><table><thead><tr><th>Row ID</th><th>Compound</th><th>Host/Matrix</th><th>掺杂比例</th><th>样品状态</th><th>气氛</th><th>温度</th><th>激发</th><th>延迟</th><th>门控</th>"""+"".join(f"<th>{h}</th>" for h in headers)+"""</tr></thead><tbody>"""+"".join(rows)+"""</tbody></table></div><details><summary>Evidence Ledger（证据台账）</summary><div class='wrap'><table><thead><tr><th>ID</th><th>Row</th><th>字段</th><th>值</th><th>位置</th><th>原文</th><th>类型</th><th>置信度</th><th>人工复核</th></tr></thead><tbody>"""+"".join(evidence_rows)+"""</tbody></table></div></details><h2>需人工复核</h2><ul>"""+review+"""</ul><h2>速率常数计算</h2><pre><code>"""+esc(json.dumps(data.get("rate_calculations", []), ensure_ascii=False, indent=2))+"""</code></pre><h2>JSON</h2><pre><code>"""+json_blob+"""</code></pre></body></html>"""
    Path(output_text).write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render_html.py paper_data.json report.html")
    main(sys.argv[1], sys.argv[2])
