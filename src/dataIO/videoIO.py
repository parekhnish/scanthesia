import traceback
import math

import imageio


class VideoReader:

    def __init__(self,
                 video_filename):

        # Open an ImageIO Reader object for the given video file
        try:
            self.video_filename = video_filename
            self.video_reader = imageio.get_reader(self.video_filename, format="ffmpeg")
        except Exception:
            print("Could not initialise the video reader!")
            print("Video filename: {}".format(video_filename))
            traceback.print_exc()
            raise

        # Extract and store metadata related to the video
        self._extract_video_metadata()

        self.curr_frame_index = -1       # Implies video has not been read yet
        self.curr_time_instant = -1.0    # Implies video has not been read yet

        super().__init__()

        return

    def _extract_video_metadata(self):

        self.vid_metadata = self.video_reader.get_meta_data()

        self.frame_height, self.frame_width = self.vid_metadata["size"]
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
                    print("Could not extract number of frames in the video")
                    print("Video filename: {}".format(self.video_filename))
                    raise

        return

    def get_frame_by_index(self, frame_index):
        assert frame_index < self.vid_num_frames, "Trying to get frame {}, but number of frames in video is {}".format(frame_index, self.vid_num_frames)

        frame = self.video_reader.get_data(frame_index)

        self.curr_frame_index = self.video_reader._pos
        self.curr_time_instant = float(self.curr_frame_index) / self.vid_fps

        return frame

    def get_frame_by_time(self, target_time):
        assert target_time < self.vid_duration_time, "Trying to get frame at time {}, but video duration is {}".format(target_time, self.vid_duration_time)

        target_frame_index = math.floor(target_time * self.vid_fps)
        frame = self.get_frame_by_index(target_frame_index)

        return frame

    def advance_frame_by_index(self, increment=1):
        try:
            frame = self.get_frame_by_index(self.curr_frame_index + increment)
            success = True
        except Exception:
            frame = None
            success = False

        return success, frame

    def advance_frame_by_time(self, increment=1.0):
        try:
            frame = self.get_frame_by_time(self.curr_time_instant + increment)
            success = True
        except Exception:
            frame = None
            success = False

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
        self.num_samples = None
        self.curr_sample_index = None
        return

    def gen_sampling_schedule_using_frame_indices(self,
                                                  start_frame=None,
                                                  end_frame=None,
                                                  samples_per_second=1):

        if start_frame is None:
            start_frame = 0
        else:
            assert isinstance(start_frame, int), "Start Frame index ({}) should be an integer".format(start_frame)
            assert (start_frame >= 0), "Start Frame index ({}) should be greater than 0".format(start_frame)
            assert (start_frame < self.vid_num_frames), "Start Frame index ({}) should be lesser than the total number of video frames ({})".format(start_frame, self.vid_num_frames)

        self.start_frame = start_frame
        self.start_time = float(self.start_frame) / self.vid_fps



        assert (isinstance(samples_per_second, int)) or (isinstance(samples_per_second, float)), "Samples per second ({}) should be a number".format(samples_per_second)
        assert samples_per_second > 0, "Samples per second ({}) should be greater than 0".format(samples_per_second)
        assert samples_per_second <= self.vid_fps, "Samples per second ({}) should be less than the video FPS ({})".format(samples_per_second, self.vid_fps)

        self.sample_step = math.floor(float(self.vid_fps) / samples_per_second)


        if end_frame is None:
            end_frame = self.vid_num_frames
        else:
            assert isinstance(end_frame, int), "End Frame index ({}) should be an integer".format(end_frame)
            assert (end_frame >= start_frame), "End Frame index ({}) should be greater than Start Frame index ({})".format(end_frame, start_frame)
            assert (end_frame < self.vid_num_frames), "End Frame index ({}) should be lesser than the total number of video frames ({})".format(end_frame, self.vid_num_frames)

        self.num_samples = math.ceil(float(end_frame - self.start_frame) / self.sample_step)

        # self.end_frame is set now, because the sample_step series might not match
        # the input end_frame. Hence, it is set by "calculating" the last frame
        self.end_frame = self.start_frame + ((self.num_samples-1) * self.sample_step)
        self.start_time = float(self.start_frame) / self.vid_fps


        self.curr_sample_index = None     # `None` implies video has not been sampled yet

        self.is_sampling_generated = True



    def gen_sampling_schedule_using_time(self,
                                         start_time=None,
                                         end_time=None,
                                         samples_per_second=1):

        if start_time is None:
            start_time = 0.0
        else:
            assert (isinstance(start_time, int)) or (isinstance(start_time, float)), "Start Time ({}) should be a number".format(start_time)
            assert (start_time >= 0), "Start Time ({}) should be greater than 0".format(start_time)
            assert (start_time < self.vid_duration_time), "Start Time ({}) should be lesser than the total video duration ({})".format(start_time, self.vid_duration_time)


        if end_time is None:
            end_time = self.vid_duration_time
        else:
            assert (isinstance(end_time, int)) or (isinstance(end_time, float)), "End Time ({}) should be a number".format(end_time)
            assert (end_time >= start_time), "End Time ({}) should be greater than Start Time ({})".format(end_time, start_time)
            assert (end_time < self.vid_duration_time), "End Time ({}) should be lesser than the total video duration ({})".format(end_time, self.vid_duration_time)

        start_frame = start_time * self.vid_fps
        end_frame = end_time * self.vid_fps

        self.gen_sampling_schedule_using_frame_indices(start_frame, end_frame, samples_per_second)

        return







    def _calc_frame_by_sample_index(self, sample_index):
        return self.start_frame + (sample_index * self.sample_step)


    def get_next_sample(self):

        # ----------------------------------------------------------------------
        # curr_sample_index need not be an integer; it can be a float (because
        # of non-integral sample steps, taken due to reading frames that are
        # outside the standard sampling step). Thus, we need a slightly
        # complicated way to determine the next sampling index
        # ----------------------------------------------------------------------





        # Less than 0; it means this will be the starting sample
        if self.curr_sample_index < 0:
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


        if next_sample_index > (self.num_samples - 1):
            success = False
            frame = None
        else:
            next_frame_index = self._calc_frame_by_sample_index(next_sample_index)
            frame = self.get_frame_by_index(next_frame_index)
            success = True

            self.curr_sample_index = next_frame_index

        return success, frame



    def get_sample_by_index(self, sample_index,
                            update_curr_sample_index=True):
        assert sample_index <= (self.num_samples - 1), "Target sample index ({}) is outside the number of possible samples ({})".format(sample_index, self.num_samples)

        frame_index = self.start_frame + (sample_index * self.sample_step)
        frame = self.get_frame_by_index(frame_index)
        if update_curr_sample_index:
            self.curr_sample_index = float(self.curr_frame_index - self.start_frame) / self.vid_fps
        return frame


    def get_frame_by_index(self, frame_index,
                           update_curr_sample_index=True):
        frame = super().get_frame_by_index(frame_index)
        if update_curr_sample_index:
            self.curr_sample_index = float(self.curr_frame_index - self.start_frame) / self.vid_fps
        return frame


    def get_frame_by_time(self, target_time,
                          update_curr_sample_index=True):
        frame = super().get_frame_by_time(target_time)
        if update_curr_sample_index:
            self.curr_sample_index = float(self.curr_frame_index - self.start_frame) / self.vid_fps
        return frame



    def close_sampler(self):
        self.close_reader()
        return
