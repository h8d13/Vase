#!/bin/sh
# script to set the keymap properly in grub2
# prereq: ckbcomp from aur #https://aur.archlinux.org/ckbcomp.git
# heavily inspired by fitzcarraldoblog cheers 
# assumes standard /boot/ 
GRUB_DEF="/etc/default/grub"
GRUB_LAY="/boot/grub/layouts"
BOOT_DIR="/boot/efi"
GRUB_CFG="/boot/grub/grub.cfg"
LOCALE=$(locale | grep "^LANG=" | sed 's/LANG=//; s/\.UTF-8.*//')
KB_LAYOUT=$(localectl status | grep "VC Keymap" | cut -d':' -f2 | tr -d ' ')
### Pre-checks
# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "Don't run this as root"
    exit 1
fi
### S1 ckbcomp
# Check if ckbcomp is installed
if command -v ckbcomp >/dev/null 2>&1; then
    echo "ckbcomp is already installed"
else 
        # Create temp directory
        TMPDIR=$(mktemp -d)
        cd "$TMPDIR"
        # Clone and build
        echo "Downloading ckbcomp from AUR..."
        curl -sL https://aur.archlinux.org/cgit/aur.git/snapshot/ckbcomp.tar.gz | tar xz
        cd ckbcomp
        echo "Building ckbcomp..."
        makepkg
        echo "Installing..."
        pacman -U --noconfirm *.pkg.tar.*
        # Cleanup
        rm -rf "$TMPDIR"
        echo "ckbcomp installation complete"
fi
### S2 prepare files for grub
mkdir -p $GRUB_LAY
### S2.1 gen layout compatible with grub
# this might generate a bunch of errors since grub only supports 1-127. but this is fine for standard terminal use.
ckbcomp $KB_LAYOUT | grub-mklayout -o $GRUB_LAY/$KB_LAYOUT.gkb
### S3 modify grub files
if grep -q "GRUB_TERMINAL_INPUT.*console" $GRUB_DEF; then
    echo "Found console setting, replacing..."
    sed -i 's/=console/=at_keyboard/g' $GRUB_DEF
else
    echo "Console setting not found or already modified"
    exit 1
fi
if ! grep -q "insmod keylayouts" /etc/grub.d/40_custom; then
    tee -a /etc/grub.d/40_custom << EOF
insmod keylayouts
keymap \$prefix/layouts/$KB_LAYOUT.gkb
EOF
fi
### S4 modify some more and apply
# Add to GRUB if not already there
if ! grep -q "locale=$LOCALE" $GRUB_DEF; then
    sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"/&locale=$LOCALE /" $GRUB_DEF
    grub-mkconfig -o $GRUB_CFG
fi
if [ -d /sys/firmware/efi ]; then
    echo "UEFI boot detected"
    grub-install --efi-directory=$BOOT_DIR
else
    echo "Legacy BIOS boot detected, skipping."
fi
