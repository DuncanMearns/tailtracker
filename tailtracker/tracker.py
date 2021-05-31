import cv2
import numpy as np
from typing import Tuple, Optional


class TailTracker:
    """Class for head-embedded tail tracking.

    Parameters
    ----------
    start_point : tuple (int, int)
        The (x, y) coordinate of the point from which to start tracking. Origin is the top left corner of the image,
        with x increasing to the right and y increasing downwards (opencv convention).
    tail_length : int
        The length of the tail (in pixels).
    n_points : int
        Number of points to fit to the tail.

    Other Parameters
    ----------------
    start_angle : float, default=0
        The baseline tail angle at rest. Zero means tail is to the right. Increases counter-clockwise.
    background : {"light", "dark"}, default="light"
        Whether the background is light or dark compared to the fish.
    ksize : int, default=7
        The size of the kernel used to filter the image.
    n_tip_points : int, default=3
        The number of points at the tip of the tail that are averaged to compute the tail angle.
    *arg, *kwargs
        Passed to super().

    Attributes
    ----------
    _image : np.ndarray
        A copy of the image to be tracked.
    _normalized : np.ndarray
        Image rescaled so that the maximum value is 1.
    _filtered : np.ndarray
        Image after applying a box filter.
    points : list
        List of tail points.
    points_array : np.ndarray
        Tail points converted to a numpy array.
    tail_angle : float
        The angle of the tail in the image. Angles increase counterclockwise starting from the right.

    Notes
    -----
    After initializing an instance of the class, the `track` method may be called to track individual images. If
    `start_point`, `tail_length`, or `n_points` is None, the `track` method will similarly return None.

    Images are first normalized and then a box filter of the specified kernel size is applied. The tracking algorithm
    finds the positions of either the darkest of brightest pixel within 180 degree arcs that propagate along the tail.
    These points are appended to the `_points` list until all points are found. The tail angle if then computed between
    the starting point and the average of the last n tip points.

    The algorithm uses the opencv coordinate convention, with the origin at the top left corner of the image. Angles are
    measures COUNTERCLOCKWISE, with zero to the RIGHT.

    Based on Thomas's old code, which in turn was based on code from Anki.
    """

    @classmethod
    def from_points(cls, points, n, **kwargs):
        p0, p1 = points
        v = np.array(p1) - p0
        d = int(np.linalg.norm(v))
        angle = np.arctan2(-v[1], v[0])
        return cls(p0, d, n, start_angle=angle, **kwargs)

    def __init__(self,
                 start_point: Optional[Tuple[int, int]],
                 tail_length: Optional[int],
                 n_points: Optional[int],
                 start_angle: float = 0.,
                 background: str = "light",
                 ksize: int = 7,
                 n_tip_points: int = 3,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Arguments that must be specified before tracking
        self.start_point = start_point
        self.tail_length = tail_length
        self.n_points = n_points
        # Arguments with defaults
        self.start_angle = start_angle
        self.background = background
        self.ksize = ksize
        self.n_tip_points = n_tip_points
        # Intermediate processing attributes specified within track method
        self._image = None
        self._normalized = None
        self._filtered = None
        self.points = []
        self.points_array = np.array([])
        self.tail_angle = 0

    @property
    def background(self) -> str:
        return self._background

    @background.setter
    def background(self, val: str):
        """Setter for the background attribute. Changing the background also changes the private attribute containing
        the function used to find tail points."""
        self._background = val.lower()
        self._minmax_function = np.argmin
        if self._background == "dark":
            self._minmax_function = np.argmax

    @staticmethod
    def compute_tail_angle(tail_points: np.ndarray, n_points=3, baseline=0.) -> float:
        """Computes the tail angle (in radians) from an array of tail points.

        Parameters
        ----------
        tail_points : np.ndarray
            An array of tail points. May contain data from a single frame or multiple frames.
        n_points : int, default=3
            The number of points that are averaged to compute the tail angle.
        baseline : float, default=0
            The baseline tail angle (radians).

        Returns
        -------
        angle : float

        Notes
        -----
        Computes a tail vector between the first point in the array and the average position of the last n points. The
        tail angle is the deflection angle of this vector from the given baseline.
        """
        v0 = np.array([np.cos(baseline), np.sin(baseline)])
        v1 = np.nanmean(tail_points[..., -n_points:, :], axis=0) - tail_points[..., 0, :]
        x, y = v1 - v0
        angle = np.arctan2(-y, x)
        return angle

    def preprocess(self, image):
        self._image = np.array(image).copy()  # copying the array prevents opencv from throwing weird errors
        # Normalize image and apply box filter
        self._normalized = self._image / np.max(self._image)
        mask = np.zeros(self._normalized.shape)
        self._filtered = cv2.boxFilter(self._normalized, -1, (self.ksize, self.ksize), mask)
        return self._filtered

    def track(self, image: np.ndarray):
        """Returns the clockwise rotation angle of the tail from the start point in an image.

        Parameters
        ----------
        image : np.ndarray

        Returns
        -------
        float
        """
        # Return None is start_xy, tail_length or n_points is not specified
        if any([self.start_point is None, self.tail_length is None, self.n_points is None]):
            return
        # Preprocess image
        track_image = self.preprocess(image)
        # Compute spacing between points
        spacing = float(self.tail_length) / self.n_points
        # Create 180 degree arc
        arc = np.linspace(-np.pi / 2, np.pi / 2, 20) + self.start_angle
        # Initialize points list
        x, y = self.start_point
        self.points = [[x, y]]
        for j in range(self.n_points):
            try:
                # Find the x and y values of the arc centred around current x and y
                xs = x + spacing * np.cos(arc)
                ys = y - spacing * np.sin(arc)
                # Convert them to integer, because of definite pixels
                xs, ys = xs.astype(int), ys.astype(int)
                # Find the index of the minimum or maximum pixel intensity along arc
                idx = self._minmax_function(track_image[ys, xs])
                # Update new x, y points
                x = xs[idx]
                y = ys[idx]
                # Create a new 180 arc centered around current angle
                arc = np.linspace(arc[idx] - np.pi / 2, arc[idx] + np.pi / 2, 20)
                # Add point to list
                self.points.append([x, y])
            except IndexError:
                self.points.append(self.points[-1])
        # Create numpy array of tail points
        self.points_array = np.array(self.points)
        # Compute tail angle
        self.tail_angle = self.compute_tail_angle(self.points_array, self.n_tip_points, self.start_angle)
        return self.tail_angle
