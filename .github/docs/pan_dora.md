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
sudo ./main -t --live
```

Complete installation normally in the TUI. The "Live medium" option will show as **Enabled** in the menu.

**Single USB Install:** You can install to the same USB you booted from! The ISO runs entirely in RAM, so the USB can be reformatted during installation.

## Optimizations Applied

**Portability:**
- GRUB with `--removable` flag (UEFI) or MBR install (BIOS)
- mkinitcpio hooks reordered (`block`/`keyboard` before `autodetect`)
- UUID-based fstab (hardware-independent)

**Flash Longevity:**
- Systemd journal in RAM (volatile storage, 30MB max)
- BFQ I/O scheduler (better USB/SSD performance)

## Technical Details

The `--pandora` or `--live` flag:
1. Sets `removable_media=True` in archinstall config
2. Displays in TUI menu as "Live medium: Enabled"
3. After installation completes, applies optimizations directly via `Installer.apply_removable_media_optimizations()`:
   - Modifies `/etc/mkinitcpio.conf` and regenerates initramfs
   - Creates `/etc/systemd/journald.conf.d/usbstick.conf`
   - Creates `/etc/udev/rules.d/60-ioschedulers.rules`
4. All changes happen before `genfstab`

**Implementation:**
- Integrated into archinstall (no external scripts)
- Code: `vase_os/hade_box/archinstall/lib/installer.py:403-460`
- Based on: https://wiki.archlinux.org/title/Install_Arch_Linux_on_a_removable_medium
