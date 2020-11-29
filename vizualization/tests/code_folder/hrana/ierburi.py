import math

from vizualization.tests.code_folder.hrana.fodder import Fodder


class Ierb(Fodder):
    def __init__(self):
        super().__init__()
        self.k_dry = 0.15
        self.btu = 0
        self.density = 0

    def __str__(self):
        return f'{self.btu}: {self.density}'

    def mass_drying(self,
                    source_mass: float,
                    temperature: float,
                    term: float) -> float:
        if source_mass <= 0:
            raise ValueError('Source mass is 0 or less')
        k_dry = self.k_dry
        temperature = math.pow(temperature, 0.8)
        return source_mass * k_dry * math.pow(term * temperature, -0.5)


class Urzica(Ierb):
    def __init__(self,
                 btu: float = 11.5,
                 density: float = 113):
        super().__init__()
        self.btu = btu
        self.density = density
        self.k_dry = 0.22

    def mass_drying(self,
                    source_mass: float,
                    temperature: float,
                    term: float) -> float:
        if source_mass <= 0:
            raise ValueError('Source mass is 0 or less')
        if temperature > 42:
            raise ValueError('Temperature is above 42')
        k_dry = self.k_dry
        temperature = math.pow(temperature, 0.8)
        return source_mass * k_dry * math.pow(term * temperature, -0.4)
