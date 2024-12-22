#%%
# !pip3 install pandas
import pandas as pd
import re

def to_link_if_markdown(cell_text: str) -> str:
    # Matches [alt](url) with regex and converts to html <a>:
    cell_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', cell_text)
    return cell_text

text = open("/home/runner/work/awesome-computational-primatology/awesome-computational-primatology/README.md", "r").readlines()
table = []
# | Year | Paper | Topic | Animal | Model? | Data? | Image/Video Count |
for line in text:
    # If line has the correct number of columns
    if len(re.findall("\|", line)) == 8:
        table.append(line.split("|")[1:-1])
table = pd.DataFrame(table[2:], columns=table[0])

# Substitutions:
table = table.applymap(to_link_if_markdown)


# %%
with open("/home/runner/work/awesome-computational-primatology/awesome-computational-primatology/index.html", "w") as f:
    f.write("""<html>
    <head>
    <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/2.0.2/css/dataTables.dataTables.css" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    <script src="https://cdn.datatables.net/2.0.2/js/dataTables.js"></script>
    </head>
    <body>
    <h1>Awesome Computational Primatology</h1>
    """)
    f.write(table.to_html(table_id="table", escape=False, index=False))
    f.write("""<script>$(document).ready( function () {
            $('#table').DataTable({
                paging: false
            });
        } );</script>
    </body>
    </html>""")
# %%
