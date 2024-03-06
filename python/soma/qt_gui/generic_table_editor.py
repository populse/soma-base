import os
import re

from soma.qt_gui.qt_backend.Qt import *


class GenericTableEditor(QWidget):
    """Table viewer / editor widget"""

    def __init__(self, file=None, context=None, parent=None):
        QWidget.__init__(self, parent)
        self.layout = QVBoxLayout(self)
        self.context = context
        self.params = None
        self.cell2tab = None
        # - ------------------------------------------------------------- - #
        self.working_dir = "."
        self.precision = 4
        self.buf_table = None
        #
        # - the menu bar
        self.menuBar = QMenuBar(self)
        self.layout.addWidget(self.menuBar)
        self.menuBar.show()

        # - File menu
        self.menu_file = self.menuBar.addMenu("&File")

        # - - open
        self.menu_file.addAction("&Open", self.menu_open_action)

        # - - save_as
        self.menu_file.addAction("&Save as", self.menu_save_as_action)

        # - Edit menu
        self.menu_edit = self.menuBar.addMenu("&Edit")

        # - - select
        self.menu_file.addAction("&Select", self.menu_select_action)
        # - - replace
        self.menu_file.addAction("&Replace", self.menu_replace_action)
        # - - add col
        self.menu_file.addAction("&Add col", self.menu_addCol)
        # - - remove col
        self.menu_file.addAction("&Remove &col(s)", self.menu_removeCols)
        # - - add line
        self.menu_file.addAction("A&dd raw(s)", self.menu_addLine)
        # - - remove line
        self.menu_file.addAction("Remove &raw(s)", self.menu_removeLines)

        # - Settings menu
        self.menu_settings = self.menuBar.addMenu("&Settings")
        # - -
        self.menu_settings.addAction("&Parameters", self.showParamsBox)

        # - - View menu
        self.menu_view = self.menu_settings.addMenu("&View")
        self.precisionButtonGrp = QActionGroup(self)
        self.precisionButtonGrp.setExclusive(True)

        self.precision_full = QAction("Full precision", self.menu_view)
        self.precision_full.setObjectName("Precision1")
        self.precision_full.setCheckable(True)

        self.precision_4 = QAction("10^-4", self.menu_view)
        self.precision_4.setObjectName("Precision2")
        self.precision_4.setCheckable(True)
        self.precision_4.setChecked(True)

        self.precision_2 = QAction("10^-2", self.menu_view)
        self.precision_2.setObjectName("Precision")
        self.precision_2.setCheckable(True)

        self.precisionButtonGrp.addAction(self.precision_full)
        self.precisionButtonGrp.addAction(self.precision_2)
        self.precisionButtonGrp.addAction(self.precision_4)
        # self.precision_full.show()

        self.menu_view.addAction(self.precision_full)
        self.menu_view.addAction(self.precision_4)
        self.menu_view.addAction(self.precision_2)

        self.precisionButtonGrp.triggered.connect(self.setPrecision)

        # - Tool menu
        # self.menu_tool=self.menuBar.addMenu("&Tools")

        # -
        # self.menu_tool.addAction("&Convert cell to table",
        # self.showCell2TabBox)

        # - ------------------------------------------------------------- - #
        # - Table
        self.gui_table = QTableWidget(self)
        self.gui_table.setSortingEnabled(False)
        self.layout.addWidget(self.gui_table)
        self.gui_table.cellChanged.connect(self.guiVal2BufVal)
        self.gui_table.horizontalHeader().sectionClicked.connect(self.buf_table_sort)

        # - ------------------------------------------------------------- - #
        # - Operation
        self.operations_widget = QWidget(self)
        self.operations_layout = QVBoxLayout(self.operations_widget)
        self.operations_widget.setLayout(self.operations_layout)
        self.operations_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.operations_widget)

        ope_sort = QPushButton("Sort", self.operations_widget)
        self.operations_layout.addWidget(ope_sort)
        ope_sort.clicked.connect(self.buf_table_sort)
        if file:
            self.load_from_file(file)

    def buf_table_sort(self, col=None, ascending=True):
        self.current_col_index = 0
        self.current_col_index = self.getSelectedCols()[0]
        self.buf_table.sort(key=self.sort_key)
        self.gui_table.setSortingEnabled(False)
        self.buf_2_gui()

    def clear(self):
        self.buf_table = None
        self.data = None
        self.fileStructure = None
        self.col_names = None
        self.col_types = None
        self.setWindowTitle("No File loaded")
        self.buf_2_gui()

    def load_from_file(self, file=None, fileStructure=None):
        """This function needs the pandas module"""
        if file:
            self.file = file
        self.fileStructure = fileStructure

        # - clear the table
        self.gui_table.clear()
        import pandas as pd

        print(self.fileStructure)
        self.data = pd.read_csv(self.file)
        if self.data.shape[1] <= 1:
            self.data = pd.read_csv(self.file, sep=";")
        if self.data.shape[1] <= 1:
            self.data = pd.read_csv(self.file, sep="\t")
        if self.data.shape[1] <= 1:
            self.data = pd.read_csv(self.file, sep=" ")
        self.col_names = self.data.columns.tolist()

        col_types = pd.Series([self.data[col].dtype for col in self.data])
        col_types = col_types.replace(
            {"object": "varchar", "float64": "float", "int64": "integer"}
        )
        self.col_types = [t for t in col_types]
        self.buf_table = [l for l in self.data.itertuples(index=False)]
        self.gui_table.setColumnCount(self.data.shape[1])
        self.gui_table.setRowCount(self.data.shape[0])

        # GenericTableEditor.convTab2NativType(self.buf_table, self.col_types)
        self.buf_2_gui()

        # set the main window name
        self.setWindowTitle(os.path.basename(self.file))
        if self.parent() is not None:
            self.parent().setWindowTitle(os.path.basename(self.file))

    def numCols(self):
        if self.col_types:
            return len(self.col_types)
        else:
            return 0

    def numRows(self):
        if self.buf_table:
            return len(self.buf_table)
        else:
            return 0

    def buf_2_gui(self):
        # disable auto sorting temporarily because we need to freeze
        # the items position while inserting them
        sortstate = self.gui_table.isSortingEnabled()
        self.gui_table.setSortingEnabled(False)
        # update gui table size if needed
        if self.gui_table.columnCount() != self.numCols():
            self.gui_table.setColumnCount(self.numCols())
        if self.gui_table.rowCount() != self.numRows():
            self.gui_table.setRowCount(self.numRows())

        # update gui header
        if self.col_names:
            self.gui_table.setHorizontalHeaderLabels(self.col_names)

        # copy buf data into gui
        if self.buf_table:
            self.gui_table.blockSignals(True)
            for i in range(len(self.buf_table)):
                for j in range(len(self.buf_table[i])):
                    val = self.buf_table[i][j]
                    if self.precision and isinstance(val, float):
                        val = round(val, self.precision)
                    elif val is None:
                        val = "-"
                    it = QTableWidgetItem(str(val))
                    self.gui_table.setItem(i, j, it)
            self.gui_table.blockSignals(False)
        self.gui_table.setSortingEnabled(sortstate)

    def sort_key(self, a):
        return a[self.current_col_index]

    def menu_open_action(self):
        file = str(
            QFileDialog.getOpenFileName(
                self, "", "", "", None, QtGui.QFileDialog.DontUseNativeDialog
            )
        )
        if file and file != "":
            self.load_from_file(file=file)

    def menu_save_as_action(self):
        file = str(
            QFileDialog.getSaveFileName(
                self, "", "", "", None, QtGui.QFileDialog.DontUseNativeDialog
            )
        )
        self.data.to_csv(file, index=False)

    def menu_select_action(self):
        selection = []
        for item in self.gui_table.selectedItems():
            selection.append(str(item.text()))
        # send an 'inputSelection' event with the selection as parameter
        if self.context:
            self.context.event("inputSelection", selection)

    def menu_replace_action(self):
        try:
            from_str = str(
                QInputDialog.getText(
                    self,
                    "Enter regular expression",
                    "Enter query to replace",
                    QLineEdit.Normal,
                    "",
                )[0]
            )
            if not from_str:
                return None
            from_re = re.compile(from_str)
            to_str = str(
                QInputDialog.getText(
                    self,
                    "Enter regular expression",
                    "Replace " + from_str + " with",
                    QLineEdit.Normal,
                    "",
                )[0]
            )
            if not to_str:
                return None
            for tSelec in self.gui_table.selectedRanges():
                for row in range(tSelec.topRow(), tSelec.bottomRow() + 1):
                    for col in range(tSelec.leftColumn(), tSelec.rightColumn() + 1):
                        # regexp.sub(  	replacement, string
                        val = str(self.buf_table[row][col])
                        # if type(val)==types.StringType : val = str(val)
                        newval = from_re.sub(to_str, val)
                        self.setBufValFromStr(row, col, newval)
            self.buf_2_gui()
        except Exception as e:
            QMessageBox.warning(self, "WARNING", str(e))
            return None

    def menu_addCol(self):
        name = str(
            QInputDialog.getText(
                self, "Add column", "Enter column name", QLineEdit.Normal, ""
            )[0]
        )
        if not name:
            return None
        # add an item for each line in the buf tab
        for line in self.buf_table:
            line.append(0)
        if self.col_names:
            self.col_names.append(name)
        self.buf_2_gui()

    def menu_removeCols(self):
        selectedCols = self.getSelectedCols()
        selectedCols.sort()
        # remove in table
        nbDeleted = 0
        for c in selectedCols:
            for line in self.buf_table:
                del line[c - nbDeleted]
            if self.col_names:
                del self.col_names[c - nbDeleted]
            del self.col_types[c - nbDeleted]
            nbDeleted += 1
        self.buf_2_gui()

    def menu_addLine(self):
        nbline = QInputDialog.getInteger(
            self, "Add line(s)", "Enter number line(s) to add", 1, 1, 2147483647, 1
        )[0]
        for i in range(nbline):
            self.buf_table.append([0] * len(self.numCols()))
        self.buf_2_gui()

    def menu_removeLines(self):
        selectedRows = self.getSelectedRows()
        selectedRows.sort()
        # remove in table
        nbDeleted = 0
        for r in selectedRows:
            del self.buf_table[r - nbDeleted]
            nbDeleted += 1
        self.buf_2_gui()

    def getSelectedCols(self):
        ret = []
        for tSelec in self.gui_table.selectedRanges():
            for col in range(tSelec.leftColumn(), tSelec.rightColumn() + 1):
                ret.append(col)
        return ret

    def getSelectedRows(self):
        ret = []
        for tSelec in self.gui_table.selectedRanges():
            for raw in range(tSelec.topRow(), tSelec.bottomRow() + 1):
                ret.append(raw)
        return ret

    def getSelectedCells(self):
        selections = []
        # print
        # 'numSelections:',self.genericTableEditor.gui_table.numSelections ()
        for selectnb in self.gui_table.selectedRanges():
            selections.append(self.gui_table.selection(selectnb))

        selectedCells = []
        selectedCellsContent = []
        for s in self.gui_table.selectedRanges():
            for row in range(s.topRow(), s.bottomRow() + 1):
                for col in range(s.leftColumn(), s.rightColumn() + 1):
                    cell = [row, col]
                    if cell not in selectedCells:
                        selectedCells.append(cell)
                        selectedCellsContent.append(
                            str(self.gui_table.item(row, col).text())
                        )
        return selectedCellsContent

    def setBufValFromStr(self, row, col, valstr):
        """Set a value and the appropriate type in the data table from a string"""
        typeConversionRequired = False
        if self.col_types[col] == "integer":
            try:
                self.buf_table[row][col] = int(valstr)
            except ValueError:
                try:
                    typeConversionRequired = True
                    self.buf_table[row][col] = float(valstr)
                    self.col_types[col] = "float"
                except ValueError:
                    self.buf_table[row][col] = valstr
                    self.col_types[col] = "varchar"
        elif self.col_types[col] == "float":
            try:
                self.buf_table[row][col] = float(valstr)
            except ValueError:
                typeConversionRequired = True
                self.buf_table[row][col] = valstr
                self.col_types[col] = "varchar"
        else:
            self.buf_table[row][col] = valstr
        if typeConversionRequired:
            GenericTableEditor.convTab2NativType(self.buf_table, self.col_types)

    def guiVal2BufVal(self, row, col):
        guiVal = str(self.gui_table.item(row, col).text())
        self.setBufValFromStr(row, col, guiVal)

    def getMenuBar(self):
        return self.menuBar

    def showParamsBox(self):
        if not self.params:
            self.params = GenericTableEditor.Parameters(self)
        self.params.initFields(self.fileStructure)
        self.params.show()

    def setPrecision(self, button):
        if button is self.precision_full:
            self.precision = None
        elif button is self.precision_4:
            self.precision = 4
        elif button is self.precision_2:
            self.precision = 2
        else:
            print("unknown precision")
        self.buf_2_gui()

    @staticmethod
    def convTab2NativType(data, colTypes):
        for col in range(len(colTypes)):
            if colTypes[col] == "integer":
                for tuple in data:
                    if tuple[col]:
                        tuple[col] = int(tuple[col])
            elif colTypes[col] == "float":
                for tuple in data:
                    if tuple[col]:
                        tuple[col] = float(tuple[col])
            elif colTypes[col] == "varchar":
                for tuple in data:
                    if tuple[col]:
                        tuple[col] = str(tuple[col])

    class Parameters(QMainWindow):
        def __init__(self, tableEditor):
            QMainWindow.__init__(self, tableEditor)
            self.setWindowTitle("File reader/writer parameters")
            self.genericTableEditor = tableEditor

        def initFields(self, fileStructure):
            self.fileStructure = fileStructure
            # print('Parameters',self.fileStructure)

            self.widget = QWidget(self)
            widgetLayout = QVBoxLayout()
            self.widget.setLayout(widgetLayout)
            self.setCentralWidget(self.widget)
            # if not fileStructure : fileStructure={}

            # - Header
            self.header = QCheckBox("Header", self.widget)
            widgetLayout.addWidget(self.header)
            if self.fileStructure is not None and "header" in self.fileStructure:
                header = self.fileStructure["header"]
                if header:
                    self.header.setChecked(True)
                else:
                    self.header.setChecked(False)
                    # self.header.show()

            # - Quoted
            self.quoted = QCheckBox("Quoted", self.widget)
            widgetLayout.addWidget(self.quoted)
            if self.fileStructure is not None and "quoted" in self.fileStructure:
                self.quoted.setChecked(self.fileStructure["quoted"])

            # - Speparators
            separator = QWidget(self.widget)
            widgetLayout.addWidget(separator)
            separatorLayout = QHBoxLayout()
            separator.setLayout(separatorLayout)
            separatorLayout.addWidget(QLabel("Separator"))
            self.separator = QComboBox()
            separatorLayout.addWidget(self.separator)
            self.separator.setObjectName("Separator")
            self.separator.addItem('""')
            self.separator.addItem('" "')
            self.separator.addItem('"\t"')
            self.separator.addItem('";"')
            self.separator.addItem('","')
            self.separator.setEditable(True)

            if self.fileStructure is not None and "separator" in self.fileStructure:
                sep = self.fileStructure["separator"]
                if not sep:
                    sep = ""
                self.separator.setEditText('"' + sep + '"')
            # self.displayColsNamesTypes()

            # - Updates
            update = QPushButton("Update", self.widget)
            widgetLayout.addWidget(update)
            update.clicked.connect(self.clickupdate)

        def displayColsNamesTypes(self):
            # - Header names and types
            columns = QWidget(self.widget)
            columnsLayout = QHBoxLayout()
            columns.setLayout(columnsLayout)
            self.columns = []
            labels = QWidget(columns)
            columnsLayout.addWidget(labels)
            labelsLayout = QVBoxLayout()
            labels.setLayout(labelsLayout)
            labelsLayout.addWidget(QLabel("Header"))
            labelsLayout.addWidget(QLabel("Types"))

            # - Get the number of columns from the gui
            try:
                nbCols = int(str(self.nbCols.text()))
            except ValueError:
                nbCols = 0

            if self.fileStructure is not None and "header" in self.fileStructure:
                header = self.fileStructure["header"]
            else:
                header = False

            if self.fileStructure is not None and "types" in self.fileStructure:
                types = self.fileStructure["types"]
            else:
                types = None

            class TypesQComboBox(QComboBox):
                def __init__(self, parent, type):
                    QComboBox.__init__(self, parent)
                    self.addItem("integer")
                    self.addItem("float")
                    self.addItem("varchar")
                    if type:
                        self.setEditText(type)

            for col in range(nbCols):  # self.fileStructure['nbCols']):
                current = QWidget(columns)
                columnsLayout.addWidget(current)
                currentLayout = QVBoxLayout()
                current.setLayout(currentLayout)
                if header:
                    try:
                        lab = header[col]
                    except IndexError:
                        lab = ""
                else:
                    lab = ""
                if types:
                    try:
                        type = types[col]
                    except IndexError:
                        types = None
                else:
                    types = None

                self.columns.append(
                    (QLineEdit(lab, current), TypesQComboBox(current, type))
                )

        def clickupdate(self):
            # Rebuild the structFile from GUI
            structFile = {}
            # - Header (If header checked, take the header tab)
            header = False
            if self.header.isChecked():
                header = True

            # - Quoted
            quoted = self.quoted.isChecked()

            # - Separator
            separator = str(self.separator.currentText()).replace('"', "")

            structFile = {
                "header": header,
                "quoted": quoted,
                "separator": separator,
            }  # , 'nbCols': nbCols}
            self.genericTableEditor.load_from_file(file=None, fileStructure=structFile)
