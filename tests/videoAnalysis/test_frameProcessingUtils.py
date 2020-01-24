import os

import pytest

import numpy as np
from skimage.color import rgb2gray
from imageio import imread

from ...src.videoAnalysis.frameProcessingUtils import (crop_frame,
                                                       convert_frame_to_grayscale,
                                                       binarise_frame)


def test_regular_crop_frame(root_data_dir):

    input_frame = imread(os.path.join(root_data_dir, "frames",
                                      "marioverehrer_minecraft_frame_0300.png"))


    # --------------------------------------------------------------------------
    # Declare some values to be reused
    top_bound = 50
    bottom_bound = 500
    left_bound = 90
    right_bound = 360

    # Crop from all sides
    cf = crop_frame(input_frame,
                    top_row=top_bound, bottom_row=bottom_bound,
                    left_col=left_bound, right_col=right_bound)
    assert np.all(cf == input_frame[top_bound: bottom_bound,
                                    left_bound: right_bound, :])

    # Crop only vertically
    cf = crop_frame(input_frame, top_row=top_bound, bottom_row=bottom_bound)
    assert np.all(cf == input_frame[top_bound: bottom_bound, :, :])

    # Crop only horizontally
    cf = crop_frame(input_frame, left_col=left_bound, right_col=right_bound)
    assert np.all(cf == input_frame[:, left_bound: right_bound, :])

    # Don't crop at all
    cf = crop_frame(input_frame)
    assert np.all(cf == input_frame)


    # Confirm floating-point image crop
    fp_frame = input_frame.astype("float")
    fp_cf = crop_frame(fp_frame,
                       top_row=top_bound, bottom_row=bottom_bound,
                       left_col=left_bound, right_col=right_bound)
    assert np.all(fp_cf == fp_frame[top_bound: bottom_bound,
                                    left_bound: right_bound, :])

    # Confirm grayscale image crop
    gray_frame = (rgb2gray(input_frame) * 255).astype("int")
    gray_cf = crop_frame(gray_frame,
                         top_row=top_bound, bottom_row=bottom_bound,
                         left_col=left_bound, right_col=right_bound)
    assert np.all(gray_cf == gray_frame[top_bound: bottom_bound,
                                        left_bound: right_bound])

    # Confirm grayscale image crop
    binary_frame = gray_frame > 90
    binary_cf = crop_frame(binary_frame,
                           top_row=top_bound, bottom_row=bottom_bound,
                           left_col=left_bound, right_col=right_bound)
    assert np.all(binary_cf == binary_frame[top_bound: bottom_bound,
                                            left_bound: right_bound])
    # --------------------------------------------------------------------------

    return


def test_irregular_crop_frame(root_data_dir):

    input_frame = imread(os.path.join(root_data_dir, "frames",
                                      "marioverehrer_minecraft_frame_0300.png"))

    # --------------------------------------------------------------------------
    # Gather some image data
    orig_num_rows = input_frame.shape[0]
    orig_num_cols = input_frame.shape[1]


    # top bound beyond 0
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, top_row=-2)

    # top bound as last row + 1
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, top_row=orig_num_rows)

    # bottom bound as 0
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, bottom_row=0)

    # bottom bound beyond last row + 1
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, bottom_row=orig_num_rows+1)

    # top bound == bottom bound
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, top_row=50, bottom_row=50)

    # top bound beyond bottom bound
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, top_row=50, bottom_row=49)



    # left bound beyond 0
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, left_col=-2)

    # left bound as last col + 1
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, left_col=orig_num_cols)

    # right bound as 0
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, right_col=0)

    # right bound beyond last col + 1
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, right_col=orig_num_cols + 1)

    # left bound == right bound
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, left_col=50, right_col=50)

    # left bound beyond right bound
    with pytest.raises(Exception):
        _ = crop_frame(input_frame, left_col=50, right_col=49)
    # --------------------------------------------------------------------------

    return


def test_convert_to_grayscale(root_data_dir):

    input_frame = imread(os.path.join(root_data_dir, "frames",
                                      "marioverehrer_minecraft_frame_0300.png"))

    # --------------------------------------------------------------------------
    # Regular convert
    expected_gray_frame = (rgb2gray(input_frame) * 255).astype("uint8")
    converted_color_to_gray_frame = convert_frame_to_grayscale(input_frame)
    assert converted_color_to_gray_frame.dtype == "uint8"
    assert np.all(converted_color_to_gray_frame == expected_gray_frame)

    # Grayscale input
    converted_gray_to_gray_frame = convert_frame_to_grayscale(expected_gray_frame)
    assert converted_gray_to_gray_frame.dtype == "uint8"
    assert np.all(converted_gray_to_gray_frame == expected_gray_frame)

    # Binary input
    binary_frame = expected_gray_frame > 90
    expected_binary_gray_frame = binary_frame.astype("uint8") * 255
    converted_binary_to_gray_frame = convert_frame_to_grayscale(expected_binary_gray_frame)
    assert converted_binary_to_gray_frame.dtype == "uint8"
    assert np.all(converted_binary_to_gray_frame == expected_binary_gray_frame)
    # --------------------------------------------------------------------------

    return


def test_binarise_frame(root_data_dir):

    input_frame = imread(os.path.join(root_data_dir, "frames",
                                      "marioverehrer_minecraft_frame_0300.png"))

    # --------------------------------------------------------------------------
    # Define a threshold
    thresh = 90

    # Create expected binary frame
    gray_frame = (rgb2gray(input_frame) * 255).astype("uint8")
    bin_frame = gray_frame > thresh

    # Binarise color frame
    color_to_bin_frame = binarise_frame(input_frame, thresh=thresh)
    assert np.all(color_to_bin_frame == bin_frame)

    # Binarise gray frame
    gray_to_bin_frame = binarise_frame(gray_frame, thresh=thresh)
    assert np.all(gray_to_bin_frame == bin_frame)
    # --------------------------------------------------------------------------

    return
