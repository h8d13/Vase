# Maintainer: Hadean <hadean-eon-dev@proton.me>
pkgname=vase-git
pkgver=0016
pkgrel=1
pkgdesc="VaseOS - Arch Linux testing suite and installation platform"
arch=('x86_64')
url="https://github.com/h8d13/Vase"
license=('GPL')
depends=('base' 'git' 'gnupg' 'jq' 'python' 'curl' 'wget' 'tree')
makedepends=('archiso' 'squashfs-tools' 'arch-install-scripts')
source=("${pkgname}::git+https://github.com/h8d13/Vase.git")
sha256sums=('SKIP')

prepare() {
    cd "$pkgname"
    git submodule update --init --recursive
}

package() {
    cd "$pkgname"

    # Install to /opt/vase using git archive (preserves permissions)
    install -dm755 "$pkgdir/opt/vase"
    git archive HEAD | tar -x -C "$pkgdir/opt/vase"

    # Copy submodules
    export pkgdir="$pkgdir"
    git submodule foreach --recursive 'mkdir -p "$pkgdir/opt/vase/$path" && git archive HEAD | tar -x -C "$pkgdir/opt/vase/$path"'

    # Include .git for update functionality
    cp -a .git "$pkgdir/opt/vase/"

    # Copy submodule .git directories
    find . -path '*/.git' -type d | while read gitdir; do
        subpath="${gitdir#./}"
        mkdir -p "$pkgdir/opt/vase/$(dirname "$subpath")"
        cp -a "$gitdir" "$pkgdir/opt/vase/$(dirname "$subpath")/"
    done

    # Create wrapper script
    install -dm755 "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/vase" <<'EOF'
#!/bin/bash
cd /opt/vase && exec sudo ./main "$@"
EOF
    chmod +x "$pkgdir/usr/bin/vase"

    # License
    install -Dm644 "$pkgdir/opt/vase/LICENSE" "$pkgdir/usr/share/licenses/vase/LICENSE"

    # Man page
    install -Dm644 "$pkgdir/opt/vase/.github/man/vase.1" "$pkgdir/usr/share/man/man1/vase.1"
}
