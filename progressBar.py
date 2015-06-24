__author__ = 'Natasha'
import subprocess
import sys
import re
from PyQt4 import QtGui, QtCore

class ProgressBar(QtGui.QMainWindow):

     def __init__(self):
        super(ProgressBar, self).__init__()
        self.setWindowTitle('FFMPEG Progress Bar example')
        window = QtGui.QWidget()

        self.centralLayout = QtGui.QGridLayout()
        window.setLayout(self.centralLayout)
        self.pBar = QtGui.QProgressBar()
        self.pBar.setValue(0)
        self.pBar.setMinimum(0)
        self.pBar.setMaximum(100)
        self.pLabel = QtGui.QLabel('Converting File')
        self.button = QtGui.QPushButton('Create')
        self.centralLayout.addWidget(self.pLabel)
        self.centralLayout.addWidget(self.pBar)
        self.centralLayout.addWidget(self.button)
        window.setLayout(self.centralLayout)
        self.button.clicked.connect(self.convertMovie)
        self.setCentralWidget(window)

     def convertMovie(self):
        moviePath = 'C:\Users\Natasha\Documents\devApps\\testmovs\e06_sh180_blocking.avi'
        outputPath = 'C:\Users\Natasha\Documents\devApps\\testmovs\e06_sh180_blocking.mov'
        cmd = 'ffmpeg.exe -y -an -i "%s" -vcodec prores -profile:v 2 "%s" ' % (moviePath, outputPath)
        p = subprocess.Popen(cmd, shell=True, bufsize=64, stderr=subprocess.PIPE)
        while True:
            chatter = p.stderr.read(1024)
            durationRes = re.search(r"Duration:\s(?P<duration>\S+)", chatter)
            if durationRes:
                durationList = durationRes.groupdict()['duration'][:-1].split(':')
                duration = int(durationList[0])*3600 + int(durationList[1])*60 + float(durationList[2])
            result = re.search(r'\stime=(?P<time>\S+)', chatter)
            if result:
                elapsed_time = result.groupdict()['time'].split(':')
                secs = int(elapsed_time[0])*3600 + int(elapsed_time[1])*60 + float(elapsed_time[2])
                progress = secs/duration * 100
                QtGui.QApplication.processEvents()
                self.pBar.setValue(int(progress))
            if not chatter:
                break

        self.pBar.setValue(100)

def main():
    app = QtGui.QApplication(sys.argv)
    gui = ProgressBar()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()