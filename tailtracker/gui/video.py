from .widget import TailInitializationWidget
from PyQt5 import QtWidgets, QtCore
from video_analysis_toolbox.video import Video


class TailTrackerVideoWidget(TailInitializationWidget):

    def __init__(self, video: Video, *args, **kwargs):
        self.video = video
        super().__init__()
        self.frame_slider.setValue(0)
        self.change_frame(0)

    def _init_ui(self):
        super()._init_ui()
        self._add_frame_slider()

    def _add_frame_slider(self):
        self.frame_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(self.video.frame_count - 1)
        self.layout().addWidget(self.frame_slider, 2, 0, 1, 1)
        self.frame_slider.valueChanged.connect(self.change_frame)

    @QtCore.pyqtSlot(int)
    def change_frame(self, val):
        frame = self.video.grab_frame(val)
        self.new_image(frame)
