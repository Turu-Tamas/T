from .collector import TarokkCollector
from torchrl.data import ReplayBuffer, LazyTensorStorage
from t.models.models import TarokkPolicy, RandomAnnouncementsPolicy, RandomPolicy
import pyspiel.hungarian_tarokk as T
from time import time

def main():
    network = TarokkPolicy(
        bidding_policy=RandomPolicy(T.HungarianTarokkPhase.BIDDING),
        announcemnets_policy=RandomAnnouncementsPolicy(),
        talon_exchange_policy=RandomPolicy(T.HungarianTarokkPhase.TALON_EXCHANGE),
        play_policy=RandomPolicy(T.HungarianTarokkPhase.PLAYING)
    ).cuda()

    collector = TarokkCollector(
        num_workers=6,
        envs_per_worker=2048,
        replay_buffer=ReplayBuffer(
            storage=LazyTensorStorage(
                max_size=20_000,
                shared_init=True
            ),
            pin_memory=True,
        ),
        network=network
    )

    start = time()
    collector.collect(num_trajs=200_000)
    end = time()
    print(f"{start - end:.2f}")

if __name__ == "__main__":
    main()
