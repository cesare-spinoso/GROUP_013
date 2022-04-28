"""
Best hyperparameters found for SAC after hyperparameter tuning
with the additional change in hyperparameters for gaming the
sample efficiency.
"""
import torch
import sklearn.model_selection


grid = [
    {
        "q_architecture": [(64, 64)],
        "q_activation_function": [torch.nn.ReLU],
        "policy_architecture": [(64, 64)],
        "policy_activation_function": [torch.nn.ReLU],
        "q_lr": [1e-2, 1e-3],
        "policy_lr": [1e-2, 1e-3],
        "alpha_lr": [3e-3, 3e-4],
        "update_alpha": [True],
        "exploration_timesteps": [100],
        "update_start_in_episodes": [100],
        "update_frequency_in_episodes": [1],
    },
    {
        "q_architecture": [(64, 64)],
        "q_activation_function": [torch.nn.ReLU],
        "policy_architecture": [(64, 64)],
        "policy_activation_function": [torch.nn.ReLU],
        "q_lr": [1e-3],
        "policy_lr": [1e-3],
        "alpha": [0.1, 0.2, 0.4, 0.8],
        "update_alpha": [False],
        "exploration_timesteps": [100],
        "update_start_in_episodes": [100],
        "update_frequency_in_episodes": [1],
    },
]

# Extra hyperparameter search w/ prioritized experience buffer
grid = [
    {
        "q_architecture": [(64, 64)],
        "q_activation_function": [torch.nn.ReLU],
        "policy_architecture": [(64, 64)],
        "policy_activation_function": [torch.nn.ReLU],
        "q_lr": [1e-3],
        "policy_lr": [1e-3],
        "alpha": [0.6, 0.7, 0.8, 0.9],
        "update_alpha": [None],
        "exploration_timesteps": [100],
        "update_start_in_episodes": [100],
        "update_frequency_in_episodes": [1],
        "replay_buffer_type": "uniform"
}

hyperparameter_grid = []
for i, params in enumerate(sklearn.model_selection.ParameterGrid(grid)):
    hyperparameter_grid.append(params)
