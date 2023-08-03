"""
Simple script to test visualization wrapper in robosuite.
"""
import argparse
import imageio
import numpy as np

import robosuite
from robosuite.wrappers import VisualizationWrapper


VIDEO_PATH = None
# VIDEO_PATH = "test.mp4"


def make_env():
    robosuite_args = dict(
        robots="Panda",
        use_camera_obs=False,
        reward_shaping=False,
        has_renderer=(VIDEO_PATH is None),
        has_offscreen_renderer=(VIDEO_PATH is not None),
        control_freq=20,
        ignore_done=True,
    )

    # OSC controller spec
    controller_args = dict(
        type="OSC_POSE",
        input_max=1,
        input_min=-1,
        output_max=[0.05, 0.05, 0.05, 0.5, 0.5, 0.5],
        output_min=[-0.05, -0.05, -0.05, -0.5, -0.5, -0.5],
        kp=150,
        damping=1,
        impedance_mode="fixed",
        kp_limits=[0, 300],
        damping_limits=[0, 10],
        position_limits=None,
        orientation_limits=None,
        uncouple_pos_ori=True,
        control_delta=True,
        interpolation=None,
        ramp_ratio=0.2
    )
    robosuite_args["controller_configs"] = controller_args

    env = robosuite.make("Stack", **robosuite_args)
    return env


if __name__ == "__main__":
    # make environment
    env = make_env()

    # wrap environment with visualization wrapper with some visualization sites
    ic = [
        {
            "type": "sphere",
            "size": [0.01],
            "rgba": [1, 1, 0, 1],
            "name": "site{}".format(i),
        }
        for i in range(8)
    ]
    half_extent = 0.025
    bb_rel = np.array(
        [
            [half_extent, half_extent, half_extent],
            [half_extent, half_extent, -half_extent],
            [half_extent, -half_extent, half_extent],
            [half_extent, -half_extent, -half_extent],
            [-half_extent, half_extent, half_extent],
            [-half_extent, half_extent, -half_extent],
            [-half_extent, -half_extent, half_extent],
            [-half_extent, -half_extent, -half_extent],
        ]
    )
    env = VisualizationWrapper(env, indicator_configs=ic)

    # reset
    env.reset()

    # set visualization site locations
    for i in range(8):
        env.set_indicator_pos("site{}".format(i), env._get_observations(force_update=True)["cubeA_pos"] + bb_rel[i])
        env.sim.forward()
    print(env.get_indicator_names())

    num_steps = 1000
    if VIDEO_PATH is not None:
        video_writer = imageio.get_writer(VIDEO_PATH, fps=20)
        num_steps = 100

    low, high = env.action_spec
    for _ in range(num_steps):
        if VIDEO_PATH is None:
            env.render()
        else:
            im = np.array(env.sim.render(height=512, width=512, camera_name="agentview")[::-1])
            video_writer.append_data(im)
        action = np.random.uniform(low, high)
        env.step(action)

    if VIDEO_PATH is not None:
        video_writer.close()

    from IPython import embed
    embed()