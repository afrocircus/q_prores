__author__ = 'Natasha'
import subprocess
import shlex
import sys
import os
import shutil
import glob
import autoit
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
        self.fileEdit.setToolTip('Click to select a file')
        self.saveFilePath = QtCore.QDir.currentPath()
        hLayout.addWidget(self.fileEdit)
        self.layout.addLayout(hLayout,1,0)

    def addOpenFileDialogEvent(self):
        self.fileEdit.mousePressEvent = self.openFileDialog

    def addSaveFileDialogEvent(self):
        self.fileEdit.mousePressEvent = self.saveFileDialog

    def openFileDialog(self, event):
        '''
        Opens a file browser when the text box is clicked.
        :param event: Event triggered when the text box is clicked.
        :return:
        '''
        dialog = QtGui.QFileDialog()
        filename = dialog.getOpenFileName(self, "Select File",
            QtCore.QDir.currentPath(), options= QtGui.QFileDialog.DontUseNativeDialog)
        self.fileEdit.setText(str(filename))

    def saveFileDialog(self, event):
        dialog = QtGui.QFileDialog()
        filename = dialog.getSaveFileName(self, "Save File",
            self.saveFilePath, options= QtGui.QFileDialog.DontUseNativeDialog)
        self.fileEdit.setText(str(filename))

    def getFilePath(self):
        '''
        :return: The file selected by the user.
        '''
        return self.fileEdit.text()

    def setFilePath(self, filename):
        filename = str(filename)
        newFilename = filename.split('/')[-1].split('.')[0]
        newFilePath = '%s/%s.mov' % (os.path.dirname(filename), newFilename)
        self.fileEdit.setText(newFilePath)
        self.saveFilePath = newFilePath

