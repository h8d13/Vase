# Vase

<img src="./vase_os/vase.svg" alt="VaseLogo" width="117" align="left">
<table>
    <tr>
        <td>
            <a href="https://github.com/h8d13/Vase/releases"><img src="https://img.shields.io/badge/Arch_Linux-v6.17.2-darkgreen" alt="Arch_Linux"></a>
        </td>
        <td>
            <a href="https://github.com/h8d13/Vase/releases"><img src="https://img.shields.io/badge/Plasma-6.4.5-darkgreen" alt="Plasma"></a>
        </td>
    </tr>
    <tr>
        <td>
            <a href="https://github.com/h8d13/Vase/releases"><img src="https://img.shields.io/badge/TUI_Status-Passing-darkgreen" alt="TUI_Status"></a>
        </td>
        <td>
            <a href="https://github.com/h8d13/Vase/releases"><img src="https://img.shields.io/badge/Qt-6.10.0-darkgreen" alt="Qt"></a>
        </td>
    </tr>
    <tr>
        <td>
            <a href="https://github.com/h8d13/Vase/releases"><img src="https://img.shields.io/badge/Git_Clones-985-blue" alt="Git_Clones"></a>
        </td>
        <td>
            <a href="https://github.com/h8d13/Vase/releases"><img src="https://img.shields.io/badge/Frameworks-6.19.0-blue" alt="Frameworks"></a>
        </td>
    </tr>
</table>
<br clear="left">

<strong>Version:</strong> 0.0.10 | <strong>Tested:</strong> 2025-10-15 10:04:27 | <strong>Size:</strong> 2.7G
<br><br>
<a href="https://github.com/h8d13/Vase/releases">Releases</a>

---

## VaseOS - Arch KDE 🏺

A testing suite to run VMs and development platform to perform Archlinux system installations. 

> Made to be able to test future installs without going into BIOS. **Without a USB or without an ISO.**
> Or test other distros from Arch without learning all the QEMU docs.

Written in bash and python. 

> Installs **6-13x faster** than any other distro with KDE, thanks to simply caching files overlayed onto the ISO. 
> And also due to tools made by the release engineering teams at Arch. CURRENT BEST TIME: **1m54s**

