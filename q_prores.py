__author__ = 'Natasha'
import subprocess
import shlex
import sys
import os
import shutil
import glob
import autoit
from widgets import FileBrowseWidget
from widgets import BatchRunWidget
from PyQt4 import QtGui, QtCore
from datetime import datetime

class Q_ProresGui(QtGui.QMainWindow):
    '''
    Main Application Class.
    '''
    def __init__(self):
        '''
        Basic UI setup.
        '''
        super(Q_ProresGui, self).__init__()
        self.setWindowTitle('Loco VFX - QX Tools 2015 v1.9')
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(320,200)
        window = QtGui.QWidget()

        from style import pyqt_style_rc         # Import the Qt Style Sheet
        f = QtCore.QFile('style/style.qss')
        f.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        ts = QtCore.QTextStream(f)
        self.stylesheet = ts.readAll()
        window.setStyleSheet(self.stylesheet)

        self.centralLayout = QtGui.QGridLayout()
        window.setLayout(self.centralLayout)
        self.setCentralWidget(window)
        self.setupUI()

    def setupUI(self):
        # Setup the input and output file widgets
        viewerBox = QtGui.QGroupBox('File Options')
        vLayout = QtGui.QVBoxLayout()
        self.inputWidget = FileBrowseWidget("Input Image File  ")
        self.inputWidget.addOpenFileDialogEvent()
        self.outputWidget = FileBrowseWidget("Output Movie File")
        self.outputWidget.addSaveFileDialogEvent()
        # Set trigger to change output path when input file is selected.
        self.inputWidget.fileEdit.textChanged.connect(self.outputWidget.setFilePath)
        # Set trigger to change label when input file is selected.
        self.inputWidget.fileEdit.textChanged.connect(self.setSlugLabel)
        vLayout.addWidget(self.inputWidget)
        vLayout.addWidget(self.outputWidget)
        viewerBox.setLayout(vLayout)
        self.centralLayout.addWidget(viewerBox)
        hLayout = QtGui.QHBoxLayout()

        # Setup the slug checkbox
        self.slugBox = QtGui.QCheckBox()
        hLayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum))
        hLayout.addWidget(QtGui.QLabel('Slug'))
        hLayout.addWidget(self.slugBox)
        self.slugBox.stateChanged.connect(self.showSlugOptions)
        hLayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed))

        # Setup the movie checkbox
        hLayout.addWidget(QtGui.QLabel('Open Output Movie'))
        self.movBox = QtGui.QCheckBox()
        hLayout.addWidget(self.movBox)
        hLayout.addItem(QtGui.QSpacerItem(20,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed))

        # Setup batch options
        hLayout.addWidget(QtGui.QLabel("Batch"))
        self.batchBox = QtGui.QCheckBox()
        hLayout.addWidget(self.batchBox)
        self.batchBox.stateChanged.connect(self.showBatchOptions)
        vLayout.addLayout(hLayout)
        vLayout.addItem(QtGui.QSpacerItem(10,1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

        # Setup the slug options and set visibility to False.
        self.slugFrameBox = QtGui.QGroupBox('Slug Options')
        self.centralLayout.addWidget(self.slugFrameBox)
        hslugLayout = QtGui.QGridLayout()
        self.slugFrameBox.setLayout(hslugLayout)
        hslugLayout.addWidget(QtGui.QLabel('Slug Label'),0,0)
        self.slugTextBox = QtGui.QLineEdit('Customize Slug Label')
        hslugLayout.addWidget(self.slugTextBox,0,1)
        self.slugFrameBox.setVisible(False)

        # Setup Batch Widget
        self.batchWidget = BatchRunWidget()
        self.centralLayout.addWidget(self.batchWidget, 0,1)
        self.batchWidget.setVisible(False)

        createButton = QtGui.QPushButton('Create Movie')
        createButton.clicked.connect(self.createMovie)
        self.centralLayout.addWidget(createButton)

        # Setup the progress bar and set visible to False
        self.pLabel = QtGui.QLabel('')
        self.pBar = QtGui.QProgressBar()
        self.pBar.setVisible(False)
        self.pLabel.setVisible(False)
        self.centralLayout.addWidget(self.pLabel)
        self.centralLayout.addWidget(self.pBar)

    def setSlugLabel(self, filename):
        '''
        Sets the slug label based on input file name.
        :param filename: Name of the input file
        '''
        inputFolder = os.path.dirname(str(filename))
        imageExt = str(filename).split('.')[-1]
        shotName, firstFrame,lastFrame, date = self.getShotInfo(str(inputFolder), str(imageExt))
        label = 'Quarks %s %s Frame#' % (date, shotName)
        self.slugTextBox.setText(label)

    def showSlugOptions(self, state):
        '''
        Sets visibilty of slug options based on state of slug check box.
        Resizes the window appropriately.
        :param state: State of the slug check box.
        '''
        if state == 2:
            self.slugFrameBox.setVisible(True)
            self.resize(self.sizeHint())
        else:
            self.slugFrameBox.setVisible(False)
            self.resize(self.sizeHint())

    def showBatchOptions(self, state):
        '''
        Sets visibilty of the batch options based on state of checkbox
        :param state: State of batch checkbox
        '''
        if state == 2:
            self.batchWidget.setVisible(True)
            self.resize(self.sizeHint())
        else:
            self.batchWidget.setVisible(False)
            self.resize(self.sizeHint())

    def createMovie(self, event):
        '''
        :param event: This event is triggered when the "Create Movie" button is pressed.
        :return:
        '''
        inputFile = self.inputWidget.getFilePath()
        outputFile = str(self.outputWidget.getFilePath())

        slugChoice = self.slugBox.checkState()
        # Check if file names are valid.
        if 'Select' in inputFile or 'Select' in outputFile:
            self.setStyleSheet(self.stylesheet)
            QtGui.QMessageBox.warning(self, "Warning", "Please select input and output folder")
            return

        inputFolder = os.path.dirname(str(inputFile))
        imageExt = str(inputFile).split('.')[-1]
        if not outputFile.endswith('.mov'):
            outputFile = '%s.mov' % outputFile

        shotName, firstFrame,lastFrame, date = self.getShotInfo(inputFolder, imageExt)
        # Check if frame numbers are valid
        if firstFrame == 0 or lastFrame == 0:
            self.setStyleSheet(self.stylesheet)
            QtGui.QMessageBox.warning(self, "Error", "Frame numbers are incorrect! Numbers must start with 1. Eg. 1001")
            return

        self.pBar.setVisible(True)
        self.pLabel.setVisible(True)
        self.resize(self.sizeHint())
        self.pBar.setValue(0)
        self.pBar.setMinimum(0)
        self.pBar.setMaximum(100)

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
        '''
        Opens the output movie file with the installed player using autoit
        :param outputFile: Output movie file
        '''
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
            # This is a hack. We wait 3 sec for the movie to load completely before sending the next signal.
            # Otherwise the signal is not registered.
            time.sleep(3)
            autoit.control_send(title, '', '{CTRLDOWN}0{CTRLUP}')

    def getVideoPlayer(self):
        '''
        Checks if QuickTimePlayer exists. If not checks for VLC player.
        :return: videoPlayerDir: Path of the video player
        '''
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
        '''
        Slug Images are generated and stored in tmpDir
        :param tmpDir: Temporary Directory in the Users local temp
        :param shotName: Name of the shot  type:str
        :param firstFrame: First frame type:int
        :param lastFrame: Last frame type: int
        :param date: Date mm/dd/yyyy type:str
        :return:
        '''

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
            args[-2] = 'label:%s %s' % (label, str(i).replace('1','0',1))
            result.append(subprocess.call(args, shell=True))
            count = count + incrValue
            self.pBar.setValue(count)
        for i in result:
            if i != 0:
                return 1
        return 0

    def getShotInfo(self, inputFolder, imageExt):
        '''
        Returns shot information
        :param inputFolder: Input Folder
        :param imageExt: Image extension
        :return: shotName, first frame, last frame and date
        '''
        date = datetime.now()
        dateStr = '%s/%s/%s' % (date.day, date.month, date.year)
        files = [file for file in os.listdir(inputFolder) if file.endswith(imageExt)]
        files.sort()
        if files:
            shotName = files[0].split('.')[0]
            firstFrame = files[0].split('.')[1]
            lastFrame = files[-1].split('.')[1]
            return shotName, int(firstFrame), int(lastFrame), dateStr
        else:
            return '',0,0,dateStr

    def generateSlugMovie(self, tmpDir, firstFrame):
        '''
        Generates a movie of the slug images. Stores it in the same temp folder
        :param tmpDir: Temp Folder in the users local temp.
        :param firstFrame: first frame
        :return:
        '''
        slugMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s\\slug.%%0%sd.jpg" ' \
                     '-vcodec prores -profile:v 2 "%s\\slug.mov"' % (firstFrame, tmpDir, len(str(firstFrame)), tmpDir)
        args = shlex.split(slugMovCmd)
        result = subprocess.call(args, shell=True)
        return result

    def generateFileMovie(self, inputFolder, tmpDir, outputFile, firstFrame, fileName, imageExt, lastFrame):
        '''
        Composites the slug movie with the input images to generate the final movie.
        '''
        if imageExt == 'exr':
            # Convert exr to exr using imagemagik to get the exr format correct.
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
        '''
        Generate the movie without the slug, only from the input image sequence.
        '''
        if imageExt == 'exr':
            # Convert exr to correct format using imagemagik
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
        '''
        Generate new exr from input exr images using ImageMagik.
        This was required as the compression type of the input exr images was not supported.
        '''
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