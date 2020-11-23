import html
from typing import Optional, Set
import regex as re
import os
import codecs

from vizualization.folder_map import FolderNode
from vizualization.source_tree_render import SourceTreeRender


class HtmlSourceTreeRender(SourceTreeRender):
    REG_ILLEGAL_PATH_CHARS = re.compile(r'[^a-z\.0-9_]', re.IGNORECASE)

    def render(self):
        self.render_styles()
        self.give_unique_filenames(self.root_folder, None, set())
        self.root_folder.plain_file_name = 'index.html'
        self.render_folder_or_file(self.root_folder)

    def render_folder_or_file(self, node: FolderNode):
        if not node.is_file:
            self.render_folder(node)
            for child in node.children:
                self.render_folder_or_file(child)
        else:
            self.render_file(node)

    def render_folder(self, node: FolderNode):
        with self.open_file_to_write(node.plain_file_name) as fw:
            self.render_head(node, fw)
            self.render_navigation_path(node, fw)
            fw.write(f'''<h3>{node.full_path}</h3>\n''')
            fw.write(f'''    <p>{node.statistics.copypastes} copypastes,                             
                             longest: {node.statistics.longest},
                             {node.statistics.functions} functions</p>
                             </br>\n''')

            folders = [c for c in node.children if not c.is_file]
            if node.ancestors:
                fw.write(f'''    <p><a href="{node.ancestors[-1].plain_file_name}">../</a></p>\n''')
            for folder in folders:
                fw.write(f'''    <p> {folder.statistics.copypastes} / {folder.statistics.functions}
                    <a href="{folder.plain_file_name}">./{folder.file_name}</a>
                        </p>\n''')
            if folders:
                fw.write(f'''    <br/>''')

            files = [c for c in node.children if c.is_file]
            for file in files:
                fw.write(f'''    <p> {file.statistics.copypastes} / {file.statistics.functions}
                    <a href="{file.plain_file_name}">{file.file_name}</a>
                        </p>\n''')
            self.render_footer(fw)

    def render_file(self, node: FolderNode):
        copypastes = self.cps_by_path.get(node.full_path, [])

        with self.open_file_to_write(node.plain_file_name) as fw:
            self.render_head(node, fw)
            self.render_navigation_path(node, fw)
            if node.ancestors:
                fw.write(f'''    <p><a href="{node.ancestors[-1].plain_file_name}">../</a></p><br/>\n''')

            fw.write('''    <pre>\n''')
            line_index = 1

            with codecs.open(node.full_path, 'r', encoding='utf-8') as fr:
                full_text = fr.read()

            line_start_index = 0
            line_end_index = full_text.find('\n')
            while True:
                cpx_hint = ''
                line = full_text[line_start_index:] if line_end_index < 0 else \
                    full_text[line_start_index:line_end_index]
                # is there some copypaste?
                for c in copypastes:
                    is_in = line_start_index <= c.start_index_a <= line_end_index  # OK
                    is_in = is_in or (line_start_index <= c.end_index_a <= line_end_index)
                    is_in = is_in or (c.start_index_a <= line_start_index <= c.end_index_a)
                    is_in = is_in or (c.start_index_a <= line_end_index <= c.end_index_a)
                    if is_in:
                        cpx_hint = str(c)

                line_num_str = f'{line_index:03}'
                line_index += 1
                line_printed = f'{line_num_str}&nbsp;&nbsp;'
                if cpx_hint:
                    line_printed += f'<a class="copy-line" href="#" title="{html.escape(cpx_hint)}">'
                line_printed += html.escape(line)
                if cpx_hint:
                    line_printed += '</a>'
                line_printed += '<br/>\n'
                fw.write(line_printed)

                if line_end_index < 0:
                    break
                line_start_index = line_end_index + 1
                line_end_index = full_text.find('\n', line_start_index)

            fw.write('''\n    </pre>\n''')
            self.render_footer(fw)

    def open_file_to_write(self, rel_path: str) -> codecs.StreamReaderWriter:
        full_path = os.path.join(self.output_folder, rel_path)
        return codecs.open(full_path, 'w', encoding='utf-8')

    def render_styles(self):
        styles_folder = os.path.join(self.output_folder, 'css')
        try:
            os.mkdir(styles_folder)
        except:
            pass
        css_file_path = os.path.join(self.output_folder, 'css', 'styles.css')
        with self.open_file_to_write(css_file_path) as fw:
            fw.write('''
            pre {
                white-space: pre-wrap;       /* Since CSS 2.1 */
                white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
                white-space: -pre-wrap;      /* Opera 4-6 */
                white-space: -o-pre-wrap;    /* Opera 7 */
                word-wrap: break-word;       /* Internet Explorer 5.5+ */
                line-height: 55%;
            }
            
            a.copy-line {
                background-color: #ffe5e5;
                text-decoration: none;
                color: black;
            }
            ''')

    def render_head(self, node: FolderNode, fw: codecs.StreamReaderWriter):
        fw.write(f'''
        <html>
          <head>
            <meta charset="utf-8">
            <title>{node.full_path}</title>
            <link rel = "stylesheet" type = "text/css" href = "css/styles.css" />
          </head>
          <body>\n
        ''')

    def render_footer(self, fw: codecs.StreamReaderWriter):
        fw.write('''\n  </body>\n</html>''')

    def render_navigation_path(self, node: FolderNode, fw: codecs.StreamReaderWriter):
        if not node.ancestors:
            return
        fw.write('    <div>')
        refs = [f'<a href="{a.plain_file_name}">{a.file_name}</a>' for a in node.ancestors]
        refs_text = ' / '.join(refs)
        fw.write(refs_text)
        fw.write('</div>')
        fw.write('<hr/><br/>\n')

    def give_unique_filenames(self,
                              node: FolderNode,
                              parent_node: Optional[FolderNode],
                              all_file_names: Set[str]):
        rel_path = node.full_path
        if parent_node:
            if rel_path.startswith(parent_node.full_path):
                rel_path = rel_path[len(parent_node.full_path):]
        # extract extension
        _, file_extension = os.path.splitext(node.file_name)
        if file_extension:
            rel_path = rel_path[:-len(file_extension)]

        # replace all not allowed characters
        file_name = self.REG_ILLEGAL_PATH_CHARS.sub('_', rel_path)
        file_name = file_name.strip(' .')

        # make file name unique
        counter = 1
        unique_name = file_name
        while True:
            if file_name not in all_file_names:
                break
            unique_name = file_name + str(counter)
            counter += 1

        all_file_names.update(unique_name)
        node.plain_file_name = unique_name + '.html'
        for child in node.children:
            self.give_unique_filenames(child, node, all_file_names)
