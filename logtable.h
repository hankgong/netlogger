#ifndef LOGTABLE_H
#define LOGTABLE_H

#include <QWidget>

namespace Ui {
class LogTable;
}

class LogTable : public QWidget
{
    Q_OBJECT

public:
    explicit LogTable(QWidget *parent = 0);
    ~LogTable();

private:
    Ui::LogTable *ui;

};

#endif // LOGTABLE_H
