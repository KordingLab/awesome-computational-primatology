#!/usr/bin/env python3
"""
Generate enhanced HTML website from README.md table
"""
import pandas as pd
import re
import os

def to_link_if_markdown(cell_text: str) -> str:
    """Convert markdown links [text](url) to HTML <a> tags"""
    if not isinstance(cell_text, str):
        return str(cell_text)
    cell_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', cell_text)
    return cell_text.strip()

def extract_table_from_readme(readme_path: str) -> pd.DataFrame:
    """Extract the 7-column paper/dataset rows from README.md.

    Captures rows under "### Projects" plus the cross-species
    "#### Dataset ..." sub-table (same 7-column schema). Every sub-table's
    header and separator row is skipped explicitly, so no markdown scaffolding
    leaks in as a fake paper. The 4-column "Reviews & Related" table is
    naturally excluded by the column-count filter.

    Args:
        readme_path: Path to README.md.

    Returns:
        DataFrame of paper/dataset rows with markdown links converted to HTML.

    Raises:
        ValueError: If no valid table is found.
    """
    with open(readme_path, "r", encoding='utf-8') as f:
        lines = f.readlines()

    header: list[str] | None = None
    data: list[list[str]] = []
    in_projects_section = False

    for line in lines:
        if line.strip() == "### Projects":
            in_projects_section = True
            continue
        if not in_projects_section:
            continue
        # Only 7-column rows (8 pipe characters) are paper/dataset rows.
        if line.count("|") != 8:
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        # Skip separator rows like |---|---|...
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        # Skip (repeated) header rows; keep the first as the column names.
        if cells[0] == "Year":
            if header is None:
                header = cells
            continue
        data.append(cells)

    if header is None or not data:
        raise ValueError("Could not find valid table in README.md")

    df = pd.DataFrame(data, columns=header)
    # Apply markdown -> HTML conversion. (applymap was removed in pandas 3.0;
    # apply + Series.map works across all pandas versions.)
    df = df.apply(lambda col: col.map(to_link_if_markdown))

    return df

