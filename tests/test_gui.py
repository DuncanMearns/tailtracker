from tailtracker.gui import TailInitializationWidget
from video_analysis_toolbox.video import Video


def run_app(path):
    v = Video.open(path)
    img = v.advance_frame()
    ret, params = TailInitializationWidget.app(img, return_object=True)
    print(ret, params)


def run_dialog(path):
    from PyQt5.QtWidgets import QApplication
    import sys
    v = Video.open(path)
    img = v.advance_frame()
    app = QApplication(sys.argv)
    dialog = TailInitializationWidget.dialog(img)
    dialog.show()
    app.exec()
    print(dialog.get_params())


if __name__ == "__main__":
    path = r"D:\DATA\embedded_prey_capture\raw_data\2021_05_21\fish01_red_centre_10%_001.avi"
    # run_app(path)
    run_dialog(path)
