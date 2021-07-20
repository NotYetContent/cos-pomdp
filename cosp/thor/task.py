from collections import namedtuple

import pomdp_py
import ai2thor
import ai2thor.util.metrics as metrics

from thortils import (thor_agent_pose,
                      thor_camera_horizon,
                      thor_object_position,
                      thor_object_in_fov,
                      thor_object_of_type_in_fov,
                      thor_closest_object_of_type)
from thortils.vision import thor_img, thor_img_depth, thor_object_bboxes
from thortils.navigation import (get_shortest_path_to_object,
                                 get_shortest_path_to_object_type)

from . import utils
from .result_types import PathsResult, HistoryResult
from .constants import TOS_REWARD_HI, TOS_REWARD_LO, TOS_REWARD_STEP
from ..framework import TaskEnv
from ..utils.math import euclidean_dist

class ThorEnv(TaskEnv):
    def __init__(self, controller):
        self.controller = controller
        self._history = []  # stores the (s', a, o, r) tuples so far
        self._init_state = self.get_state(self.controller)
        self._history.append((self._init_state, None, None, 0))

    @property
    def init_state(self):
        return self._init_state

    def get_step_info(self, step):
        raise NotImplementedError

    def execute(self, action):
        state = self.get_state(self.controller)
        event = self.controller.step(action=action.name, **action.params)
        self.controller.step(action="Pass")

        next_state = self.get_state(event)
        observation = self.get_observation(event)
        reward = self.get_reward(state, action, next_state)
        self._history.append((next_state, action, observation, reward))
        return (observation, reward)

    def done(self):
        raise NotImplementedError

    def get_state(self, event_or_controller):
        """Returns groundtruth state"""
        raise NotImplementedError

    def get_observation(self, event):
        """Returns groundtruth observation (i.e. correct object detections)"""
        raise NotImplementedError

    def get_reward(self, state, action, next_state):
        raise NotImplementedError

# ------------- Object Search ------------- #
class TOS(ThorEnv):
    """
    TOS is short for ThorObjectSearch
    This represents the environment of running a single object search task.
    """
    # State, Action, Observation used in object search task
    Action = namedtuple("Action", ['name', 'params'])
    State = namedtuple("State", ['agent_pose', 'horizon'])
    Observation = namedtuple("Observation", ["img", "img_depth", "bboxes"])

    def __init__(self, controller, task_config):
        """
        If task_type is "class", then target is an object type.
        If task_type is "object", then target is an object ID.
        """
        task_type = task_config["task_type"]
        target = task_config["target"]
        if task_type not in {"class", "object"}:
            raise ValueError("Invalid target type: {}".format(task_type))
        super().__init__(controller)
        self.target = target
        self.task_type = task_type
        self.goal_distance = task_config["goal_distance"]
        self.task_config = task_config

    def compute_results(self):
        """
        We will compute:
        1. Discounted cumulative reward
           Will save the entire trace of history.

        2. SPL. Even though our problem involves open/close,
           the optimal path should be just the navigation length,
           because the agent just needs to navigate to the container, open it
           and then perhaps look down, which doesn't change the path length.
           This metric alone won't tell the full story. Because it obscures the
           cost of actions that don't change the robot's location. So a combination with
           discounted reward is better.

           Because SPL is a metric over all trials, we will return the
           result for individual trials, namely, the path length, shortest path length,
           and success

        Note: it appears that the shortest path from ai2thor isn't snapped to grid,
        or it skips many steps. That makes it slightly shorter than the path found by
        our optimal agent. But will still use it per
        """
        init_position, init_rotation = self.init_state.agent_pose

        if self.task_type == "class":
            get_path_func = get_shortest_path_to_object_type
        else:
            get_path_func = get_shortest_path_to_object

        shortest_path = get_path_func(
            self.controller, self.target,
            init_position, init_rotation,
            positions_only=True,
            **self.task_config)

        actual_path = self.get_current_path()
        last_reward = self._history[-1][-1]
        success = last_reward == TOS_REWARD_HI
        return [PathsResult(shortest_path, actual_path, success),
                HistoryResult(self._history)]

    def get_current_path(self):
        """Returns a list of dict(x=,y=,z=) positions,
        using the history up to now, for computing results"""
        path = []
        for tup in self._history:
            state = tup[0]
            x, y, z = state.agent_pose[0]
            agent_position = dict(x=x, y=y, z=z)
            path.append(agent_position)
        return path

    def get_observation(self, event):
        img = thor_img(event)
        img_depth = thor_img(event)
        bboxes = thor_img(event)
        return TOS.Observation(img, img_depth, bboxes)

    def get_state(self, event):
        # stores agent pose as tuple, for convenience.
        agent_pose = thor_agent_pose(event, as_tuple=True)
        horizon = thor_camera_horizon(event)
        return TOS.State(agent_pose, horizon)

    def get_reward(self, state, action, next_state):
        """We will use a sparse reward."""
        if self.done(action):
            if self.success(action,
                            agent_pose=state.agent_pose,
                            horizon=state.horizon):
                return TOS_REWARD_HI
            else:
                return TOS_REWARD_LO
        else:
            return TOS_REWARD_STEP

    def done(self, action):
        """Returns true if  the task is over. The object search task is over when the
        agent took the 'Done' action.
        """
        return action.name == "Done"

    def success(self, action, agent_pose=None, horizon=None):
        """Returns True if the task is a success.
        The task is success if the agent takes 'Done' and
        (1) the target object is within the field of view.
        (2) the robot is close enough to the target.
        Note: uses self.controller to retrieve target object position."""
        if action.name != "Done":
            return False

        event = self.controller.step(action="Pass")
        backup_state = self.get_state(event)

        if agent_pose is not None:
            # Teleport to the given agent pose then evaluate
            position, rotation = agent_pose
            self.controller.step(action="Teleport",
                                 position=position,
                                 rotation=rotation,
                                 horizon=horizon)

        # Check if the target object is within the field of view
        event = self.controller.step(action="Pass")
        if self.task_type == "class":
            object_type = self.target
            in_fov = thor_object_of_type_in_fov(event, object_type)
            p = thor_closest_object_of_type(event, object_type)["position"]
            objpos = (p['x'], p['y'], p['z'])
        else:
            object_id = self.target
            in_fov = thor_object_of_type_in_fov(event, object_id)
            objpos = thor_object_position(event, object_id, as_tuple=True)

        agent_position = thor_agent_pose(event, as_tuple=True)[0]
        object_distance = euclidean_dist(objpos, agent_position)
        close_enough = object_distance <= self.goal_distance
        success = in_fov and close_enough

        # Teleport back, if necessary (i.e. if agent_pose is provided)
        if agent_pose is not None:
            position, rotation = backup_state.agent_pose
            horizon = backup_state.horizon
            self.controller.step(action="Teleport",
                                 position=position,
                                 rotation=rotation,
                                 horizon=horizon)
        if not success:
            if not in_fov:
                print("Object not in field of view!")
            if not close_enough:
                print("Object not close enough! Minimum distance: {}; Actual distance: {}".\
                      format(self.goal_distance, object_distance))
        return success

    def get_step_info(self, step):
        sp, a, o, r = self._history[step]
        return "Step {}: Action: {}, Reward: {}".format(step, a.name, r)


# Class naming aliases
ThorObjectSearch = TOS