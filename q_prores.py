__author__ = 'Natasha'
import subprocess
import shlex
import sys
import os
import shutil
from PyQt4 import QtGui, QtCore
from datetime import datetime

class FileBrowseWidget(QtGui.QWidget):
    '''
    Creates a widget that contains a label and a file browser
    '''
    def __init__(self, labelName):
        '''
        Creates the elements of the widget.
        :param labelName: Name of the label
        '''
        super(FileBrowseWidget, self).__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        hLayout = QtGui.QHBoxLayout()
        fileLabel = QtGui.QLabel(labelName)
        hLayout.addWidget(fileLabel)
        self.fileEdit = QtGui.QLineEdit("Select %s" % labelName)
        self.fileEdit.setReadOnly(True)
        self.fileEdit.setToolTip('Click to select a folder')
        self.fileEdit.mousePressEvent = self.openFileDialog
        hLayout.addWidget(self.fileEdit)
        self.layout.addLayout(hLayout,1,0)

    def openFileDialog(self, event):
        '''
        Opens a file browser when the text box is clicked.
        :param event: Event triggered when the text box is clicked.
        :return:
        '''
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        filename = dialog.getExistingDirectory(self, "Open Directory",
            QtCore.QDir.currentPath())
        self.fileEdit.setText(str(filename))

    def getFilePath(self):
        '''
        :return: The file selected by the user.
        '''
        return self.fileEdit.text()

class Q_ProresGui(QtGui.QMainWindow):
    '''
    Main Application Class.
    '''
    def __init__(self):
        '''
        Basic UI setup.
        '''
        super(Q_ProresGui, self).__init__()
        self.setWindowTitle('Q_ProresGui')
        window = QtGui.QWidget()
        self.centralLayout = QtGui.QHBoxLayout()
        window.setLayout(self.centralLayout)
        self.setCentralWidget(window)
        self.setupUI()

    def setupUI(self):
        viewerBox = QtGui.QGroupBox('File Options')
        vLayout = QtGui.QVBoxLayout()
        self.inputWidget = FileBrowseWidget("Input Image Folder")
        self.outputWidget = FileBrowseWidget("Output Movie Folder")
        vLayout.addWidget(self.inputWidget)
        vLayout.addWidget(self.outputWidget)
        viewerBox.setLayout(vLayout)
        self.centralLayout.addWidget(viewerBox)
        createButton = QtGui.QPushButton('Create Movie')
        createButton.clicked.connect(self.createMovie)
        vLayout.addWidget(createButton)

    def createMovie(self, event):
        inputFolder = self.inputWidget.getFilePath()
        outputFolder = self.outputWidget.getFilePath()
        if 'Select' in inputFolder or 'Select' in outputFolder:
            QtGui.QMessageBox.warning(self, "Warning", "Please select input and output folder")
            return
        tmpDir = '%s\\tmp' % inputFolder
        if not os.path.exists(tmpDir):
            os.mkdir(tmpDir)

        shotName, firstFrame,lastFrame, date = self.getShotInfo(inputFolder)

        self.generateSlugImages(tmpDir, shotName, firstFrame,lastFrame, date)
        self.generateSlugMovie(tmpDir, firstFrame)
        self.generateFileMovie(inputFolder, tmpDir, outputFolder, firstFrame, shotName)
        QtGui.QMessageBox.about(self, "Complete", "Conversion Complete")
        shutil.rmtree(tmpDir)

    def generateSlugImages(self, tmpDir, shotName, firstFrame, lastFrame, date):

        slugCommand = 'convert.exe -size 450x40 -background black -fill white -pointsize 28 ' \
                      'label:"quarks %s ball frames:10" %s\\slug.jpg' % (date,tmpDir)
        args = shlex.split(slugCommand)
        for i in range(firstFrame, lastFrame+1):
            args[-1] = '%s\\slug.%s.jpg' % (tmpDir, i)
            args[-2] = 'label:"quarks %s %s frames:%s"' % (date, shotName, i)
            subprocess.call(args, shell=True)

    def getShotInfo(self, inputFolder):
        date = datetime.now()
        dateStr = '%s/%s/%s' % (date.day, date.month, date.year)
        files =  [file for file in os.listdir(inputFolder) if file.endswith('.exr')]
        shotName = files[0].split('.')[0]
        firstFrame = files[0].split('.')[1]
        lastFrame = files[-1].split('.')[1]
        return shotName, int(firstFrame), int(lastFrame), dateStr

    def generateSlugMovie(self, tmpDir, firstFrame):
        slugMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s\\slug.%%0%sd.jpg" ' \
                     '-vcodec prores -profile:v 2 "%s\\slug.mov"' % (firstFrame, tmpDir, len(str(firstFrame)), tmpDir)
        args = shlex.split(slugMovCmd)
        subprocess.call(args, shell=True)

    def generateFileMovie(self, inputFolder, tmpDir, outputFolder, firstFrame, fileName):
        finalMovCmd = 'ffmpeg.exe -y -start_number 101 -an -i "%s\\%s.%%0%sd.exr" ' \
                      '-i "%s\\slug.mov" -filter_complex "overlay=1:1" ' \
                      '-vcodec prores -profile:v 2 "%s\\%s.mov" ' % (inputFolder,
                                                                        fileName,
                                                                        len(str(firstFrame)),
                                                                        tmpDir, outputFolder, fileName)
        args = shlex.split(finalMovCmd)
        subprocess.call(args, shell=True)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    gui = Q_ProresGui()
    gui.show()
    app.exec_()