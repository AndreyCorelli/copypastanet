import os
import codecs
import regex as re
from typing import List, Optional, Dict

from astexplorer.ast_comparer import AstComparer, Copypaste
from astexplorer.ast_parser import go_down_tree
from astexplorer.func_tree import FuncTree
from pythonparser import parse
from vizualization.folder_map import FolderNode


class SourceTreeRender:
    def __init__(self):
        self.source_folder = ''
        self.output_folder = ''
        self.ignore_list: List[str] = ['venv']
        self.include_list: List[str] = ['*.py']
        self.root_folder: Optional[FolderNode] = None
        self.functions: List[FuncTree] = []
        self.copypastes: List[Copypaste] = []
        self.func_by_path: Dict[str, List[FuncTree]] = {}
        self.cps_by_path: Dict[str, List[Copypaste]] = {}

    def explore_sources(self,
                        source_folder='',
                        output_folder='',
                        ignore_list: List[str] = None,
                        include_list: List[str] = None):
        self.source_folder = source_folder
        self.output_folder = output_folder
        self.ignore_list = ignore_list if ignore_list is not None else self.ignore_list
        self.include_list = include_list if include_list is not None else self.include_list

        self.read_folder_tree(source_folder, None)
        if not self.root_folder:
            print(f'No source files / directories are found at {source_folder}')
            return
        self.read_functions(self.root_folder)
        self.find_copypastes()
        self.summarize_node_stats()

    def render(self):
        raise NotImplemented()

    def summarize_node_stats(self) -> None:
        for f in self.functions:
            if f.file in self.func_by_path:
                self.func_by_path[f.file].append(f)
            else:
                self.func_by_path[f.file] = [f]

        for c in self.copypastes:
            if c.func_a.file in self.cps_by_path:
                self.cps_by_path[c.func_a.file].append(c)
            else:
                self.cps_by_path[c.func_a.file] = [c]

        self.summarize_node_stats_iter(self.root_folder)

    def summarize_node_stats_iter(self,
                                  node: FolderNode) -> None:
        if node.is_file:
            functions = self.func_by_path.get(node.full_path) or []
            copypastes = self.cps_by_path.get(node.full_path) or []
            node.statistics.functions = len(functions)
            node.statistics.copypastes = len(copypastes)
            node.statistics.longest = max([c.count for c in copypastes])
            return
        for child in node.children:
            self.summarize_node_stats_iter(child)
            node.statistics.functions += child.statistics.functions
            node.statistics.copypastes += child.statistics.copypastes
            node.statistics.longest = max(node.statistics.longest, child.statistics.longest)

    def find_copypastes(self) -> None:
        cmp = AstComparer()
        cmp.compare_pre_process_functions(self.functions)
        self.copypastes = cmp.find_copypastes(self.functions)
        print(f'{len(self.copypastes)} copy-pastes are found')

    def read_functions(self, node: FolderNode) -> None:
        if node.is_file:
            try:
                with codecs.open(node.full_path, 'r', encoding='utf-8') as myfile:
                    data = myfile.read()
                ast = parse(data, node.file_name, "exec")
                functions = go_down_tree(ast)
                for f in functions:
                    f.file = node.full_path
                    self.functions.append(f)
            except Exception as e:
                print(f'There were error parsing file "{node.file_name}": {e}')
            return
        for child in node.children:
            self.read_functions(child)

    def read_folder_tree(self, path: str, parent: Optional[FolderNode]) -> None:
        if not self.should_parse(path):
            return
        node = FolderNode(path)
        if not parent:
            self.root_folder = node
        else:
            parent.children.append(node)
        for file_name in os.listdir(path):
            sub_path = os.path.join(path, file_name)
            self.read_folder_tree(sub_path, node)

    def should_parse(self, path: str) -> bool:
        file_name = os.path.basename(path)
        is_file = os.path.isfile(path)
        if is_file and self.include_list and \
                not any([self.name_matches_pattern(file_name, p) for p in self.include_list]):
            return False
        if self.ignore_list and \
                any([self.name_matches_pattern(file_name, p) for p in self.ignore_list]):
            return False
        return True

    @classmethod
    def name_matches_pattern(cls, name: str, ptrn: str):
        if '*' in ptrn:
            regex_str = re.sub('.', '\\.', ptrn).sub('*', '.*', ptrn)
            reg = re.compile(regex_str, re.IGNORECASE)
            return reg.match(name)

        return name.lower() == ptrn.lower()
