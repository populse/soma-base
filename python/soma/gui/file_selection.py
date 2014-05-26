import os, re
from glob import glob
from soma.qt_gui import qt_backend
if __name__ == '__main__':
    qt_backend.set_qt_backend('PyQt4')
from soma.qt_gui.qt_backend.QtGui import QDialog, QTableWidgetItem, QVBoxLayout
from soma.qt_gui.qt_backend import loadUi


class CATIScanSelector(QDialog):
    '''
    Dirty implementation of selection dialog for CATI FOM.
    This class will be modified or removed and should not be used directly.
    '''
    labels = ['Study', 'Subject', 'Time point']
    glob = ('*', 'CONVERTED', '*', '*', '*')
    path_re = ('(?P<study>.*)', '(?P<test>CONVERTED)', '(?P<center>.*)',
        '(?P<subject>.*)', '(?P<time_point>.*)')
    match_groups = ['study', 'subject', 'time_point']

    def __init__(self, directory=None, parent=None):
        super(CATIScanSelector, self).__init__(parent=parent)
        ui = os.path.join(__file__[: __file__.rfind('.')] + '.ui')
        ui_obj = loadUi(ui, self)
        if qt_backend.get_qt_backend() == 'PySide':
            self.table = ui_obj.table
            self.status = ui_obj.status
            layout = QVBoxLayout(self)
            self.setLayout(layout)
            layout.addWidget(ui_obj)
        if directory:
            self.reset(directory)


    def reset(self, directory):
        '''
        Clear the selection dialog and parse directory to extract selectable
        attributes.
        '''
        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(self.labels)
        self.table.setRowCount(0)
        studies = set()
        time_points = set()
        subjects = set()
        path_re = re.compile(os.path.join(os.path.join(
            directory, *self.path_re)))
        self.attributes = []
        for i in glob(os.path.join(directory, *self.glob)):
            match = path_re.match(i)
            if match:
                self.attributes.append(match.groupdict())
                row = self.table.rowCount()
                self.table.setRowCount(row + 1)
                for i in xrange(len(self.match_groups)):
                    self.table.setItem(row, i,
                        QTableWidgetItem(match.group(self.match_groups[i])))
        self.table.resizeColumnsToContents()
        self.table.itemSelectionChanged.connect(self._update_selection)
        self._update_selection()


    def _update_selection(self):
      '''
      Called each time the selection is changed to update QDialog (e.g. the
      status bar with number of items selected).
      '''
      count = 0
      for range in self.table.selectedRanges():
        count += range.bottomRow() - range.topRow() + 1
      if count:
        self.status.setText('%d item selected' % count)
      else:
        self.status.setText('No item selected')


    def select(self):
        '''
        After a modal execution of the QDialog, returns a list of dictionaries
        (one for each selected item) or False if the user did not pressed "Ok".
        '''
        if self.exec_() == self.Accepted:
            result = []
            for range in self.table.selectedRanges():
                result.extend(
                    self.attributes[range.topRow() : range.bottomRow() + 1])
            return result
        else:
            return False


class BrainVISAScanSelector(CATIScanSelector):
    '''
    Dirty implementation of selection dialog for Morphologist FOM.
    This class will be modified or removed and should not be used directly.
    '''
    labels = ['Center', 'Subject', 'Acquisition']
    glob = ('*', '*', 't1mri', '*')
    path_re = ('(?P<center>.*)', '(?P<subject>.*)', 't1mri',
        '(?P<acquisition>.*)')
    match_groups = ['center', 'subject', 'acquisition']


class FileAttributeSelection(object):
    '''
    A FileAttributeSelection is used to select multiple files according to
    their attributes as defined in a given FOM.

    Example:

    from soma.gui.file_selection import FileAttributeSelection
    file_selection = FileAttributeSelection()
    selection = file_selection.select(fom, 'unused', ['unused'], sys.argv[1])

    '''
    _selectors = {
        ('.*cati.*', '.*'): CATIScanSelector,
        ('.*brainvisa.*', '.*'): BrainVISAScanSelector,
        ('morphologist.*', '.*'): BrainVISAScanSelector,
    }

    def __init__(self):
        self._selector_rules = [(re.compile(i[0]), re.compile(i[1]), j) \
            for i,j in self._selectors.iteritems()]


    def find_selector(self, fom_name, process_name, parameters):
        '''
        Find the selector class allowing to select multiple files for a given
        process.
        fom_name : FileOrganisationModel name
        process_name: name of the process
        parameters : list of parameter names

        return: a class derived from QDialog or None if none is found for the
                given parameters.

        Actual implementation is incomplete. It ignores parameters and only
        use a pattern matching on the FOM name and process_name.
        '''
        for fom_re, process_re, selector_class in self._selector_rules:
            if fom_re.match(fom_name) and process_re.match(process_name):
                return selector_class
        return None


    def select(self,fom_name, process, parameters, directory, parent=None):
        '''
        Find a selector class according to fom, process_name and parameters
        and display the selecion dialog.
        Return value can be:
            - None if no selector class had been found
            - False if the used did not closed the dialog by clicking "Ok"
            - a list of dictionaries (one for each selected item)
        '''
        selector_class = self.find_selector(fom_name, process, parameters)
        print 'selection_class', selector_class
        if selector_class:
            return selector_class(directory=directory).select()
        return None



if __name__ == '__main__':
    import sys
    from soma.qt_gui.qt_backend.QtGui import QApplication
    from pprint import pprint

    from soma.application import Application
    # First thing to do is to create an Application with name and version
    app = Application('soma.fom', '1.0')
    # Register module to load and call functions before and/or after
    # initialization
    app.plugin_modules.append('soma.fom')
    # Application initialization (e.g. configuration file may be read here)
    app.initialize()

    from pprint import pprint
    #fom = app.fom_manager.load_foms( 'morphologist-brainvisa-1.0' )
    fom_name = 'morphologist-brainvisa-1.0'
    #fom_name='morphologist-cati-memento'
    fom = app.fom_manager.load_foms(fom_name)


    app = QApplication(sys.argv)

    if len(sys.argv) >= 2:
        direct = sys.argv[1]
    else:
        direct = '/home/mb236582/datafom'
        #direct = '/nfs/neurospin/cati/cati_shared'
    file_selection = FileAttributeSelection()
    selection = file_selection.select(fom_name, 'unused', ['unused'], direct)

    #pprint( selection )

