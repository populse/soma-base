# -*- coding: utf-8 -*-

import sys
from main_window import MainWindow

from PyQt4.QtGui import QLabel, QApplication
 
# On utilise la syntaxe from x import *, parce que 
# tous les objets de Qt commencent par un Q et l'on
# n'aura pas de problème d'espace de noms ainsi. 
 
if __name__=='__main__':
 
    app = QApplication(sys.argv)
    w=MainWindow()
    w.show()
    sys.exit(app.exec_())


