import os
import math

import pytest
import numpy as np

from ...src.dataIO.videoIO import VideoReader, VideoSampler


def test_vid_reader_metadata(root_data_dir):
    # -------------------------------------------------------------------------
    # Erroneous initialisation
    with pytest.raises(Exception):
        _ = VideoReader("file_not_present.webm")
    # -------------------------------------------------------------------------


    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")

    # Open File
    vid_reader = VideoReader(input_video_filename)
    assert not vid_reader.video_reader.closed

    # -------------------------------------------------------------------------
    # Assert metadata
    assert vid_reader.frame_height == 720
    assert vid_reader.frame_width == 1274
    assert math.isclose(vid_reader.vid_fps, 30.0)
    assert math.isclose(vid_reader.vid_duration_time, 131.73)
    assert vid_reader.vid_num_frames == 3952

    # Assert curr_* variables
    assert vid_reader.curr_frame_index == -1
    assert math.isclose(vid_reader.curr_time_instant, -1.0)
    # -------------------------------------------------------------------------

    # Close File
    vid_reader.close_reader()
    assert vid_reader.video_reader.closed

    return


def test_vid_reader_random_access(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_reader = VideoReader(input_video_filename)

    # --------------------------------------------------------------------------
    # Test get_frame_by_index
    s1, f1 = vid_reader.get_frame_by_index(120)
    assert s1
    assert vid_reader.curr_frame_index == 120
    assert math.isclose(vid_reader.curr_time_instant, 4.0)

    # Test get_frame_by_time
    s2, f2 = vid_reader.get_frame_by_time(4.0)
    assert s2
    assert vid_reader.curr_frame_index == 120
    assert math.isclose(vid_reader.curr_time_instant, 4.0)

    # Test that both frames are the same
    assert np.all(f1 == f2)
    # --------------------------------------------------------------------------

    vid_reader.close_reader()
    return


def test_vid_reader_illegal_access(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_reader = VideoReader(input_video_filename)

    # --------------------------------------------------------------------------
    # Frame index more than max
    with pytest.warns(Warning):
        s, f = vid_reader.get_frame_by_index(3952)
        assert (not s)
        assert (f is None)

    # Frame index below 0
    with pytest.warns(Warning):
        s, f = vid_reader.get_frame_by_index(-1)
        assert (not s)
        assert (f is None)

    # Frame index as floating point number
    with pytest.raises(Exception):
        _, f = vid_reader.get_frame_by_index(4.2)

    # Frame time below 0
    with pytest.warns(Warning):
        s, f = vid_reader.get_frame_by_time(-0.1)
        assert (not s)
        assert (f is None)

    # Frame time above max time
    with pytest.warns(Warning):
        s, f = vid_reader.get_frame_by_time(131.75)
        assert (not s)
        assert (f is None)
    # --------------------------------------------------------------------------

    vid_reader.close_reader()
    return


def test_vid_reader_advancing_access(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_reader = VideoReader(input_video_filename)

    # --------------------------------------------------------------------------
    # Increment by one frame
    s, f_start = vid_reader.get_frame_by_index(120)
    s, f_plus_1 = vid_reader.advance_frame_by_index()
    assert vid_reader.curr_frame_index == 121

    # Increment by four more frames
    s, f_plus_5 = vid_reader.advance_frame_by_index(increment=4)
    assert vid_reader.curr_frame_index == 125

    assert not np.all(f_start == f_plus_1)
    assert not np.all(f_plus_1 == f_plus_5)

    # Increment by one second
    s, f_start = vid_reader.get_frame_by_time(4.0)
    s, f_plus_1 = vid_reader.advance_frame_by_time()
    assert math.isclose(vid_reader.curr_time_instant, 5.0)

    # Increment by four more seconds
    s, f_plus_5 = vid_reader.advance_frame_by_time(increment=4.0)
    assert math.isclose(vid_reader.curr_time_instant, 9.0)

    assert not np.all(f_start == f_plus_1)
    assert not np.all(f_plus_1 == f_plus_5)
    # --------------------------------------------------------------------------

    vid_reader.close_reader()
    return








def test_vid_sampler_metadata(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_sampler = VideoSampler(input_video_filename)

    # -------------------------------------------------------------------------
    # Check initialised variables
    assert not vid_sampler.is_sampling_generated
    assert vid_sampler.start_frame is None
    assert vid_sampler.start_time is None
    assert vid_sampler.end_frame is None
    assert vid_sampler.end_time is None
    assert vid_sampler.sample_step is None
    assert vid_sampler.sample_time_diff is None
    assert vid_sampler.num_samples is None
    assert vid_sampler.curr_sample_index is None
    # -------------------------------------------------------------------------

    vid_sampler.close_sampler()

    return


def test_vid_sampler_gen_sampling_normal(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_sampler = VideoSampler(input_video_filename)

    # ------------------------------------------------------------------------
    # Default sampling using frame_indices()
    vid_sampler.gen_sampling_schedule_using_frame_indices()
    assert vid_sampler.is_sampling_generated
    assert vid_sampler.start_frame == 0
    assert math.isclose(vid_sampler.start_time, 0.0)
    assert vid_sampler.end_frame == 3930
    assert math.isclose(vid_sampler.end_time, 131.0)
    assert vid_sampler.sample_step == 30
    assert math.isclose(vid_sampler.sample_time_diff, 1.0)
    assert vid_sampler.num_samples == 132
    assert vid_sampler.curr_sample_index is None

    # Default sampling using time()
    vid_sampler.gen_sampling_schedule_using_time()
    assert vid_sampler.is_sampling_generated
    assert vid_sampler.start_frame == 0
    assert math.isclose(vid_sampler.start_time, 0.0)
    assert vid_sampler.end_frame == 3930
    assert math.isclose(vid_sampler.end_time, 131.0)
    assert vid_sampler.sample_step == 30
    assert math.isclose(vid_sampler.sample_time_diff, 1.0)
    assert vid_sampler.num_samples == 132
    assert vid_sampler.curr_sample_index is None

    # Sampling using arguments for frame_indices()
    vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=120, end_frame=740,
                                                          samples_per_second=2)
    assert vid_sampler.start_frame == 120
    assert math.isclose(vid_sampler.start_time, 4.0)
    assert vid_sampler.sample_step == 15
    assert math.isclose(vid_sampler.sample_time_diff, 0.5)
    assert vid_sampler.num_samples == 42
    assert vid_sampler.end_frame == 735
    assert math.isclose(vid_sampler.end_time, 24.5)

    # Sampling using arguments for time()
    vid_sampler.gen_sampling_schedule_using_time(start_time=1.5, end_time=4.5,
                                                 samples_per_second=10)
    assert math.isclose(vid_sampler.start_time, 1.5)
    assert vid_sampler.start_frame == 45
    assert vid_sampler.sample_step == 3
    assert math.isclose(vid_sampler.sample_time_diff, 0.1)
    assert vid_sampler.num_samples == 31
    assert vid_sampler.end_frame == 135
    assert math.isclose(vid_sampler.end_time, 4.5)

    # Sampling with reset_sample_index = True (default)
    _, _ = vid_sampler.get_sample_by_index(3)
    assert vid_sampler.curr_sample_index == 3
    vid_sampler.gen_sampling_schedule_using_frame_indices(reset_sample_index=True)
    assert vid_sampler.curr_sample_index is None

    # Sampling with reset_sample_index = False, new sampling start much closer
    # to current sample index
    _, _ = vid_sampler.get_sample_by_index(2)
    assert vid_sampler.curr_frame_index == 60
    vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=50,
                                                          samples_per_second=2,
                                                          reset_sample_index=False)
    assert vid_sampler.curr_frame_index == 60
    assert math.isclose(vid_sampler.curr_sample_index, 10.0/15.0)

    # Sampling with reset_sample_index = False, new sampling start at a frame
    # after frame at current sample index
    vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=80,
                                                          samples_per_second=2,
                                                          reset_sample_index=False)
    assert vid_sampler.curr_frame_index == 60
    assert math.isclose(vid_sampler.curr_sample_index, -20.0 / 15.0)

    # Sampling with reset_sample_index = False, new sampling ends before frame
    # at current sample index
    vid_sampler.gen_sampling_schedule_using_frame_indices(end_frame=30,
                                                          samples_per_second=2,
                                                          reset_sample_index=False)
    assert vid_sampler.curr_frame_index == 60
    assert vid_sampler.curr_sample_index == 4
    # ------------------------------------------------------------------------

    # Close File
    vid_sampler.close_sampler()

    return


def test_vid_sampler_iterator(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_sampler = VideoSampler(input_video_filename)

    # -------------------------------------------------------------------------
    # 1) Generate sampling
    vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=20, end_frame=120,
                                                          samples_per_second=2,
                                                          reset_sample_index=True)

    # 2) Make the array of expected sample indices when iterating
    expected_index_arr = np.arange(vid_sampler.num_samples).astype("int")

    # 3) Actually iterate, and record the indices
    index_list = []
    for _ in vid_sampler:
        index_list.append(vid_sampler.curr_sample_index)
    run_index_arr = np.array(index_list)

    # 4) Assert that expected indices match the indices recorded
    assert np.all(expected_index_arr == run_index_arr)
    # -------------------------------------------------------------------------

    vid_sampler.close_sampler()

    return


def test_vid_sampler_gen_sampling_abnormal(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_sampler = VideoSampler(input_video_filename)

    # -------------------------------------------------------------------------
    # Float start frame
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=0.5)

    # Start frame < 0
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=-1.0)

    # Start frame >= max num frames
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=3953)

    # sps not a number
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(samples_per_second=None)

    # sps <= 0
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(samples_per_second=0)

    # sps > fps
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(samples_per_second=31)

    # Float end frame
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(end_frame=2.5)

    # End frame < start frame
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=60, end_frame=55)

    # End frame >= max num frames
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_frame_indices(end_frame=3953)


    # Non-numerical start time
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_time(start_time="4.0")

    # Start time < 0
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_time(start_time=-1.0)

    # Start time >= Max time
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_time(start_time=132.0)

    # Non-numerical end time
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_time(end_time="4.0")

    # End time < start time
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_time(start_time=4.0, end_time=3.9)

    # End time >= Max time
    with pytest.raises(Exception):
        vid_sampler.gen_sampling_schedule_using_time(end_time=132.0)
    # -------------------------------------------------------------------------

    vid_sampler.close_sampler()

    return


