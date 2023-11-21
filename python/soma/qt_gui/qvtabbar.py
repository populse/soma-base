from soma.qt_gui.qt_backend import Qt


class QVTabBar(Qt.QTabBar):
    """
    A vertical QTabBar, as in
    https://stackoverflow.com/questions/50578661/how-to-implement-vertical-tabs-in-qt
    """

    def __init__(self, parent=None, tab_width=None, tab_height=None):
        super().__init__(parent)
        self.tab_width = tab_width
        self.tab_height = tab_height
        self._first_paint = True

    def tabSizeHint(self, index):
        s = Qt.QTabBar.tabSizeHint(self, index)
        s.transpose()
        if self.tab_width is not None:
            s.setWidth(self.tab_width)
        if self.tab_height is not None:
            s.setHeight(self.tab_height)
        return s

    def paintEvent(self, event):
        if self._first_paint:
            self._first_paint = True
            self.update_buttons()

        painter = Qt.QStylePainter(self)
        opt = Qt.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(Qt.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = Qt.QRect(Qt.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(Qt.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()

        Qt.QWidget.paintEvent(self, event)

    def resize_optimal(self):
        sizes = [self.tabSizeHint(i) for i in range(self.count())]
        width = max([s.width() for s in sizes])
        height = sum([s.height() for s in sizes])
        self.resize(width, height)

    def update_buttons(self):
        # check if tab is closable
        if self.tabsClosable():
            opt = Qt.QStyleOptionTab()

            for i in range(self.count()):
                self.initStyleOption(opt, i)
                optRect = opt.rect
                optRect.setX(optRect.width() - 14)  # set X pos of close button
                optRect.setY(optRect.y() + 8)  # calcs the Y pos of close button
                optRect.setSize(Qt.QSize(12, 12))
                self.tabButton(i, Qt.QTabBar.RightSide).setGeometry(optRect)


class QVTabWidget(Qt.QTabWidget):
    """
    A vertical QTabWidget, as in
    https://stackoverflow.com/questions/50578661/how-to-implement-vertical-tabs-in-qt
    """

    def __init__(self, parent=None, width=None, height=None):
        super().__init__(parent)
        self.setTabBar(QVTabBar(parent, width, height))
        self.setTabPosition(Qt.QTabWidget.West)

    def setTabControlSize(self, width, height):
        self.tabBar().tab_width = width
        self.tabBar().tab_height = height
        self.tabBar().resize_optimal()
        self.resize(self.sizeHint())

    def update_buttons(self):
        self.tabBar().update_buttons()