def get_enhanced_html_template() -> str:
    """Return the enhanced HTML template"""
    return '''<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Awesome Computational Primatology</title>
        
        <!-- External Libraries -->
        <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
        <link rel="stylesheet" href="https://cdn.datatables.net/2.0.2/css/dataTables.dataTables.css" />
        <link rel="stylesheet" href="https://cdn.datatables.net/buttons/3.0.0/css/buttons.dataTables.css" />

        <script src="https://cdn.datatables.net/2.0.2/js/dataTables.js"></script>
        <script src="https://cdn.datatables.net/buttons/3.0.0/js/dataTables.buttons.js"></script>
        <script src="https://cdn.datatables.net/buttons/3.0.0/js/buttons.html5.min.js"></script>
        
        <!-- Icons -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        
        <!-- Google Fonts -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

        <style>
            :root {
                /* Base palette */
                --primary-color: #1e3a5f;
                --secondary-color: #2563eb;
                --accent-color: #dc2626;
                --success-color: #16a34a;
                --warning-color: #ca8a04;
                --background-color: #fafbfc;
                --card-background: #ffffff;
                --text-color: #1e293b;
                --border-color: #e2e8f0;

                /* Elevation system */
                --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04);
                --shadow-md: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
                --shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.08);

                /* Neutral text */
                --muted-color: #64748b;
                --subtle-bg: #f8fafc;

                /* Topic colors */
                --topic-pd: #ef4444;
                --topic-bpe: #f97316;
                --topic-fd: #eab308;
                --topic-fle: #84cc16;
                --topic-fr: #22c55e;
                --topic-fac: #14b8a6;
                --topic-hd: #06b6d4;
                --topic-hpe: #0ea5e9;
                --topic-br: #6366f1;
                --topic-am: #8b5cf6;
                --topic-si: #a855f7;
                --topic-rl: #d946ef;
                --topic-av: #ec4899;
                --topic-o: #6b7280;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: var(--background-color);
                margin: 0;
                padding: 0;
                color: var(--text-color);
                line-height: 1.6;
                -webkit-font-smoothing: antialiased;
            }

            /* Top header bar */
            .topbar {
                background: var(--card-background);
                border-bottom: 1px solid var(--border-color);
                padding: 14px 28px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .topbar-brand {
                font-size: 1.05rem;
                font-weight: 600;
                color: var(--primary-color);
                text-decoration: none;
                letter-spacing: -0.01em;
            }
            .topbar-brand:hover { color: var(--secondary-color); }
            .topbar-actions {
                display: flex;
                align-items: center;
                gap: 18px;
            }
            .topbar-actions a {
                color: var(--muted-color);
                font-size: 1.35rem;
                text-decoration: none;
                line-height: 1;
                transition: color 0.15s ease;
            }
            .topbar-actions a:hover {
                color: var(--primary-color);
            }

            .container {
                max-width: 1280px;
                margin: 28px auto;
                background: var(--card-background);
                padding: 32px;
                border-radius: 8px;
                box-shadow: var(--shadow-sm);
            }

            .header {
                text-align: center;
                margin-bottom: 28px;
            }

            h1 {
                color: var(--primary-color);
                font-size: 2.25rem;
                margin: 0 0 8px 0;
                font-weight: 700;
                letter-spacing: -0.02em;
            }

            .subtitle {
                color: var(--muted-color);
                font-size: 1.05rem;
                margin: 0 0 18px 0;
            }

            .stat-strip {
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                color: var(--muted-color);
                font-size: 0.95rem;
            }
            .stat-strip span { white-space: nowrap; }
            .stat-strip span + span::before {
                content: "·";
                margin: 0 14px;
                color: #cbd5e1;
            }
            .stat-strip strong {
                color: var(--primary-color);
                font-weight: 600;
            }
            
            .legend {
                background: var(--subtle-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                margin-bottom: 24px;
            }

            .legend > summary {
                padding: 12px 16px;
                cursor: pointer;
                font-weight: 600;
                color: var(--primary-color);
                list-style: none;
                user-select: none;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .legend > summary::-webkit-details-marker { display: none; }
            .legend > summary::before {
                content: "";
                display: inline-block;
                width: 0;
                height: 0;
                border-left: 5px solid var(--muted-color);
                border-top: 4px solid transparent;
                border-bottom: 4px solid transparent;
                transition: transform 0.15s ease;
            }
            .legend[open] > summary::before {
                transform: rotate(90deg);
            }
            .legend > summary:hover { color: var(--secondary-color); }

            .legend-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                padding: 0 16px 16px;
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .legend-badge {
                background: var(--secondary-color);
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: bold;
                min-width: 35px;
                text-align: center;
            }
            
            .table-container {
                background: white;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                overflow: hidden;
            }

            table.dataTable {
                border-collapse: separate;
                border-spacing: 0;
                width: 100% !important;
                margin: 0 !important;
            }

            table.dataTable thead th {
                background: var(--primary-color);
                color: white;
                padding: 13px 12px;
                font-weight: 600;
                font-size: 0.9rem;
                letter-spacing: 0.01em;
                text-align: left;
                border: none;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            
            table.dataTable tbody td {
                padding: 12px 10px;
                border-bottom: 1px solid #eee;
                vertical-align: middle;
            }

            /* Zebra striping */
            table.dataTable tbody tr:nth-child(even) {
                background-color: #f8fafc;
            }

            table.dataTable tbody tr:nth-child(odd) {
                background-color: #ffffff;
            }

            table.dataTable tbody tr:hover {
                background-color: #e0f2fe;
                transition: background-color 0.15s ease;
            }
            
            .status-badge {
                padding: 4px 8px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                text-decoration: none !important;
                display: inline-block;
            }
            
            .status-yes {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .status-no {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .status-partial {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
            }
            
            .status-request {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            
            .topic-tag {
                background: #eef2f7;
                color: #475569;
                padding: 2px 7px;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 500;
                margin-right: 4px;
                display: inline-block;
                margin-bottom: 2px;
                border: 1px solid #e2e8f0;
            }

            .year-cell {
                font-weight: 600;
                color: var(--primary-color);
                text-align: center;
            }
            
            .species-macaque { background-color: #e8f5e8; }
            .species-chimp { background-color: #fff3e0; }
            .species-gorilla { background-color: #f3e5f5; }
            .species-marmoset { background-color: #e1f5fe; }
            .species-cross { background-color: #f9f9f9; }
            
            .dt-button {
                background: var(--secondary-color) !important;
                color: white !important;
                border: none !important;
                padding: 8px 15px !important;
                border-radius: 6px !important;
                margin-left: 8px !important;
                margin-right: 0 !important;
                font-size: 0.9rem !important;
                transition: all 0.3s ease !important;
            }

            .dt-button:hover {
                background: #1d4ed8 !important;
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            }

            /* Search + Buttons toolbar layout */
            .dt-toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
                padding: 16px 20px;
                background: #f8fafc;
                border-radius: 8px 8px 0 0;
                border-bottom: 1px solid var(--border-color);
            }
            div.dt-container .dt-search {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            div.dt-container .dt-search input {
                padding: 10px 16px;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                font-size: 0.95rem;
                min-width: 280px;
                transition: border-color 0.2s, box-shadow 0.2s;
            }
            div.dt-container .dt-search input:focus {
                outline: none;
                border-color: var(--secondary-color);
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }
            div.dt-container .dt-buttons {
                display: flex;
                align-items: center;
                gap: 0;
            }

            @media (max-width: 640px) {
                .dt-toolbar {
                    flex-direction: column;
                    align-items: stretch;
                }
                div.dt-container .dt-search input {
                    min-width: 100%;
                    width: 100%;
                }
                div.dt-container .dt-buttons {
                    justify-content: flex-end;
                }
            }
            
            /* Footer */
            .footer {
                margin-top: 32px;
                padding: 24px 20px;
                background: var(--subtle-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                text-align: center;
            }

            .footer p {
                margin: 6px 0;
                color: var(--muted-color);
                font-size: 0.92rem;
            }
            
            .footer a {
                color: var(--secondary-color);
                text-decoration: none;
                font-weight: 500;
                transition: color 0.3s ease;
            }
            
            .footer a:hover {
                color: var(--primary-color);
                text-decoration: underline;
            }
            
            .footer-note {
                font-size: 0.9rem;
                color: #888;
            }
            
            #last-updated {
                font-weight: 600;
                color: var(--secondary-color);
            }
            
            /* Accessibility - Focus states */
            a:focus,
            button:focus,
            input:focus,
            select:focus {
                outline: 2px solid var(--secondary-color);
                outline-offset: 2px;
            }

            /* Skip link for keyboard navigation */
            .skip-link {
                position: absolute;
                top: -40px;
                left: 0;
                padding: 8px 16px;
                background: var(--primary-color);
                color: white;
                z-index: 100;
                transition: top 0.2s ease;
            }
            .skip-link:focus {
                top: 0;
            }

            /* Tablets/small laptops */
            @media (max-width: 1024px) {
                .legend-grid { grid-template-columns: repeat(2, 1fr); }
            }

            /* Tablets */
            @media (max-width: 768px) {
                .container { margin: 16px; padding: 20px; }
                .topbar { padding: 12px 16px; }
                h1 { font-size: 1.85rem; }
                table.dataTable thead th,
                table.dataTable tbody td { padding: 8px 6px; font-size: 0.9rem; }
                .legend-grid { grid-template-columns: 1fr; }
                .footer { margin-top: 20px; padding: 20px 15px; }
            }

            /* Small phones */
            @media (max-width: 480px) {
                .container { margin: 12px; padding: 14px; }
                h1 { font-size: 1.5rem; }
                .subtitle { font-size: 0.95rem; }
                .stat-strip { font-size: 0.85rem; }
                .stat-strip span + span::before { margin: 0 8px; }
                table.dataTable thead th,
                table.dataTable tbody td { padding: 6px 4px; font-size: 0.8rem; }
                .topic-tag { font-size: 0.65rem; padding: 1px 4px; }
                .status-badge { font-size: 0.7rem; padding: 3px 6px; }
                .legend-badge { font-size: 0.7rem; padding: 2px 6px; }
            }
        </style>
    </head>
    <body>
        <a href="#table" class="skip-link">Skip to papers table</a>

        <header class="topbar">
            <a href="#" class="topbar-brand">Awesome Computational Primatology</a>
            <div class="topbar-actions">
                <a href="https://github.com/KordingLab/awesome-computational-primatology"
                   target="_blank" rel="noopener"
                   aria-label="View source on GitHub" title="View on GitHub">
                    <i class="fa-brands fa-github"></i>
                </a>
            </div>
        </header>

        <div class="container">
            <div class="header">
                <h1>Awesome Computational Primatology</h1>
                <p class="subtitle">A curated list of machine learning research for non-human primatology</p>

                <div class="stat-strip" aria-label="Collection statistics">
                    <span><strong id="total-papers">{total_papers}</strong> papers</span>
                    <span><strong id="years-span">{years_span}</strong> years</span>
                    <span><strong id="with-code">{with_code}</strong> with code</span>
                    <span><strong id="with-data">{with_data}</strong> with data</span>
                </div>
                <img class="growth-plot" src="https://raw.githubusercontent.com/KordingLab/awesome-computational-primatology/main/docs/assets/paper_growth_xkcd.png" alt="Computational primatology papers per year: this curated list vs. the broader 'primate + ML' literature" style="max-width: 720px; width: 100%; margin: 1.25rem auto 0; display: block;">
            </div>

            <details class="legend">
                <summary>Topic Legend</summary>
                <div class="legend-grid">
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-pd);">PD</span>
                        <span>Primate Detection</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-bpe);">BPE</span>
                        <span>Body Pose Estimation</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-fd);">FD</span>
                        <span>Face Detection</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-fle);">FLE</span>
                        <span>Facial Landmark</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-fr);">FR</span>
                        <span>Face Recognition</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-fac);">FAC</span>
                        <span>Facial Action Coding</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-hd);">HD</span>
                        <span>Hand Detection</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-hpe);">HPE</span>
                        <span>Hand Pose Estimation</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-br);">BR</span>
                        <span>Behavior Recognition</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-am);">AM</span>
                        <span>Avatar/Mesh</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-si);">SI</span>
                        <span>Species Identification</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-rl);">RL</span>
                        <span>Reinforcement Learning</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-av);">AV</span>
                        <span>Audio/Vocalization</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge" style="background: var(--topic-o);">O</span>
                        <span>Other</span>
                    </div>
                </div>
            </details>

            <div class="table-container">
                {table_html}
            </div>

            <div class="footer">
                <p>
                    Maintained by
                    <a href="https://kordinglab.com" target="_blank" rel="noopener">Kording Lab</a> ·
                    <a href="mailto:fparodi@upenn.edu">Felipe Parodi</a>
                </p>
                <p class="footer-note">
                    Found a paper we missed?
                    <a href="https://github.com/KordingLab/awesome-computational-primatology/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">Contribute on GitHub</a>
                    · Last updated <span id="last-updated"></span>
                </p>
            </div>
        </div>
        
        <script>
        $(document).ready(function() {
            var table = $('#table').DataTable({
                paging: true,
                pageLength: 25,
                lengthMenu: [10, 25, 50, 100, -1],
                searching: true,
                ordering: true,
                info: true,
                responsive: true,
                
                dom: '<"dt-toolbar"fB>rtip',
                buttons: [
                    {
                        extend: 'copy',
                        text: '<i class="fas fa-copy"></i> Copy'
                    },
                    {
                        extend: 'csv',
                        text: '<i class="fas fa-file-csv"></i> CSV'
                    },
                    {
                        text: '<i class="fas fa-times"></i> Clear',
                        action: function(e, dt, node, config) {
                            dt.search('').columns().search('').draw();
                        }
                    }
                ],
                
                columnDefs: [
                    {
                        targets: 0,
                        type: 'num',
                        className: 'year-cell',
                        width: '80px'
                    },
                    {
                        targets: 2,
                        width: '150px',
                        render: function(data, type, row) {
                            if (type === 'display') {
                                const topics = data.split(', ');
                                return topics.map(function(topic) {
                                    const t = topic.trim();
                                    return '<span class="topic-tag">' + t + '</span>';
                                }).join(' ');
                            }
                            return data;
                        }
                    },
                    {
                        targets: 3,
                        width: '120px',
                        render: function(data, type, row) {
                            if (type === 'display') {
                                let className = 'species-cross';
                                const lowerData = data.toLowerCase();
                                if (lowerData.includes('macaque')) className = 'species-macaque';
                                else if (lowerData.includes('chimp')) className = 'species-chimp';
                                else if (lowerData.includes('gorilla')) className = 'species-gorilla';
                                else if (lowerData.includes('marmoset')) className = 'species-marmoset';
                                
                                return '<span class="' + className + '" style="padding: 4px 8px; border-radius: 4px; display: inline-block;">' + data + '</span>';
                            }
                            return data;
                        }
                    },
                    {
                        targets: [4, 5],
                        width: '100px',
                        render: function(data, type, row) {
                            if (type === 'display') {
                                let className = 'status-no';
                                let icon = '<i class="fas fa-times"></i> ';
                                
                                if (data.includes('Yes')) {
                                    className = 'status-yes';
                                    icon = '<i class="fas fa-check"></i> ';
                                } else if (data.includes('Code only') || data.includes('Some')) {
                                    className = 'status-partial';
                                    icon = '<i class="fas fa-code"></i> ';
                                } else if (data.includes('Upon request')) {
                                    className = 'status-request';
                                    icon = '<i class="fas fa-envelope"></i> ';
                                }
                                
                                return '<span class="status-badge ' + className + '">' + icon + data + '</span>';
                            }
                            return data;
                        }
                    }
                ],
                
                order: [[0, 'desc']],
                
                language: {
                    search: '<i class="fas fa-search"></i>',
                    searchPlaceholder: 'Search papers...',
                    lengthMenu: 'Show _MENU_ papers per page',
                    info: 'Showing _START_ to _END_ of _TOTAL_ papers',
                    processing: '<i class="fas fa-spinner fa-spin"></i> Loading...'
                }
            });
            
            // Set last updated date
            const lastUpdated = new Date().toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            document.getElementById('last-updated').textContent = lastUpdated;
        });
        </script>
    </body>
</html>'''

