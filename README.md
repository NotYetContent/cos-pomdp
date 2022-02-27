# cos-pomdp

COS-POMDP is a POMDP.
This package defines that POMDP and a planner to solve it.
This package also includes instantiation of this POMDP to Ai2Thor for object search.

How should a POMDP project be developed?
You define the POMDP. Then, instantiate it on your domain.
Do all the necessary state (e.g. coordinate) conversions.
You create one or more planner given that POMDP.
Then, you have a POMDP and a solver for it!

## Organization
Contains two packages: `cospomdp` and `cospomdp_apps`.
The former defines the COS-POMDP (domain, models, agent, planner)
and the latter applies COS-POMDP to specific applications
such as ai2thor.


## Installation and Setup

### Requirements
* Ubuntu 18.04+
* Python 3.8+ 

Check out instructions to use the Dockerfile if you don't meet these requirements

### Setup Repo
Clone the repo:
```
git clone git@github.com:zkytony/cos-pomdp.git
```
After cloning do the following three commands separately.
```
source setup.bash
source setup.bash -I
source setup.bash -s
```

It is recommended to use a virtualenv with Python3.8+

To test if it is working: Do `pip install pytest` and then go to `tests/` folder and run
```
pytest
```
You are expected to see something like:
```
-- Docs: https://docs.pytest.org/en/stable/warnings.html
======= 14 passed, 2 skipped, 3 warnings in 43.71s ======
```

At this point, you should be able to run a basic object search domain with COS-POMDP. A
```
python -m cospomdp_apps.basic.search
```
pygame window will be displayed

### To Run in Ai2Thor 
(Skip this if you are running on a computer connected to a display) If you are running offline, or on a server, make sure there is an x server running.
You can do this by:
1. Creating the [`xorg_conf`](https://www.x.org/releases/current/doc/man/man5/xorg.conf.5.xhtml) file. (Check [this out](https://github.com/allenai/ai2thor/issues/886))
2. Then run:
```
sudo Xorg -noreset +extension GLX +extension RANDR +extension RENDER -config xorg_conf :0
```
Note that depending on your local configuration you may want to use something other than `:0`. If there is already an x server running at `:0` but your `$DISPLAY` shows nothing, you should run it at another display number.

Now, download necessary models by running the following script. This will download three files: `yolov5-training-data.zip`, `yolov5-detectors.zip`, `corrs.zip`, place them in the desired location and decompress them.
```
# run at repository root
python download.py
```

Then, main test we will run is
```
cd tests/thor
python test_vision_detector_search.py
```
This will run a search trial for AlarmClock in a bedroom scene. When everything works, you may see something like this:

<img src="https://user-images.githubusercontent.com/7720184/155869506-d7d1b8df-cb2b-43b9-9ca2-8da31ce6d9eb.png" width="800px">

Note that the search process may vary due to random sampling during planning.


Installation: see the Wiki page  ["Setting up COS POMDP project"](https://github.com/zkytony/cos-pomdp/wiki/Setting-up-COS-POMDP-project). This will install `cospomdp` which is the core code for the POMDP components,
and `cospomdp_apps` which contains application to the POMDP to several domains.
After installation is successful, you could test out the basic example:
```
python -m cospomdp_apps.basic.search
```

### Caveats
The external methods, e.g. SAVN, MJOLNIR, are placed under `cos-pomdp/external`.
However, for importability, a symbolic link to the `cos-pomdp/external/mjolnir`
directory is created under `cos-pomdp/cospomdp_apps/thor/mjolnir`. Please
make sure that link points to the right absolute path on your computer.
For example, you can directly create a new one by:
```
cd repo/cos-pomdp/cospomdp_apps/thor
ln -sf $HOME/repo/cos-pomdp/external/mjolnir/ mjolnir
```

**Note**: setup for SAVN, MJOLNIR etc. were attempted during the project; MJOLNIR can run but does not work well.


## AI2-Thor Setup

Compare with:
- [1] IQA (CVPR'18)
- [2] Visual Semantic Navigation Using Scene Priors (ICRL'19)
- [3] Learning hierarchical relationships for object-goal navigation (CoRL'20)
- [4] Hierarchical and Partially Observable Goal-driven Policy Learning with Goals
  Relational Graph (CVPR'21)


|                  | grid size | h_rotate | v_rotate | fov |
|------------------|-----------|----------|----------|-----|
| [1] IQA          | 0.25      | 90       | 30       | 60  |
| [2] Scene Priors | 0.25      | 45       | 30       | 90  |
| [3] MJONIR       | 0.25      | 45       | 30       | 100 |
| [4] HRL-GRG      | 0.25      | 90       | 30       | 90  |
| [5] ALFRED       | 0.25      | 90       | 15       | 90  |
| ours             | 0.25      | 45       | 30       | 90  |

Constants can be found in `cospomdp_apps/thor/constants.py`.


## Citation
```
@inproceedings{zheng2022towards,
  title={Towards Optimal Correlational Object Search,
  booktitle={IEEE International Conference on Robotics and Automation (ICRA)},
  author={Zheng, Kaiyu and Chitnis, Rohan and Sung, Yoonchang and Konidaris, George and Tellex, Stefanie},
  year={2022}
}
```
