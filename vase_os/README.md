# Project structure

1. hade_box = Installer fork
2. zazulago_vms = Testing suite
3. kaes_arch = Post-install script
4. pacto_pac = Pacman GUI

Main program contains ISO building scripts and more ways to interact with all the project.

## Features

### Main VM Menu

> Assumes KVM availability Intel/AMD.

Inside `vase_os/zazulago_vms/vm_start` to modify VM behaviours/options.
> Useful to run QEMU with specific options or with attached storage. Or test other distros/architectures from Arch.

---

## Specifications of other files

- Inside `vase_os/env` main detection logic for kernel version, distro, GPU/CPU.

- Inside `vase_os/zazulago_vms/setup_arch` for needed packages for QEMU/KVM.

- Inside `vase_os/hade_box/altodeps` to see check all subdeps used by archinstall for installs without a USB (detected automatically).

- Inside `vase_os/bench_io`, `vase_os/bench_cpu`, `vase_os/bench_gpu` for system benchmarks (outputs to `vase.log`).

---

## Info for nerds / Benchmarks

### Time

Original: 142.1s to build ISO with 12 virt-cores / ~600-900s for complete install (with a 5-8mb/s mirror).

New: Reduced to <200s (+ configuration in TUI) using custom ISO overlay (caching plasma packages + stuff that is always required). Current best: 2m15s

I'm aiming for the installer to be the fastest way to install KDE + a good base system and lightest compared to same env on diffrent distros thanks to Archlinux tools/compression.

Storage is inexpensive while **time on the other hand is the only real currency.** If you are wondering what I'm talking about Inside `vase_os/zazulago_vms/iso_mod` to create overlay custom ISOs. 

### Weight

Original: ~1,42Gb ISO installation image size / New: ~2,67Gb ISO with plasma overlay (extra ~150s to generate ISO)

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