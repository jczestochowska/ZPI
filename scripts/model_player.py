from random import random

from scripts.game_session import GameSession
from scripts.models import Estimator, probability_A, Qlearning, RescorlaWagner


class ModelPlayer:
    def __init__(self, game_skeleton, *params):
        self.condition_left = game_skeleton['StimulusLeft']
        self.condition_right = game_skeleton['StimulusRight']
        self.left_rewards = game_skeleton['LeftReward']
        self.right_rewards = game_skeleton['RightReward']
        self.better_stimulus = game_skeleton['BetterStimulus']
        self.decisions = []
        self.rewards = []
        self.correct_actions = []
        self.params = params

    def play(self, model):
        T = self.params[0]
        for index, condition_left in enumerate(self.condition_left):
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
            estimator = Estimator(decisions=self.decisions,
                                  condition_left=self.condition_left,
                                  condition_right=self.condition_right,
                                  rewards=self.rewards, model=model)
            self.params = self.search_parameters(estimator)
            print(self.params)

    def search_parameters(self, estimator):
        return estimator.max_log_likelihood().x

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


if __name__ == '__main__':
    game = GameSession()
    player = ModelPlayer(game.game_skeleton, 0.1, 0.1, 0.1)
    model = Qlearning()
    player.play(model)