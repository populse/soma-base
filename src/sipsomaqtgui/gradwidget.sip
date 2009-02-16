%Module gradwidget 0

class GradientWidget : QWidget {

%TypeHeaderCode
#include <soma/gradwidget.h>
%End

%TypeCode
#include <qcolor.h>
%End

public:
    GradientWidget(QWidget* parent /TransferThis/ = 0,
        const char* name = 0, 
        const QString& gradString = "", double vMin = 0,
        double vMax = 1.0);

    QSize minimumSizeHint() const;
    QSize sizeHint() const;
    QString getGradientString() const;
    void setGradient(const QString& s);
    bool hasAlpha() const;
    void setHasAlpha( bool );
    double minBound() const;
    double maxBound() const;
    void setBounds( double vMin = 0, double vMax = 1.0 );
    QByteArray fillGradient( int length = 4096, bool withAlpha = false ) const;
%MethodCode
#if QT_VERSION >= 0x040000
  sipRes = new QByteArray( a0 * sizeof(QRgb), '\0' );
#else
  sipRes = new QByteArray( a0 * sizeof(QRgb) );
#endif
  sipCpp->getGradient().fillGradient
    ( reinterpret_cast<QRgb*>( sipRes->data() ), a0, 0, a1 );
%End
    void newRgb();
    void newHsv();
    bool isHsv() const;
%MethodCode
  sipRes = sipCpp->getGradient().isHsv();
%End

signals:
    void gradientChanged(QString);

private:
  // process events
  void paintEvent(QPaintEvent* e);
  void resizeEvent(QResizeEvent* e);
  void mousePressEvent(QMouseEvent* e);
  void mouseReleaseEvent(QMouseEvent* e);
  void mouseMoveEvent(QMouseEvent* e);
};

