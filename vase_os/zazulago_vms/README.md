# Zazulago VMs

This module is dedicated to testing stuff quickly inside Virtual Machines.

This is handy to test both Grub2 configurations without going into BIOS. Or straight up firmware/hardware stuff.

<img width="1920" height="1080" alt="Screenshot_20251007_153942" src="https://github.com/user-attachments/assets/2e250e9c-8eef-45e3-a3aa-54968926bf14" />

---

A good example is running Adwaita apps (used frequently by GNOME). Other relevant examples like mission-center, gnome-disk-utility, etc. Natively without flatpak or similar.

This was fixed using `vulkan-swrast` in version 0.0.03. The way it was fixed was by making a snapshot of my VM, then install one package, test and repeat... 
