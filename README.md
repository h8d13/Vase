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

### Settings

In project root, `...` file contains every single configuration constants.

For logging: Inside `.pyla.d` you can find:
```
#FORMAT= # 1 Start enabled / 0 Start disabled
COLORS=1 # 0 Disables colors of all output
TIMING=1 # 0 Disables timing output of rcw
DEBUGS=1 # 0 Disables info outputs from program
TEELOG=1 # 0 Disables complete log file
LOGMEM=0 # 1 Enables keeping previous log
LOGCLR=0 # 1 Enables non standard ascii in log
CATART=1 # 0 Disables cli art sadface
```
