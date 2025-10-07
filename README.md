# Vase

<div>
    <img src="./vase.svg" alt="VaseLogo" width="72">
    <a href="https://github.com/h8d13/Vase/releases">
        <img src="https://img.shields.io/badge/Arch_Linux-v6.16.10-darkgreen" alt="Arch">
    </a>
    <br><br>
    <strong>Version:</strong> 0.0.04 | <strong>Tested:</strong> 2025-10-07 14:39:19 | <strong>Size:</strong> 2.7G
    <br><br>
    <a href="https://github.com/h8d13/Vase/releases">Releases</a>
</div>

---

A testing suite to run VMs and perform Archlinux system installations. 

> Made to be able to test future installs without going into BIOS. **Without a USB or without an ISO.**
> Or test other distros from Arch without learning all the QEMU docs.

Written in bash and python. 

> Installs **6-13x faster** than any other distro with KDE, thanks to simply caching files overlayed onto the ISO. 
> And also due to tools made by the release engineering teams at Arch. At the cost of having to do more frequent builds.

---

<a href="https://github.com/h8d13/Vase/releases">
    <img src="https://img.shields.io/badge/Install_Time-00:02:35-blue" alt="InstallTime">
</a>

## Installation/Usage

### From USB/ISO

> By default you are already root in the ISO env. 
> This should work from official arch ISO (using mirrors) or the one built here (using cached).

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

Go grab some coffee during installation (it'll be done when you come back).

After initial install pick `Reboot` and switch to hard disk.

Open `Konsole` and type `cd KAES-ARCH` this is where the post install script lives and more assets.

Then `sudo vim post` edit to desired values, then `sudo ./post` when ready.

[![VaseInstallVideo](http://img.youtube.com/vi/j7YnkxY1mVo/0.jpg)](http://www.youtube.com/watch?v=j7YnkxY1mVo "Vase Installation Demo")

See an example installation on YouTube [here.](https://www.youtube.com/watch?v=j7YnkxY1mVo)

---

### From an existing arch installation (For devs)

`$ git clone https://github.com/h8d13/Vase`

`$ sudo ./main -t (*args)` : Launch TUI forked KDE install
> This will check system subdeps for Arch to Arch installs.

`$ sudo ./main`    : Check envir deps for QEMU/KVM

`$ sudo ./main -s` : Start VMs testing suite menu

`$ sudo ./main -q brick` : Skip menu pass directly

`$ sudo ./main -i` : Create ISO overlays w RELENG

`$ sudo ./main -r` : Reset logs, log settings and rcw

`$ sudo ./main -u` : Check for updates from GitHub

`$ sudo ./main -b <type>` : Run benchmarks (io/cpu/gpu)

`$ sudo ./main -f /dev/sdX` : Flash ISO to USB device

`$ sudo ./main -a /dev/sdX` : Complete workflow (build, sign, flash, log) 

> Assumes valid GPG key setup: `gpg --full-generate-key` and follow prompts. `gpg --list-secret-keys` for building and KVM compatible hardware for VM options.
> Mostly tooling for devs... More readmes included. 

To change the post install code aswell:

Run in project root: `git submodule init && git submodule update` 

Find files in `/vase_os/kaes_arch/` or better yet fork all the repos and send me patches.

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
