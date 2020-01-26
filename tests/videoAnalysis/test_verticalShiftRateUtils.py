import os

import pytest

from imageio import imread

from ...src.dataIO.videoIO import VideoSampler
from ...src.videoAnalysis.verticalShiftRateUtils import (_get_bin_cropped_frame,
                                                         calc_shift,
                                                         find_vertical_shift_rate)


def test_calc_shift(root_data_dir):
    input_prev_frame = imread(os.path.join(root_data_dir, "frames",
                                           "marioverehrer_minecraft_frame_0300.png"))

    input_curr_frame = imread(os.path.join(root_data_dir, "frames",
                                           "marioverehrer_minecraft_frame_0315.png"))

    top_bound = 15
    bottom_bound = 550
    left_bound = None
    right_bound = None
    bin_thresh = 90

    # --------------------------------------------------------------------------
    # Compute bin cropped prev frame
    bin_cropped_prev_frame = _get_bin_cropped_frame(input_prev_frame,
                                                    top_bound=top_bound, bottom_bound=bottom_bound,
                                                    left_bound=left_bound, right_bound=right_bound,
                                                    bin_thresh=bin_thresh)

    # Compute bin cropped prev frame
    bin_cropped_curr_frame = _get_bin_cropped_frame(input_curr_frame,
                                                    top_bound=top_bound, bottom_bound=bottom_bound,
                                                    left_bound=left_bound, right_bound=right_bound,
                                                    bin_thresh=bin_thresh)

    # Compute shift between the two frames
    curr_shift = calc_shift(bin_cropped_prev_frame, bin_cropped_curr_frame)

    assert curr_shift == 86
    # --------------------------------------------------------------------------

    return


def test_find_vertical_shift_rate(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")

    top_bound = 15
    bottom_bound = 550
    left_bound = None
    right_bound = None
    bin_thresh = 90

    # --------------------------------------------------------------------------
    # (1): Definite shift rate found
    vid_sampler = VideoSampler(input_video_filename)
    vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=300, end_frame=1200,
                                                          samples_per_second=2)

    with pytest.warns(None) as warn_list:
        vertical_shift_rate = find_vertical_shift_rate(vid_sampler,
                                                       top_bound=top_bound, bottom_bound=bottom_bound,
                                                       left_bound=left_bound, right_bound=right_bound,
                                                       bin_thresh=bin_thresh,
                                                       num_shift_count_threshold=10)

    assert not warn_list
    assert vertical_shift_rate == 86

    vid_sampler.close_sampler()



    # (2): Definite shift rate not found, closest contender returned
    vid_sampler = VideoSampler(input_video_filename)
    vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=300, end_frame=420,
                                                          samples_per_second=2)

    with pytest.warns(Warning):
        vertical_shift_rate = find_vertical_shift_rate(vid_sampler,
                                                       top_bound=top_bound, bottom_bound=bottom_bound,
                                                       left_bound=left_bound, right_bound=right_bound,
                                                       bin_thresh=bin_thresh,
                                                       num_shift_count_threshold=20)

    assert vertical_shift_rate == 86

    vid_sampler.close_sampler()
    # --------------------------------------------------------------------------

    return
