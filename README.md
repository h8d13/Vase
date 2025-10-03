# Vase

A testing suite to run VMs and perform Archlinux system installations.

> Made to be able to test future installs without going into BIOS. **Without a USB or without an ISO.**
> Or test other distros from Arch without learning all the QEMU docs.

Written in bash to wrap Archinstall.

---

## Installation/Usage

### From USB/ISO

> By default you are already root in the ISO env.

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

Go grab some coffee during installation.

After initial install pick `Reboot` and switch to hard disk.

Open `Konsole` and type `cd KAES-ARCH` this is where the post install script lives and more assets.

Then `sudo vim post` edit to desired values, then `sudo ./post` when ready.

---

### From an existing arch installation

`$ git clone https://github.com/h8d13/Vase`

`$ sudo ./main`    : Check envir deps for QEMU/KVM

`$ sudo ./main -s` : Start VMs testing suite menu

`$ sudo ./main -q brick` : Skip menu pass directly

`$ sudo ./main -i` : Create ISO overlays w RELENG

`$ sudo ./main -t` : Launch TUI forked KDE install

`$ sudo ./main -r` : Reset logs, log settings and rcw

`$ sudo ./main -u` : Check for updates from GitHub

All long-form commands: 

```
--reset                 # Resets logs
--update                # Checks git for updates
--tuimenu               # Launch modified TUI
--isomod                # Create iso default `iso_profiles/fat.conf`
--start                 # Start VM menu
--quick <command>       # Lanch VM "help" to see options
```

---

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

---

## Features

### Main VM Menu

Inside `vase_os/zazulago_vms/vm_start` to modify VM behaviours/options.
> Useful to run QEMU with specific options or with attached storage. Or test other distros/architectures from Arch.

---

## Specifications of other files

- Inside `vase_os/env` main detection logic for kernel version, distro, GPU/CPU.

- Inside `vase_os/zazulago_vms/setup_arch` for needed packages for QEMU/KVM.

- Inside `vase_os/hade_box/altodeps` to see check all subdeps used by archinstall for installs without a USB (detected automatically).

---

## Info for nerds / Benchmarks

### Time

Original: 142.1s to build ISO with 12 virt-cores / ~600-900s for complete install (with a 5-8mb/s mirror).

New: Reduced to <200s (+ configuration in TUI) using custom ISO overlay (caching plasma packages + stuff that is always required).

I'm aiming for the installer to be the fastest way to install KDE + a good base system and lightest compared to same env on diffrent distros thanks to Archlinux tools/compression.

Storage is inexpensive while **time on the other hand is the only real currency.** If you are wondering what I'm talking about Inside `vase_os/zazulago_vms/iso_mod` to create overlay custom ISOs. 

### Weight

Original: ~1,42Gb ISO installation image size / New: ~2,31Gb ISO with plasma overlay (extra ~150s to generate ISO)

~4-5 Gb after initial install (minimal Intel graphics)

> Btrfs will be much lighter as it uses compression built-in (+CoW optional) + integrated snapshots using snapper/timeshift.
> Note: Best is usually to use what you already have on other disks for compatibility (stick to your choices).

## Order of operations

- base, base-devel, linux-firmware, kernel variants, grub2-bootloader
- file compression/dec utils (needed to build)
- microcode (based on hardware detection)
- xorg / waylands libs + SDDM (display server + manager)
- alsa + utils (sound)
- graphics drivers (based on choice/hardware detection)
- network-manager (connectivity)
- bluetooth (optional)
- extra x11 legacy libs (optional)

**PACKGS:** ~720 Base then ~750 with post install script essentials (Flatpak, Zsh, Python-gobject, Adwaita, Gtk4, Firefox) Extra ~30s 

> Built this tool because I knew that maintaining Archinstall seems like hell (judging by issues reported) 
> So I had to have a safe space to test AND change installer code OR create ISOs directly. 
> This would let me expand on sections I thought were missing out on like grub configs, hardware specific stuff, snapshots, etc... 

Another relevant example is setting latin keymaps for Grub in case of using password/rescue shell/editing launch lines. I've included this in [Grub2_Utils](https://github.com/h8d13/Vase/tree/master/vase_os/hade_box/archinstall/grub2_utils)

Special shout to the devs at archlinux and other open-source contributors for making this project possible. 