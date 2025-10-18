# klar_tix

Artix Linux bootstrap installer with multi-init support and optional LUKS2 encryption.

## Overview

Klartix bootstraps Artix Linux from any Linux distro without requiring an ISO. 
Handles partitioning, encryption, bootloader, and base system configuration for x86_64 UEFI systems.

## Components

- **`klartix`** - Main installer (disk setup, LUKS, bootloader, users)
- **`klartix.conf`** - Configuration file (init system, partitions, encryption)
- **`klartix_desktop`** - KDE Plasma installer with Wayland/SDDM/Pipewire

## Quick Start

```bash
# 1. Configure
vim vase_os/klar_tix/klartix.conf

# 2. Install base system (-v for verbose outputs)
sudo vase_os/klar_tix/klartix

# 3. Reboot to hard disk, clone inside the target then install desktop
git clone https://github.com/h8d13/Vase && cd Vase/vase_os/klar_tix

sudo vim klartix_desktop # Please edit these values according to hardware.

sudo ./klartix_desktop
## This will trigger another reboot.
## Login again with user in SDDM screen
cd Vase && ./main -u

./main -pe  # Edit post script
sudo ./main -p  # Run post-install
```

## Configuration

Please edit this: `klartix.conf` is essential (Pre-install conf)

## Encryption Options

| Config | Boot | Root | Prompts | Use Case |
|--------|------|------|---------|----------|
| `SEPARATE_BOOT=0` | Encrypted | - | 1 (GRUB) | Simple, single prompt |
| `SEPARATE_BOOT=1, ENCRYPT_BOOT=0` | Unencrypted | Encrypted | 1 (initramfs) | Fast boot |
| `SEPARATE_BOOT=1, ENCRYPT_BOOT=1` | Encrypted | Encrypted | 2 (GRUB+initramfs) | Maximum security |

**⚠️ LUKS passwords:** GRUB uses US keyboard layout at boot. See `vase_os/grome_lum/grub_keymaps` Avoid special characters.

Also make sure to check which drive you are overwriting.

## Desktop Installation

**`klartix_desktop` options:**

```bash
# Minimal Plasma (saves ~1GB)
KLAGAN_MODE="-desktop"

# Full Plasma (default about 2,5gb)
#KLAGAN_MODE=""

# Optional additions (uncomment in script)
# konsole ark dolphin        # Individual apps
# kde-applications           # Full KDE suite (Much heavier)

# Hardware choices please configure !! 
```

**What gets installed:**
- Plasma desktop (minimal or full)
- Wayland + SDDM (runit service)
- Pipewire audio stack
- NetworkManager applet

## VaseOS Compatibility

- ✅ **pacto_pac** - GUI package manager 
- ✅ **kaes_arch** - Post-install script
- ⚠️ **hade_box** - Not used (Arch TUI only)

## Technical Notes

- Uses official `artix-bootstrap.sh` tool
- GPT/UEFI x86_64 only (no legacy BIOS)

Made for **Klagan** - minimalism and systemd-free systems.
