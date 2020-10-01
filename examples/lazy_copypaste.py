class Animal:
    def __str__(self):
        raise NotImplemented()

    def functionez(self, **kwargs):
        raise NotImplemented()


class Lapin(Animal):
    def __str__(self):
        name = 'Lapin'
        # NB: the lines are not exactly the same as for Lup
        name_fancy = '--== ' + ' ' * 3 + name
        if len(name_fancy) < 40:
            name_fancy += ' ' * (40 - len(name_fancy))
        name_fancy += ' ==--'
        return name_fancy

    def functionez(self, **kwargs):
        pass


class Lup(Animal):
    def __str__(self):
        nume = 'Lup'
        # NB: the lines are not exactly the same as for Lup
        name_fancy = '--== ' + ' '*3 + nume

        if len(name_fancy) < 40:
            name_fancy += ' ' * (40 - len(name_fancy))
        name_fancy += ' ==--'
        return name_fancy

    def functionez(self, **kwargs):
        pass
