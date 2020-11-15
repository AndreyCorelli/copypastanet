from typing import List, Tuple

from vizualization.tests.code_folder.hrana.fodder import Fodder


class Animal:
    def __init__(self):
        self.latin_name = ''
        self.is_domestic = False

    def produce_mass(self,
                     initial_mass: float,
                     term: float,
                     fodder: List[Tuple[Fodder, float]]) -> float:
        raise NotImplemented()
