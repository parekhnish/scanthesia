import sys
import traceback

import numpy as np
from skimage.color import rgb2gray
from skimage.filters import threshold_otsu


DEFAULT_BIN_THRESH_METHOD = "otsu"


def crop_frame(full_frame,
               top_row=None,
               bottom_row=None,
               left_col=None,
               right_col=None):

    frame_shape = full_frame.shape
    orig_num_rows = frame_shape[0]
    orig_num_cols = frame_shape[1]

    if top_row is None:
        top_row = 0
    if bottom_row is None:
        bottom_row = orig_num_rows

    if top_row < 0 or top_row >= orig_num_rows:
        raise Exception("Frame crop: top row {} outside limits: [0, {}]".format(top_row, orig_num_rows-1))
    if bottom_row < 1 or bottom_row > orig_num_rows:
        raise Exception("Frame crop: bottom row {} outside limits: [1, {}]".format(bottom_row, orig_num_rows))
    if (bottom_row - top_row) < 1:
        raise Exception("Frame crop: bottom row {} should be at least one more than top row {}".format(bottom_row, top_row))



    if left_col is None:
        left_col = 0
    if right_col is None:
        right_col = orig_num_cols

    if left_col < 0 or left_col >= orig_num_cols:
        raise Exception("Frame crop: left column {} outside limits: [0, {}]".format(left_col, orig_num_cols-1))
    if right_col < 1 or right_col > orig_num_cols:
        raise Exception("Frame crop: right column {} outside limits: [1, {}]".format(right_col, orig_num_cols))
    if (right_col - left_col) < 1:
        raise Exception("Frame crop: right column {} should be at least one more than left column {}".format(right_col, left_col))

    cropped_frame = full_frame[top_row: bottom_row, left_col: right_col]

    return cropped_frame


def convert_frame_to_grayscale(frame):

    try:
        gray_frame = rgb2gray(frame)

        # If input frame was 2-D, it was already grayscale.
        if frame.ndim == 2:

            # If input frame was boolean, scale to uint8;
            # If not, the rgb2gray() return value is unchanged
            if frame.dtype == np.bool:
                gray_frame = gray_frame.astype("uint8") * 255


        # Else, it means rgb2gray() returned a grayscale image in the range [0, 1]
        # Thus, perform scaling to uint8
        else:
            gray_frame = (gray_frame * 255).astype("uint8")

    except Exception:
        raise sys.exc_info()

    return gray_frame


def binarise_frame(frame,
                   thresh):

    if frame.ndim > 2:
        gray_frame = convert_frame_to_grayscale(frame)
    else:
        gray_frame = frame

    return gray_frame > thresh
