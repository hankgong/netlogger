#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QLineEdit>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    QPixmap openFilePix("icons/document-open.svg");
    QPixmap closeFilePix("icons/process-stop.svg");

    btn1 = new QAction(QIcon(openFilePix), "Open Connection", this);
    btn2 = new QAction(QIcon(closeFilePix), "Close Connection", this);

    QObject::connect(btn1, SIGNAL(triggered()), this, SLOT(newDocument()) );
    QObject::connect(btn2, SIGNAL(triggered()), this, SLOT(closeDocument()) );

    ui->mainToolBar->addAction(btn1);
    ui->mainToolBar->addAction(btn2);
    ui->mainToolBar->addSeparator();

    QLineEdit *myLineEdit = new QLineEdit();
    ui->mainToolBar->addWidget(myLineEdit);
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::newDocument()
{
    ChildWindow *childWindow = new ChildWindow(ui->mdiArea);
    childWindow->setAttribute(Qt::WA_DeleteOnClose);
    childWindow->show();
}

void MainWindow::closeDocument()
{

}
