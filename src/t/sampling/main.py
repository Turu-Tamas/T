from .env import TarokkCollector
from torchrl.data import ReplayBuffer, LazyTensorStorage
from t.models.models import TarokkPolicy, PhasePolicy, RandomAnnouncementsPolicy, RandomPolicy
from tensordict.nn import TensorDictModule
from torchrl.modules import ProbabilisticActor
import pyspiel.hungarian_tarokk as T
from t.models.input_struct import InputTensorClass
from torch.distributions import Categorical

def main():
    network = TarokkPolicy(
        bidding_policy=RandomPolicy(T.HungarianTarokkPhase.BIDDING),
        announcemnets_policy=RandomAnnouncementsPolicy(),
        talon_exchange_policy=RandomPolicy(T.HungarianTarokkPhase.TALON_EXCHANGE),
        play_policy=RandomPolicy(T.HungarianTarokkPhase.PLAYING)
    ).cuda()

    collector = TarokkCollector(
        num_workers=1,
        envs_per_worker=32,
        replay_buffer=ReplayBuffer(
            storage=LazyTensorStorage(
                max_size=20_000,
                shared_init=True
            ),
            pin_memory=True,
        ),
        network=network
    )
    collector.collect(10_000 * 110)

if __name__ == "__main__":
    main()