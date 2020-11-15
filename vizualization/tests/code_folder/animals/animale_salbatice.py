import math
from typing import List, Tuple

from vizualization.tests.code_folder.animals.animal import Animal
from vizualization.tests.code_folder.hrana.fodder import Fodder


class Vipera(Animal):
    def __init__(self):
        super().__init__()
        self.latin_name = 'Vipera Berus'
        self.is_domestic = False

    def produce_mass(self,
                     initial_mass: float,
                     term: float,
                     fodder: List[Tuple[Fodder, float]]):
        return initial_mass * 0