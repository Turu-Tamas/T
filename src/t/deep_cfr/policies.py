import numpy as np
import torch
from ..models.input_struct import InputTensorClass

def get_policies(config, model):
    def _target(raw_advantage, action_mask):
        # Action dimension is the last dimension.
        positive = np.clip(raw_advantage, 0.0, None)
        positive = np.where(action_mask, positive, 0.0)

        total = positive.sum(axis=-1, keepdims=True)

        # Normal regret-matching case.
        result = np.divide(
            positive,
            total,
            out=np.zeros_like(positive),
            where=total >= 1e-6,
        )

        # If there are no positive advantages, choose the best legal action.
        fallback = total[..., 0] < 1e-6
        if np.any(fallback):
            masked_advantage = np.where(
                action_mask,
                raw_advantage,
                -np.inf,
            )
            idx = masked_advantage.argmax(axis=-1)

            fallback_result = np.zeros_like(result)
            np.put_along_axis(
                fallback_result,
                idx[..., None],
                1.0,
                axis=-1,
            )

            result = np.where(
                fallback[..., None],
                fallback_result,
                result,
            )

        return result

    def _sampling(raw_advantage, action_mask):
        result = _target(raw_advantage, action_mask)

        # Exploration decision independently for every batch element.
        explore = np.random.random(raw_advantage.shape[:-1]) < config["exploration"]

        if np.any(explore):
            num_actions = action_mask.sum(axis=-1, keepdims=True)

            exploration_policy = np.divide(
                action_mask.astype(np.float64),
                num_actions,
                out=np.zeros_like(raw_advantage, dtype=np.float64),
                where=num_actions > 0,
            )

            result = np.where(
                explore[..., None],
                exploration_policy,
                result,
            )

        return result

    @torch.inference_mode
    def _policies(x: InputTensorClass):
        raw_advantage = model(x).cpu().numpy().astype(np.float64)
        action_mask = np.asarray(x.action_mask.cpu(), dtype=bool)

        return (
            _sampling(raw_advantage, action_mask),
            _target(raw_advantage, action_mask),
        )

    return _policies