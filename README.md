# Vase

A testing suite to run VMs and perform system installations.
> Made for archlinux to be able to test future installs without going into BIOS.

Written in raw shell to wrap Archinstall.

---

## Usage

### From USB/ISO

> By default you are already root in the ISO env.

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

### From an existing arch installation

`$ git clone https://github.com/h8d13/Vase`

`$ sudo ./main`    : Check envir deps for QEMU/KVM

`$ sudo ./main -s` : Start VMs testing suite menu

`$ sudo ./main -t` : Launch TUI forked KDE install

`$ sudo ./main -i` : Create ISO overlays w RELENG

> Includes the TUI inside the ISO directly by default

`$ sudo ./main -r` : Reset logs, log settings and rcw

### Settings

In project root, `...` file contains every single configuration constants.
> VM Config, paths, custom names, etc...

For logging: Inside `.vase.d` you can find `logs.conf`:
```
#FORMAT= # 1 Start enabled / 0 Start disabled
COLORS=1 # 0 Disables colors of all output
TIMING=1 # 0 Disables timing output of rcw
DEBUGS=1 # 0 Disables all info outputs
TEELOG=1 # 0 Disables complete log file
LOGMEM=0 # 1 Enables keeping previous log
LOGCLR=0 # 1 Enables non standard ascii in log
CATART=1 # 0 Disables cli art sadface
```

## Features

### Main VM Menu

Inside `vase_os/zazulago_vms/vm_start` to modify VM behaviours/options.

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

> Useful to run QEMU with specific options or with attached storage. Or test other distros/architectures from Arch.

## Specifications for Contribs

Inside `vase_os/env` main detection logic for kernel version, distro, GPU/CPU.

Inside `vase_os/zazulago_vms/setup_arch` for needed packages for QEMU/KVM.

Inside `vase_os/zazulago_vms/iso_mod` to create custom ISOs. And inside `vase_os/hade_box` to change overlay files/installer.

Inside `vase_os/hade_box/altodeps` to see check all subdeps used by archinstall.

### Main utilities

Inside `util_f` can find all shell utility functions used throughout codebase.

> Useful for simple syntax like:
```
if file_ex "${file_p}${file_n}"; then
    echo "Do something"
fi
```