class Q_ProresGui(QtGui.QMainWindow):
    '''
    Main Application Class.
    '''
    def __init__(self):
        '''
        Basic UI setup.
        '''
        super(Q_ProresGui, self).__init__()
        self.setWindowTitle('Loco VFX - QX Tools 2015 v1.6')
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(300,200)
        window = QtGui.QWidget()

        from style import pyqt_style_rc
        f = QtCore.QFile('style/style.qss')
        f.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        ts = QtCore.QTextStream(f)
        self.stylesheet = ts.readAll()
        window.setStyleSheet(self.stylesheet)
        self.centralLayout = QtGui.QVBoxLayout()
        window.setLayout(self.centralLayout)
        self.setCentralWidget(window)
        self.setupUI()

    def setupUI(self):
        viewerBox = QtGui.QGroupBox('File Options')
        vLayout = QtGui.QVBoxLayout()
        self.inputWidget = FileBrowseWidget("Input Image File  ")
        self.inputWidget.addOpenFileDialogEvent()
        self.outputWidget = FileBrowseWidget("Output Movie File")
        self.outputWidget.addSaveFileDialogEvent()
        self.inputWidget.fileEdit.textChanged.connect(self.outputWidget.setFilePath)
        self.inputWidget.fileEdit.textChanged.connect(self.setSlugLabel)
        vLayout.addWidget(self.inputWidget)
        vLayout.addWidget(self.outputWidget)
        viewerBox.setLayout(vLayout)
        self.centralLayout.addWidget(viewerBox)
        hLayout = QtGui.QHBoxLayout()

        self.slugBox = QtGui.QCheckBox()
        hLayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum))
        hLayout.addWidget(QtGui.QLabel('Slug'))
        hLayout.addWidget(self.slugBox)
        hLayout.addItem(QtGui.QSpacerItem(75,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed))
        hLayout.addWidget(QtGui.QLabel('Open Output Movie'))
        self.movBox = QtGui.QCheckBox()
        hLayout.addWidget(self.movBox)
        vLayout.addLayout(hLayout)
        self.slugBox.stateChanged.connect(self.showSlugOptions)

        self.slugFrameBox = QtGui.QGroupBox('Slug Options')
        self.centralLayout.addWidget(self.slugFrameBox)
        hslugLayout = QtGui.QGridLayout()
        self.slugFrameBox.setLayout(hslugLayout)
        hslugLayout.addWidget(QtGui.QLabel('Slug Label'),0,0)
        self.slugTextBox = QtGui.QLineEdit('Customize Slug Label')
        hslugLayout.addWidget(self.slugTextBox,0,1)
        self.slugFrameBox.setVisible(False)

        createButton = QtGui.QPushButton('Create Movie')
        createButton.clicked.connect(self.createMovie)
        self.centralLayout.addWidget(createButton)

        self.pLabel = QtGui.QLabel('')
        self.pBar = QtGui.QProgressBar()
        self.pBar.setVisible(False)
        self.pLabel.setVisible(False)
        self.centralLayout.addWidget(self.pLabel)
        self.centralLayout.addWidget(self.pBar)

    def setSlugLabel(self, filename):
        inputFolder = os.path.dirname(str(filename))
        imageExt = str(filename).split('.')[-1]
        shotName, firstFrame,lastFrame, date = self.getShotInfo(str(inputFolder), str(imageExt))
        label = 'Quarks %s %s Frame#' % (date, shotName)
        self.slugTextBox.setText(label)

    def showSlugOptions(self, state):
        if state == 2:
            self.slugFrameBox.setVisible(True)
            self.resize(self.sizeHint())
        else:
            self.slugFrameBox.setVisible(False)
            self.resize(310,200)

    def createMovie(self, event):
        inputFile = self.inputWidget.getFilePath()
        outputFile = str(self.outputWidget.getFilePath())

        slugChoice = self.slugBox.checkState()
        if 'Select' in inputFile or 'Select' in outputFile:
            self.setStyleSheet(self.stylesheet)
            QtGui.QMessageBox.warning(self, "Warning", "Please select input and output folder")
            return

        inputFolder = os.path.dirname(str(inputFile))
        imageExt = str(inputFile).split('.')[-1]
        if not outputFile.endswith('.mov'):
            outputFile = '%s.mov' % outputFile

        shotName, firstFrame,lastFrame, date = self.getShotInfo(inputFolder, imageExt)
        if shotName == '':
            self.setStyleSheet(self.stylesheet)
            QtGui.QMessageBox.warning(self, "Warning", "No files found with %s extension" % imageExt)
            return

        self.pBar.setVisible(True)
        self.pLabel.setVisible(True)
        self.resize(self.sizeHint())
        self.pBar.setValue(0)
        self.pBar.setMinimum(0)
        self.pBar.setMaximum(100)
        animation = QtCore.QPropertyAnimation(self.pBar, "value")

        if slugChoice == 2:
            self.pLabel.setText('Creating Slug...')
            tmpDir = '%s\\tmp' % os.environ['TEMP']
            if not os.path.exists(tmpDir):
                os.mkdir(tmpDir)
            slugResult = self.generateSlugImages(tmpDir, shotName, firstFrame,lastFrame, date)
            if slugResult != 0:
                self.setStyleSheet(self.stylesheet)
                QtGui.QMessageBox.warning(self, "Error", "Error while creating slug images!")
                return
            slugMovResult = self.generateSlugMovie(tmpDir, firstFrame)
            if slugMovResult != 0:
                self.setStyleSheet(self.stylesheet)
                QtGui.QMessageBox.warning(self, "Error", "Error while creating slug movie!")
                return
            self.pLabel.setText('Encoding movie...')
            result = self.generateFileMovie(inputFolder, tmpDir, outputFile, firstFrame, shotName, imageExt, lastFrame)
            if result != 0:
                self.setStyleSheet(self.stylesheet)
                QtGui.QMessageBox.warning(self, "Error", "Error during final movie conversion!")
                return
            '''animation.setDuration(1000)
            animation.setStartValue(self.pBar.value())
            animation.setEndValue(100)
            animation.finished.connect(self.progressBarAnimationComplete)
            animation.start()'''
            self.pBar.setValue(100)
            self.progressBarAnimationComplete()
            shutil.rmtree(tmpDir)
        else:
            self.pLabel.setText('Encoding Movie...')
            result = self.generateFileMovieNoSlug(inputFolder, outputFile, firstFrame, shotName, imageExt, lastFrame)
            if result == 0:
                self.pLabel.setText('Encoding Complete')
                self.pBar.setValue(100)
                self.setStyleSheet(self.stylesheet)
                QtGui.QMessageBox.about(self, "Complete", "Conversion Complete")
                if self.movBox.checkState() == 2:
                    self.openOutputMovie(outputFile)
            else:
                self.setStyleSheet(self.stylesheet)
                QtGui.QMessageBox.warning(self, "Error", "Conversion Error!")

    def progressBarAnimationComplete(self):
        self.pLabel.setText('Encoding complete.')
        self.setStyleSheet(self.stylesheet)
        QtGui.QMessageBox.about(self, "Complete", "Conversion Complete")
        if self.movBox.checkState() == 2:
            self.openOutputMovie(str(self.outputWidget.getFilePath()))

    def openOutputMovie(self, outputFile):
        videoPlayerDir = self.getVideoPlayer()
        if videoPlayerDir == '':
            return
        self.pLabel.setText('Opening Movie %s' % outputFile.split('/')[-1])
        title = outputFile.split('/')[-1].split('.')[0]
        outputFile = outputFile.replace('/','\\')
        autoit.run('%s %s' % (videoPlayerDir, outputFile))
        if 'QuickTime' in videoPlayerDir:
            autoit.win_wait(title, 100)
            import time
            time.sleep(3)
            autoit.control_send(title, '', '{CTRLDOWN}0{CTRLUP}')

    def getVideoPlayer(self):
        videoPlayerDir = ''
        videoPlayerDirList = glob.glob('C:\\Program*\\QuickTime*')
        if videoPlayerDirList:
            videoPlayerDir = '%s\\QuickTimePlayer.exe' % videoPlayerDirList[0]
        else:
            videoPlayerDirList = glob.glob('C:\Program*\\VideoLan*')
            if videoPlayerDirList:
                videoPlayerDir = '%s\\VLC\\vlc.exe' % videoPlayerDirList[0]
            else:
                self.setStyleSheet(self.stylesheet)
                QtGui.QMessageBox.warning(self, "Video Player Error", "QuickTime or VLC not installed.")
        return videoPlayerDir

    def generateSlugImages(self, tmpDir, shotName, firstFrame, lastFrame, date):

        slugCommand = 'convert.exe -size 450x40 -background black -fill white -pointsize 20 ' \
                      'label:"quarks %s ball frames:10" %s\\slug.jpg' % (date,tmpDir)
        args = shlex.split(slugCommand)
        result = []
        label = str(self.slugTextBox.text())
        label = label.replace('Frame#', '')
        totalFrames = lastFrame - firstFrame
        incrValue = 40.0/totalFrames
        count = self.pBar.value()
        for i in range(firstFrame, lastFrame+1):
            args[-1] = '%s\\slug.%s.jpg' % (tmpDir, i)
            args[-2] = 'label:%s %s' % (label, i)
            result.append(subprocess.call(args, shell=True))
            count = count + incrValue
            self.pBar.setValue(count)
        for i in result:
            if i != 0:
                return 1
        return 0

    def getShotInfo(self, inputFolder, imageExt):
        date = datetime.now()
        dateStr = '%s/%s/%s' % (date.day, date.month, date.year)
        files = [file for file in os.listdir(inputFolder) if file.endswith(imageExt)]
        if files:
            shotName = files[0].split('.')[0]
            firstFrame = files[0].split('.')[1]
            lastFrame = files[-1].split('.')[1]
            return shotName, int(firstFrame), int(lastFrame), dateStr
        else:
            return '',0,0,dateStr

    def generateSlugMovie(self, tmpDir, firstFrame):
        slugMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s\\slug.%%0%sd.jpg" ' \
                     '-vcodec prores -profile:v 2 "%s\\slug.mov"' % (firstFrame, tmpDir, len(str(firstFrame)), tmpDir)
        args = shlex.split(slugMovCmd)
        result = subprocess.call(args, shell=True)
        return result

    def generateFileMovie(self, inputFolder, tmpDir, outputFile, firstFrame, fileName, imageExt, lastFrame):
        if imageExt == 'exr':
            self.convertExr(inputFolder, fileName, firstFrame, lastFrame)
            filePath = '%s\\exrTmp\\%s' % (os.environ['TEMP'], fileName)
        else:
            filePath = '%s\\%s' % (inputFolder, fileName)
        inputFile = '%s.%s.%s' % (fileName, firstFrame, imageExt)

        finalMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s.%%0%sd.%s" ' \
                      '-i "%s\\slug.mov" -metadata comment="Source Image:%s" -filter_complex "overlay=1:1" ' \
                      '-vcodec prores -profile:v 2 "%s" ' % (firstFrame, filePath, len(str(firstFrame)),
                                                                     imageExt, tmpDir, inputFile,
                                                                     outputFile)
        args = shlex.split(finalMovCmd)
        result = subprocess.call(args, shell=True)
        if imageExt == '.exr':
            shutil.rmtree('%s/exrTmp' % inputFolder)
        return result

    def generateFileMovieNoSlug(self, inputFolder, outputFile, firstFrame, fileName, imageExt, lastFrame):
        if imageExt == 'exr':
            self.convertExr(inputFolder, fileName, firstFrame, lastFrame)
            filePath = '%s\\exrTmp\\%s' % (os.environ['TEMP'], fileName)
        else:
            filePath = '%s\\%s' % (inputFolder, fileName)

        finalMovCmd = 'ffmpeg.exe -y -start_number %s  -an -i "%s.%%0%sd.%s" ' \
                      '-metadata comment="Source Image:%s.%s.%s" -vcodec prores ' \
                      '-profile:v 2 "%s" ' % (firstFrame, filePath,
                                              len(str(firstFrame)),
                                              imageExt, fileName,firstFrame,imageExt, outputFile)
        args = shlex.split(finalMovCmd)
        result = subprocess.call(args, shell=True)
        if imageExt == '.exr':
            shutil.rmtree('%s/exrTmp' % inputFolder)
        return result

    def convertExr(self, inputFolder, fileName, firstFrame, lastFrame):
        if not os.path.exists('%s/exrTmp' % os.environ['TEMP']):
            os.mkdir('%s/exrTmp' % os.environ['TEMP'])
        slugCommand = 'convert.exe %s\\%s.exr "%s\\exrTmp\\%s.exr"' % (inputFolder,fileName,os.environ['TEMP'],fileName)
        args = shlex.split(slugCommand)
        totalFrames = lastFrame-firstFrame
        incrValue = 50.0/totalFrames
        count = self.pBar.value()
        for i in range(firstFrame, lastFrame+1):
            args[1] = '%s/%s.%s.exr' % (inputFolder, fileName, i)
            args[2] = '%s/exrTmp/%s.%s.exr' % (os.environ['TEMP'], fileName, i)
            subprocess.call(args, shell=True)
            count = count + incrValue
            self.pBar.setValue(count)

def main():
    app = QtGui.QApplication(sys.argv)
    gui = Q_ProresGui()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()