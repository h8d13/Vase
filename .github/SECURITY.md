# Security - VaseOS Arch KDE 🛡️

- All ISOs are signed using `gpg` default `1M - 4096b` with valid email.
- They can be mounted and explored and other than what is in `iso_mod` have not been altered otherwise.
    - Cached KDE files, motd and added git to packages.
    - Local package repo in ISO - Uses `TrustAll` sig level (live environment only, doesn't persist on installed system)
- We have included in the post-install script:
    - First `ufw` defaults essentially makes firewall effective (allows `443/tcp` and `22/tcp` and `deny incoming`)
    - Kernel `sysctl` config I call this the `not a router` stuff

## User configuration is the real key to security

- In post install script we have included a util to create a `guest` account for example. Useful if you have siblings or kids. 
- User/Guest Account Security:
  - Guest users optionally password-protected or passwordless
  - Guest sudo access only when password enabled (`GUEST_SUDO=true` requires `GUEST_USE_PASSWORD=true`)
  - Groups limited: `audio, video, games, power, optical, storage, scanner, lp, network` (no wheel by default)
  - Restricted shell option: `/bin/rbash` available for heavily restricted guest
- Setting up Grub passwords for laptops see `grome_lum`

- Can go deeper into it by looking into `apparmor` & `firejail/fail2ban/bubblewrap` & `flatseal`
