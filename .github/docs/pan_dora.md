# PAN_DORA - Portable Arch Installation

Install Arch Linux + KDE to USB drives with optimizations for portability and flash longevity.

## What It Does

Makes your USB installation:
- **Portable** - Boot on any computer (UEFI or BIOS)
- **Flash-friendly** - Reduces writes to extend USB life
- **Hardware-agnostic** - Works across different hardware

## Usage

```bash
sudo ./main -t --pandora
# or
sudo ./main -t --usb
```

Complete installation normally in the TUI to the same USB that you had the ISO on.
After installation, USB optimizations apply automatically.

The idea is that you can install on the same drive because it's all coped to RAM.

## Optimizations Applied

**Portability:**
- GRUB with `--removable` flag (UEFI) or MBR install (BIOS)
- mkinitcpio hooks reordered (`block`/`keyboard` before `autodetect`)
- UUID-based fstab (hardware-independent)

**Flash Longevity:**
- Systemd journal in RAM (volatile storage, 30MB max)
- BFQ I/O scheduler (better USB performance)

## Single USB Install

You can install to the same USB you booted from! The ISO runs entirely in RAM, so the USB can be reformatted during installation.

## Files

- `./pan_dora/post_install` - Post-installation script (runs in chroot)

## Technical Details

The `--pandora` or `--usb` flag:
1. Copies `post_install` script to RAM
2. Passes it to archinstall as a custom command
3. Script runs in chroot after base installation
4. Applies USB-specific optimizations before genfstab

Based on some of the points here: https://wiki.archlinux.org/title/Install_Arch_Linux_on_a_removable_medium
