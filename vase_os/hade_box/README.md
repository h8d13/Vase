# Hade_box - KDE ARCH LINUX

----

An unofficial **stripped-down version** of the official archinstall that **is only for KDE Plasma**.
> Primary goal was to make it easier to test for devs, and also remove complexity from codebase so that I could expand on sections I wanted for my use cases or installs.

This is a modified version (fork) of [archinstall](https://github.com/archlinux/archinstall), originally developed by the Arch Linux team. Which has many more up-to-date features like UKI, systemd-boot, disk encryption, etc.

This version is for users who know they want KDE and it's dependencies **(NetworkManager, Pipewire, and SDDM)**.

## Installation

**Pre-req:** 1 USB (minimum 2GB), 1 target Drive (minimum 16GB).

Boot Arch Linux Live ISO (using f10, f12 or del)

Get internet access; `iwctl station wlan0 connect "SSID"` SSID being the name of your WiFi (case sensitive) and it should prompt you for password.
Ethernet works out of the box. Plug a cable and go.

Test: ping archlinux.org, you should see 64 bytes from xx.xxx.xxx.xxx (xx.xxx.xxx.xxxx): icmp_seq=1 ttl=109 time=13.9 ms then means you are all good to go!

- No secureboot or set to `other OS`

## After initial install

You will have 3 options: Chroot, Reboot or exit. Pick reboot.

Go to BIOS again to **switch to hard disk.**

Login the ugly SDDM screen using user you created earlier (you will only see this once!)

---
Open the apps launcher > type `Konsole`
> I've taken the liberty to clone the other repo in sudo user 0's home.

```
cd KAES-ARCH/
```
Edit the targets: user and kb using editor of your choice.

Example: `sudo vim post` or `sudo nano post`

```
DTHEME=dark
KB_LAYOUT=us
VARIANT=""
```
> Variant is optional, can be left empty. Applies for the current sudo user by default. Do check out some of the parts that you can configure (additional packages, removing stuff, guest account, etc).

Then run: `sudo ./post`

After running the script it will restart one last time. **And you are done!**

---

For more info see main repo: [KAES-ARCH](https://github.com/h8d13/KAES-ARCH)

### Modifications

- Hybrid setup detection (common case of Nvidia-Intel) in `hardware.py` > VM Setups additional packages for QEMU/KVM
- Fixed mesa errors running adwaita apps under VMs using `vulkan-swarst`
- Fixed a case where it would pick up on host fstab zram causing boot hangs. `genfstab {flags} -f {self.target} {self.target}` note the `-f` for filter.
- Change `f'pacstrap -C /etc/pacman.conf -K {self.target} {" ".join(packages)} --needed --noconfirm'` note the `--needed` flag to prevent re-installs.
- Change `arch-chroot {self.target} mkinitcpio {" ".join(flags)}')` to remove `peek_output=True` causing broken pipe errors. Comestic but important.
- Added `sof-firmware` to base to avoid another mkinitcpio hook
- Expanded on brtfs-snapper/timeshift integration
- Fixed fallbacks in case endpoints are down: Real important is https://archlinux.org/mirrors/status/json/ and for manual https://archlinux.org/mirrorlist/
> I think this is too critical to only have at only one location. And yes it's down for everyone 

Made a re-order menu for this case if mirrors endpoints are down.
 
- Added CTRL + Q to actually close TUI properly
- Swap config inside disks to make possible swap on partition
- Removed all BOOTLOADERS/HSM/LVM/FIDO2/LUKS2 logic >  Replaced by default: Grub > To be able to expand on snapper/timeshift features + Grub config and people can do what they want after.
- Stripped a lot of code for defaults to be simpler. And for display (translations, certain menus, etc)
- Removed plugins for maintanability of installer code (scripts still available).
- Logging inside dir > Auto-save/Load configs also inside dir. Utility `./clean_all` script.
- Legacy x11 server options
- Change certain OOO flow:
    - mount > format filesystem > create new paritions (swap) > set mirrors and base settings > base install > audio > video > KDE plasma > bootloader
    - /etc/environment variables > network manager > users > final tz, ntp, services, fstab

- The idea was to create a declerative flow that can be easy to reproduce/modify but also to benchmark from scratch each time and having hardware specific bootloader entries (and env vars) without having to think.

- These are widely *debated/changing*and can result in performance enhancements/or correcting non-functional hardware.

Here is the exact code block in question: [Here](https://github.com/h8d13/Vase/blob/2247002707d68fb5b92542aae27d1fbfd18ed978/vase_os/hade_box/archinstall/lib/installer.py#L871C1-L875C10) This could be expanded upon to build hardware-aware and optimized presets considering hardware detection modules.

And the reference for why: [Wiki-KernelParameters](https://wiki.archlinux.org/title/Kernel_parameters) and [Wiki-Env](https://wiki.archlinux.org/title/Environment_variables)

This code is mostly commented out for now until I start benchmarking.

## Hade_box Explained

**Boot ISO** → Run Hade_box (Archinstall but modified for KDE)

→ **Reboot to hard disk** → (Clones for you) KAES-ARCH → Run post script (Many improvements to defaults)

→ (Clones for you) PACTOPAC →  **Reboot** → Use PACTOPAC settings page to quickly setup

→ **Normal usages** → Use PACTOPAC for ongoing management if needed (or use command line if familiar).

> This set-up with a rolling release is ideal because we have single sources of truth for each critical aspect. Keep my work on the side and be able to brick an install if needed in 15 minutes. We can also easily allow for self-upgrades by simply running `git pull` in the right location.

---

## DEVS

### GRUB2 Utility scripts

For further grub configuration:

[SYMAN](https://github.com/h8d13/Vase/tree/master/vase_os/hade_box/archinstall/grub2_utils)
