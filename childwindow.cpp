#include "childwindow.h"

#include "logtable.h"

ChildWindow::ChildWindow(QWidget *parent) :
    QMdiSubWindow(parent)
{
    logTable = new LogTable(this);
    this->setWidget(logTable);
}

ChildWindow::~ChildWindow()
{
    logTable->~LogTable();
}

