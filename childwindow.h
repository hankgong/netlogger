#ifndef CHILDWINDOW_H
#define CHILDWINDOW_H

#include <QObject>
#include <QWidget>
#include <QMdiSubWindow>

#include "logtable.h"

class ChildWindow : public QMdiSubWindow
{
    Q_OBJECT

public:
    explicit ChildWindow(QWidget *parent = 0);
    ~ChildWindow();

private:
     LogTable *logTable;

signals:

public slots:
};

#endif // CHILDWINDOW_H
