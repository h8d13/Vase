# VASE 

Main program contains ISO building scripts and more ways to interact with all the project.

## Features

### Main VM Menu

Inside `vase_os/zazu_lago/setup_vms` to see the deps that are pulled in.
Inside `vase_os/zazu_lago/vm_start` to modify VM behaviours/options.
> Useful to run QEMU with specific options or with attached storage. Or test other distros/architectures from Arch.

---

### From existing arch system (For devs)

`$ ./main -t (*args)` : Launch TUI forked KDE install

> This will check system subdeps for Arch to Arch installs. On an existing install use sudo.  

#### Main Commands

When no args are provided we simply: Check for KVM/QEMU deps/Check permissions/Check Vase is built okay

```
--update                   # -u  # Checks git for updates & pull submodules
--check-deps               # -c  # Check build deps 

--post-edit                # -pe # Edits post install script
--post                     # -p  # Runs post install script

--start                    # -s  # Start VM menu
--quick <command>          # -q  # Pass direct VM options "help"
--bench <type>             # -b  # Run benchmarks: io, cpu, gpu
--isomod                   # -i  # Create iso default `iso_profiles/fat.conf`
--flash <device>           # -f  # Flash ISO to USB device (e.g., /dev/sdd)
--workflow <device>        # -w  # Complete workflow
--dev                      # -d  # Development mode flag entry script
--grub <args>              # -g  # GRUB utilities -h for help

--reset                    # -r  # Resets logs and rcw
```

> Assumes KVM compatible hardware for VM options. And valid GPG key setup: `gpg --full-generate-key` and follow prompts for building.
> Mostly tooling for devs... More readmes included. 

---

## Specifications of other files

- Inside `vase_os/env` main detection logic for kernel version, distro/init system, GPU/CPU.

- Inside `vase_os/hade_box/altodeps` to see check all subdeps used by archinstall for installs without a USB (detected automatically).

- Inside `vase_os/mindeps` deps used by Vase it-self.

- Inside `vase_os/hade_box/install` main TUI entry script for ArchKDE.

## Philosophy

- Always works scenario > Simple TUI choices
- Init systems compatible for post script and GUI for fast set-up
- Automate as much of workflows as possible
- Document changes and tweaks as I go
- Brickable: Feel no shame in re-installing 

> Advanced stuff can be applied to Artix while simpler system stays with Arch. 

Inside `vase_os/klar_tix/` to see Artix related features.

## Info for nerds / Benchmarks

### Time

Original: 142.1s to build ISO with 12 virt-cores / ~600-900s for complete install (with a 5-8mb/s mirror).

New: Reduced to <200s (+ configuration in TUI) using custom ISO overlay (caching plasma packages + stuff that is always required).

I'm aiming for the installer to be the fastest way to install KDE + a good base system and lightest compared to same env on diffrent distros thanks to Archlinux tools/compression.

Storage is inexpensive while **time on the other hand is the only real currency.** If you are wondering what I'm talking about Inside `vase_os/zazu_lago/iso_mod` to create overlay custom ISOs. 

### Weight

Original: ~1,42Gb ISO installation image size / New: ~2,67Gb ISO with plasma overlay (extra ~150s to generate ISO)

~4-5 Gb after initial install (minimal Intel graphics)

> Btrfs will be much lighter as it uses compression built-in (+CoW optional) + integrated snapshots using snapper/timeshift.
> Note: Best is usually to use what you already have on other disks for compatibility (stick to your choices).

## Order of operations

(Reflector mirrors sorting ran directly as internet is found.)

- Format target > Mount ordered layout
- Partitionning FS (Including swap if required on FS)
- Filesystem packages (e.g., btrfs-progs, dosfstools)
- Base, base-devel, kernel, linux-firmware
- Micro-code (AMD/Intel)
- Hostname/Locale/KB layout/Timezone
- Mkinitcpio 
- Set mirrors on target
- Enable swap type (zram, swapfile or partition)
- Audio (sof/alsa)
- Profile: Plasma, graphics drivers, kernel headers (Needed to build against Nvidia drivers) , X11 optionals
- Bootloader (Grub2 UEFI vs MBR) 
- Network + Users
- Enable services (SDDM, NetworkManager, NTP)
- Snapshots if enabled
- Optional live media optis
- Gen fstab 

**PACKGS:** ~720 Base then ~750 with post install script essentials (Flatpak, Zsh, Python-gobject, Adwaita, Gtk4, Firefox) Extra ~30s 
