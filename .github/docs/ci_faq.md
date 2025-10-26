# FAQ

- My USB won't boot
Check that when flashing it you use `mbr/gpt` appropriate to hardware. Usually gpt for UEFI newer hardware.

- BIOS Options errors
  - Secure boot: Off or Other OS (In some case that can allow for simple grub os-prober integration to other OSes.)
  - Check that SATA mode is correct (usually AHCPI)

For full secure-boot setup: [Wiki](https://wiki.archlinux.org/title/GRUB#Secure_Boot_support)

# Common Issues

- IO Exceptions during Partitionning step

This can be due to incorrect manual configuration, our builds are tested using best-effort full disk installs.

- GPG errors during `pacstrap`

This is often caused by the BIOS clock not being on time (since gpg is time sensitive and is critical to verifying the integrity of pkgs).
This also means in the TUI make sure to pick a timezone that is actually correct.

You can also fix this manually in terminal before install if you desire `$ timedatectl status` or directly in BIOS.

`$ timedatectl list-timezones` 

`$ timedatectl set-timezone Asia/Honk_Kong`

Sometimes if the CMOS battery of a BIOS is dead, the issue is that your preferred settings can get reset. And cause issues for example older BIOS can reset to `Octane RST` for SATA Mode.
