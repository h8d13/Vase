# Vase

## Latest Release

**Version:** 0.0.03 | **Tested:** 2025-10-06 14:25:22 | **ISO:** VASE-2025.10.06-x86_64.iso | **Size:** 2.7G

[Releases](https://github.com/h8d13/Vase/releases/tag/ISOs)

---

A testing suite to run VMs and perform Archlinux system installations.

> Made to be able to test future installs without going into BIOS. **Without a USB or without an ISO.**
> Or test other distros from Arch without learning all the QEMU docs.

Written in bash to wrap Archinstall.

---

## Installation/Usage

### From USB/ISO

> By default you are already root in the ISO env.

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

Go grab some coffee during installation (it'll be done when you come back).

After initial install pick `Reboot` and switch to hard disk.

Open `Konsole` and type `cd KAES-ARCH` this is where the post install script lives and more assets.

Then `sudo vim post` edit to desired values, then `sudo ./post` when ready.

---

### From an existing arch installation

`$ git clone https://github.com/h8d13/Vase`

`$ sudo ./main`    : Check envir deps for QEMU/KVM

`$ sudo ./main -s` : Start VMs testing suite menu

`$ sudo ./main -q brick` : Skip menu pass directly

`$ sudo ./main -i` : Create ISO overlays w RELENG

`$ sudo ./main -t (*args)` : Launch TUI forked KDE install

`$ sudo ./main -r` : Reset logs, log settings and rcw

`$ sudo ./main -u` : Check for updates from GitHub

`$ sudo ./main -b <type>` : Run benchmarks (io/cpu/gpu)

`$ sudo ./main -f /dev/sdX` : Flash ISO to USB device

`$ sudo ./main -a /dev/sdX` : Complete workflow (build, sign, flash, log) 

> Assumes valid GPG key setup: `gpg --full-generate-key` and follow prompts. `gpg --list-secret-keys`

All long-form commands:

```
--reset                 # Resets logs
--update                # Checks git for updates
--tuimenu               # Launch modified TUI
--isomod                # Create iso default `iso_profiles/fat.conf`
--start                 # Start VM menu
--quick <command>       # Lanch VM "help" to see options
--bench <type>          # Run benchmarks: io, cpu, gpu
--flash <device>        # Flash ISO to USB device (e.g., /dev/sdd)
--all <device>          # Complete workflow: build ISO, sign, flash, log to tests.status
```

---

### Settings

In project root, `...` file contains every single configuration constants.
> VM Config, paths, custom names, etc...

For logging: Inside `.vase.d` you can find `logs.conf`:
```
#FORMAT= # 1 Start enabled / 0 Start disabled
COLORS=1 # 0 Disables colors of all output
TIMING=1 # 0 Disables timing output of rcw
DEBUGS=1 # 0 Disables all info outputs
TEELOG=1 # 0 Disables complete log file
LOGMEM=0 # 1 Enables keeping previous log
LOGCLR=0 # 1 Enables non standard ascii in log
CATART=1 # 0 Disables cli art sadface
```

Special shout to the devs at archlinux and other open-source contributors for making this project possible. 

---

[![VaseInstallVideo](http://img.youtube.com/vi/j7YnkxY1mVo/0.jpg)](http://www.youtube.com/watch?v=j7YnkxY1mVo "Vase Installation Demo")

See the video on YouTube [here.](https://www.youtube.com/watch?v=j7YnkxY1mVo)
