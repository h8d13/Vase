# Vase
A testing suite to run VMs and perform system installations.
> Made for archlinux to be able to test future installs without going into BIOS.

Written in raw shell to wrap Archinstall.

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

## Features

### Main VM Menu

```
########################################
Zazulago VM Tooling: rdisk, then brick.
Display: sdl | GL: on
########################################
 rk      : Refresh key
 rdisk   : Reset myvm1 60G
 dupk    : Permanent copy
 duck    : Temporary copy
 mayk    : Maybe Y/N copy
 brick   : Boot ISO + Run
 vncd    : Boot ISO (VNC)
 vnck    : Run with (VNC)
 std     : Run (standard VGA)
 cupkd   : Boot ISO w /dev/sde1
 cupk    : Run w /dev/sde1
 taild   : Headless w logs
 bootk   : Boot headless w/ logs
 macg    : Generate MAC + run
 conkd   : Boot ISO w /dev/sde1 and disk
 conk    : Run w /dev/sde1 and disk
 potk    : Delete key + encrypt
 exit    : Exit without encrypt
########################################
Choice (any key for default): exit
[-] Exiting without encryption
```

> Useful to run QEMU with specific options or with attached storage.
