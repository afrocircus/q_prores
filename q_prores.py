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
        #self.fileEdit.mousePressEvent = self.openFileDialog
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
            QtCore.QDir.currentPath())
        self.fileEdit.setText(str(filename))

    def saveFileDialog(self, event):
        dialog = QtGui.QFileDialog()
        filename = dialog.getSaveFileName(self, "Save File",
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
        self.inputWidget = FileBrowseWidget("Input Image File")
        self.inputWidget.addOpenFileDialogEvent()
        self.outputWidget = FileBrowseWidget("Output Movie File")
        self.outputWidget.addSaveFileDialogEvent()
        vLayout.addWidget(self.inputWidget)
        vLayout.addWidget(self.outputWidget)
        viewerBox.setLayout(vLayout)
        self.centralLayout.addWidget(viewerBox)
        hLayout = QtGui.QHBoxLayout()
        self.extBox = QtGui.QComboBox()
        self.extBox.addItems(['.jpg','.exr','.tif'])
        self.slugBox = QtGui.QCheckBox()
        hLayout.addItem(QtGui.QSpacerItem(20,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
        hLayout.addWidget(QtGui.QLabel('Image Extension'))
        hLayout.addWidget(self.extBox)
        hLayout.addItem(QtGui.QSpacerItem(20,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
        hLayout.addWidget(QtGui.QLabel('Slug'))
        hLayout.addWidget(self.slugBox)
        vLayout.addLayout(hLayout)
        createButton = QtGui.QPushButton('Create Movie')
        createButton.clicked.connect(self.createMovie)
        vLayout.addWidget(createButton)

    def createMovie(self, event):
        inputFile = self.inputWidget.getFilePath()
        outputFile = str(self.outputWidget.getFilePath())

        imageExt = self.extBox.currentText()
        slugChoice = self.slugBox.checkState()
        if 'Select' in inputFile or 'Select' in outputFile:
            QtGui.QMessageBox.warning(self, "Warning", "Please select input and output folder")
            return

        inputFolder = os.path.dirname(str(inputFile))
        if not outputFile.endswith('.mov'):
            outputFile = '%s.mov' % outputFile

        shotName, firstFrame,lastFrame, date = self.getShotInfo(inputFolder, imageExt)
        if shotName == '':
            QtGui.QMessageBox.warning(self, "Warning", "No files found with %s extension" % imageExt)
            return

        if slugChoice == 2:
            tmpDir = '%s\\tmp' % os.path.dirname(inputFolder)
            if not os.path.exists(tmpDir):
                os.mkdir(tmpDir)
            slugResult = self.generateSlugImages(tmpDir, shotName, firstFrame,lastFrame, date)
            if slugResult != 0:
                QtGui.QMessageBox.warning(self, "Error", "Error while creating slug images!")
                return
            slugMovResult = self.generateSlugMovie(tmpDir, firstFrame)
            if slugMovResult != 0:
                QtGui.QMessageBox.warning(self, "Error", "Error while creating slug movie!")
                return
            result = self.generateFileMovie(inputFolder, tmpDir, outputFile, firstFrame, shotName, imageExt, lastFrame)
            if result != 0:
                QtGui.QMessageBox.warning(self, "Error", "Error during final movie conversion!")
                return
            QtGui.QMessageBox.about(self, "Complete", "Conversion Complete")
            shutil.rmtree(tmpDir)
        else:
            result = self.generateFileMovieNoSlug(inputFolder, outputFile, firstFrame, shotName, imageExt, lastFrame)
            if result == 0:
                QtGui.QMessageBox.about(self, "Complete", "Conversion Complete")
            else:
                QtGui.QMessageBox.warning(self, "Error", "Conversion Error!")

    def generateSlugImages(self, tmpDir, shotName, firstFrame, lastFrame, date):

        slugCommand = 'convert.exe -size 450x40 -background black -fill white -pointsize 20 ' \
                      'label:"quarks %s ball frames:10" %s\\slug.jpg' % (date,tmpDir)
        args = shlex.split(slugCommand)
        result = []
        for i in range(firstFrame, lastFrame+1):
            args[-1] = '%s\\slug.%s.jpg' % (tmpDir, i)
            args[-2] = 'label:"quarks %s %s frames:%s"' % (date, shotName, i)
            result.append(subprocess.call(args, shell=True))
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
        if imageExt == '.exr':
            self.convertExr(inputFolder, fileName, firstFrame, lastFrame)
            fileName = 'exrTmp\\%s' % fileName

        finalMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s\\%s.%%0%sd%s" ' \
                      '-i "%s\\slug.mov" -filter_complex "overlay=1:1" ' \
                      '-vcodec prores -profile:v 2 "%s" ' % (firstFrame, inputFolder,
                                                                     fileName, len(str(firstFrame)),
                                                                     imageExt, tmpDir,
                                                                     outputFile)
        args = shlex.split(finalMovCmd)
        result = subprocess.call(args, shell=True)
        if imageExt == '.exr':
            shutil.rmtree('%s/exrTmp' % inputFolder)
        return result

    def generateFileMovieNoSlug(self, inputFolder, outputFile, firstFrame, fileName, imageExt, lastFrame):
        if imageExt == '.exr':
            self.convertExr(inputFolder, fileName, firstFrame, lastFrame)
            fileName = 'exrTmp\\%s' % fileName

        finalMovCmd = 'ffmpeg.exe -y -start_number %s  -an -i "%s\\%s.%%0%sd%s" ' \
                      '-vcodec prores -profile:v 2 "%s" ' % (firstFrame, inputFolder,
                                                                     fileName, len(str(firstFrame)),
                                                                     imageExt,
                                                                     outputFile)
        args = shlex.split(finalMovCmd)
        result = subprocess.call(args, shell=True)
        if imageExt == '.exr':
            shutil.rmtree('%s/exrTmp' % inputFolder)
        return result

    def convertExr(self, inputFolder, fileName, firstFrame, lastFrame):
        if not os.path.exists('%s/exrTmp' % inputFolder):
            os.mkdir('%s/exrTmp' % inputFolder)
        slugCommand = 'convert.exe %s\\%s.exr "%s\\exrTmp\\%s.exr"' % (inputFolder,fileName,inputFolder,fileName)
        args = shlex.split(slugCommand)
        for i in range(firstFrame, lastFrame+1):
            args[1] = '%s/%s.%s.exr' % (inputFolder, fileName, i)
            args[2] = '%s/exrTmp/%s.%s.exr' % (inputFolder, fileName, i)
            subprocess.call(args, shell=True)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    gui = Q_ProresGui()
    gui.show()
    app.exec_()