def calculate_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics from the dataframe"""
    total_papers = len(df)
    
    # Count years
    years = set()
    for year in df.iloc[:, 0]:  # First column is year
        if str(year).isdigit():
            years.add(int(year))
    years_span = len(years)
    
    # Count papers with code (Model column)
    with_code = 0
    model_col = df.iloc[:, 4] if len(df.columns) > 4 else pd.Series()  # Model column
    for value in model_col:
        if isinstance(value, str) and ('Yes' in value or 'Code only' in value):
            with_code += 1
    
    # Count papers with data (Data column)  
    with_data = 0
    data_col = df.iloc[:, 5] if len(df.columns) > 5 else pd.Series()  # Data column
    for value in data_col:
        if isinstance(value, str) and 'Yes' in value:
            with_data += 1
    
    return {
        'total_papers': total_papers,
        'years_span': years_span,
        'with_code': with_code,
        'with_data': with_data
    }

def main():
    """Main function to generate the website"""
    # Determine if running in GitHub Actions or locally
    if os.path.exists("/home/runner/work"):
        # GitHub Actions
        base_path = "/home/runner/work/awesome-computational-primatology/awesome-computational-primatology"
    else:
        # Local development - go up 1 level from scripts/
        script_dir = os.path.dirname(os.path.abspath(__file__))  # scripts/
        base_path = os.path.dirname(script_dir)  # repository root
    
    readme_path = os.path.join(base_path, "README.md")
    output_path = os.path.join(base_path, "index.html")
    
    print(f"Script location: {os.path.abspath(__file__)}")
    print(f"Base path: {base_path}")
    print(f"README path: {readme_path}")
    print(f"Output path: {output_path}")
    
    try:
        # Extract table from README
        df = extract_table_from_readme(readme_path)
        print(f"Extracted table with {len(df)} rows and {len(df.columns)} columns")
        
        # Calculate statistics
        stats = calculate_stats(df)
        print(f"Statistics: {stats}")
        
        # Generate table HTML
        table_html = df.to_html(
            table_id="table",
            escape=False,
            index=False,
            classes="display"
        )
        
        # Get template and format with data
        template = get_enhanced_html_template()
        html_content = template.replace('{table_html}', table_html)
        html_content = html_content.replace('{total_papers}', str(stats['total_papers']))
        html_content = html_content.replace('{years_span}', str(stats['years_span']))
        html_content = html_content.replace('{with_code}', str(stats['with_code']))
        html_content = html_content.replace('{with_data}', str(stats['with_data']))
        
        # Write output
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Generated enhanced website: {output_path}")
        
    except Exception as e:
        print(f"❌ Error generating website: {e}")
        raise

if __name__ == "__main__":
    main()