import os
import subprocess

brain_dir = r"C:\Users\anshi\.gemini\antigravity-ide\brain\4e20a1f7-8030-4ae2-bbd1-4390c91a81c4"
output_md = "Project_Report.md"

chapters = [
    "cover_page.md",
    "chapter_1_executive_summary.md",
    "chapter_2_system_architecture.md",
    "chapter_3_deployment_topology.md",
    "chapter_4_local_setup.md",
    "chapter_5_backend_engineering.md",
    "chapter_6_ai_orchestration.md",
    "chapter_7_semantic_parsing.md",
    "chapter_8_frontend_architecture.md",
    "chapter_9_vscode_extension.md",
    "chapter_10_conclusion.md",
    "appendix_a.md",
    "appendix_b.md"
]

style = """<style>
.page-break { page-break-after: always; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }
h1, h2, h3 { color: #2A1B3D; }
h2 { border-bottom: 2px solid #6D3D8E; padding-bottom: 5px; margin-top: 30px; }
pre { background-color: #f6f8fa; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.9em; }
code { background-color: #f1f1f1; padding: 2px 4px; border-radius: 4px; }
img { max-width: 100%; height: auto; }
</style>

"""

with open(output_md, "w", encoding="utf-8") as outfile:
    outfile.write(style)
    for chapter in chapters:
        path = os.path.join(brain_dir, chapter)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as infile:
                content = infile.read()
                if chapter == "cover_page.md":
                    # Replace placeholder with image
                    content = content.replace("*(Company Logo Placeholder)*", "<img src='https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Tech_Mahindra_New_Logo.svg/512px-Tech_Mahindra_New_Logo.svg.png' width='300'>")
                outfile.write(content)
                # Don't add a page break after the very last chapter
                if chapter != chapters[-1]:
                    outfile.write("\n\n<div class='page-break'></div>\n\n")

print("Combined markdown created.")
