import re

with open('Project_Report.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the TOC table
toc_start = content.find('| Chapter | Title | Page |')
if toc_start != -1:
    toc_end = content.find('\n\n', toc_start)
    if toc_end == -1:
        toc_end = len(content)
    
    # We also have an issue where the table could be followed by something else. We just want to parse the table rows.
    # Actually, we can just replace every line in the file that looks like a TOC table row.
    lines = content.split('\n')
    new_lines = []
    in_toc = False
    for line in lines:
        if line.startswith('| Chapter | Title | Page |'):
            in_toc = True
            new_lines.append(line)
        elif in_toc and line.startswith('|---'):
            new_lines.append(line)
        elif in_toc and line.startswith('|'):
            parts = line.split('|')
            if len(parts) >= 4:
                chapter = parts[1].strip()
                title = parts[2].strip()
                page = parts[3].strip()
                
                # Check if it already has a link
                if '](#' not in title:
                    clean_title = title.replace('**', '')
                    
                    if '**' in chapter: # Main chapter
                        num = chapter.replace('**', '')
                        if num:
                            heading_text = f'Chapter {num}: {clean_title}'
                        else:
                            heading_text = clean_title
                    elif chapter:
                        heading_text = f'{chapter} {clean_title}'
                    else: # Appendices
                        heading_text = clean_title
                        
                    anchor = heading_text.lower().replace(' ', '-').replace('&', '').replace('(', '').replace(')', '').replace(':', '').replace('.', '').replace('`', '').replace(',', '')
                    anchor = re.sub(r'-+', '-', anchor) # remove double hyphens
                    
                    if title.startswith('**') and title.endswith('**'):
                        new_title = f'**[{clean_title}](#{anchor})**'
                    else:
                        new_title = f'[{title}](#{anchor})'
                    
                    parts[2] = f' {new_title} '
                    new_lines.append('|'.join(parts))
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        else:
            in_toc = False
            new_lines.append(line)
            
    content = '\n'.join(new_lines)


# Fix font size
content = content.replace('font-size: 0.10em;', 'font-size: 0.9em;')

# Fix Cover Page title sizes (the user says fonts are too short/blank cover page and purple line in the middle)
# The previous cover page had:
# # INTERNSHIP PROJECT REPORT
# ## ON
# # REAL TIME CODE ANALYZER
# We want to replace this with explicit large styles.
content = content.replace('# INTERNSHIP PROJECT REPORT \n## ON \n# REAL TIME CODE ANALYZER', 
                          '<h1 style="font-size: 3em; font-weight: bold; margin-bottom: 10px; border: none;">INTERNSHIP PROJECT REPORT</h1>\n'
                          '<h2 style="font-size: 2em; margin-bottom: 10px; border: none; text-align: center;">ON</h2>\n'
                          '<h1 style="font-size: 3.5em; font-weight: bold; color: #2A1B3D; margin-bottom: 40px; border: none;">REAL TIME CODE ANALYZER</h1>')
content = content.replace('h2 { border-bottom: 2px solid #6D3D8E; padding-bottom: 5px; margin-top: 30px; }', 
                          'h2 { border-bottom: 1px solid #eaecef; padding-bottom: 5px; margin-top: 30px; }')

with open('Project_Report.md', 'w', encoding='utf-8') as f:
    f.write(content)