def test_vid_sampler_get_sample(root_data_dir):
    input_video_filename = os.path.join(root_data_dir, "videos",
                                        "marioverehrer_minecraft.mp4")
    vid_sampler = VideoSampler(input_video_filename)

    # -------------------------------------------------------------------------
    # Abnormal - next() without gen sampling
    with pytest.warns(Warning):
        _, _ = vid_sampler.get_next_sample()

    # Abnormal - sample_by_index() without gen sampling
    with pytest.warns(Warning):
        _, _ = vid_sampler.get_sample_by_index(sample_index=5)

    # From the start
    vid_sampler.gen_sampling_schedule_using_frame_indices()
    assert vid_sampler.curr_sample_index is None
    s, _ = vid_sampler.get_next_sample()
    assert s
    assert vid_sampler.curr_sample_index == 0
    assert vid_sampler.curr_frame_index == 0

    s, _ = vid_sampler.get_next_sample()
    assert s
    assert vid_sampler.curr_sample_index == 1
    assert vid_sampler.curr_frame_index == 30

    # Float sampling
    s, _ = vid_sampler.get_sample_by_index(4.2)
    assert s
    assert math.isclose(vid_sampler.curr_sample_index, 4.2)
    assert vid_sampler.curr_frame_index == 126

    # Next sample after float curr_sample_index
    s, _ = vid_sampler.get_next_sample()
    assert s
    assert vid_sampler.curr_sample_index == 5
    assert vid_sampler.curr_frame_index == 150

    # Sampling outside the subset range
    with pytest.warns(Warning):
        s, _ = vid_sampler.get_sample_by_index(132)
        assert not s

    with pytest.warns(Warning):
        s, _ = vid_sampler.get_sample_by_index(-2)
        assert not s

    # Sampling from before the first sample
    _, _ = vid_sampler.get_sample_by_index(5)
    vid_sampler.gen_sampling_schedule_using_frame_indices(start_frame=160,
                                                          reset_sample_index=False)
    s, _ = vid_sampler.get_next_sample()
    assert s
    assert vid_sampler.curr_sample_index == 0
    assert vid_sampler.curr_frame_index == 160

    # Sampling without update
    s, _ = vid_sampler.get_sample_by_index(2, update_curr_sample_index=False)
    assert s
    assert vid_sampler.curr_sample_index == 0
    assert vid_sampler.curr_frame_index == 220
    s, _ = vid_sampler.get_next_sample()
    assert s
    assert vid_sampler.curr_sample_index == 1
    assert vid_sampler.curr_frame_index == 190
    # -------------------------------------------------------------------------

    vid_sampler.close_sampler()

    return
