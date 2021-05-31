from ..tracker import TailTracker
from PyQt5 import QtWidgets, QtCore
from .collapsible_widget import QCollapsibleWidget
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from collections import namedtuple
import sys


class TailInitializationWidget(QtWidgets.QWidget):

    BUTTON_HEIGHT = 25
    BUTTON_WIDTH = 150

    changeImage = QtCore.pyqtSignal()
    pointAdded = QtCore.pyqtSignal(int, int)
    pointsErased = QtCore.pyqtSignal()

    accept = QtCore.pyqtSignal()
    reject = QtCore.pyqtSignal()

    params = namedtuple("parameters", ("points", "n_points", "params"))
    title = "Initialize tail tracking"

    def __init__(self, image=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a tracker object
        self.tracker = TailTracker(None, None, 10)
        # Initialize user interface
        self._init_ui()
        # Image
        self.image = image
        self.get_display_image = self.get_image
        if self.image is not None:
            self.new_image(image)
            self.draw()
        # Clicked points
        self.points = []
        # Return val
        self.ret = False

    def _init_ui(self):
        # Set layout
        self.resize(800, 600)
        self.setLayout(QtWidgets.QGridLayout())
        self._init_canvas()
        self._init_params()
        self._init_states()
        self._init_connections()

    def _init_canvas(self):
        # Create hint label
        self.hints = [
            "LEFT click on base of the swim bladder.",
            "LEFT click at the end of the tail. RIGHT click to start over.",
            "Click accept. RIGHT click to start over."
        ]
        self.hint_label = QtWidgets.QLabel(self.hints[0])
        self.layout().addWidget(self.hint_label, 0, 0, 1, 2)
        # Create canvas widget and figure
        self.figure = Figure()
        self.canvas_widget = FigureCanvas(self.figure)
        self.layout().addWidget(self.canvas_widget, 1, 0)
        # Create axis for plotting
        self.ax = self.figure.add_subplot(111)
        self.ax.axis('off')
        self.path, = self.ax.plot([], [], 'o-', color='y', lw=3)
        self.tracked, = self.ax.plot([], [], 'o', color='c', lw=3)

    def _init_params(self):
        self.params_widget = QtWidgets.QWidget()
        self.params_widget.setLayout(QtWidgets.QVBoxLayout())
        self.params_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().addWidget(self.params_widget, 1, 1)
        # --------------------
        # Create basic options
        # --------------------
        # New image button
        self.new_button = QtWidgets.QPushButton("NEW IMAGE")
        self.new_button.setFixedSize(self.BUTTON_WIDTH, 2 * self.BUTTON_HEIGHT)
        self.params_widget.layout().addWidget(self.new_button)
        # N points spinbox
        self.n_points_spinbox = QtWidgets.QSpinBox()
        self.n_points_spinbox.setSuffix(" points")
        self.n_points_spinbox.setRange(3, 51)
        self.n_points_spinbox.setValue(self.tracker.n_points)
        self.params_widget.layout().addWidget(self.n_points_spinbox)
        # Show/hide tracking
        self.tracking_checkbox = QtWidgets.QCheckBox("Show tracking")
        self.tracking_checkbox.setChecked(True)
        self.params_widget.layout().addWidget(self.tracking_checkbox)
        # -----------------------
        # Create advanced options
        # -----------------------
        self.advanced_layout = QtWidgets.QFormLayout()
        self.advanced_layout.setAlignment(QtCore.Qt.AlignTop)
        # Background setter
        self.background_combo = QtWidgets.QComboBox()
        self.background_combo.addItem("Light")
        self.background_combo.addItem("Dark")
        self.background_combo.setCurrentIndex(0)
        self.advanced_layout.addRow("Background", self.background_combo)
        # Image selector
        self.image_combo = QtWidgets.QComboBox()
        self.image_combo.addItem("Original")
        self.image_combo.addItem("Filtered")
        self.image_combo.setCurrentIndex(0)
        self.advanced_layout.addRow("Image", self.image_combo)
        # Kernel size spinbox
        self.ksize_spinbix = QtWidgets.QSpinBox()
        self.ksize_spinbix.setRange(1, 21)
        self.ksize_spinbix.setValue(self.tracker.ksize)
        self.advanced_layout.addRow("Kernel size", self.ksize_spinbix)
        # Add advanced options widget
        self.advanced_widget = QCollapsibleWidget("Advanced options")
        self.advanced_widget.setContentLayout(self.advanced_layout)
        self.params_widget.layout().addWidget(self.advanced_widget)
        # -------------------------
        # Accept and cancel buttons
        # -------------------------
        divider = QtWidgets.QFrame()
        divider.setFrameStyle(divider.HLine | divider.Plain)
        self.params_widget.layout().addWidget(divider)
        self.accept_button = QtWidgets.QPushButton("ACCEPT")
        self.accept_button.setFixedSize(self.BUTTON_WIDTH, 2 * self.BUTTON_HEIGHT)
        self.accept_button.setEnabled(False)
        self.cancel_button = QtWidgets.QPushButton("cancel")
        self.cancel_button.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.params_widget.layout().addWidget(self.accept_button)
        self.params_widget.layout().addWidget(self.cancel_button)

    def _init_states(self):
        # Create state machine
        self.state_machine = QtCore.QStateMachine()
        # Create states
        self.s0 = QtCore.QState()  # no points
        self.s1 = QtCore.QState()  # one point
        self.s2 = QtCore.QState()  # two points
        self.states = (self.s0, self.s1, self.s2)
        # Set transitions
        self.s0.addTransition(self.pointAdded, self.s1)
        self.s1.addTransition(self.pointAdded, self.s2)
        self.s1.addTransition(self.pointsErased, self.s0)
        self.s2.addTransition(self.pointsErased, self.s0)
        # Start state machine
        self.state_machine.addState(self.s0)
        self.state_machine.addState(self.s1)
        self.state_machine.addState(self.s2)
        self.state_machine.setInitialState(self.s0)
        self.state_machine.start()

    def _init_connections(self):
        # Button clicks
        self.new_button.clicked.connect(self.changeImage)
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        # Handle mouse click events
        self.canvas_widget.mpl_connect('button_press_event', self.mouse_button_pressed)
        # Change diagnostic image
        self.image_combo.currentIndexChanged.connect(self.change_displayed_image)
        # Toggle tracking
        self.tracking_checkbox.stateChanged.connect(self.update_tracking)
        # Change tracker parameters
        self.n_points_spinbox.valueChanged.connect(self.update_tracker_params)
        self.ksize_spinbix.valueChanged.connect(self.update_tracker_params)
        self.background_combo.currentIndexChanged.connect(self.update_tracker_params)
        # State changes
        self.s0.entered.connect(lambda: self.accept_button.setEnabled(False))
        self.s2.entered.connect(lambda: self.accept_button.setEnabled(True))
        self.s0.entered.connect(lambda : self.hint_label.setText(self.hints[0]))
        self.s1.entered.connect(lambda: self.hint_label.setText(self.hints[1]))
        self.s2.entered.connect(lambda: self.hint_label.setText(self.hints[2]))
        self.s2.entered.connect(self.initialize_tracker)
        self.s0.entered.connect(self.update_tracking)
        # Set retval
        self.accept.connect(lambda: self.set_retval(True))
        self.reject.connect(lambda: self.set_retval(False))

    @property
    def current_state(self):
        for s in self.states:
            if s in self.state_machine.configuration():
                return s

    @property
    def n_points(self):
        return self.n_points_spinbox.value()

    @property
    def background(self):
        return self.background_combo.currentText()

    @property
    def kernel_size(self):
        return self.ksize_spinbix.value()

    def mouse_button_pressed(self, event):
        if (not event.inaxes) or (self.image is None):
            return
        elif event.button == 1:  # left mouse button
            x, y = int(event.xdata), int(event.ydata)
            self.new_point(x, y)
        elif event.button == 3:  # right mouse button
            self.erase()

    def new_image(self, image):
        self.image = image
        self.update_image_data()
        self.update_tracking()

    def new_point(self, x, y):
        if len(self.points) < 2:
            self.points.append((x, y))
        self.update_point_data()
        self.pointAdded.emit(x, y)

    def erase(self):
        self.points = []
        self.update_point_data()
        self.pointsErased.emit()

    def update_image_data(self):
        img = self.get_display_image()
        if img is not None:
            img = img / img.max()
            try:
                self.image_data.set_data(img)
            except AttributeError:
                self.image_data = self.ax.imshow(img, origin='upper', cmap='Greys_r')
        self.draw()

    def update_point_data(self):
        x = [p[0] for p in self.points]
        y = [p[1] for p in self.points]
        self.path.set_data(x, y)
        self.draw()

    def update_tracking(self):
        if self.tracking_checkbox.checkState() and (self.current_state is self.s2):
            self.tracker.track(self.image)
            x = [p[0] for p in self.tracker.points]
            y = [p[1] for p in self.tracker.points]
            self.tracked.set_data(x, y)
        else:
            self.tracked.set_data([], [])
        self.draw()

    @QtCore.pyqtSlot(int)
    def update_tracker_params(self, val):
        self.tracker.n_points = self.n_points
        self.tracker.background = self.background
        self.tracker.ksize = self.kernel_size
        self.update_image_data()
        self.update_tracking()

    @QtCore.pyqtSlot()
    def initialize_tracker(self):
        points, n, kw = self.get_params()
        self.tracker = TailTracker.from_points(points, n, **kw)
        self.update_tracking()

    def get_image(self):
        return self.image

    def get_diagnostic_image(self):
        if self.image is not None:
            return self.tracker.preprocess(self.image)

    @QtCore.pyqtSlot(int)
    def change_displayed_image(self, idx):
        self.get_display_image = (self.get_image, self.get_diagnostic_image)[idx]
        self.update_image_data()

    def draw(self):
        self.canvas_widget.draw()

    def set_retval(self, val):
        self.ret = val

    def get_params(self):
        params = self.params(self.points, self.n_points, dict(background=self.background, ksize=self.kernel_size))
        return params

    @staticmethod
    def app(image, return_object=True):
        app = QtWidgets.QApplication(sys.argv)
        main = QtWidgets.QMainWindow()
        w = TailInitializationWidget(image)
        w.accept.connect(main.close)
        w.reject.connect(main.close)
        main.setCentralWidget(w)
        main.setWindowTitle(w.title)
        main.show()
        app.exec()
        if return_object:
            return w.ret, w.tracker
        else:
            return w.ret, w.get_params()

    @staticmethod
    def dialog(image=None, *args, **kwargs):
        dialog = TailInitializationDialog(image, *args, **kwargs)
        return dialog


class TailInitializationDialog(QtWidgets.QDialog):

    def __init__(self, image, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        # Add widget
        self.widget = TailInitializationWidget(image)
        self.layout().addWidget(self.widget)
        # Set title
        self.setWindowTitle(self.widget.title)
        # Connect signals
        self.widget.accept.connect(self.accept)
        self.widget.reject.connect(self.reject)

    def get_params(self):
        return self.widget.ret, self.widget.get_params()

    def get_tracker(self):
        return self.widget.ret, self.widget.tracker
