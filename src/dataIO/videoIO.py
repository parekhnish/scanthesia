import sys
import math
import warnings


import imageio


class VideoReader:

    def __init__(self,
                 video_filename):

        # Open an ImageIO Reader object for the given video file
        try:
            self.video_filename = video_filename
            self.video_reader = imageio.get_reader(self.video_filename, format="ffmpeg")
        except Exception:
            raise sys.exc_info()

        # Extract and store metadata related to the video
        self._extract_video_metadata()

        self.curr_frame_index = -1       # Implies video has not been read yet
        self.curr_time_instant = -1.0    # Implies video has not been read yet

        super().__init__()

        return

    def _extract_video_metadata(self):

        self.vid_metadata = self.video_reader.get_meta_data()

        self.frame_width, self.frame_height = self.vid_metadata["size"]
        self.vid_fps = self.vid_metadata["fps"]
        self.vid_duration_time = self.vid_metadata["duration"]

        # ----------------------------------------------------------------------
        # Not all videos have their num_frames perfectly defined in metadata
        # Hence, we try to iterate through various options, from best to worst
        # See [1] for more details
        #
        # [1]: https://imageio.readthedocs.io/en/stable/format_ffmpeg.html
        # ----------------------------------------------------------------------

        self.vid_num_frames = self.vid_metadata["nframes"]          # --1--: Directly from metadata
        if (self.vid_num_frames == 0) or (math.isinf(self.vid_num_frames)):
            self.vid_num_frames = self.video_reader.count_frames()    # --2--: From the count_frames() function
            if (self.vid_num_frames == 0) or (math.isinf(self.vid_num_frames)):
                self.vid_num_frames = math.floor(self.vid_fps * self.vid_num_frames)    # --3--: From (fps * duration in seconds)

                # If none of these work, return an Error
                if (self.vid_num_frames == 0) or (math.isinf(self.vid_num_frames)):
                    raise Exception("Could not extract number of frames in the video: {}".format(self.video_filename))

        return

    def get_frame_by_index(self, frame_index):
        frame = None
        success = False

        if not isinstance(frame_index, int):
            raise Exception("Illegal frame index: {}".format(frame_index))


        if (frame_index < 0) or (frame_index >= self.vid_num_frames):
            warnings.warn("Trying to get frame {}, but index should be in [0, {}]".format(frame_index, self.vid_num_frames))
        else:
            frame = self.video_reader.get_data(frame_index)

            self.curr_frame_index = self.video_reader._pos
            self.curr_time_instant = float(self.curr_frame_index) / self.vid_fps
            success = True

        return success, frame

    def get_frame_by_time(self, target_time):
        frame = None
        success = False

        if (target_time < 0.0) or (target_time >= self.vid_duration_time):
            warnings.warn("Trying to get frame at time {}, but video time is limited to [0, {}]".format(target_time, self.vid_duration_time))
        else:
            target_frame_index = math.floor(target_time * self.vid_fps)
            success, frame = self.get_frame_by_index(target_frame_index)

        return success, frame

    def advance_frame_by_index(self, increment=1):
        success, frame = self.get_frame_by_index(self.curr_frame_index + increment)
        return success, frame

    def advance_frame_by_time(self, increment=1.0):
        success, frame = self.get_frame_by_time(self.curr_time_instant + increment)
        return success, frame

    def close_reader(self):
        self.video_reader.close()
        return


