class Rule(object):
    def __init__(self, name, slots):
        self.name = name
        self.slots = slots

    def __len__(self):
        return len(self.slots)

    def __getitem__(self, index):
        return self.slots[index]

    def _expand_to_rules(self, visited, result):
        if self in visited:
            return
        visited.add(self)
        result.append(self)

class Symbol(object):
    def __init__(self):
        pass

    def _expand_to_rules(self, visited, result):
        return

class Context(object):
    def __init__(self, name):
        self.name = name
        self.accept = set()

    @property
    def rules(self):
        visited = set()
        result = []
        for rule in self.accept:
            rule._expand_to_rules(visited, result)
        return result

    def _expand_to_rules(self, visited, result):
        if self in visited:
            return
        visited.add(self)
        for rule in self.accept:
            rule._expand_to_rules(visited, result)
