#-------------------------------------------------
#
# Project created by QtCreator 2015-09-02T20:56:51
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = VOBCNetLogger
TEMPLATE = app


SOURCES += main.cpp\
        mainwindow.cpp \
    logtable.cpp \
    childwindow.cpp

HEADERS  += mainwindow.h \
    logtable.h \
    childwindow.h

FORMS    += mainwindow.ui \
    logtable.ui
