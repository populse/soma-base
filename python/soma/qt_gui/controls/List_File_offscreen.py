# -*- coding: utf-8 -*-
#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
from __future__ import print_function
from __future__ import absolute_import
from .List_offscreen import OffscreenListControlWidget
from soma.qt_gui.qt_backend import Qt
from soma.qt_gui import qt_backend
from functools import partial
import os


class OffscreenListFileControlWidget(OffscreenListControlWidget):

    @staticmethod
    def create_widget(parent, control_name, control_value, trait,
                      label_class=None, user_data=None):
        """ Method to create the list widget.

        Parameters
        ----------
        parent: QWidget (mandatory)
            the parent widget
        control_name: str (mandatory)
            the name of the control we want to create
        control_value: list of items (mandatory)
            the default control value
        trait: Tait (mandatory)
            the trait associated to the control
        label_class: Qt widget class (optional, default: None)
            the label widget will be an instance of this class. Its constructor
            will be called using 2 arguments: the label string and the parent
            widget.

        Returns
        -------
        out: 2-uplet
            a two element tuple of the form (control widget: ,
            associated labels: (a label QLabel, the tools QWidget))
        """
        widget, labels = OffscreenListControlWidget.create_widget(
            parent, control_name, control_value, trait,
            label_class=label_class, user_data=user_data)

        button = Qt.QPushButton("...", widget)
        button.setObjectName('files_button')
        button.setStyleSheet('QPushButton#files_button '
                             '{padding: 2px 10px 2px 10px; margin: 0px;}')
        layout = widget.layout()
        layout.addWidget(button)
        button.clicked.connect(partial(
            OffscreenListFileControlWidget.select_files, widget))

        return (widget, labels)


    @staticmethod
    def select_files(control_instance):
        """ Browse the file system and update the control instance accordingly.

        If a valid file path has already been entered the file dialogue will
        automatically point to the file folder, otherwise the current working
        directory is used.

        Parameters
        ----------
        control_instance: QWidget (mandatory)
            the file widget item
        """
        # Get the current file path
        init_dir = os.getcwd()

        # get widget via a __self__ in a method, because control_instance may
        # be a weakproxy.
        widget = control_instance.__repr__.__self__
        ext = []
        trait = control_instance.trait.handler.inner_traits()[0]
        if trait.allowed_extensions:
            ext = trait.allowed_extensions
        if trait.extensions:
            ext = trait.extensions
        ext = ['*%s' % e for e in ext]
        ext = ' '.join(ext)
        if ext:
            ext += ';; All files (*)'
        # Create a dialog to select a file
        if control_instance.trait.output:
            fname = qt_backend.getSaveFileName(
                widget, "Output files", init_dir, ext,
                None, Qt.QFileDialog.DontUseNativeDialog)
            fnames = [fname]
        else:
            fnames = Qt.QFileDialog.getOpenFileNames(
                widget, "Open files", init_dir, ext, None,
                Qt.QFileDialog.DontUseNativeDialog)
            if fnames:
                fnames = fnames[0]

        if fnames:
            # Set the selected files path to the control
            controller = control_instance.parent().controller
            print('controller:', controller)
            print('param:', control_instance.trait_name)
            print('value:', fnames)
            setattr(controller, control_instance.trait_name, fnames)
