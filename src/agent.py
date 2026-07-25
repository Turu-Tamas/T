from observation_tensorclass import ObservationTensor
from pyspiel.hungarian_tarokk import HungarianTarokkPhase
import torch.nn as nn

class HungarianTarokkAgent(nn.Module):
    def __init__(
            self,
            bidding_agent: nn.Module,
            skart_agent: nn.Module,
            announcement_agent: nn.Module,
            play_agent: nn.Module,
            ):
        super().__init__()
        self.submodules = nn.ModuleList([bidding_agent, skart_agent, announcement_agent, play_agent])

    def forward(self, obs: ObservationTensor):
        return self.submodules[int(obs.phase.argmax().item())](obs)

class AlwaysPassBiddingAgent(nn.Module):
    def forward(self, obs: ObservationTensor):
        return 
