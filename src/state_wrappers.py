import pyspiel

class HungarianTarokkStateWrapper(pyspiel.State):
    def __init__(self, state):
        self.state = state
