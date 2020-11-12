import os
from typing import List


class ModuleStatistics:
    def __init__(self,
                 copypastes: int = 0,
                 longest: int = 0,
                 functions: int = 0,
                 function_leaves: int = 0):
        self.copypastes = copypastes
        self.longest = longest
        self.functions = functions
        self.function_leaves = function_leaves

    def __str__(self):
        return f'{self.copypastes} in {self.functions} functions, longest: {self.longest}'


class FolderNode:
    def __init__(self, full_path: str):
        self.full_path = full_path
        self.file_name = os.path.basename(full_path)
        self.is_file = os.path.isfile(full_path)
        self.children: List['FolderNode'] = []
        self.statistics: ModuleStatistics = ModuleStatistics()

    def __str__(self):
        prefix = 'file' if self.is_file else 'dir'
        return f'{prefix}: {self.full_path} [{self.statistics}]'
