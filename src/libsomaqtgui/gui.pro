#!include ../../config-cpp-libgui

TEMPLATE= lib
TARGET  = somaqtgui${BUILDMODEEXT}

INCBDIR = soma

HEADERS = \
        spline.h \
        gradwidget.h \
        gradient.h

SOURCES = \
        gradwidget.cpp \
        spline.cpp \
        gradient.cpp

