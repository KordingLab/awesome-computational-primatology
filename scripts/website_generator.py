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
                --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
                --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
                --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);

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
                padding: 20px;
                color: var(--text-color);
                line-height: 1.6;
                -webkit-font-smoothing: antialiased;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: var(--card-background);
                padding: 30px;
                border-radius: 12px;
                box-shadow: var(--shadow-md);
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
                background: linear-gradient(135deg, var(--secondary-color), #3b82f6);
                color: white;
                border-radius: 8px;
                min-width: 120px;
                box-shadow: var(--shadow-md);
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
                box-shadow: var(--shadow-md);
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
                .container { padding: 15px; }
                h1 { font-size: 2rem; }
                .stats { gap: 15px; }
                .stat-item { min-width: 100px; padding: 10px; }
                table.dataTable thead th,
                table.dataTable tbody td { padding: 8px 6px; font-size: 0.9rem; }
                .legend-grid { grid-template-columns: 1fr; }
                .footer { margin-top: 20px; padding: 20px 15px; }
            }

            /* Small phones */
            @media (max-width: 480px) {
                .container { padding: 10px; }
                h1 { font-size: 1.5rem; }
                .subtitle { font-size: 0.95rem; }
                .stats { flex-direction: column; gap: 10px; }
                .stat-item { min-width: 100%; padding: 12px; }
                table.dataTable thead th,
                table.dataTable tbody td { padding: 6px 4px; font-size: 0.8rem; }
                .topic-tag { font-size: 0.65rem; padding: 1px 4px; }
                .status-badge { font-size: 0.7rem; padding: 3px 6px; }
                .legend { padding: 12px; }
                .legend-badge { font-size: 0.7rem; padding: 2px 6px; }
            }

            /* Chat Widget Styles */
            .chat-toggle {
                position: fixed;
                bottom: 24px;
                right: 24px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--secondary-color), #3b82f6);
                border: none;
                cursor: pointer;
                box-shadow: var(--shadow-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .chat-toggle:hover {
                transform: scale(1.05);
                box-shadow: 0 12px 24px rgba(37, 99, 235, 0.3);
            }
            .chat-toggle i {
                color: white;
                font-size: 1.5rem;
            }
            .chat-toggle .chat-badge {
                position: absolute;
                top: -4px;
                right: -4px;
                background: var(--success-color);
                color: white;
                font-size: 0.7rem;
                padding: 2px 6px;
                border-radius: 10px;
                font-weight: 600;
            }

            .chat-panel {
                position: fixed;
                bottom: 100px;
                right: 24px;
                width: 380px;
                max-height: 500px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
                display: none;
                flex-direction: column;
                z-index: 999;
                overflow: hidden;
            }
            .chat-panel.open { display: flex; }

            .chat-header {
                background: linear-gradient(135deg, var(--primary-color), #34495e);
                color: white;
                padding: 16px 20px;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            .chat-header i { font-size: 1.3rem; }
            .chat-header-text h4 {
                margin: 0;
                font-size: 1rem;
                font-weight: 600;
            }
            .chat-header-text p {
                margin: 2px 0 0 0;
                font-size: 0.75rem;
                opacity: 0.8;
            }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                max-height: 320px;
                background: #f8fafc;
            }

            .chat-message {
                margin-bottom: 12px;
                display: flex;
                flex-direction: column;
            }
            .chat-message.user {
                align-items: flex-end;
            }
            .chat-message.assistant {
                align-items: flex-start;
            }
            .chat-bubble {
                max-width: 85%;
                padding: 10px 14px;
                border-radius: 16px;
                font-size: 0.9rem;
                line-height: 1.5;
            }
            .chat-message.user .chat-bubble {
                background: var(--secondary-color);
                color: white;
                border-bottom-right-radius: 4px;
            }
            .chat-message.assistant .chat-bubble {
                background: white;
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-bottom-left-radius: 4px;
            }
            .chat-sources {
                margin-top: 8px;
                padding: 8px 12px;
                background: #e0f2fe;
                border-radius: 8px;
                font-size: 0.75rem;
                max-width: 85%;
            }
            .chat-sources strong { color: var(--primary-color); }
            .chat-sources a {
                color: var(--secondary-color);
                text-decoration: none;
            }
            .chat-sources a:hover { text-decoration: underline; }

            .chat-input-area {
                padding: 12px 16px;
                background: white;
                border-top: 1px solid var(--border-color);
                display: flex;
                gap: 8px;
            }
            .chat-input {
                flex: 1;
                padding: 10px 14px;
                border: 1px solid var(--border-color);
                border-radius: 24px;
                font-size: 0.9rem;
                outline: none;
                transition: border-color 0.2s;
            }
            .chat-input:focus {
                border-color: var(--secondary-color);
            }
            .chat-send {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: var(--secondary-color);
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            .chat-send:hover { background: #1d4ed8; }
            .chat-send:disabled { background: #94a3b8; cursor: not-allowed; }
            .chat-send i { color: white; font-size: 0.9rem; }

            .chat-typing {
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 10px 14px;
                background: white;
                border: 1px solid var(--border-color);
                border-radius: 16px;
                border-bottom-left-radius: 4px;
            }
            .chat-typing span {
                width: 8px;
                height: 8px;
                background: #94a3b8;
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }
            .chat-typing span:nth-child(1) { animation-delay: 0s; }
            .chat-typing span:nth-child(2) { animation-delay: 0.2s; }
            .chat-typing span:nth-child(3) { animation-delay: 0.4s; }
            @keyframes typing {
                0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }

            .chat-error {
                background: #fef2f2;
                color: #dc2626;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 0.8rem;
                margin-bottom: 12px;
            }

            @media (max-width: 480px) {
                .chat-panel {
                    width: calc(100% - 32px);
                    right: 16px;
                    bottom: 90px;
                    max-height: 60vh;
                }
                .chat-toggle {
                    right: 16px;
                    bottom: 16px;
                    width: 52px;
                    height: 52px;
                }
            }
        </style>
    </head>
    <body>
        <a href="#table" class="skip-link">Skip to papers table</a>
        <div class="container">
            <div class="header">
                <h1>Awesome Computational Primatology</h1>
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
                <h3>Topic Legend</h3>
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
            </div>
            
            <div class="table-container">
                {table_html}
            </div>
            
            <div class="footer">
                <p>
                    <strong>Maintained by:</strong>
                    <a href="https://kordinglab.com" target="_blank">Kording Lab</a> |
                    <a href="mailto:fparodi@upenn.edu">Felipe Parodi</a> |
                    <a href="https://github.com/KordingLab/awesome-computational-primatology" target="_blank">Star on GitHub</a>
                </p>
                <p class="footer-note">
                    Found a paper we missed? <a href="https://github.com/KordingLab/awesome-computational-primatology/blob/main/CONTRIBUTING.md">Contribute here!</a>
                    • Last updated: <span id="last-updated"></span>
                </p>
            </div>
        </div>

        <!-- Chat Widget -->
        <button class="chat-toggle" id="chatToggle" aria-label="Open paper chat">
            <i class="fas fa-comments"></i>
            <span class="chat-badge">AI</span>
        </button>

        <div class="chat-panel" id="chatPanel">
            <div class="chat-header">
                <i class="fas fa-robot"></i>
                <div class="chat-header-text">
                    <h4>Paper Assistant</h4>
                    <p>Ask questions about {total_papers} papers</p>
                </div>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="chat-message assistant">
                    <div class="chat-bubble">
                        Hi! I can help you find papers about computational primatology. Try asking:
                        <br><br>
                        <em>"What methods exist for macaque pose estimation?"</em>
                        <br><br>
                        <em>"Which papers have open-source code?"</em>
                    </div>
                </div>
            </div>
            <div class="chat-input-area">
                <input type="text" class="chat-input" id="chatInput" placeholder="Ask about the papers..." autocomplete="off">
                <button class="chat-send" id="chatSend" aria-label="Send message">
                    <i class="fas fa-paper-plane"></i>
                </button>
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
                                const topicColors = {
                                    'PD': '#ef4444', 'BPE': '#f97316', '2D BPE': '#f97316', '3D BPE': '#f97316',
                                    'FD': '#eab308', 'FLE': '#84cc16', 'FR': '#22c55e', 'FAC': '#14b8a6',
                                    'HD': '#06b6d4', 'HPE': '#0ea5e9', 'BR': '#6366f1', 'AM': '#8b5cf6',
                                    'SI': '#a855f7', 'RL': '#d946ef', 'AV': '#ec4899', 'O': '#6b7280',
                                    '3D': '#8b5cf6'
                                };
                                const topics = data.split(', ');
                                return topics.map(function(topic) {
                                    const t = topic.trim();
                                    const color = topicColors[t] || '#6b7280';
                                    return '<span class="topic-tag" style="background-color: ' + color + ';">' + t + '</span>';
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

        // Chat Widget Functionality
        (function() {
            const API_URL = 'https://primatology-chat-914790111728.us-central1.run.app';
            const chatToggle = document.getElementById('chatToggle');
            const chatPanel = document.getElementById('chatPanel');
            const chatMessages = document.getElementById('chatMessages');
            const chatInput = document.getElementById('chatInput');
            const chatSend = document.getElementById('chatSend');
            let chatHistory = [];
            let isLoading = false;

            // Toggle chat panel
            chatToggle.addEventListener('click', function() {
                chatPanel.classList.toggle('open');
                if (chatPanel.classList.contains('open')) {
                    chatInput.focus();
                }
            });

            // Send message on button click
            chatSend.addEventListener('click', sendMessage);

            // Send message on Enter key
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            async function sendMessage() {
                const question = chatInput.value.trim();
                if (!question || isLoading) return;

                // Add user message to UI
                addMessage('user', question);
                chatInput.value = '';
                chatInput.disabled = true;
                chatSend.disabled = true;
                isLoading = true;

                // Create assistant message bubble for streaming
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chat-message assistant';
                const bubbleDiv = document.createElement('div');
                bubbleDiv.className = 'chat-bubble';
                bubbleDiv.innerHTML = '<span class="chat-typing"><span></span><span></span><span></span></span>';
                messageDiv.appendChild(bubbleDiv);
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;

                let fullResponse = '';
                let sources = [];

                try {
                    const response = await fetch(API_URL + '/chat/stream', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            question: question,
                            history: chatHistory.slice(-6)
                        })
                    });

                    if (!response.ok) {
                        if (response.status === 429) throw new Error('Rate limit exceeded. Please wait a bit.');
                        if (response.status === 503) throw new Error('Daily limit reached. Try again tomorrow!');
                        if (response.status === 403) throw new Error('Access denied.');
                        throw new Error('Something went wrong.');
                    }

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const text = decoder.decode(value);
                        const lines = text.split('\\n');

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));

                                    if (data.sources) {
                                        sources = data.sources;
                                    }
                                    if (data.text) {
                                        fullResponse += data.text;
                                        bubbleDiv.innerHTML = formatMessage(fullResponse);
                                        chatMessages.scrollTop = chatMessages.scrollHeight;
                                    }
                                    if (data.error) {
                                        throw new Error(data.error);
                                    }
                                } catch (e) {
                                    // Skip invalid JSON
                                }
                            }
                        }
                    }

                    // Add sources after streaming completes
                    if (sources.length > 0) {
                        const sourcesDiv = document.createElement('div');
                        sourcesDiv.className = 'chat-sources';
                        const sourceLinks = sources.map(s => {
                            const title = s.title || 'Paper';
                            const year = s.year ? ' (' + s.year + ')' : '';
                            if (s.url) return '<a href="' + s.url + '" target="_blank">' + title + year + '</a>';
                            return title + year;
                        });
                        sourcesDiv.innerHTML = '<strong>Sources:</strong> ' + sourceLinks.join(', ');
                        messageDiv.appendChild(sourcesDiv);
                    }

                    // Update history
                    chatHistory.push({ role: 'user', content: question });
                    chatHistory.push({ role: 'assistant', content: fullResponse });

                } catch (error) {
                    bubbleDiv.innerHTML = '';
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'chat-error';
                    errorDiv.textContent = error.message || 'Something went wrong.';
                    messageDiv.replaceWith(errorDiv);
                } finally {
                    chatInput.disabled = false;
                    chatSend.disabled = false;
                    isLoading = false;
                    chatInput.focus();
                }
            }

            function addMessage(role, content, sources) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chat-message ' + role;

                const bubbleDiv = document.createElement('div');
                bubbleDiv.className = 'chat-bubble';
                bubbleDiv.innerHTML = formatMessage(content);
                messageDiv.appendChild(bubbleDiv);

                // Add sources if available
                if (sources && sources.length > 0) {
                    const sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'chat-sources';
                    const sourceLinks = sources.slice(0, 3).map(s => {
                        const title = s.title || 'Paper';
                        const year = s.year ? ' (' + s.year + ')' : '';
                        if (s.url) {
                            return '<a href="' + s.url + '" target="_blank">' + title + year + '</a>';
                        }
                        return title + year;
                    });
                    sourcesDiv.innerHTML = '<strong>Sources:</strong> ' + sourceLinks.join(', ');
                    messageDiv.appendChild(sourcesDiv);
                }

                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function formatMessage(text) {
                // Basic markdown-like formatting
                return text
                    .replace(/\\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>');
            }
        })();
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