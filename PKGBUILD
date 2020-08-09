pkgname=qtile-widget-livefootballscores-git
_pkgname=qtile-widget-livefootballscores
pkgver=0.0.1
pkgrel=1
provides=("$_pkgname")
conflicts=("$_pkgname")
pkgdesc="Qtile widget to display live football scores."
url="https://github.com/elparaguayo/qtile-widget-livefootballscores.git"
license=("MIT")
depends=("python" "qtile" "python-dateutil")
source=("git+https://github.com/elparaguayo/$_pkgname.git")
md5sums=("SKIP")

pkgver()
{
  cd "$_pkgname"
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package()
{
  cd "$_pkgname"
  python setup.py install --root="$pkgdir"
}
