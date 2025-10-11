# zazulago_vms

This module is dedicated to testing stuff quickly inside Virtual Machines.

This is handy to test both Grub2 configurations without going into BIOS. Or straight up firmware/hardware stuff.

<img width="1920" height="1080" alt="Screenshot_20251007_153942" src="https://github.com/user-attachments/assets/2e250e9c-8eef-45e3-a3aa-54968926bf14" />

---

A good example is running Adwaita apps (used frequently by GNOME). Other relevant examples like mission-center, gnome-disk-utility, etc. Natively without flatpak or similar.

This was fixed using `vulkan-swrast` in version 0.0.03. The way it was fixed was by making a snapshot of my VM, then install one package, test and repeat... 

### Workflow example

- Branch code for today
- Modify stuff

Create ISO if I modified there or use previous one. Using dev_mode=1 & script dev_entry (copies local vs remote).

- Test in VM: `sudo ./main -q rdisk` resets the disk, then `sudo ./main -q brick` boot off ISO.
- Then `sudo ./main -q std` to test everything looks good in the env. 

I also have a few neat options to test in VM with attached storage if I'm lazy (install from VM test on real hardware.)
Then once I'm happy with how everything works out: `sudo ./main -a /dev/sdX` this being a good USB stick.

And try it:

- on first a horrible laptop from 2015 (Hybrid Nvidia/Intel) 
- on Entreprise more recent Dell laptop to compare.
- on my main desktop set-up (have several disks). Where I also code and game :D