# Note:
from cosp.thor.trial import ThorTrial
from cosp.thor import constants


def test_out_optimal_agent():
    target = "Apple"
    task_type = "class"

    thor_config = {**constants.CONFIG, **{"scene": "FloorPlan1"}}
    config = {
        "thor": thor_config,
        "max_steps": 100,
        "task_env": "ThorObjectSearch",
        "task_env_config": {
            "task_type": task_type,
            "target": target,
            "goal_distance": constants.GOAL_DISTANCE
        },
        "agent_class": "ThorObjectSearchOptimalAgent",
        "agent_config": {}
    }

    trial = ThorTrial("test_optimal", config, verbose=True)
    trial.run(logging=True)


if __name__ == "__main__":
    test_out_optimal_agent()
