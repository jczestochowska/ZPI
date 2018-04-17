from math import log
from random import random

import numpy as np
from pandas import read_excel
from scipy.optimize import minimize

from models import probability_A, RescorlaWagner

MAX_EXP = 700
MIN_LOG = 0.01


class RealPlayer:
    def __init__(self, path, model):
        data = self._read_real_player_excel(path)
        self.decisions = data['Action'].tolist()
        self.condition_left = data['StimulusLeft'].tolist()
        self.condition_right = data['StimulusRight'].tolist()
        self.rewards = data['Reward'].tolist()
        self.model = model

    @staticmethod
    def _read_real_player_excel(path):
        data = read_excel(path, header=None)
        data = data.T
        data.columns = data.iloc[0]
        data = data.reindex(data.index.drop(0))
        data.drop(['StimulusPair'], axis=1, inplace=True)
        data.drop(['Response time'], axis=1, inplace=True)
        data = data[0:90]
        return data.astype(int)

    def search_parameters(self):
        return self.max_log_likelihood().x

    def log_likelihood_function(self, params, sign):
        T = params[0]
        log_likelihood = 0
        for index, decision in enumerate(self.decisions):
            Q_A = self.model.Q_table[self.condition_left[index] - 1]
            p_a = probability_A(Q_A, 1 - Q_A, T)
            game_status = {'StimuliLeft': self.condition_left[index],
                           'StimuliRight': self.condition_right[index],
                           'Action': decision,
                           'Reward': self.rewards[index]}
            self.model.update_q_table(game_status, params)
            log_likelihood += sign * (
                decision * log(max(p_a, MIN_LOG)) + (1 - decision) * log(1 - min(p_a, 1 - MIN_LOG)))
        return log_likelihood

    def max_log_likelihood(self):
        return minimize(self.log_likelihood_function, x0=self._get_optimization_start_points(), method='Nelder-Mead',
                        args=(-1.0))

    def _get_optimization_start_points(self):
        if isinstance(self.model, RescorlaWagner):
            x0 = np.array([0.1, 0.1, 0.1])
        else:
            x0 = np.array([0.1, 0.1])
        return x0


class VirtualPlayer(RealPlayer):
    def __init__(self, game_skeleton, model, *params):
        # type (DataFrame, Tuple[float|int]) -> None
        self.condition_left = game_skeleton['StimulusLeft']
        self.condition_right = game_skeleton['StimulusRight']
        self.left_rewards = game_skeleton['LeftReward']
        self.right_rewards = game_skeleton['RightReward']
        self.better_stimulus = game_skeleton['BetterStimulus']
        self.decisions = []
        self.rewards = []
        self.correct_actions = []
        self.params = list(params)
        self.model = model

    def decide(self, model):
        T = self.params[0]
        for index, condition_left in enumerate(self.condition_left):
            self.simulate_game(T, condition_left, index, model)

    def simulate_game(self, T, condition_left, index, model):
        left_reward = self.left_rewards[index]
        right_reward = self.right_rewards[index]
        condition_right = self.condition_right[index]
        Q_A = model.Q_table[condition_left - 1]
        p_a = probability_A(Q_A, 1 - Q_A, T)
        decision = self._check_threshold(p_a)
        self._is_action_correct(decision, index)
        self.decisions.append(decision)
        reward = self.get_reward(decision, left_reward, right_reward)
        self.rewards.append(reward)
        game_status = {'StimuliLeft': condition_left, 'StimuliRight': condition_right,
                       'Action': decision, 'Reward': reward}
        model.update_q_table(game_status, self.params)

    @staticmethod
    def get_reward(decision, left_reward, right_reward):
        if decision == 1:
            reward = left_reward
        elif decision == 0:
            reward = right_reward
        if reward == 0:
            reward = -1
        return reward

    @staticmethod
    def _check_threshold(p_a):
        return int(random() < p_a)

    def _is_action_correct(self, decision, index):
        if decision == self.better_stimulus[index]:
            self.correct_actions.append(1)
        else:
            self.correct_actions.append(0)


class ModelPlayer(VirtualPlayer):
    def play_game(self):
        T = self.params[0]
        for index, condition_left in enumerate(self.condition_left):
            self.simulate_game(T, condition_left, index, self.model)
            self.search_parameters()
            self.params = self.search_parameters()

