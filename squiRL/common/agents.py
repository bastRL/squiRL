"""Base agent class which handles interacting with the environment for
generating experience
"""
import gym3
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple
from squiRL.common.data_stream import Experience


class Agent:
    """
    Base Agent class handling the interaction with the environment

    Args:
        env: training environment

    Attributes:
        env (gym3.Env): OpenAI gym training environment
        obs (int): Array of env observation state
        replay_buffer (TYPE): Data collector for saving experience
    """
    def __init__(self, env: gym3.Env, replay_buffer) -> None:
        """Initializes agent class

        Args:
            env (gym3.Env): OpenAI gym training environment
            replay_buffer (TYPE): Data collector for saving experience
        """
        self.env = env
        self.replay_buffer = replay_buffer

    def process_obs(self, obs: int) -> torch.Tensor:
        """Converts obs np.array to torch.Tensor for passing through NN

        Args:
            obs (int): Array of env observation state

        Returns:
            torch.Tensor: Torch tensor of observation
        """
        return torch.from_numpy(obs).float().unsqueeze(0)

    def get_action(
        self,
        net: nn.Module,
    ) -> int:
        """
        Using the given network, decide what action to carry out

        Args:
            net (nn.Module): Policy network

        Returns:
            action (int): Action to be carried out
        """
        reward, self.obs, first = self.env.observe()
        obs = self.process_obs(self.obs)

        action_logit = net(obs)
        probs = F.softmax(action_logit, dim=-1)
        dist = torch.distributions.Categorical(probs)
        action = dist.sample().item()
        action = int(action)
        return action

    @torch.no_grad()
    def play_step(
        self,
        net: nn.Module,
    ) -> Tuple[float, bool]:
        """
        Carries out a single interaction step between the agent and the
        environment

        Args:
            net (nn.Module): Policy network

        Returns:
            reward (float): Reward received due to taken step
            done (bool): Indicates if a step is terminal
        """
        action = self.get_action(net)

        # do step in the environment
        self.env.act([action])
        reward, new_obs, first = self.env.observe()
        exp = Experience(self.obs, action, reward, first, new_obs)
        self.replay_buffer.append(exp)

        self.obs = new_obs
        return reward, first
