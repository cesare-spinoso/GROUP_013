import argparse
import importlib

import os
from os import listdir
from os.path import isfile, join
from pathlib import Path
from copy import deepcopy


from utils.logging_utils import start_logging
from utils.json_utils import get_json_data

from utils.environment import get_environment
from utils.evaluation import evaluate_agent
from utils.metrics import calc_sample_efficiency


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--group", type=str, default="GROUP1", help="group directory")
    parser.add_argument(
        "--model_path",
        type=str,
        default="None",
        help="Relative path to model (without .pth.tar) with respect GROUP_13 directory",
    )
    parser.add_argument(
        "--json_path",
        type=str,
        default="None",
        help="Path to json file containing the paths of the models",
    )

    args = parser.parse_args()

    path = "./" + args.group + "/"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if ("agent.py" not in files) or ("env_info.txt" not in files):
        print("Your GROUP folder does not contain agent.py or env_info.txt!")
        exit()

    with open(path + "env_info.txt") as f:
        lines = f.readlines()
    env_type = lines[0].lower()

    env = get_environment(env_type)
    env_eval = get_environment(env_type)
    if "jellybean" in env_type:
        env_specs = {
            "scent_space": env.scent_space,
            "vision_space": env.vision_space,
            "feature_space": env.feature_space,
            "action_space": env.action_space,
        }
    if "mujoco" in env_type:
        env_specs = {
            "observation_space": env.observation_space,
            "action_space": env.action_space,
        }

    # starting a logger - results stored in folder labeled w/ date+time
    logger = start_logging(logger_name="evaluation")

    # load in the pretrained model if one is provided
    agent_pretrained = None
    agents_pretrained = None
    if args.model_path == "None" and args.json_path == "None":
        # Load untrained instance of the agent, will only evaluate sample efficiency
        agent_module = importlib.import_module(args.group + ".agent")
        agent_untrained = agent_module.Agent(env_specs)
    elif args.model_path != "None":
        agent_module = importlib.import_module(args.group + ".agent")
        # Load single agent (requires manually changing the parameters to the agent's constructor in the
        # next line), will evaluate average reward and sample efficiency
        agent_untrained = agent_module.Agent(env_specs)
        agent_pretrained = deepcopy(agent_untrained)
        agent_pretrained.load_weights(os.getcwd(), args.model_path)
        logger.log(f"Pretrained model loaded: {args.model_path}")
    else:
        # Load json file containing the paths of the models
        json_data = get_json_data(args.json_path)
        # Load the hyperparameters corresponding to the json file
        hyperparameter_module = importlib.import_module(args.group + ".hyperparameters")
        grid = hyperparameter_module.hyperparameter_grid
        # Load the different agents
        agent_module = importlib.import_module(args.group + ".agent")
        agents_untrained = [agent_module.Agent(env_specs, **params) for params in grid]
        agents_pretrained = [deepcopy(agent) for agent in agents_untrained]
        for agent_pretrained, json in zip(agents_pretrained, json_data):
            agent_pretrained.load_weights(
                os.path.join(os.getcwd(), args.group, "results"),
                Path(Path(json["path_to_best_model"]).stem).stem,
            )

    # "Out-of-sample" Evaluation
    n_episodes_to_evaluate_average_reward = 100

    # Sample efficiency
    num_seeds = 5
    total_timesteps = 100_000
    evaluation_freq = 1000
    n_episodes_to_evaluate_sample_efficiency = 20


    ########################################## evaluate a single/multiple model(s) ##########################################
    if agent_pretrained is None and agents_pretrained is None:
        logger.log("Evaluation starting ... ")
        # Calculate the sample efficiency
        logger.log(f"Training model for {num_seeds} seeds ...")
        sample_efficiency, time_to_train = calc_sample_efficiency(
            agent_untrained,
            env,
            env_eval,
            total_timesteps,
            evaluation_freq,
            n_episodes_to_evaluate_sample_efficiency,
            num_seeds,
            logger
        )
        logger.log(f"Sample efficiency: {sample_efficiency}")
        logger.log(f"Time to train: {time_to_train}")    
    elif agents_pretrained is None:
        logger.log("Evaluation starting ... ")
        # Calculate the sample efficiency
        logger.log(f"Retraining model for {num_seeds} seeds ...")
        sample_efficiency, time_to_train = calc_sample_efficiency(
            agent_untrained,
            env,
            env_eval,
            total_timesteps,
            evaluation_freq,
            n_episodes_to_evaluate_sample_efficiency,
            num_seeds,
            logger
        )
        # Calculate the average (out-of-sample) reward
        logger.log("Evaluating the average return of the pretrained model ... ")
        average_reward_per_episode = evaluate_agent(
            agent_pretrained, env_eval, n_episodes_to_evaluate_average_reward
        )
        logger.log(f"Average reward per episode: {average_reward_per_episode}")
        logger.log(f"Sample efficiency: {sample_efficiency}")
        logger.log(f"Time to train: {time_to_train}")
    else:
        logger.log("Evaluating the sample efficiency of the untrained agents ... ")
        sample_efficiencies = []
        times_to_train = []
        for agent_untrained, json in zip(agents_untrained, json_data):
            logger.log(f"Retraining {json['model_name']} for {num_seeds} seeds ...")
            sample_efficiency, time_to_train = calc_sample_efficiency(
                agent_untrained,
                env,
                env_eval,
                total_timesteps,
                evaluation_freq,
                n_episodes_to_evaluate_sample_efficiency,
                num_seeds,
                logger
            )
            sample_efficiencies.append(sample_efficiency)
            times_to_train.append(time_to_train)

        logger.log("Evaluating the average return of the pretrained models ... ")
        average_rewards_per_episode = []
        for agent, json in zip(agents_pretrained, json_data):
            logger.log(f"Average reward evaluation starting for ... {json['model_name']}") 
            average_reward_per_episode = evaluate_agent(
                agent, env_eval, n_episodes_to_evaluate_average_reward
            )
            average_rewards_per_episode.append(average_reward_per_episode)
        logger.log("Evaluation finished! Results ...")
        for sample_efficiency, time_to_train, average_reward_per_episode, json in zip(sample_efficiencies, times_to_train, average_rewards_per_episode, json_data):
            logger.log(f"Results for {json['model_name']}")
            logger.log(f"Sample efficiency: {sample_efficiency}")
            logger.log(f"Average time to train {total_timesteps} timesteps: {time_to_train}")
            logger.log(f"Average reward per episode: {average_reward_per_episode}")