# Vase
A testing suite to run VMs and perform system installations.
> Made for archlinux to be able to test future installs without going into BIOS.

## Usage

### From an existing arch installation

`$ sudo ./main`    : Check envir deps for QEMU/KVM

`$ sudo ./main -s` : Start VMs testing suite menu

`$ sudo ./main -t` : Launch TUI forked KDE install

`$ sudo ./main -i` : Create ISO overlays w RELENG

> Includes the TUI inside the ISO directly by default

`$ sudo ./main -r` : Reset logs, log settings and rcw

### From USB/ISO

`$ sudo ./main -t` : Launch TUI forked KDE install
