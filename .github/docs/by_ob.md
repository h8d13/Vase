# Bring Your Own B****

Clone then run `-u` to pull submodules. Be faomiliar with `...` file and main options.

1. Modify `vase_os/zazu_lago/iso_profiles/?.conf` and `vase_os/hade_box/archinstall/default_profiles/desktops/?.py` 

> Here you might also need to search in `hade_box` term: `class ProfileHandler:` 

2 Generate an ISO using `-i` just for ISO or `-w` for gpg signing for PROD.

> `dev_mode=1` for copying local uncommited changes to root of ISO

3. Create a post script inside `vase_os/kaes_arch` with name `post_dename`

> This for quick set-up is cloned automatically also in sudo_user0's home

4. Test in VM, then on hardware. Using VM tooling.

> `rdisk`, `brick`, `dupk`, `std`

And run post you created... `sudo ./main -pe ?` `sudo ./main -p ?`
