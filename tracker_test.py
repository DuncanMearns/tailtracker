import numpy as np
from matplotlib import pyplot as plt
from tailtracker.tracker import TailTracker
from video_analysis_toolbox.video import Video
import cv2

path = r"D:\DATA\embedded_prey_capture\raw_data\2021_05_21\fish01_red_centre_10%_001.avi"
v = Video.open(path)
# v.scroll(first_frame=0, last_frame=2500)

# f = v.advance_frame()
# f = np.array(f)
# cv2.circle(f, (180, 155), 5, 0, -1)  # start point
# cv2.circle(f, (320, 155), 5, 0, -1)  # end point
# cv2.imshow("start", f)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
# start_xy = (180, 155)
# length = 320 - 180
# tracker = TailTracker(start_xy, length, 10)

f = v.advance_frame()
f = f.T[::-1].copy()
h, w = f.shape
cv2.circle(f, (155, 180), 5, 0, -1)  # start point
cv2.circle(f, (155, h - 320), 5, 0, -1)  # end point
cv2.imshow("start", f)
cv2.waitKey(0)
cv2.destroyAllWindows()
start_xy = (155, 180)
length = 140
tracker = TailTracker(start_xy, length, 10, start_angle=np.pi / 2)

angles = []
for i in range(2500):
    f = v.advance_frame()
    f = f.T[::-1].copy()
    angle = tracker.track(f)
    angles.append(angle)

plt.plot(angles)
plt.show()
