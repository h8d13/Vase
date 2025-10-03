# Vase

A testing suite to run VMs and perform archlinux system installations.
> Made to be able to test future installs without going into BIOS. **Without a USB or without an ISO.**

Written in bash to wrap Archinstall.

---

## Usage

### From USB/ISO

> By default you are already root in the ISO env.

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

Go grab some coffee during installation.

After initial install pick `Reboot` and switch to hard disk.

Open `Konsole` and type `cd KAES-ARCH`

Then `sudo vim post` edit to desired values then `sudo ./post`

### From an existing arch installation

`$ git clone https://github.com/h8d13/Vase`

`$ sudo ./main`    : Check envir deps for QEMU/KVM

`$ sudo ./main -s` : Start VMs testing suite menu

`$ sudo ./main -i` : Create ISO overlays w RELENG
> Includes the TUI inside the ISO directly by default

`$ sudo ./main -t` : Launch TUI forked KDE install

`$ sudo ./main -r` : Reset logs, log settings and rcw

All avaible commands: `--tuimenu --reset --isomod --start`

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

### Info for nerds / Benchmarks

**TIMINGS:** 142.1s to build ISO with 12 virt-cores / ~600-900s for complete install (with a 5-8mb/s mirror) 

**WEIGHTS:** ~1,42Gb ISO installation image size 

~5,7 Gb after initial install (minimal Intel graphics)
> Btrfs will be much lighter as it uses compression built-in (+CoW optional) + integrated snapshots using snapper/timeshift.
> Note: Best is usually to use what you already have on other disks for compatibility (stick to your choices).

- base, base-devel, linux-firmware, kernel variants, grub2-bootloader
- file compression/dec utils (needed to build)
- microcode (based on hardware detection)
- xorg / waylands libs + SDDM (display server + manager)
- alsa + utils (sound)
- graphics drivers (based on choice/hardware detection)
- network-manager (connectivity)
- bluetooth (optional)
- extra x11 legacy libs (optional)

**PACKGS:** ~720 Base then ~790 with post install script essentials (Flatpak, Zsh, Python-gobject, Adwaita, Gtk4, Firefox) Extra ~30s 

> Built this tool because I knew that maintaining Archinstall seems like hell (judging by issues reported) 
> So I had to have a safe space to test AND change installer code OR create ISOs directly. 
> This would let me expand on sections I thought were missing out on like grub configs, hardware specific stuff, snapshots, etc... 

Another relevant example is setting latin keymaps for Grub in case of using password/rescue shell/editing launch lines. I've included this in [Grub2_Utils](https://github.com/h8d13/Vase/tree/master/vase_os/hade_box/archinstall/grub2_utils)

Special shout to the devs at archinstall and other open-source contributors for making this project possible. 