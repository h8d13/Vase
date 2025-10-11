# klar_tix

Artix Linux bootstrap installer with multi-init support and optional LUKS2 encryption.

## Overview

Klartix bootstraps Artix Linux from any Linux distro without requiring an ISO. 
Handles partitioning, encryption, bootloader, and base system configuration for x86_64 UEFI systems.

## Components

- **`klartix`** - Main installer (disk setup, LUKS, bootloader, users)
- **`klartix.conf`** - Configuration file (init system, partitions, encryption)
- **`klartix_desktop`** - KDE Plasma installer with Wayland/SDDM/Pipewire
- **`klartix_hw`** - Hardware driver definitions (Intel/Intel system example)

## Quick Start

```bash
# 1. Configure
vim vase_os/klar_tix/klartix.conf

# 2. Install base system
sudo vase_os/klar_tix/klartix

# 3. Reboot, then install desktop
sudo vase_os/klar_tix/klartix_desktop
```

## Configuration

**`klartix.conf` essentials:**
Please edit this. 

## Desktop Installation

**`klartix_desktop` options:**

```bash
# Minimal Plasma (saves ~1GB)
KLAGAN_MODE="-desktop"

# Full Plasma (default)
#KLAGAN_MODE=""

# Optional additions (uncomment in script)
# konsole ark dolphin        # Individual apps
# kde-applications           # Full KDE suite (Much heavier)
```

**What gets installed:**
- Plasma desktop (minimal or full via `KLAGAN_MODE`)
- Wayland + SDDM (runit service)
- Pipewire audio stack
- NetworkManager applet

## Encryption Options

| Config | Boot | Root | Prompts | Use Case |
|--------|------|------|---------|----------|
| `SEPARATE_BOOT=0` | Encrypted | - | 1 (GRUB) | Simple, single prompt |
| `SEPARATE_BOOT=1, ENCRYPT_BOOT=0` | Unencrypted | Encrypted | 1 (initramfs) | Fast boot |
| `SEPARATE_BOOT=1, ENCRYPT_BOOT=1` | Encrypted | Encrypted | 2 (GRUB+initramfs) | Maximum security |

**⚠️ LUKS passwords:** GRUB uses US keyboard layout at boot. See `vase_os/grome_lum/grub_keymaps` Avoid special characters.

## Hardware Example (Intel GPU)

```bash
# Enable lib32 in /etc/pacman.conf
sudo vim /etc/pacman.conf  # Uncomment [lib32]

# Install drivers
sudo pacman -S lib32-mesa lib32-libgl vulkan-intel lib32-vulkan-intel intel-media-driver
```

## Init System Support

Services auto-configured per init system:

- **runit:** `ln -sf /etc/runit/sv/sddm /run/runit/service/`
- **OpenRC:** `rc-update add NetworkManager default`
- **s6:** `s6-rc-bundle-update add default NetworkManager`
- **dinit:** `dinitctl enable NetworkManager`

## VaseOS Compatibility

- ✅ **PacToPac** - GUI package manager 
- ✅ **KAES-ARCH** - Post-install script
- ⚠️ **hade_box** - Not used (Arch TUI only)

## Technical Notes

- Uses official `artix-bootstrap.sh` tool
- GPT/UEFI x86_64 only (no legacy BIOS)
- LUKS2 with PBKDF2 (GRUB) or argon2id (kernel)
- Keyfile for auto-unlock (combined boot+root only)
- Extensive cleanup prevents host pollution

Made for **Klagan** - minimalism and systemd-free systems.
