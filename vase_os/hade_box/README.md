# KADEBOOT - KDE ARCH LINUX

----

An unofficial **stripped-down version** of the official archinstall that **is only for KDE Plasma**.
> Primary goal was to make it easier to test for devs, and also remove complexity from codebase so that I could expand on sections I wanted for my use cases or installs.

This is a modified version (fork) of [archinstall](https://github.com/archlinux/archinstall), originally developed by the Arch Linux team. Which has many more up-to-date features like UKI, systemd-boot, disk encryption, etc. 

This version is for users who know they want KDE and it's dependencies **(NetworkManager, Pipewire, and SDDM)**. 

## Installation

**Pre-req:** 1 USB (minimum 2GB), 1 target Drive (minimum 16GB). 

Boot Arch Linux Live ISO (using f10, f12 or del), get internet access, then:
- No secureboot or set to `other OS`

```bash
pacman -Sy git

git clone https://github.com/h8d13/KADEBOOT

cd KADEBOOT && ./install
```

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

<img width="736" height="456" alt="image" src="https://github.com/user-attachments/assets/ae511cc6-ff58-4026-8689-f7e3ff662501" />


### Modifications

- Hybrid setup detection (common case of Nvidia-Intel) in `hardware.py` > VM Setups additional packages for QEMU/KVM
- Swap config inside disks to make possible swap on partition
- Removed all BOOTLOADERS/HSM/LVM/FIDO2/LUKS2 logic >  Replaced by default: Grub > To be able to expand on snapper/timeshift features + Grub config
- Stripped a lot of code for defaults to be simpler. And for display (translations, certain menus, etc) 
- Removed plugins for maintanability of installer code (scripts still available).
- Logging inside dir > Auto-save/Load configs also inside dir. Utility `./clean_all` script.
- Fixed a case where it would pick up on host fstab zram causing boot hangs. `genfstab {flags} -f {self.target} {self.target}` note the `-f` for filter. 
- Change `f'pacstrap -C /etc/pacman.conf -K {self.target} {" ".join(packages)} --needed --noconfirm'` note the `--needed` flag to prevent re-installs.
- Change `arch-chroot {self.target} mkinitcpio {" ".join(flags)}')` to remove `peek_output=True` causing broken pipe errors. Comestic but important. 
- Added legacy swap types + Legacy x11 option
- Change certain OOO flow: 
    - mount > format filesystem > create new paritions (swap) > set mirrors and base settings > base install > audio > video > KDE plasma > bootloader 
    - /etc/environment variables > network manager > users > final tz, ntp, services, fstab
- Removed pre-mounted options for true guided approach only

- The idea was to create a declerative flow that can be easy to reproduce/modify but also to benchmark from scratch each time and having hardware specific bootloader entries (and env vars) without having to think.

- These are widely *debated/changing*and can result in performance enhancements/or correcting non-functional hardware.

Here is the exact code block in question: [Here](https://github.com/h8d13/KADEBOOT/blob/master/archinstall/lib/installer.py#L963) This could be expanded upon to build hardware-aware and optimized presets considering hardware detection modules. 

And the reference for why: [Wiki-KernelParameters](https://wiki.archlinux.org/title/Kernel_parameters) and [Wiki-Env](https://wiki.archlinux.org/title/Environment_variables)

## KADEBOOT under the hood

**Boot ISO** → Run KADEBOOT (Archinstall but modified for KDE)

→ **Reboot to hard disk** → (Clones for you) KAES-ARCH → Run post script (Many improvements to defaults)

→ (Clones for you) PACTOPAC →  **Reboot** → Use PACTOPAC settings page to quickly setup 

→ **Normal usages** → Use PACTOPAC for ongoing management if needed (or use command line if familiar).

> This set-up with a rolling release is ideal because we have single sources of truth for each critical aspect. Keep my work on the side and be able to brick an install if needed in 15 minutes. We can also easily allow for self-upgrades by simply running `git pull` in the right location.  

--- 

## DEVS

### GRUB2 Utility scripts 

For further configuration: 

[SYMAN](https://github.com/h8d13/SYMAN-GRUB2)

### (ARCH) Linux to Linux install (without ISO/USB)

``` ./install -d ``` This checks all system sub deps in case not running from ISO.

### Quick QEMU testing

Included a devs folder with KVM check and how to run in QEMU. 
