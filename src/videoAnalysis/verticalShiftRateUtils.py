import warnings

import numpy as np

from .frameProcessingUtils import (crop_frame,
                                   convert_frame_to_grayscale,
                                   binarise_frame)

DEFAULT_BINARY_THRESH = 90
DEFAULT_NUM_SHIFT_COUNT_THRESHOLD = 10


def _get_bin_cropped_frame(full_frame,
                           top_bound, bottom_bound,
                           left_bound, right_bound,
                           bin_thresh):

    # Crop Frame
    cropped_frame = crop_frame(full_frame,
                               top_row=top_bound, bottom_row=bottom_bound,
                               left_col=left_bound, right_col=right_bound)

    # Convert to grayscale
    gray_frame = convert_frame_to_grayscale(cropped_frame)

    # Binarise frame
    bin_frame = binarise_frame(gray_frame, bin_thresh)

    return bin_frame


def calc_shift(prev_frame, curr_frame):

    # Decide the shift limits
    frame_height = prev_frame.shape[0]
    start_index = 1                     # Minimum shift = 1
    end_index = frame_height            # Maximum shift = Full height of frame

    first_match_val = None
    best_match_val = None
    best_match_pos = None

    # --> cumul_count_prev[i] = np.count_nonzero(prev_frame[0: -i, :])
    cumul_count_prev = np.cumsum(np.count_nonzero(prev_frame, axis=1))[::-1]

    # --> cumul_count_curr[i] = np.count_nonzero(curr_frame[i: end, :])
    cumul_count_curr = np.cumsum(np.count_nonzero(curr_frame, axis=1)[::-1])[::-1]

    # Looping over each valid shift value ...
    for i in range(start_index, end_index):

        # Find the intersection of the shifted prev frame with the curr frame
        intersect_map = np.logical_and(prev_frame[:-i, :],
                                       curr_frame[i:, :])

        # Find the intersection and the union count
        intersect_count = np.count_nonzero(intersect_map)
        union_count = cumul_count_prev[i] + cumul_count_curr[i] - intersect_count

        # Compute Intersection-over-Union (with care to prevent divide-by-0)
        ratio_match_pixels = float(intersect_count) / (union_count + 1)

        # (Only encountered for the first shift value)
        if first_match_val is None:
            first_match_val = ratio_match_pixels
            best_match_val = ratio_match_pixels
            best_match_pos = i

        # update the best IoU and its corresponding shift value
        if ratio_match_pixels > best_match_val:
            best_match_val = ratio_match_pixels
            best_match_pos = i

    # Return the best shift value i.e. the shift at which IoU is the highest
    best_shift = best_match_pos
    return best_shift


def find_vertical_shift_rate(vid_sampler,
                             top_bound, bottom_bound,
                             left_bound, right_bound,
                             bin_thresh=DEFAULT_BINARY_THRESH,
                             num_shift_count_threshold=DEFAULT_NUM_SHIFT_COUNT_THRESHOLD):


    # Get the first frame from the sampling and crop, binarise it
    full_frame_prev = next(vid_sampler)
    bin_cropped_frame_prev = _get_bin_cropped_frame(full_frame_prev,
                                                    top_bound=top_bound, bottom_bound=bottom_bound,
                                                    left_bound=left_bound, right_bound=right_bound,
                                                    bin_thresh=bin_thresh)

    shift_count_dict = {}           # Dict to hold  how many times a shift value was found
    absolute_best_shift = None      # The best shift (determined)
    running_best_shift = None       # The best shift as of <this iteration>
    count_running_best_shift = 0    # Number of times running_best_shift has been found
    is_best_shift_found = False     # Flag to say whether the best shift was "surely" found


    for full_frame_curr in vid_sampler:

        # Get the next frame from the sampling and crop, binarise it
        bin_cropped_frame_curr = _get_bin_cropped_frame(full_frame_curr,
                                                        top_bound=top_bound, bottom_bound=bottom_bound,
                                                        left_bound=left_bound, right_bound=right_bound,
                                                        bin_thresh=bin_thresh)

        # Calculate the best shift for this pair of frames
        curr_shift = calc_shift(bin_cropped_frame_prev, bin_cropped_frame_curr)

        # Update the count for this value of shift
        if curr_shift not in shift_count_dict:
            shift_count_dict[curr_shift] = 0
        shift_count_dict[curr_shift] += 1

        # Update the running_best_shift and associated values
        if curr_shift == running_best_shift:
            count_running_best_shift += 1
        else:
            if shift_count_dict[curr_shift] > count_running_best_shift:
                running_best_shift = curr_shift
                count_running_best_shift = shift_count_dict[curr_shift]

        # If running_best_shift has occured <threshold> times,
        # It is definitely the constant rate of shift!
        # Hence, break after setting the flag
        if count_running_best_shift >= num_shift_count_threshold:
            absolute_best_shift = running_best_shift
            is_best_shift_found = True
            break

        # Replace prev frame with current frame, to continue onto next iteration
        bin_cropped_frame_prev = bin_cropped_frame_curr


    # If flag is set, that means the best shift rate was definitely found
    if is_best_shift_found:
        best_shift = absolute_best_shift

    # Else, the loop ran through all samples, but was unable to definitely
    # determine the best shift rate. In this case, display a warning and
    # return the best candidate.
    else:
        warnings.warn("Unable to determine the undisputed best shift rate.\n"
                      "The closest contender for best shift rate:\n"
                      "Shift: {}, occurred {} times".format(running_best_shift,
                                                            count_running_best_shift))

        best_shift = running_best_shift


    return best_shift
