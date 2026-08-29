import lightning.pytorch as L
from lightning.pytorch.loggers import TensorBoardLogger
from lightning.pytorch.callbacks.early_stopping import EarlyStopping
import torch
import torch.nn as nn
import numpy as np
from .memory import ReservoirBuffer, AdvantageMemory, StrategyMemory
from torch.utils.data import Dataset, DataLoader
from ..models.models import TarokkModelNoAnnouncements
from ..models.input_struct import get_input, InputTensorClass
from ..models.constants import *
from .sampling import GameSampler
import pyspiel
import pyspiel.hungarian_tarokk as T
import hydra
from tensordict import TensorClass

def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


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
        iters = batch.iteration.sqrt().unsqueeze(-1)
        loss = self.loss(iters * y, iters * outs)
        return loss

    def validation_step(self, batch: StrategyMemory):
        x = batch.inputs
        y = batch.action_probs
        outs = self.network(x)
        probs = torch.softmax(outs, dim=-1)
        iters = batch.iteration.sqrt().unsqueeze(-1)
        print(iters.shape, y.shape, probs.shape)
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
        iters = batch.iteration.sqrt().unsqueeze(-1)
        loss = self.loss(iters * y, iters * outs)
        return loss

    def validation_step(self, batch: AdvantageMemory):
        x = batch.inputs
        y = batch.advantage
        outs = self.network(x)
        iters = batch.iteration.sqrt().unsqueeze(-1)
        loss = self.loss(iters * y, iters * outs)
        self.log("val_loss", loss, prog_bar=True, on_epoch=True, on_step=False)

    def configure_optimizers(self):
        optim = torch.optim.AdamW(self.parameters(), lr=self.lr)
        return optim

def make_dataloaders(config, buf: ReservoirBuffer):
    train_count = int(len(buf) * config["train_split"])
    val_count = len(buf) - train_count
    def _make_dloader(dataset):
        return DataLoader(
            dataset,
            batch_size=config["batch_size"],
            num_workers=config["workers"],
            collate_fn=lambda x: x # tensorclass handles batch indices
        )

    train_idx = np.random.choice(len(buf), size=[train_count])
    val_idx = np.random.choice(len(buf), size=[val_count])
    return _make_dloader(buf[train_idx]), _make_dloader(buf[val_idx])

def train_advantage_network(config, advantage_buffer: ReservoirBuffer, network, iteration: int):
    tensorboard_logger = TensorBoardLogger(
        save_dir="lightning_logs",
        sub_dir=f"it_{iteration}",
        name=f"advantage",
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
        save_dir="lightning_logs",
        name=f"policy"
    )
    early_stopping = EarlyStopping("val_loss")
    trainer = L.Trainer(
        logger=tensorboard_logger,
        callbacks=[early_stopping]
    )

    module = PolicyTrainingModule(config, TarokkModelNoAnnouncements(config["model"]))
    train_loader, val_loader = make_dataloaders(config["data"]["strategy"], strategy_buffer)
    trainer.fit(module, train_loader, val_loader)

def get_policies(config, model):
    def _target(raw_advantage, action_mask):
        # regret matching policy
        positive = raw_advantage.clip(min=0.0)
        total = positive.sum()
        if total < 1e-6:
            result = np.zeros_like(positive)
            idx = np.where(action_mask, raw_advantage, -np.inf).argmax()
            result[idx] = 1.
            return result
        return positive / total

    def _sampling(raw_advantage, action_mask):
        if np.random.random() < config["exploration"]:
            result = np.zeros_like(raw_advantage)
            result[action_mask] = 1. / action_mask.sum()
            return result / result.sum()
        return _target(raw_advantage, action_mask)

    @torch.inference_mode
    def _policies(x: InputTensorClass):
        raw_advantage = model(x).cpu().numpy().astype(np.float64)
        return _sampling(raw_advantage, x.action_mask), _target(raw_advantage, x.action_mask)

    return _policies

@hydra.main(config_path="conf/", config_name="config")
def main(config):
    set_seed(config["seed"])
    game = pyspiel.load_game("hungarian_tarokk")
    sampler = GameSampler(get_input, game, **config["sampler"])
    model = TarokkModelNoAnnouncements(config["model"]).to(config["device"])
    for iteration in range(config["num_iterations"]):
        print(f"Training Advantage networks at iteration {iteration}")
        sampler.run_traversals(iteration, get_policies(config, model))
        train_advantage_network(config, sampler.advantage_memory, model, iteration)

    print("Training Policy Network")
    train_policy_network(config, sampler.strategy_memory)

if __name__ == "__main__":
    main()
