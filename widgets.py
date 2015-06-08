__author__ = 'Natasha'
import os
from PyQt4 import QtGui, QtCore

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
        '''
        Opens a file browser when the text box is clicked.
        :param event: Event triggered when the text box is clicked.
        :return:
        '''
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
        '''
        :param filename: The text box is set with this filename
        '''
        filename = str(filename)
        newFilename = filename.split('/')[-1].split('.')[0]
        newFilePath = '%s/%s.mov' % (os.path.dirname(filename), newFilename)
        self.fileEdit.setText(newFilePath)
        self.saveFilePath = newFilePath

class BatchRunWidget(QtGui.QWidget):
    '''
    Creates a widget that contains a label and a file browser
    '''
    def __init__(self):
        '''
        Creates the elements of the widget.
        '''
        super(BatchRunWidget, self).__init__()
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        viewerBox = QtGui.QGroupBox('Batch Options')
        vLayout = QtGui.QVBoxLayout()
        viewerBox.setLayout(vLayout)
        layout.addWidget(viewerBox)
        hLayout = QtGui.QHBoxLayout()
        vLayout.addLayout(hLayout)
        hLayout2 = QtGui.QHBoxLayout()
        vLayout.addLayout(hLayout2)
        hLayout.addWidget(QtGui.QLabel('Input Folder   '))
        self.fileEdit = QtGui.QLineEdit('Select Input Folder')
        hLayout.addWidget(self.fileEdit)
        self.fileEdit.setReadOnly(True)
        self.fileEdit.setToolTip('Click to select a folder')
        self.fileEdit.mousePressEvent = self.openFileDialog
        hLayout2.addWidget(QtGui.QLabel('Output Folder'))
        self.opFileEdit = QtGui.QLineEdit('Select Output Folder')
        hLayout2.addWidget(self.opFileEdit)
        self.opFileEdit.setReadOnly(True)
        self.opFileEdit.setToolTip('Click to select a folder')
        self.opFileEdit.mousePressEvent = self.saveFileDialog
        self.listWidget = QtGui.QListWidget()
        self.listWidget.setMaximumSize(200,150)
        self.listWidget.setAutoScroll(True)
        vLayout.addWidget(self.listWidget)
        vLayout.addItem(QtGui.QSpacerItem(10,1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

    def openFileDialog(self, event):
        '''
        Opens a file browser when the text box is clicked.
        :param event: Event triggered when the text box is clicked.
        :return:
        '''
        dialog = QtGui.QFileDialog()
        filename = dialog.getExistingDirectory(self, "Select Folder",
            QtCore.QDir.currentPath(), options= QtGui.QFileDialog.DontUseNativeDialog)
        self.fileEdit.setText(str(filename))
        self.opFileEdit.setText(str(filename))
        self.listWidget.clear()
        self.fileDict = {}
        self.getAllImageSequences(str(filename))
        for key in self.fileDict.keys():
            folder = key.replace('%s' % str(filename), '')
            if folder[1:] == '':
                folder = '/./'
            self.addCheckBoxes(folder[1:])

    def saveFileDialog(self, event):
        '''
        Opens a file browser when the text box is clicked.
        :param event: Event triggered when the text box is clicked.
        :return:
        '''
        saveFilePath = self.fileEdit.text()
        if str(saveFilePath) == '':
            saveFilePath = QtCore.QDir.currentPath()

        dialog = QtGui.QFileDialog()
        filename = dialog.getExistingDirectory(self, "Save File",
                saveFilePath, options= QtGui.QFileDialog.DontUseNativeDialog)
        self.opFileEdit.setText(str(filename))

    def getFilePath(self):
        '''
        :return: The file selected by the user.
        '''
        return self.fileEdit.text()

    def addCheckBoxes(self, dirName):
        '''
        Add checkbox with label dirName. Set state to checked.
        :param dirName: Name of directory
        :return:
        '''
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        checkbox = QtGui.QCheckBox(dirName)
        checkbox.setCheckState(2)
        self.listWidget.setItemWidget(item, checkbox)

    def getAllImageSequences(self, inputFolder):
        '''
        Determines all image sequences in the given folder recursively.
        Creates a dict where the key is the folder name and list is the image sequences file list.
        :param inputFolder: The root folder.
        :return:
        '''
        fileList = []
        numList = []
        for filePath in os.listdir(inputFolder):
            if os.path.isdir('%s/%s' % (inputFolder,filePath)):
                self.getAllImageSequences('%s/%s' % (inputFolder,filePath))
            else:
                fileParts = filePath.split('.')
                if len(fileParts) == 3 and fileParts[1].isdigit():
                    fileList.append(filePath)
                    numList.append(int(fileParts[1]))
        if len(fileList) != 0:
            numList.sort()
            temp = [numList[i+1]-numList[i] for i in range(len(numList)-1)]
            if len(set(temp)) == 1:
                self.fileDict[inputFolder] = fileList

    def getAllCheckedItems(self):
        '''
        :return: dirList: List of all the checked items in the list widget.
        '''
        dirList = []
        for index in xrange(self.listWidget.count()):
            checkBox = self.listWidget.itemWidget(self.listWidget.item(index))
            if checkBox.checkState() == 2:
                dirList.append(checkBox.text())
