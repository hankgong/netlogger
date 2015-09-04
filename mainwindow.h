#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

#include "childwindow.h"

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();

public slots:
    void newDocument();
    void closeDocument();

private:
    Ui::MainWindow *ui;

    QAction* btn1;
    QAction* btn2;
};

#endif // MAINWINDOW_H
