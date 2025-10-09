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

> Assumes valid GPG key setup: `gpg --full-generate-key` and follow prompts for building and KVM compatible hardware for VM options. 
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

## Components

| Component | Desc | Docs |
|:----------|:------------|:--------------|
| **hade_box** | Installer fork - Modified TUI for fast Arch Linux KDE installation | [README](./vase_os/hade_box/README.md) |
| **zazulago_vms** | Testing suite - VM meny QEMU/KVM testing environment | [README](./vase_os/zazulago_vms/README.md) |
| **kaes_arch** | Post-install - System configuration and package installation | [README](https://github.com/h8d13/KAES-ARCH) |
| **pacto_pac** | GUI - Pacman commons operations Adwaita app | [README](https://github.com/h8d13/PACTOPAC) |

#### Settings

In project root, `...` file contains all configuration constants.
> VM Config, paths, custom names, etc...

For logging: Inside `.vase.d` you can find `logs.conf` & main program logs.

Turn Konqi in Kodzilla.

![ConkyGif](https://private-user-images.githubusercontent.com/52324046/438629100-a8912369-a8cc-49be-af79-80994e8d2ab6.gif?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTk5OTYxODUsIm5iZiI6MTc1OTk5NTg4NSwicGF0aCI6Ii81MjMyNDA0Ni80Mzg2MjkxMDAtYTg5MTIzNjktYThjYy00OWJlLWFmNzktODA5OTRlOGQyYWI2LmdpZj9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTEwMDklMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUxMDA5VDA3NDQ0NVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWJhMDY3NWEzZGViMmQ1ZTMyZmVlNmVlZWNkMjljNTMwNDM2YzUyZWFmNTgzNGI1ZDJlODRlYTNlNDJhMmMzNTEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.riBvUa6we5z4KaHiTc1WixmVkjrkwbUOntNdRpJow9c)