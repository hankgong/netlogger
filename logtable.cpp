#include "logtable.h"
#include "ui_logtable.h"

LogTable::LogTable(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::LogTable)
{
    ui->setupUi(this);
    ui->tableWidget->setRowCount(3);
    ui->tableWidget->setColumnCount(3);

}

LogTable::~LogTable()
{
    delete ui;
}
