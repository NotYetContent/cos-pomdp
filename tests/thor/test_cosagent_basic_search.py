import thortils

from cospomdp.utils.corr_funcs import around
from cospomdp_apps.thor.common import TaskArgs, make_config
from cospomdp_apps.thor.trial import ThorObjectSearchTrial

__all__ = ['_test_basic_search']

def _test_basic_search(target,
                       other,
                       prior='uniform',
                       scene="FloorPlan1",
                       dist=3,
                       target_range=5,
                       other_range=6,
                       target_accuracy=0.7,
                       other_accuracy=0.8,
                       max_depth=30,
                       num_sims=500,
                       max_steps=100,
                       discount_factor=0.95,
                       exploration_const=100,
                       show_progress=True,
                       step_act_cb=None,
                       step_act_args={},
                       step_update_cb=None):
    print("Test cospomdp_basic search (prior={})".format(prior))
    detectables = [target]
    if other is not None:
        detectables.append(other)

    agent_init_inputs = ['grid_map', 'agent_pose']
    if prior == "informed":
        agent_init_inputs.append('groundtruth_prior')

    detector_specs = {
        target: ("fan-nofp", dict(fov=90, min_range=1, max_range=target_range), (target_accuracy, 0.1))
    }
    corr_specs = {}
    if other is not None:
        corr_specs[(target, other)] = (around, dict(d=dist))
        detector_specs[other] =\
            ("fan-nofp", dict(fov=90, min_range=1, max_range=other_range), (other_accuracy, 0.1))

    args = TaskArgs(detectables=detectables,
                    scene='FloorPlan1',
                    target=target,
                    agent_class="ThorObjectSearchBasicCosAgent",
                    task_env="ThorObjectSearch",
                    max_steps=max_steps,
                    agent_init_inputs=agent_init_inputs,
                    agent_detector_specs=detector_specs,
                    corr_specs=corr_specs)
    config = make_config(args)

    config["agent_config"]["solver"] = "pomdp_py.POUCT"
    config["agent_config"]["solver_args"] = dict(max_depth=max_depth,
                                                 num_sims=num_sims,
                                                 discount_factor=discount_factor,
                                                 exploration_const=exploration_const,
                                                 show_progress=show_progress)
    config["visualize"] = True
    config["viz_config"] = {
        'res': 30
    }
    trial = ThorObjectSearchTrial("test_cosagent-basic", config, verbose=True)
    print("Trial created")
    trial.run(step_act_cb=step_act_cb,
              step_act_args=step_act_args,
              step_update_cb=step_update_cb)


if __name__ == "__main__":
    _test_basic_search('Bowl', 'Book')
