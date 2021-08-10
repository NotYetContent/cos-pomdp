from collections import namedtuple
from ..framework import TaskEnv, Agent

# State, Action, Observation used in object search task
TOS_Action = namedtuple("Action", ['name', 'params'])
TOS_State = namedtuple("State", ['agent_pose', 'horizon'])
TOS_Observation = namedtuple("Observation", ["img", "img_depth", "detections"])

# Generic classes for task and agent in Thor environments.
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

    def execute(self, agent, action):
        state = self.get_state(self.controller)
        event = self.controller.step(action=action.name, **action.params)
        self.controller.step(action="Pass")

        next_state = self.get_state(event)
        observation = self.get_observation(event, detector=agent.detector)
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

    def visualizer(self, **config):
        raise NotImplementedError


class ThorAgent(Agent):
    @property
    def detector(self):
        return None