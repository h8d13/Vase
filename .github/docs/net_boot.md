# Netbooting Vase

Acquiring ipxe UEFI file (1mb)

```
$ mkdir -p /tmp/efi/EFI/BOOT
$ cp /home/user/Downloads/ipxe-arch.efi /tmp/efi/EFI/BOOT/BOOTx64.EFI
```

Making it readable

```
$ truncate -s 64M /tmp/ipxe.img
$ mkfs.fat /tmp/ipxe.img
$ mcopy -i /tmp/ipxe.img -s /tmp/efi/* ::/
```

Testing in QEMU:
> Use at least 3G of memory or you will get kernel panic on boot.
```
$ sudo qemu-system-x86_64 \
  -enable-kvm \
  -m 6G \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/edk2/x64/OVMF_CODE.4m.fd \
  -drive if=pflash,format=raw,file=/usr/share/edk2/x64/OVMF_VARS.4m.fd \
  -drive file=/tmp/ipxe.img,format=raw,if=virtio \
  -netdev user,id=net0 \
  -device e1000,netdev=net0
```

## USB ipxe boot

The same process but need a fat32 part on the USB.

```
$ sudo fdisk -l /dev/sdX
$ sudo mkfs.fat -F32 /dev/sdX1
$ sudo mkdir -p /mnt/EFI/BOOT
$ sudo cp /home/user/Downloads/ipxe-arch.efi /mnt/EFI/BOOT/BOOTx64.EFI
sudo umount /mnt
```

Then simply boot off of it.

---

For bios equivalent see wiki: [NetBoot](https://wiki.archlinux.org/title/Netboot)