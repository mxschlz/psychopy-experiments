import re

with open('forms/infos.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove underscores used for italics
content = content.replace('_', '')

# Replace bold markers
content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

pages = []
parts = re.split(r'(?=<strong>\d+\.)', content)
for i, p in enumerate(parts):
    p = p.strip()
    if not p: continue
    
    lines = [line.rstrip() for line in p.split('\n') if line.strip()]
    
    html = '<div class="instruction-text" style="text-align: left; overflow-y: auto; max-height: 70vh; padding-right: 15px;">\n'
    in_list = False
    in_exclusion = False
    in_footnote = False
    in_contact = False
    
    for line in lines:
        # Detect if we should start a contact box
        if line.startswith('Für die Datenverarbeitung verantwortlich ist:') or \
           line.startswith('Im Falle einer Beschwerde wenden Sie sich bitte') or \
           line.startswith('Sie können sich mit einer Beschwerde auch an die zuständige'):
            if in_list: html += '    </ul>\n'; in_list = False
            html += f'    <p style="color: #f1f5f9; margin-bottom: 8px;">{line.strip()}</p>\n'
            html += '    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin: 10px 0 20px 0;">\n'
            in_contact = True
            continue

        if line.startswith('<strong>') and line.endswith('</strong>'):
            if in_list: html += '    </ul>\n'; in_list = False
            if in_footnote: html += '    </div>\n'; in_footnote = False
            html += f'    <h3 style="color: #4da8da; margin-top: 25px; border-bottom: 1px solid rgba(77, 168, 218, 0.3); padding-bottom: 5px;">{line}</h3>\n'
        elif line.startswith('* '):
            if not in_list: html += '    <ul style="margin-left: 20px; line-height: 1.8;">\n'; in_list = True
            if in_footnote: html += '    </div>\n'; in_footnote = False
            if "Auschlusskriterien" in line or "Ausschlusskriterien" in line:
                in_exclusion = True
                html += f'        <li style="margin-top: 10px; font-weight: 600;">{line[2:]}</li>\n'
            elif "Einschlusskriterien" in line:
                in_exclusion = False
                html += f'        <li style="margin-top: 10px; font-weight: 600;">{line[2:]}</li>\n'
            else:
                html += f'        <li>{line[2:]}</li>\n'
        elif line.startswith('  * '):
            if not in_list: html += '    <ul style="margin-left: 20px; line-height: 1.8;">\n'; in_list = True
            if in_footnote: html += '    </div>\n'; in_footnote = False
            color_style = 'color: #ff6b6b;' if in_exclusion else 'color: #4caf50;'
            html += f'        <li style="{color_style}">{line[4:]}</li>\n'
        elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.'):
            if in_list: html += '    </ul>\n'; in_list = False
            if in_footnote: html += '    </div>\n'; in_footnote = False
            html += f'    <p style="margin-left: 20px; color: #e2e8f0;">{line}</p>\n'
        elif line.startswith('[^'):
            if in_list: html += '    </ul>\n'; in_list = False
            if in_footnote: html += '    </div>\n'
            in_footnote = True
            # Replace [^1] with just the number for footnote definitions
            line = re.sub(r'\[\^(\d+)\]', r'<strong style="color: #4da8da; font-size: 16px; margin-right: 5px;">\1</strong>', line)
            html += f'    <div style="font-size: 14px; color: #94a3b8; margin-top: 12px; padding-left: 12px; border-left: 3px solid #3b82f6; font-style: italic; background: rgba(59, 130, 246, 0.05); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0;">\n'
            html += f'        <p style="margin: 0 0 5px 0;">{line}</p>\n'
        else:
            if in_list: html += '    </ul>\n'; in_list = False
            line = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="mailto:\2" style="color: #4da8da; text-decoration: none; font-weight: 600;">\1</a>', line)
            
            # Replace inline footnotes [^1] with nice superscripts
            line = re.sub(r'\[\^(\d+)\]', r'<sup style="color: #4da8da; font-weight: bold; margin-left: 2px;">\1</sup>', line)

            if line == '---':
                if in_footnote: html += '    </div>\n'; in_footnote = False
                html += '    <hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 20px 0;">\n'
            elif in_footnote:
                html += f'        <p style="margin: 0 0 5px 0;">{line.strip()}</p>\n'
            else:
                margin = "margin-bottom: 4px;" if in_contact else "margin-bottom: 12px;"
                html += f'    <p style="color: #f1f5f9; {margin}">{line.strip()}</p>\n'
                
                # Close contact box if we just printed an email line
                if in_contact and 'E-Mail:' in line:
                    html += '    </div>\n'
                    in_contact = False
                
    if in_footnote: html += '    </div>\n'
    if in_contact: html += '    </div>\n'
            
    if in_list: html += '    </ul>\n'
    html += '</div>'
    pages.append(html)

js = 'let pages = [\n' + ',\n\n'.join(['`' + page + '`' for page in pages]) + '\n];'
with open('temp_js.txt', 'w', encoding='utf-8') as out:
    out.write(js)
print('Done!')
