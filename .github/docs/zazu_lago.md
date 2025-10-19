# zazu_lago

This module is dedicated to testing stuff quickly inside Virtual Machines.

This is handy to test both Grub2 configurations without going into BIOS. Or straight up firmware/hardware stuff.

<img width="1920" height="1080" alt="Screenshot_20251007_153942" src="https://github.com/user-attachments/assets/2e250e9c-8eef-45e3-a3aa-54968926bf14" />

---

A good example is running Adwaita apps (used frequently by GNOME). Other relevant examples like mission-center, gnome-disk-utility, etc. Natively without flatpak or similar.

This was fixed using `vulkan-swrast` in version 0.0.03. The way it was fixed was by making a snapshot of my VM, then install one package, test and repeat... 

## Main VM Menu

```
[+] Quick command: help
########################################
Zazu_lago VM Tooling: rdisk, brick, then dupk.
Display: gtk | GL: on
########################################
 rdisk   : Reset myvm1 60G
 dupk    : Permanent copy
 duck    : Temporary copy
 mayk    : Maybe Y/N copy
 brick   : Boot ISO VASE-2025.10.19-x86_64
 vncd    : Boot w VNC only
 vnck    : Run w VNC only
 std     : Run (standard VGA)
 cupkd   : Boot w /dev/sdf
 cupk    : Run w /dev/sdf
 conkd   : Boot w /dev/sdf and disk
 conk    : Run w /dev/sdf and disk
 taild   : Headless w logs
 bootk   : Boot headless w/ logs
 macg    : Generate MAC + run
 exit    : Exit
########################################
Any key to skip and use standard CMD...
```


### Example usage

Edit `...` file to match: where is my ISO `vm_d="a"` I use a drive for dev builds and `d` for regular ISOs.

Edit `iso_n="VASE-2025.10.18-x86_64"` to match you own.

Edit `vm_name="myvm1" #anydistro` this will be the Cqow2 disk.

Then `sudo ./main -q rdisk`, `brick` then `dupk`.

You can also for example use `sudo ./main -q none` this uses the default CMD.


