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
            <img src="https://img.shields.io/badge/Git_Clones-668-blue" alt="Clones">
        </td>
    </tr>
</table>
<br clear="left">

<strong>Version:</strong> 0.0.06 | <strong>Tested:</strong> 2025-10-09 16:01:19 | <strong>Size:</strong> 2.7G
<br><br>
<a href="https://github.com/h8d13/Vase/releases">Releases</a>

---

## VaseOS - Archlinux KDE 🏺

A testing suite to run VMs and development platform to perform Archlinux system installations. 

> Made to be able to test future installs without going into BIOS. **Without a USB or without an ISO.**
> Or test other distros from Arch without learning all the QEMU docs.

Written in bash and python. 

> Installs **6-13x faster** than any other distro with KDE, thanks to simply caching files overlayed onto the ISO. 
> And also due to tools made by the release engineering teams at Arch. 

This works from official arch [ISO](https://archlinux.org/download/) (using mirrors slower, depending on internet speed) or the one built [here](https://github.com/h8d13/Vase/releases) (faster, using cached files).

> At our compute cost of having to do more frequent builds whenever something is borken. 
> Or at major releases of upstream sources which we have to track closely.

---

## Installation/Usage

### From USB/ISO

> By default you are already root in the ISO env. 

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase.git && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

> Follow the prompts here: Some critical sections include disk setup, hardware profiles, bluetooth needed, x11 optional (old NVIDIA hardware for example).

Go grab some coffee during installation (it'll be done when you come back).

After initial install pick `Reboot` and switch to hard disk.

Open `Konsole` and type `cd KAES-ARCH` this is where the post install script lives and more assets.

Then `sudo vim post` edit to desired values, then `sudo ./post` when ready.

[![VaseInstallVideo](http://img.youtube.com/vi/j7YnkxY1mVo/0.jpg)](http://www.youtube.com/watch?v=j7YnkxY1mVo "Vase Installation Demo")

See an example installation on YouTube [here.](https://www.youtube.com/watch?v=j7YnkxY1mVo)

If this helped you and earned you some time to touch grass (or you even just learned things), please consider sharing the project, opening pull requests, or even just a star ⭐. 

> If you do want to contribrute to the project more in depth or want to chat about the next feature, I'm also active on reddit u/Responsable-Sky-1336 do message me! 


<a href="https://github.com/h8d13/Vase/releases">
    <img src="https://img.shields.io/badge/Install_Time-00:02:35-blue" alt="InstallTime">
</a>


---

### From an existing arch installation (For devs)

> On an existing install use sudo.  

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

`$ ./main -a /dev/sdX`  : Complete workflow

[![VaseOSinOS](http://img.youtube.com/vi/T-g_V_WIOt0/0.jpg)](http://www.youtube.com/watch?v=T-g_V_WIOt0 "Vase Installation Demo")

See an example QEMU install [here.](https://www.youtube.com/watch?v=T-g_V_WIOt0)

> Assumes valid GPG key setup: `gpg --full-generate-key` and follow prompts for building and KVM compatible hardware for VM options. 
> Mostly tooling for devs... More readmes included. 

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
--all <device>          # Complete workflow
```

## Components

> Tools used: mainly archinstall, mkarchiso, arch-install-scripts, dd, jq. Compression: squashfs (xz), .tar.zst (pkgs) and tar.gz (db of pkgs) pacman confs. 

Run in project root: `git submodule init && git submodule update` 

Or better yet, fork all the repos and send me patches.


| Component | Desc | Docs |
|:----------|:------------|:--------------|
| **hade_box** | Installer fork - Modified TUI for fast Arch Linux KDE installation | [README](./vase_os/hade_box/README.md) |
| **zazulago_vms** | Testing suite - VM meny QEMU/KVM testing environment | [README](./vase_os/zazulago_vms/README.md) |
| **kaes_arch** | Post-install - System configuration and package installation | [README](https://github.com/h8d13/KAES-ARCH) |
| **pacto_pac** | GUI - Pacman commons operations Gtk/Adwaita app | [README](https://github.com/h8d13/PACTOPAC) |

[QEMU Docs](https://www.qemu.org/documentation/)

#### Settings

In project root, `...` file contains all configuration constants.
> VM Config, paths, custom names, etc...

For logging: Inside `.vase.d` you can find `logs.conf` & main program logs.

#### Turning Konqi in Konqzilla.

Making it all open so people can edit anything they desire from the flow, while reducing the scope of archinstall, which is impossible to maintain. 

> Idea was simple: Faster testing/installs, fixing host to target installs, **saving mirror providers TBs in bandwith** and less choices to break something in TUI (kind of work for all scenario) testing on weird/old hardware like Hybrid Nvidia/Intel setups or more recent desktops too.

![konqzilla](https://github.com/user-attachments/assets/8c7d7050-f58a-4dbc-aa69-2d9ee9716edc)
