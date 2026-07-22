import random
import pyspiel
from pyspiel.hungarian_tarokk import HungarianTarokkState
import numpy as np
from typing import cast

game = pyspiel.load_game("hungarian_tarokk")
state = cast(HungarianTarokkState, game.new_initial_state())
print(state)