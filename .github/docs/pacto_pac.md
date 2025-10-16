# Making Arch accessible to anyone <3

## PACTOPAC
Simple GUI for pacman/flatpak using Subprocess.

![Screenshot_20250524_173817](https://github.com/user-attachments/assets/377cad96-f707-497a-9729-c949c9626663)
![image](https://github.com/user-attachments/assets/f9e196b8-49d4-452c-8479-205069277ae0)

---

### Get it running:
```
$ pacman -S python-gobject gtk4 libadwaita vte4 pacman-contrib
$ sudo python3 main.py
``` 

#### What?

**Settings:**
> Settings was the most important part for me in this project because they correct things you'd have to do manually.

Pacman Stuff
- Enable multi-lib
- Styling
- Mirrors

Not Pacman Stuff
- Flatpak

**Core features:**

- Subprocess display
- Package info/install/remove/clean
- Search
