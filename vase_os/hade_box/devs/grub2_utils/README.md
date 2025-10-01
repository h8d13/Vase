# SYMAN

## Grub2 Keymaps

Took me 24h to not be on outdated documentation (which will break your setup btw) so made a script to save time for others. 

Thanks to this blog post [FitzBlog](https://fitzcarraldoblog.wordpress.com/2019/04/21/how-to-change-the-keymap-keyboard-layout-used-by-the-grub-shell-in-gentoo-linux/) And W to gentoo users for going in exact detail and how to do something.

---

Basically when running `grub-mklayout` to generate the layout file: get error: `ckbcomp` not found on arch. So you just need to make sure to have it from the AUR (hopefully becomes a core package). This is a large perl script that just maps/converts keys to a grub compatible format `.gkb` I've included it directly in the repo here as it's unlikely to change that much. 

Then follow the steps from the guide on Fitz's blog or the script [here](https://github.com/h8d13/SYMAN-GRUB2/blob/master/grub_keymaps). 

```
KB_LAYOUT="fr"
KB_VARIANT="azerty"
```

Make sure to set these and variant can be left empty as `""`. 

Careful that grub (and system critical pieces in general) are often restricted to 1-127 range. So don't use special chars in users/passwords, etc. And are case sensitive! 

> At this point you can verify it works by pressing `c` in the grub menu and checking keys are properly registered.

This part does assume you have an install with existing `/usr/share/X11/xkb/symbols` but these are pretty standard and are included in `xkeyboard-config` required by: `libxkbcommon  xorg-server-common`

## Grub2 Passwords

Included a second script that can generate the hash append it to the same file we just modified.

But this already covers a large vector that nobody can edit your launch lines (common exploit of adding rw and spawing a shell) or use the rescue shell without your user/pw.

Script [here](https://github.com/h8d13/SYMAN-GRUB2/blob/master/grub_passw). 

By default I've set that root + sudo user invoker can use the password you have set. 

But you can easily modify:

Using `grub-mkpasswd-pbkdf2`

1. Single/Multiple superusers with full access:
```
set superusers="root alice bob"
password_pbkdf2 root [root_hash]
password_pbkdf2 alice [alice_hash]
password_pbkdf2 bob [bob_hash]
```

2. (Optional) Different permission levels - regular users vs superusers:
```
set superusers="root"
password_pbkdf2 root [root_hash]
password_pbkdf2 user1 [user1_hash]  # Regular user, no superuser privs
```

3. (Optional) Per-entry types
```
# Find the info you need:
sudo grep -A15 "menuentry 'Arch Linux'" /boot/grub/grub.cfg | head -20

menuentry 'Arch Linux (Protected)' --users "root,hadean" {
      load_video
      set gfxpayload=keep
      insmod gzio
      insmod part_gpt
      insmod fat
      echo 'Loading Linux linux-zen ...'
      linux /vmlinuz-linux-zen root=UUID=YOURUUID rw zswap.enabled=0 rootfstype=ext4 locale=en_GB loglevel=3 quiet
      initrd /intel-ucode.img /initramfs-linux-zen.img
  }
```

Can also use `--unrestricted` or `--users root` for example.

4. Too lazy for custom entries but still want some protection.

```
sudo sed -i 's/\${CLASS} \\\$menuentry_id_option/\${CLASS} --unrestricted \\$menuentry_id_option/g' /etc/grub.d/10_linux
```

You can use `sed -i.backup` if you want to keep the original file to check/compare. But make sure to remove it after so it doesn't get parsed by `grub-mkconfig`

This will remove the restriction from default boot entry but keep the password protection for command line and edit launch config. Edits line 113 and 115. 

Then `sudo grub-mkconfig -o /boot/grub/grub.cfg`

## Grub2 Rescue

Basically let's say you `rm -rf /usr/bin` this provides a utility script to have a rescue env (copied from a USB to a physical partition) in your grub entries. To then mount and perform required maintenance. This is also useful for testing installations . Find script [here](https://github.com/h8d13/SYMAN-GRUB2/blob/master/grub_rescue). 

