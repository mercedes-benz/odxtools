#!/usr/bin/env python
# SPDX-License-Identifier: MIT
"""
HTML report exporter for ODX diagnostic comparison.

This module provides HTML report generation with:
- Collapsible sections for each layer
- Color-coded change severity
- Search/filter functionality
- Summary statistics cards
- Responsive design for desktop and mobile

No external dependencies — pure HTML/CSS/JS.
"""

from pathlib import Path
from typing import Optional

from .compare import SpecsChangesVariants, Exporter


class HtmlExporter(Exporter):
    """
    Export comparison results to an HTML report.

    The HTML report provides an interactive, visually rich view of
    diagnostic changes, suitable for sharing with management teams
    or archiving for compliance purposes.

    Features:
        - Collapsible layers with severity color-coding
        - Live search/filter input
        - Summary statistics cards
        - Mobile-responsive design
        - No external dependencies
        - Print-friendly
    """

    def export(self, data: SpecsChangesVariants, target: Optional[Path]) -> Path:
        """Export comparison data to an HTML file."""
        destination = target or Path.cwd() / "compare-report.html"
        html = self._render(data)
        with open(destination, "w", encoding="utf-8") as f:
            f.write(html)
        return destination

    def _render(self, data: SpecsChangesVariants) -> str:
        """Render complete HTML report."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ODX Comparison Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f0f2f5;
            padding: 20px;
            color: #1a1a2e;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px 40px;
            border-radius: 12px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }}
        .header h1 {{ font-size: 28px; font-weight: 700; }}
        .header .subtitle {{ color: #aab; font-size: 14px; margin-top: 5px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        .summary-card {{
            background: white;
            padding: 18px 22px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 4px solid #1a1a2e;
        }}
        .summary-card .label {{ font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
        .summary-card .value {{ font-size: 28px; font-weight: 700; color: #1a1a2e; margin-top: 4px; }}
        .summary-card.critical {{ border-left-color: #e74c3c; }}
        .summary-card.high {{ border-left-color: #e67e22; }}
        .summary-card.medium {{ border-left-color: #f1c40f; }}
        .summary-card.low {{ border-left-color: #2ecc71; }}
        .search-box {{
            margin-bottom: 20px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .search-box input {{
            flex: 1;
            min-width: 250px;
            padding: 12px 18px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.2s;
        }}
        .search-box input:focus {{
            outline: none;
            border-color: #1a1a2e;
        }}
        .stats-bar {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            padding: 12px 0;
        }}
        .stats-bar .stat {{
            font-size: 14px;
            color: #555;
        }}
        .stats-bar .stat strong {{ color: #1a1a2e; }}
        .layer {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 12px;
            overflow: hidden;
        }}
        .layer summary {{
            padding: 18px 24px;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.15s;
            user-select: none;
        }}
        .layer summary:hover {{ background: #f8f9fa; }}
        .layer summary .badge {{
            font-size: 12px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 20px;
            background: #e9ecef;
            color: #495057;
        }}
        .layer details {{
            padding: 0 24px 24px 24px;
        }}
        .layer table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .layer th {{
            text-align: left;
            padding: 10px 12px;
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #e9ecef;
        }}
        .layer td {{
            padding: 9px 12px;
            border-bottom: 1px solid #f1f3f5;
            vertical-align: top;
        }}
        .layer tr:hover td {{ background: #f8f9fa; }}
        .layer .severity-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .severity-critical {{ background: #e74c3c; color: white; }}
        .severity-high {{ background: #e67e22; color: white; }}
        .severity-medium {{ background: #f1c40f; color: #1a1a2e; }}
        .severity-low {{ background: #2ecc71; color: white; }}
        .severity-info {{ background: #95a5a6; color: white; }}
        code {{
            background: #f1f3f5;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 13px;
            font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
            word-break: break-all;
        }}
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }}
        .empty-state h3 {{ font-size: 20px; color: #333; margin-bottom: 8px; }}
        @media (max-width: 768px) {{
            .header {{ padding: 20px; flex-direction: column; text-align: center; }}
            .header h1 {{ font-size: 22px; }}
            .summary {{ grid-template-columns: repeat(2, 1fr); }}
            .layer summary {{ font-size: 14px; padding: 14px 18px; flex-wrap: wrap; }}
            .layer details {{ padding: 0 16px 16px 16px; }}
            .layer table {{ font-size: 12px; }}
            .layer th, .layer td {{ padding: 6px 8px; }}
        }}
        @media print {{
            body {{ background: white; padding: 10px; }}
            .header {{ background: #1a1a2e; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .summary-card {{ box-shadow: none; border: 1px solid #ddd; }}
            .layer {{ box-shadow: none; border: 1px solid #ddd; }}
            .search-box input {{ display: none; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1>ODX Comparison Report</h1>
            <div class="subtitle">Generated by odxtools</div>
        </div>
        <div style="font-size:13px; color:#aab;">
            <div>Total Change Score: <strong style="color:white;">{data.summary.get('total_change_score', 0)}</strong></div>
        </div>
    </div>

    <!-- Summary Cards -->
    <div class="summary">
        <div class="summary-card"><div class="label">New Layers</div><div class="value">{len(data.new_diagnostic_layers)}</div></div>
        <div class="summary-card critical"><div class="label">Deleted Layers</div><div class="value">{len(data.deleted_diagnostic_layers)}</div></div>
        <div class="summary-card high"><div class="label">Changed Layers</div><div class="value">{len(data.changed_diagnostic_layers)}</div></div>
        <div class="summary-card"><div class="label">New Services</div><div class="value">{data.summary.get('new_services', 0)}</div></div>
        <div class="summary-card critical"><div class="label">Deleted Services</div><div class="value">{data.summary.get('deleted_services', 0)}</div></div>
        <div class="summary-card medium"><div class="label">Renamed Services</div><div class="value">{data.summary.get('renamed_services', 0)}</div></div>
    </div>

    <!-- Search -->
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="Filter changes (layer, service, attribute, value...)" oninput="filterTable()">
        <span class="stats-bar">
            <span class="stat"><strong id="visibleCount">0</strong> items visible</span>
        </span>
    </div>

    <!-- Layers -->
    <div id="layerContainer">
        {self._render_layers(data)}
    </div>

    <div style="text-align:center; padding:30px 0 10px; font-size:13px; color:#aaa;">
        Report generated by odxtools
    </div>
</div>

<script>
function filterTable() {{
    const query = document.getElementById('searchInput').value.toLowerCase();
    const layers = document.querySelectorAll('.layer');
    let visible = 0;
    layers.forEach(layer => {{
        const text = layer.textContent.toLowerCase();
        const match = text.includes(query);
        layer.style.display = match ? '' : 'none';
        if (match) visible++;
    }});
    document.getElementById('visibleCount').textContent = visible;
}}
document.addEventListener('DOMContentLoaded', () => {{
    const layers = document.querySelectorAll('.layer');
    document.getElementById('visibleCount').textContent = layers.length;
}});
</script>
</body>
</html>"""

    def _render_layers(self, data: SpecsChangesVariants) -> str:
        """Render all changed layers."""
        if not data.changed_diagnostic_layers:
            return '<div class="empty-state"><h3>No changes detected</h3><p>All diagnostic layers are identical.</p></div>'

        html = ""
        for layer in data.changed_diagnostic_layers:
            html += f"""
    <details class="layer" open>
        <summary>
            <span>{layer.diag_layer}</span>
            <span class="badge">Score: {layer.change_score} - {layer.diag_layer_type}</span>
        </summary>
        <details>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Attribute</th>
                        <th>Old Value</th>
                        <th>New Value</th>
                        <th>Severity</th>
                    </tr>
                </thead>
                <tbody>"""

            # New Services
            for service in layer.new_services:
                html += f"""
                    <tr>
                        <td><strong>{service.short_name}</strong></td>
                        <td colspan="3"><span style="color:#2ecc71;">New service</span></td>
                        <td><span class="severity-badge severity-low">LOW</span></td>
                    </tr>"""

            # Deleted Services
            for service in layer.deleted_services:
                html += f"""
                    <tr>
                        <td><strong>{service.short_name}</strong></td>
                        <td colspan="3"><span style="color:#e74c3c;">Deleted service</span></td>
                        <td><span class="severity-badge severity-critical">CRITICAL</span></td>
                    </tr>"""

            # Renamed Services
            for renamed in layer.renamed_services:
                html += f"""
                    <tr>
                        <td><strong>{renamed.new_service_name}</strong></td>
                        <td colspan="3"><span style="color:#e67e22;">Renamed from <code>{renamed.old_service_name}</code></span></td>
                        <td><span class="severity-badge severity-medium">MEDIUM</span></td>
                    </tr>"""

            # Parameter Changes
            for service_change in layer.services_with_parameter_changes:
                for param_change in service_change.changed_parameters_of_service:
                    for attr in param_change.changed_attributes:
                        old_val = str(attr.old_value) if attr.old_value is not None else '&lt;undefined&gt;'
                        new_val = str(attr.new_value) if attr.new_value is not None else '&lt;undefined&gt;'
                        severity = getattr(attr, 'severity', None)
                        severity_name = severity.name if severity else 'INFO'
                        severity_class = f"severity-{severity_name.lower()}"
                        html += f"""
                    <tr>
                        <td><strong>{service_change.service.short_name}</strong></td>
                        <td>{attr.attribute}</td>
                        <td><code>{old_val}</code></td>
                        <td><code>{new_val}</code></td>
                        <td><span class="severity-badge {severity_class}">{severity_name}</span></td>
                    </tr>"""

            html += """
                </tbody>
            </table>
        </details>
    </details>"""
        return html