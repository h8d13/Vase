# hade_box

----

An unofficial **stripped-down version** of the official archinstall that **is only for KDE Plasma**.
> Primary goal was to make it easier to test for devs, and also remove complexity from codebase so that I could expand on sections I wanted for my use cases or installs.

This is a modified version (fork) of [archinstall](https://github.com/archlinux/archinstall), originally developed by the Arch Linux team. Which has many more up-to-date features like UKI, systemd-boot, disk encryption, etc.

This version is for users who know they want KDE and it's dependencies **(NetworkManager, Pipewire, and SDDM)**.

## Installation

**Pre-req:** 1 USB (minimum 2GB), 1 target Drive (minimum 8GB). 
Or: One USB (minimum 8GB) using `./main -t --live` or `./main -t --pandora`

Boot Arch Linux Live ISO or our builds (using f10, f12 or del)

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
cd Vase/
```

Edit the post script using: `./main -pe`

```
DTHEME=dark
KB_LAYOUT=us
VARIANT=""
```
> Variant is optional, can be left empty. Applies for the current sudo user by default. Do check out some of the parts that you can configure (additional packages, removing stuff, guest account, etc).

Then run: `sudo ./main -p`

After running the script it will restart one last time. **And you are done!**

---

## Debug Logs

Install logs can be found inside `vase_os/hade_box/logs` 
There are `install.log`,`cmd_output.txt` and `cmd_history.txt` avaible but contain more verbose info.

And post install logs `vase_os/kaes_arch`

We also have a helper to extract logs: `vase_os/hade_box/extract_logs` this will return a URL with a short ex: `https://0x0.st/KjFo.log`

For more info see main post-install repo: [KAES-ARCH](https://github.com/h8d13/KAES-ARCH)

### Modifications

- Hybrid setup detection (common case of Nvidia-Intel) in `hardware.py` > VM Setups additional packages for QEMU/KVM
- Fixed mesa errors running adwaita apps under VMs using `vulkan-swarst`
- Fixed a case where it would pick up on host fstab zram causing boot hangs. `genfstab {flags} -f {self.target} {self.target}` note the `-f` for filter.
- Change `f'pacstrap -C /etc/pacman.conf -K {self.target} {" ".join(packages)} --needed --noconfirm'` note the `--needed` flag to prevent re-installs.
- Change `arch-chroot {self.target} mkinitcpio {" ".join(flags)}')` to remove `peek_output=True` causing broken pipe errors. Comestic but important.
- Expanded on brtfs-snapper/timeshift integration

- **Fixed fallbacks in case endpoints are down:** Critical endpoints like https://archlinux.org/mirrors/status/json/ fail or manual one: https://archlinux.org/mirrorlist/

  - Added 5-second timeout to `fetch_data_from_url()` to prevent hanging (shoudl be plenty)
  - Added 30-second timeout for reflector service (falls back to existing mirrors)
  - Added 30-second timeout for keyring WKD sync service (continues with existing keyring)
  - Mirror region loading falls back to local `/etc/pacman.d/mirrorlist` with proper region parsing
  - **Interactive mirror editor** when falling back to local mirrors:
    - Select regions first (Germany, USA, etc. from local mirrorlist)
    - Then optionally filter/reorder those region's mirrors
    - Filter to HTTPS-only mirrors
    - Reorder mirrors interactively (first selected = highest priority)
    - Preserves region structure (`## Germany`) when writing edited mirrorlist
  - **Keyring optimization:** Skips WKD sync if keyring already initialized (detects `/etc/pacman.d/gnupg` populated)

- **HOST POLLUTION PREVENTION:**
  - Created `running_from_iso()` utility function in `lib/general.py` to detect ISO vs host environment
  - **Keyboard layout protection:** `set_kb_layout()` now skips `localectl` when running from host (only modifies ISO environment)
  - **Mirror list protection:** Uses temp copy `/tmp/archinstall_mirrorlist` when installing from host (doesn't modify host's mirrorlist)
  - **Environment detection:** Installer displays "Running from ISO" or "Running from Host" at startup
  - Target system keymap is still properly configured via `installer.set_keyboard_language()` in chroot

- Auto-restores backup pacman.conf from `/etc/pacman.conf.backup` if pacstrap fails (created by iso_mod for CUSTOM ISOs)
- Swap config inside disks to make possible swap on partition
- Removed all BOOTLOADERS/HSM/LVM/FIDO2/LUKS2 logic >  Replaced by default: Grub > To be able to expand on snapper/timeshift features + Grub config and people can do what they want after.
- Stripped a lot of code for defaults to be simpler. And for display (translations, certain menus, etc)
- Removed plugins/scripts for maintanability IDEA was that the stripped version could be forked itself to add more advanced features directly in the flow instead.
- Logging inside dir > Auto-save/Load configs also inside dir.
- Legacy x11 server options
- Change certain OOO flow:
    - mount > format filesystem > create new paritions (swap) > set mirrors and base settings > base install > audio > video > KDE plasma > bootloader
    - /etc/environment variables > network manager > users > final tz, ntp, services, fstab


## Hade_box Explained

**Boot ISO** → Run Hade_box (Archinstall but modified for KDE)

→ **Reboot to hard disk** → (Clones for you) KAES-ARCH → Run post script (Many improvements to defaults)

→ (Clones for you) PACTOPAC →  **Reboot** → Use PACTOPAC settings page to quickly setup

→ **Normal usages** → Use PACTOPAC for ongoing management if needed (or use command line if familiar).

> This set-up with a rolling release is ideal because we have single sources of truth for each critical aspect. Keep my work on the side and be able to brick an install if needed in 15 minutes. We can also easily allow for self-upgrades by simply running `git pull` in the right location.