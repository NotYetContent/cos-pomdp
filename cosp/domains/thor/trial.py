from sciex import Trial, Event
import ai2thor

class ThorTrial(Trial):

    RESULT_TYPES = []
    REQUIRED_CONFIGS = [
        "thor",
        ("thor", "scene")
    ]

    def __init__(self, name, config, verbose=False):
        super().__init__(self, name, config, verbose=verbose)

    def _start_controller(self):
        thor_config = self.config["thor"]
        controller = ai2thor.Controller(
            scene=thor_config["scene"],
            agentMode=thor_config["AGENT_MODE"],
            gridSize=thor_config["GRID_SIZE"],
            visibilityDistance=thor_config["VISIBILITY_DISTANCE"],
            snapToGrid=thor_config["SNAP_TO_GRID"],
            renderDepthImage=thor_config["RENDER_DEPTH"],
            renderInstanceSegmentation=thor_config["RENDER_INSTANCE_SEGMENTATION"],
            width=thor_config["IMAGE_WIDTH"],
            height=thor_config["IMAGE_HEIGHT"],
            fieldOfView=thor_config["FOV"],
            rotateStepDegrees=thor_config["H_ROTATION"],
            x_display=thor_config.get("x_display", None),
            host=thor_config.get("host", "127.0.0.1"),
            port=thor_config.get("port", 0),
            headless=thor_config.get("headless", False))
        return controller

    def run(self, logging=False):
        controller = self._start_controller()
        task_env = eval(self.config["task_env"])(controller, **self.config["task_env_config"])
        agent = eval(self.config["agent_class"])(**self.config["agent_config"])

        max_steps = self.config["max_steps"]
        for i in range(max_steps):
            action = agent.act()
            observation, reward = task_env.execute(action)
            agent.update(observation, reward)
            planner.update(observation, reward)

            _step_info = task_env.get_step_info(step=i)
            if logging:
                self.log_event(Event("Trial %s | %s" % (self.name, _step_info)))
            else:
                print(_step_info)

            if task_env.done():
                break
        results = task_env.compute_results()
        return results