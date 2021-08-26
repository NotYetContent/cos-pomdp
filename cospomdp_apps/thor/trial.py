# Generic class for experiment trial in thor
import sys
from sciex import Trial, Event
from ai2thor.controller import Controller
import thortils
import time

from cospomdp.utils.misc import _debug
from cospomdp.utils import cfg
cfg.DEBUG_LEVEL = 0

from .object_search import ThorObjectSearch
from .agent import (ThorObjectSearchOptimalAgent,
                    ThorObjectSearchCosAgent)
from .external import ThorObjectSearchExternalAgent
from .replay import ReplaySolver
from .result_types import PathResult, HistoryResult
from . import constants
from .common import make_config, TaskArgs

class ThorTrial(Trial):

    RESULT_TYPES = []

    def __init__(self, name, config, verbose=False):
        if self.__class__ == ThorTrial:
            raise ValueError("ThorTrial is generic. Please create the Trial object"\
                             "for your specific task!")
        super().__init__(name, config, verbose=verbose)

    def _start_controller(self):
        controller = thortils.launch_controller(self.config["thor"])
        return controller

    def run(self, logging=False, step_act_cb=None, step_update_cb=None):
        """
        Functions intended for debugging purposes:
            step_act_cb: Called after the agent has determined its action
            step_update_cb: Called after the agent has executed the action and updated
                given environment observation.
        """
        controller = self._start_controller()
        task_env = eval(self.config["task_env"])(controller, **self.config["task_env_config"])
        agent_class = eval(self.config["agent_class"])
        if agent_class.AGENT_USES_CONTROLLER:
            agent = agent_class(controller, **self.config["agent_config"])
        else:
            agent = agent_class(**self.config["agent_config"])

        if self.config.get("visualize", False):
            viz = task_env.visualizer(**self.config["viz_config"])
            viz.visualize(task_env, agent, step=0)

        max_steps = self.config["max_steps"]
        for i in range(1, max_steps+1):
            action = agent.act()
            if not logging:
                a_str = action.name if not action.name.startswith("Open")\
                    else "{}({})".format(action.name, action.params)
                sys.stdout.write(f"Step {i} | Action: {a_str}; ")
                sys.stdout.flush()
            if step_act_cb is not None:
                step_act_cb(task_env, agent)

            observation, reward = task_env.execute(agent, action)
            agent.update(action, observation)

            if logging:
                _step_info = task_env.get_step_info(step=i)
                self.log_event(Event("Trial %s | %s" % (self.name, _step_info)))
            else:
                sys.stdout.write("Observation: {}; Reward: {}\n".format(observation, reward))
                sys.stdout.flush()

            if self.config.get("visualize", False):
                viz.visualize(task_env, agent, step=i)

            if step_update_cb is not None:
                step_act_cb(task_env, agent)

            if task_env.done(action):
                success, msg = task_env.success(action)
                if logging:
                    self.log_event(Event("Trial %s | %s" % (self.name, msg)))
                else:
                    print(msg)
                break
        results = task_env.compute_results()
        controller.stop()
        return results

    @property
    def scene(self):
        return self.config["thor"]["scene"]


# ------------- Object search trial ------------- #
class ThorObjectSearchTrial(ThorTrial):
    RESULT_TYPES = [PathResult, HistoryResult]


def build_object_search_trial(scene, target, task_type,
                              max_steps=100):
    """
    Returns a ThorTrial for object search.
    """
    args = TaskArgs(scene=scene, target=target, detectables={target},
                    max_steps=max_steps)
    config = make_config(args)
    trial = ThorObjectSearchTrial("test_optimal", config, verbose=True)
    return trial
