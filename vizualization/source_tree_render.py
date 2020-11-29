import os
import regex as re
from typing import List, Optional, Dict
from astexplorer.ast_comparer import AstComparer, Copypaste
from astexplorer.ast_parser import AstParser
from astexplorer.func_tree import FuncTree
from vizualization.folder_map import FolderNode


class SourceTreeRender:
    def __init__(self):
        self.source_folders: List[str] = []
        self.output_folder = ''
        self.ignore_list: List[str] = ['venv']
        self.include_list: List[str] = ['*.py']
        self.root_folder: Optional[FolderNode] = None
        self.functions: List[FuncTree] = []
        self.copypastes: List[Copypaste] = []
        self.func_by_path: Dict[str, List[FuncTree]] = {}
        self.cps_by_path: Dict[str, List[Copypaste]] = {}
        self.file_parse_errors: Dict[str, str] = {}
        self.total_files = 0
        self.files_ok = 0
        self.files_not_parsed = 0
        # copypaste filter params
        self.min_cps_len = 2
        self.min_cps_weight = 2

    def explore_sources(self,
                        source_folders: List[str],
                        output_folder='',
                        ignore_list: List[str] = None,
                        include_list: List[str] = None,
                        min_cps_len: int = 2,
                        min_cps_weight: int = 2):
        if not source_folders:
            raise ValueError('source_folders argument should contain at least one path')
        self.source_folders = source_folders
        self.output_folder = output_folder
        self.ignore_list = ignore_list if ignore_list is not None else self.ignore_list
        self.include_list = include_list if include_list is not None else self.include_list

        if len(self.source_folders) == 1:
            self.read_folder_tree(source_folders[0], None)
        else:
            self.root_folder = FolderNode('.', '.', False)
            for path in self.source_folders:
                self.read_folder_tree(path, self.root_folder)
        if not self.root_folder:
            print(f'No source files / directories are found at {", ".join(source_folders)}')
            return
        print(f'{self.total_files} files total')
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
            node.statistics.longest = max([c.count for c in copypastes]) if copypastes else 0
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
        old_len = len(self.copypastes)
        self.copypastes = [c for c in self.copypastes
                           if c.count >= self.min_cps_len and c.weight >= self.min_cps_weight]
        print(f'{old_len} copy-pastes are found, {len(self.copypastes)} left after filtering')

    def read_functions(self, node: FolderNode) -> None:
        if node.is_file:
            try:
                functions = AstParser().parse_module(node.full_path)
                self.functions += functions
                self.files_ok += 1
                self.report_file_parsing_progress()
            except Exception as e:
                print(f'There were error parsing file "{node.full_path}": {e}')
                self.file_parse_errors[node.full_path] = str(e)
                self.files_not_parsed += 1
                self.report_file_parsing_progress()
            return
        for child in node.children:
            self.read_functions(child)

    def report_file_parsing_progress(self):
        percent_int = int(1000 * (self.files_not_parsed + self.files_ok) / self.total_files)
        percent = percent_int / 10
        if self.files_not_parsed:
            print(f'progress: {percent}%, {self.files_ok} parsed, {self.files_not_parsed} failed')
        else:
            print(f'progress: {percent}%, {self.files_ok} parsed')

    def read_folder_tree(self, path: str, parent: Optional[FolderNode]) -> None:
        if not self.should_parse(path):
            return
        node = FolderNode(path)
        if not parent:
            self.root_folder = node
        else:
            node.ancestors = list(parent.ancestors)
            node.ancestors.append(parent)
            parent.children.append(node)
        if os.path.isdir(path):
            for file_name in os.listdir(path):
                sub_path = os.path.join(path, file_name)
                self.read_folder_tree(sub_path, node)
        else:
            self.total_files += 1

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
            regex_str = re.sub(r'\.', r'\.', ptrn)
            regex_str = re.sub(r'\*', '.*', regex_str)
            reg = re.compile(regex_str, re.IGNORECASE)
            return reg.match(name)

        return name.lower() == ptrn.lower()
