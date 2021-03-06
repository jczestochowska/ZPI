import csv
import os
from itertools import product

import numpy as np
from scipy.optimize import minimize
from scripts.models import Qlearning, RescorlaWagner
from scripts.player import RealPlayer


def save_all_real_players_parameters_to_csv(data_dir_path, new_filename, model, get_parameters):
    # type (str, str, Qlearning, function) -> None
    all_filenames = os.listdir(data_dir_path)
    with open('{}.csv'.format(new_filename), 'w') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(get_header(model))
        for filename in all_filenames:
            if filename.endswith('xls'):
                row = []
                rp = RealPlayer(os.path.join(data_dir_path, filename), get_model(model))
                name = os.path.splitext(os.path.basename(filename))[0][:-8]
                player_parameters, starting_points = get_parameters(real_player=rp)
                criteria = rp.model_selection()
                row.append(name)
                row.extend(player_parameters)
                row.extend(starting_points)
                row.extend(criteria)
                writer.writerow(row)


def get_model(model):
    if isinstance(model, RescorlaWagner):
        model = RescorlaWagner()
    else:
        model = Qlearning()
    return model


def get_header(model):
    if isinstance(model, RescorlaWagner):
        header = ['name', 'T', 'alpha gain', 'alpha lose', 'T0', 'alpha0', 'LLE', 'AIC', 'pR2']
    else:
        header = ['name', 'T', 'alpha', 'T0', 'alpha0', 'LLE', 'AIC', 'pR2']
    return header


def get_optimal_parameters(real_player):
    return real_player.get_optimized_parameters()


def get_optimal_parameters_and_starting_points(real_player):
    optimal_func_value = []
    optimal_params = []
    for start_points in get_possible_starting_points(real_player.model):
        max_loglikelihood = minimize(real_player.log_likelihood_function, x0=np.array(start_points),
                                     method='Nelder-Mead')
        optimal_func_value.append(max_loglikelihood.fun)
        optimal_params.append(max_loglikelihood.x)
    max_value_index = optimal_func_value.index(min(optimal_func_value))
    optimal_starting_points = get_possible_starting_points(real_player.model)[max_value_index]
    return optimal_params[max_value_index], optimal_starting_points


def get_possible_starting_points(model, T_interval=(1, 10, 0.1), alpha_interval=(0.1, 1, 0.05)):
    T_array = np.arange(*T_interval)
    if isinstance(model, RescorlaWagner):
        alpha_gain = np.arange(*alpha_interval)
        alpha_lose = np.arange(*alpha_interval)
        start_points_list = list(product(T_array, alpha_gain, alpha_lose))
    else:
        alpha_array = np.arange(*alpha_interval)
        start_points_list = list(product(T_array, alpha_array))
    return start_points_list


def make_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def round_number(number):
    return round(number, 2)