This works from official arch [ISO](https://archlinux.org/download/) (using mirrors slower, depending on internet speed) or the one built [here](https://github.com/h8d13/Vase/releases) (faster, using cached files).

> At our compute cost of having to do more frequent builds whenever something is borken. 
> Or at major releases of upstream sources which we have to track closely.

## Prep

You can use [rufus](https://rufus.ie/) for Winslows or [KDEImageWriter](https://apps.kde.org/isoimagewriter/) from Linux (or dd)
> Select mbr/gpt according to your hardware (ususally gpt) And then when pressing "start" use dd mode for full copy.

---

## Installation/Usage

### From the official [ISO](https://archlinux.org/download/) or our builds [here](https://github.com/h8d13/Vase/releases)

> By default you are already root in the ISO env.

`$ pacman-key --init && pacman -Sy git`

`$ git clone https://github.com/h8d13/Vase && cd Vase`

`$ ./main -t` : Launch TUI forked KDE install

> In the TUI: Some critical sections include disk setup, hardware profiles, bluetooth needed, x11 optional (old NVIDIA hardware for example).

<img width="1070" height="746" alt="Screenshot_20251012_120728" src="https://github.com/user-attachments/assets/b7c2ca05-2f03-44bb-abd7-6cc5881856e9" />

Go grab some coffee during installation (it'll be done when you come back). 

After initial install pick `Reboot` and **switch to hard disk** in BIOS. 
> Note: I recommend only plugging-in one screen at this step. you can then add as many as you want later.

After login in with your user > Open `Konsole` and type `cd KAES-ARCH` this is where the post install script lives and more assets.

Then `sudo vim post` edit to desired values, then `sudo ./post` when ready.

[![VaseInstallVideo](http://img.youtube.com/vi/j7YnkxY1mVo/0.jpg)](http://www.youtube.com/watch?v=j7YnkxY1mVo "Vase Installation Demo")

See an example installation on YouTube [here.](https://www.youtube.com/watch?v=j7YnkxY1mVo)

If this helped you earn you some time to touch grass (or you even just learned things), please consider sharing the project, open a pull request, or even just a star ⭐.

> We also have a discussions tab for any general purposes questions, ideas, etc...

---

## Hardware Compat [README](./.github/docs/hard_ware.md)

VaseOS automatically detects hardware and recommends appropriate drivers based on modified archinstall `hardware.py` detection logic, but is only a recommendation. You are free to **select the drivers** you want to try. See a full table of supported stuff in the link above. 
> Generally AMD/Intel stuff will be straight-forward.

## Languages Compat 🌐

Before running the post install script you can uncomment any of these lines for extended support:
```
#LG_PACKS+=" noto-fonts-cjk"         # Chinese, Japanese, Korean
#LG_PACKS+=" noto-fonts-extra"       # Arabic, Hebrew, Greek, Cyrillic, Thai extended symbols
#LG_PACKS+=" noto-fonts-devanagari"  # Hindi/Devanagari
```
## Live installations

You can also use `./main -t --live` for installs in place/removable media (For installing with only one USB: min 8GiB, use newer ones or it will take ages)

---

### Turning Konqi in Konqzilla.

We believe builds should receive almost daily updates (we are currently building one ISO per day or two), proactively fixing issues that others have overlooked for too long, in an idempotent and perennial way. This does incur some compute costs.

Making it all open so people can edit anything they desire from the flow, while reducing the scope of archinstall, which is impossible to maintain. 

> Idea was simple: Faster testing/installs, fixing host to target installs, **saving mirror providers TBs in bandwith** and less choices to break something in TUI (kind of work for all scenario) testing on weird/old hardware like Hybrid Nvidia/Intel setups or more recent desktops too.

![konqzilla](https://github.com/user-attachments/assets/8c7d7050-f58a-4dbc-aa69-2d9ee9716edc)

---

## For Devs [README](./.github/docs/docs_main.md)

## Artix Compat Layer 🥶

<a href="./.github/docs/klar_tix.md"><img src="https://img.shields.io/badge/Artix_Linux-v6.17.1-blue" alt="Artix_Linux"></a>

> Made specially for my friend Klagan who likes runit and minimalist installs with little bandwidth <3 

Bootstrap Artix Linux with desired init system. From any existing Linux install to a live disk. Should be appreciated by purists and elitists of the community. 

[![VaseOSinOS](http://img.youtube.com/vi/N1Uy02KVnXU/0.jpg)](http://www.youtube.com/watch?v=N1Uy02KVnXU "Vase Installation Demo")

See an example Klartix install [here.](https://www.youtube.com/watch?v=N1Uy02KVnXU)

## Components

Run in project root: `sudo ./main -u` or `--update` this pulls in the submodules and checks for updates.  

Or better yet, fork all the repos and send me patches.

| Components | Desc | Docs |
|:----------|:------------|:--------------|
| **hade_box** | Installer fork - Modified TUI for Arch Linux KDE installation | [README](./.github/docs/hade_box.md) |
| **grome_lum** | Grub2 utils - Setting keymaps, passwords, or custom entries | [README](./.github/docs/grom_lum.md) |
| **kaes_arch** | Post-install - System configuration and package installation | [README](https://github.com/h8d13/KAES-ARCH) |
| **pacto_pac** | GUI - Pacman common operations Gtk/Adwaita app | [README](https://github.com/h8d13/PACTOPAC) |
| **zazu_lago** | Testing suite - VM menu QEMU/KVM testing environment | [README](./.github/docs/zazu_lago_.md) |
| **klar_tix** | Artix bootstrap - Init system compatible minimal installer | [README](./.github/docs/klar_tix.md) |
| **chap_pie** | System utils - Benchmarking and testing tools for new installs | [README](./.github/docs/chap_pie.md) |

[QEMU Docs](https://www.qemu.org/documentation/)

### Settings

In project root, `...` file contains all configuration constants.
> VM Config, paths, custom names, etc...

For logging: Inside `.vase.d` you can find `logs.conf` & main program logs.
