import lightning.pytorch as L
from lightning.fabric.loggers.tensorboard import TensorBoardLogger
from lightning.pytorch.callbacks.early_stopping import EarlyStopping
import torch
import torch.nn as nn
import numpy as np
from .memory import ReservoirBuffer, AdvantageMemory, StrategyMemory
from torch.utils.data import Dataset, DataLoader
from ..models.models import TarokkModel
from ..models.input_struct import get_input, InputTensorClass
from ..models.constants import *
from .sampling import GameSampler
import pyspiel
import pyspiel.hungarian_tarokk as T
import hydra

def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class GameDataSet(Dataset):
    def __init__(self, buf: ReservoirBuffer):
        super().__init__()
        self.buf = buf

    def __len__(self):
        return len(self.buf)

    def __getitem__(self, index):
        return self.buf[index]

class PolicyTrainingModule(L.LightningModule):
    def __init__(self, config, network):
        super().__init__()
        self.network = network
        self.loss = nn.MSELoss()
        self.lr = config["training"]["lr"]

    def training_step(self, batch: StrategyMemory):
        x = batch.inputs
        y = batch.action_probs
        outs = self.network(x)
        iters = batch.iteration.sqrt()
        loss = self.loss(iters * y, iters * outs)
        return loss

    def validation_step(self, batch: StrategyMemory):
        x = batch.inputs
        y = batch.action_probs
        outs = self.network(x)
        probs = torch.softmax(outs, dim=-1)
        iters = batch.iteration.sqrt()
        loss = self.loss(iters * y, iters * probs)
        self.log("val_loss", loss, prog_bar=True, on_epoch=True, on_step=False)

    def configure_optimizers(self):
        optim = torch.optim.AdamW(self.parameters(), lr=self.lr)
        return optim


class AdvantageTrainingModule(L.LightningModule):
    def __init__(self, config, network):
        super().__init__()
        self.network = network
        self.loss = nn.MSELoss(reduction="mean")
        self.lr = config["training"]["lr"]

    def training_step(self, batch: AdvantageMemory):
        x = batch.inputs
        y = batch.advantage
        outs = self.network(x)
        iters = batch.iteration.sqrt()
        loss = self.loss(iters * y, iters * outs)
        return loss

    def validation_step(self, batch: AdvantageMemory):
        x = batch.inputs
        y = batch.advantage
        outs = self.network(x)
        iters = batch.iteration.sqrt()
        loss = self.loss(iters * y, iters * outs)
        self.log("val_loss", loss, prog_bar=True, on_epoch=True, on_step=False)

    def configure_optimizers(self):
        optim = torch.optim.AdamW(self.parameters(), lr=self.lr)
        return optim

def make_dataloaders(config, buf: ReservoirBuffer):
    train_count = int(len(buf) * config["train_split"])
    val_count = len(buf) - train_count
    train_idx = np.random.choice(len(buf), size=[train_count])
    val_idx = np.random.choice(len(buf), size=[val_count])
    train_dataset = GameDataSet(buf[train_idx])
    val_dataset = GameDataSet(buf[val_idx])
    def _make_dloader(dataset):
        return DataLoader(
            dataset,
            batch_size=config["batch_size"],
            num_workers=config["workers"],
        )

    return _make_dloader(train_dataset), _make_dloader(val_dataset)

def train_advantage_network(config, advantage_buffer: ReservoirBuffer, network, iteration: int):
    tensorboard_logger = TensorBoardLogger(
        root_dir="lightning_logs",
        sub_dir=f"it_{iteration}",
        name=f"advantage"
    )
    early_stopping = EarlyStopping("val_loss")
    trainer = L.Trainer(
        logger=tensorboard_logger,
        callbacks=[early_stopping]
    )

    module = AdvantageTrainingModule(config, network)
    train_loader, val_loader = make_dataloaders(config["data"]["advantage"], advantage_buffer)
    trainer.fit(module, train_loader, val_loader)

def train_policy_network(config, strategy_buffer: ReservoirBuffer):
    tensorboard_logger = TensorBoardLogger(
        root_dir="lightning_logs",
        name=f"policy"
    )
    early_stopping = EarlyStopping("val_loss")
    trainer = L.Trainer(
        logger=tensorboard_logger,
        callbacks=[early_stopping]
    )

    module = PolicyTrainingModule(config, TarokkModel(config["model"]))
    train_loader, val_loader = make_dataloaders(config["data"]["strategy"], strategy_buffer)
    trainer.fit(module, train_loader, val_loader)

@hydra.main(config_path="conf/", config_name="config")
def main(config):
    set_seed(config["seed"])
    game = pyspiel.load_game("hungarian_tarokk")
    sampler = GameSampler(get_input, game, **config["sampler"])
    sampler.set_advantage_network(TarokkModel(config["model"]))
    for iteration in range(config["num_iterations"]):
        print(f"Training Advantage networks at iteration {iteration}")
        for player in range(NUM_PLAYERS):
            print(f"Traversals for player {player}")
            sampler.run_traversals(player, iteration)
        train_advantage_network(config, sampler.advantage_memory, sampler.network, iteration)

    print("Training Policy Network")
    train_policy_network(config, sampler.strategy_memory)

if __name__ == "__main__":
    main()
