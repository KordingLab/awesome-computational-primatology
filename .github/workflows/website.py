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
    """Extract the main projects table from README.md"""
    with open(readme_path, "r", encoding='utf-8') as f:
        text = f.readlines()
    
    table = []
    in_projects_section = False
    
    for line in text:
        # Check if we're in the Projects section
        if line.strip() == "### Projects":
            in_projects_section = True
            continue
        
        # Stop if we hit another section
        if in_projects_section and line.startswith("### ") and "Projects" not in line:
            break
            
        # Extract table rows (has 8 | characters for 7 columns)
        if in_projects_section and len(re.findall(r"\|", line)) == 8:
            row = [cell.strip() for cell in line.split("|")[1:-1]]
            table.append(row)
    
    if len(table) < 2:
        raise ValueError("Could not find valid table in README.md")
    
    # First row is header, second row is separator, rest is data
    header = table[0]
    data = table[2:] if len(table) > 2 else []
    
    df = pd.DataFrame(data, columns=header)
    # Apply markdown to HTML conversion
    df = df.applymap(to_link_if_markdown)
    
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
        <link rel="stylesheet" href="https://cdn.datatables.net/searchpanes/2.3.0/css/searchPanes.dataTables.css" />
        <link rel="stylesheet" href="https://cdn.datatables.net/select/2.0.0/css/select.dataTables.css" />
        
        <script src="https://cdn.datatables.net/2.0.2/js/dataTables.js"></script>
        <script src="https://cdn.datatables.net/buttons/3.0.0/js/dataTables.buttons.js"></script>
        <script src="https://cdn.datatables.net/buttons/3.0.0/js/buttons.html5.min.js"></script>
        <script src="https://cdn.datatables.net/searchpanes/2.3.0/js/dataTables.searchPanes.js"></script>
        <script src="https://cdn.datatables.net/select/2.0.0/js/dataTables.select.js"></script>
        
        <!-- Icons -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        
        <style>
            :root {
                --primary-color: #2c3e50;
                --secondary-color: #3498db;
                --accent-color: #e74c3c;
                --success-color: #27ae60;
                --warning-color: #f39c12;
                --background-color: #f8f9fa;
                --card-background: #ffffff;
                --text-color: #2c3e50;
                --border-color: #dee2e6;
                --shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--background-color);
                margin: 0;
                padding: 20px;
                color: var(--text-color);
                line-height: 1.6;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: var(--card-background);
                padding: 30px;
                border-radius: 12px;
                box-shadow: var(--shadow);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 2px solid var(--border-color);
            }
            
            h1 {
                color: var(--primary-color);
                font-size: 2.5rem;
                margin-bottom: 10px;
                font-weight: 700;
            }
            
            .subtitle {
                color: #666;
                font-size: 1.1rem;
                margin-bottom: 20px;
            }
            
            .stats {
                display: flex;
                justify-content: center;
                gap: 30px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            
            .stat-item {
                text-align: center;
                padding: 15px;
                background: linear-gradient(135deg, var(--secondary-color), #5dade2);
                color: white;
                border-radius: 8px;
                min-width: 120px;
                box-shadow: var(--shadow);
            }
            
            .stat-number {
                font-size: 1.8rem;
                font-weight: bold;
                display: block;
            }
            
            .stat-label {
                font-size: 0.9rem;
                opacity: 0.9;
            }
            
            .legend {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                border-left: 4px solid var(--secondary-color);
            }
            
            .legend h3 {
                margin-top: 0;
                color: var(--primary-color);
            }
            
            .legend-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 15px;
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
                border-radius: 8px;
                overflow: hidden;
                box-shadow: var(--shadow);
            }
            
            table.dataTable {
                border-collapse: separate;
                border-spacing: 0;
                width: 100% !important;
                margin: 0 !important;
            }
            
            table.dataTable thead th {
                background: linear-gradient(135deg, var(--primary-color), #34495e);
                color: white;
                padding: 15px 10px;
                font-weight: 600;
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
            
            table.dataTable tbody tr:hover {
                background-color: #f8f9fa;
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
                background: var(--secondary-color);
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 0.75rem;
                margin-right: 4px;
                display: inline-block;
                margin-bottom: 2px;
            }
            
            .year-cell {
                font-weight: 600;
                color: var(--primary-color);
                background: linear-gradient(135deg, #ecf0f1, #bdc3c7);
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
                margin-right: 8px !important;
                font-size: 0.9rem !important;
                transition: all 0.3s ease !important;
            }
            
            .dt-button:hover {
                background: #2980b9 !important;
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            }
            
            /* Footer */
            .footer {
                margin-top: 40px;
                padding: 30px 20px;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 8px;
                text-align: center;
                border-top: 3px solid var(--secondary-color);
            }
            
            .footer p {
                margin: 8px 0;
                color: #666;
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
            
            @media (max-width: 768px) {
                .container { padding: 15px; }
                h1 { font-size: 2rem; }
                .stats { gap: 15px; }
                .stat-item { min-width: 100px; padding: 10px; }
                table.dataTable thead th,
                table.dataTable tbody td { padding: 8px 6px; font-size: 0.9rem; }
                .legend-grid { grid-template-columns: 1fr; }
                .footer { margin-top: 20px; padding: 20px 15px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐒 Awesome Computational Primatology</h1>
                <p class="subtitle">A curated list of machine learning research for non-human primatology</p>
                
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-number" id="total-papers">{total_papers}</span>
                        <span class="stat-label">Papers</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number" id="years-span">{years_span}</span>
                        <span class="stat-label">Years</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number" id="with-code">{with_code}</span>
                        <span class="stat-label">With Code</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number" id="with-data">{with_data}</span>
                        <span class="stat-label">With Data</span>
                    </div>
                </div>
            </div>
            
            <div class="legend">
                <h3>🏷️ Topic Legend</h3>
                <div class="legend-grid">
                    <div class="legend-item">
                        <span class="legend-badge">PD</span>
                        <span>Primate Detection</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">BPE</span>
                        <span>Body Pose Estimation</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">FD</span>
                        <span>Face Detection</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">FLE</span>
                        <span>Facial Landmark Estimation</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">FR</span>
                        <span>Face Recognition</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">FAC</span>
                        <span>Facial Action Coding</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">BR</span>
                        <span>Behavior Recognition</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">AM</span>
                        <span>Avatar/Mesh</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">SI</span>
                        <span>Species Identification</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-badge">RL</span>
                        <span>Reinforcement Learning</span>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                {table_html}
            </div>
            
            <div class="footer">
                <p>
                    <strong>Maintained by:</strong> 
                    <a href="http://kordinglab.com" target="_blank">🧠 Kording Lab</a> • 
                    <a href="mailto:fparodi@upenn.edu">📧 Felipe Parodi</a> • 
                    <a href="https://github.com/KordingLab/awesome-computational-primatology" target="_blank">⭐ Star on GitHub</a>
                </p>
                <p class="footer-note">
                    Found a paper we missed? <a href="https://github.com/KordingLab/awesome-computational-primatology/blob/main/CONTRIBUTING.md">Contribute here!</a> 
                    • Last updated: <span id="last-updated"></span>
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
                
                dom: 'Bfrtip',
                buttons: [
                    {
                        extend: 'searchPanes',
                        config: {
                            cascadePanes: true,
                            viewTotal: true,
                            columns: [0, 2, 3, 4, 5]
                        }
                    },
                    'copy', 'csv', 'excel',
                    {
                        text: 'Clear Filters',
                        action: function(e, dt, node, config) {
                            dt.searchPanes.clearSelections();
                        }
                    }
                ],
                
                searchPanes: {
                    cascadePanes: true,
                    viewTotal: true,
                    columns: [0, 2, 3, 4, 5],
                    initCollapsed: true
                },
                
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
                                return topics.map(topic => 
                                    '<span class="topic-tag">' + topic.trim() + '</span>'
                                ).join(' ');
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
        # Local development - go up 2 levels from .github/workflows/
        script_dir = os.path.dirname(os.path.abspath(__file__))  # .github/workflows/
        base_path = os.path.dirname(os.path.dirname(script_dir))  # repository root
    
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