class VideoSampler(VideoReader):

    def __init__(self,
                 video_filename):
        super().__init__(video_filename)

        # Flag to determine whether a sampling has been generated or not
        self.is_sampling_generated = False

        # Placeholder variables, that will be updated once a sampling is generated
        self.start_frame = None
        self.start_time = None
        self.end_frame = None
        self.end_time = None

        self.sample_step = None
        self.sample_time_diff = None
        self.num_samples = None
        self.curr_sample_index = None
        return

    def gen_sampling_schedule_using_frame_indices(self,
                                                  start_frame=None,
                                                  end_frame=None,
                                                  samples_per_second=1,
                                                  reset_sample_index=True):

        if start_frame is None:
            start_frame = 0
        else:
            if not isinstance(start_frame, int):
                raise Exception("Start Frame index ({}) should be an integer".format(start_frame))
            if start_frame < 0:
                raise Exception("Start Frame index ({}) should be greater than 0".format(start_frame))
            if start_frame >= self.vid_num_frames:
                raise Exception("Start Frame index ({}) should be lesser than the total number of video frames ({})".format(start_frame, self.vid_num_frames))

        self.start_frame = start_frame
        self.start_time = float(self.start_frame) / self.vid_fps


        if not (isinstance(samples_per_second, int)) or (isinstance(samples_per_second, float)):
            raise Exception("Samples per second ({}) should be a number".format(samples_per_second))
        if samples_per_second <= 0:
            raise Exception("Samples per second ({}) should be greater than 0".format(samples_per_second))
        if samples_per_second > self.vid_fps:
            raise Exception("Samples per second ({}) should be less than the video FPS ({})".format(samples_per_second, self.vid_fps))

        self.sample_step = math.floor(float(self.vid_fps) / samples_per_second)
        self.sample_time_diff = float(self.sample_step) / self.vid_fps


        if end_frame is None:
            end_frame = self.vid_num_frames
        else:
            if not isinstance(end_frame, int):
                raise Exception("End Frame index ({}) should be an integer".format(end_frame))
            if end_frame < start_frame:
                raise Exception("End Frame index ({}) should be greater than Start Frame index ({})".format(end_frame, start_frame))
            if end_frame >= self.vid_num_frames:
                raise Exception("End Frame index ({}) should be lesser than the total number of video frames ({})".format(end_frame, self.vid_num_frames))


        self.num_samples = math.ceil(float(end_frame - self.start_frame + 1) / self.sample_step)

        # self.end_frame is set now, because the sample_step series might not match
        # the input end_frame. Hence, it is set by "calculating" the last frame
        self.end_frame = self.start_frame + ((self.num_samples-1) * self.sample_step)

        self.start_time = float(self.start_frame) / self.vid_fps
        self.end_time = float(self.end_frame) / self.vid_fps

        if reset_sample_index:
            self.curr_sample_index = None     # `None` implies video has not been sampled yet
        else:
            self.curr_sample_index = self._calc_sample_index_by_frame(self.curr_frame_index)

        self.is_sampling_generated = True



    def gen_sampling_schedule_using_time(self,
                                         start_time=None,
                                         end_time=None,
                                         samples_per_second=1,
                                         reset_sample_index=True):

        if start_time is None:
            start_time = 0.0
        else:
            if not (isinstance(start_time, int) or isinstance(start_time, float)):
                raise Exception("Start Time ({}) should be a number".format(start_time))
            if start_time < 0:
                raise Exception("Start Time ({}) should be greater than 0".format(start_time))
            if start_time >= self.vid_duration_time:
                raise Exception("Start Time ({}) should be lesser than the total video duration ({})".format(start_time, self.vid_duration_time))




        if end_time is None:
            end_time = self.vid_duration_time - (1.0 / self.vid_fps)    # i.e. the smallest time difference before end of video
        else:
            if not (isinstance(end_time, int) or isinstance(end_time, float)):
                raise Exception("End Time ({}) should be a number".format(end_time))
            if end_time < start_time:
                raise Exception("End Time ({}) should be greater than Start Time ({})".format(end_time, start_time))
            if end_time >= self.vid_duration_time:
                raise Exception("End Time ({}) should be lesser than the total video duration ({})".format(end_time, self.vid_duration_time))

        start_frame = math.floor(start_time * self.vid_fps)
        end_frame = math.floor(end_time * self.vid_fps)

        self.gen_sampling_schedule_using_frame_indices(start_frame, end_frame,
                                                       samples_per_second,
                                                       reset_sample_index)

        return







    def _calc_frame_by_sample_index(self, sample_index):
        return math.floor(self.start_frame + (sample_index * self.sample_step))

    def _calc_sample_index_by_frame(self, frame_index):
        sample_index = float(frame_index - self.start_frame) / self.sample_step

        # Check if the calculated value is actually an integer or not, and
        # return appropriately
        if sample_index.is_integer():
            return int(sample_index)
        else:
            return sample_index


    def get_next_sample(self,
                        update_curr_sample_index=True):

        if not self.is_sampling_generated:
            warnings.warn("Requesting next sample, but a sampling subset has not been initialised!")
            return False, None

        # ----------------------------------------------------------------------
        # curr_sample_index need not be an integer; it can be a float (because
        # of non-integral sample steps, taken due to reading frames that are
        # outside the standard sampling step). Thus, we need a slightly
        # complicated way to determine the next sampling index
        # ----------------------------------------------------------------------
        # NONE, or less than 0; it means this will be the starting sample
        if (self.curr_sample_index is None) or self.curr_sample_index < 0:
            next_sample_index = 0

        # More than num_samples: It is already outside the valid range, will error out later
        elif self.curr_sample_index > self.num_samples:
            next_sample_index = self.curr_sample_index + 1

        else:
            # If curr_sample_index is an integer, simply advance to the next
            # sample by +1
            # If curr_sample_index is not an integer, advance to the next
            # nearest sample
            is_curr_index_integer = ((isinstance(self.curr_sample_index, int)) or
                                     (self.curr_sample_index.is_integer()))
            if is_curr_index_integer:
                next_sample_index = self.curr_sample_index + 1
            else:
                next_sample_index = math.ceil(self.curr_sample_index)


        success, frame = self.get_sample_by_index(next_sample_index,
                                                  update_curr_sample_index)

        return success, frame



    def get_sample_by_index(self, sample_index,
                            update_curr_sample_index=True):
        frame = None
        success = False

        if not self.is_sampling_generated:
            warnings.warn("Requesting sample at index {}, but a sampling subset has not been initialised!".format(sample_index))
        elif (sample_index < 0) or (sample_index >= self.num_samples):
            warnings.warn("Target sample index ({}) is outside the number of possible samples ({})".format(sample_index, self.num_samples))
        else:
            frame_index = self._calc_frame_by_sample_index(sample_index)
            success, frame = self.get_frame_by_index(frame_index, update_curr_sample_index)

        return success, frame




    def get_frame_by_index(self, frame_index,
                           update_curr_sample_index=True):
        success, frame = super().get_frame_by_index(frame_index)
        if success and update_curr_sample_index:
            self.curr_sample_index = self._calc_sample_index_by_frame(self.curr_frame_index)
        return success, frame


    def get_frame_by_time(self, target_time,
                          update_curr_sample_index=True):
        success, frame = super().get_frame_by_time(target_time)
        if success and update_curr_sample_index:
            self.curr_sample_index = self._calc_sample_index_by_frame(self.curr_frame_index)
        return success, frame


    def __iter__(self):
        return self


    def __next__(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            success, frame = self.get_next_sample(update_curr_sample_index=True)
            if success:
                return frame
            else:
                raise StopIteration



    def close_sampler(self):
        self.close_reader()
        return
