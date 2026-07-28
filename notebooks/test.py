#%%
import pyspiel

game = pyspiel.load_game("hungarian_tarokk")
state = game.new_initial_state()
print(state)
print(pyspiel.hungarian_tarokk.CardActions)