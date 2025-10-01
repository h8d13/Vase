# VaseOS
A testing suite to run VMs and perform system installations.
Made for archlinux to be able to test installs without going into BIOS.

## Usage

### From an existing installation
`$ sudo ./main`    : Check envir deps for QEMU/KVM
`$ sudo ./main -s` : Start VMs testing suite menu
`$ sudo ./main -t` : Launch TUI forked KDE install
`$ sudo ./main -i` : Create ISO overlays w RELENG
`$ sudo ./main -r` : Reset logs and log settings
