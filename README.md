# Vase

<img src="./vase.svg" alt="VaseLogo" width="117" align="left">
<table>
    <tr>
        <td>
            <a href="https://github.com/h8d13/Vase/releases">
                <img src="https://img.shields.io/badge/Arch_Linux-v6.17.1-darkgreen" alt="Arch">
            </a>
        </td>
    </tr>
    <tr>
        <td>
            <a href="https://github.com/h8d13/Vase/releases">
                <img src="https://img.shields.io/badge/Menu_Status-Passing-darkgreen" alt="TUIStatus">
            </a>
        </td>
    </tr>
    <tr>
        <td>
            <img src="https://img.shields.io/badge/Git_Clones-600-blue" alt="Clones">
        </td>
    </tr>
</table>
<br clear="left">

<strong>Version:</strong> 0.0.05 | <strong>Tested:</strong> 2025-10-08 13:34:04 | <strong>Size:</strong> 2.7G
<br><br>
<a href="https://github.com/h8d13/Vase/releases">Releases</a>

---

A testing suite to run VMs and development platforn to perform Archlinux system installations. 

> Made to be able to test future installs without going into BIOS. **Without a USB or without an ISO.**
> Or test other distros from Arch without learning all the QEMU docs.

Written in bash and python. 

> Installs **6-13x faster** than any other distro with KDE, thanks to simply caching files overlayed onto the ISO. 
> And also due to tools made by the release engineering teams at Arch. 

This works from official arch ISO (using mirrors slower, depending on internet speed) or the one built here (faster, using cached files).

> At our compute cost of having to do more frequent builds whenever something is borken. 
> Or at major releases of upstream sources which we have to track closely.

---

<a href="https://github.com/h8d13/Vase/releases">
    <img src="https://img.shields.io/badge/Install_Time-00:02:35-blue" alt="InstallTime">
</a>

## Installation/Usage

### From USB/ISO

> By default you are already root in the ISO env. 

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase.git && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

Go grab some coffee during installation (it'll be done when you come back).

After initial install pick `Reboot` and switch to hard disk.

Open `Konsole` and type `cd KAES-ARCH` this is where the post install script lives and more assets.

Then `sudo vim post` edit to desired values, then `sudo ./post` when ready.

[![VaseInstallVideo](http://img.youtube.com/vi/j7YnkxY1mVo/0.jpg)](http://www.youtube.com/watch?v=j7YnkxY1mVo "Vase Installation Demo")

See an example installation on YouTube [here.](https://www.youtube.com/watch?v=j7YnkxY1mVo)

---

### From an existing arch installation (For devs)

> On an exisitng install use sudo.  

`$ ./main -t (*args)` : Launch TUI forked KDE install
> This will check system subdeps for Arch to Arch installs.

`$ ./main`              : Check envir deps for QEMU/KVM

`$ ./main -s`           : Start VMs testing suite menu

`$ ./main -q help`      : Skip menu pass directly

`$ ./main -i`           : Create ISO overlays w RELENG

`$ ./main -r`           : Reset logs, log settings and rcw

`$ ./main -u`           : Check for updates from GitHub

`$ ./main -b <type>`    : Run benchmarks (io/cpu/gpu)

`$ ./main -f /dev/sdX`  : Flash ISO to USB device

`$ ./main -a /dev/sdX`  : Complete workflow (build, sign, flash, log) 

> Assumes valid GPG key setup: `gpg --full-generate-key` and follow prompts. `gpg --list-secret-keys` for building and KVM compatible hardware for VM options. Also assumes valid sudo profile.
> Mostly tooling for devs... More readmes included. 

To change the post install code aswell:

Run in project root: `git submodule init && git submodule update` 

Find files in `/vase_os/kaes_arch/` or better yet, fork all the repos and send me patches.

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
#### Settings

In project root, `...` file contains all configuration constants.
> VM Config, paths, custom names, etc...

For logging: Inside `.vase.d` you can find `logs.conf` & main program logs.