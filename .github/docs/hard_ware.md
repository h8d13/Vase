# hard_ware

## Basics

  ### HW TABLE

  | Hardware Profile | Packages Installed | Notes |
  |:----------------|:-------------------|:------|
  | **All Open-Source** | Installs a lot of packages... | Universal fallback |
  | **AMD / ATI** | mesa, xf86-video-amdgpu, xf86-video-ati, libva-mesa-driver, vulkan-radeon | Generic AMD |
  | **Intel** | mesa, libva-intel-driver, intel-media-driver, vulkan-intel | HD Graphics, Iris Xe, Arc, etc |
  | **Nvidia (Proprietary)** | nvidia-dkms, dkms, libva-nvidia-driver | GTX 900+ / RTX 20-50 series. Auto-adds nvidia-prime if Intel iGPU detected |
  | **Nvidia (Open Kernel)** | nvidia-open-dkms, dkms, libva-nvidia-driver | Turing+ and newer. Auto-adds nvidia-prime if Intel iGPU detected |
  | **Nvidia (Nouveau)** | mesa, xf86-video-nouveau, libva-mesa-driver, vulkan-nouveau | For legacy/unsupported cards |
  | **QEMU/KVM VM** | mesa, vulkan-virtio, qemu-guest-agent, vulkan-swrast, libva-mesa-driver | VM optimized |
  | **VirtualBox VM** | mesa, vulkan-swrast, virtualbox-guest-utils, libva-mesa-driver | VBox guest |
  | **AMD/Intel CPU** | amd-ucode, intel-ucode | Microcode Auto-detected |
  | **SOF Audio** | sof-firmware | Auto-detected (modern Intel audio) |
  | **ALSA Audio** | alsa-firmware | Auto-detected (legacy cards) |

### NVIDIA Table :(

- GTX 600/700 (Kepler) → needs nvidia-470xx-dkms (AUR)
- GTX 400/500 (Fermi) → needs nvidia-390xx-dkms (AUR)
- GTX 200/8800 (Tesla) → needs nvidia-340xx-dkms (AUR)
- Older than GTX 200 → No longer supported.

> For these above use Nouveau then install from AUR appropriately. [WikiNVIDIA](https://wiki.archlinux.org/title/NVIDIA)

### NVIDIA Table :) 
> Refer back to top table.

- Maxwell = GTX 900 series (GTX 950, 960, 970, 980)
- Pascal = GTX 10 series (GTX 1050, 1060, 1070, 1080)
- Turing = RTX 20 series & GTX 16 series (RTX 2060, 2070, 2080, GTX 1650, 1660)
- Ampere = RTX 30 series (RTX 3060, 3070, 3080, 3090)
- Ada Lovelace = RTX 40 series (RTX 4060, 4070, 4080, 4090)
- Blackwell = RTX 5000+

> They are a bit of a hit or miss. But what is cool is that you can try several drivers (prop vs open vs fallback), kernels (zen, lts) in little time and run `Glmark2` or `3dmax` or similar to test perf. My Ada series (4060Ti) works perfectly fine on proprietary for example.

### Hybrid Graphics (Intel + Nvidia)

When both Intel and Nvidia GPUs are detected, `nvidia-prime` is automatically included with any Nvidia driver selection. This enables GPU switching for laptops with Optimus.

**Usage:**
```bash
prime-run <intensiveapp>
```

Example:
```bash
prime-run steam           # Steam
prime-run prismlauncher   # Minecraft
prime-run kdenlive        # Video editor
```

This runs the application on the Nvidia dGPU instead of the Intel iGPU, useful for power management and performance. 

---

## System info: 

The easiet way if you are intrested in digging a bit deeper (and you should): 

`sudo dmidecode -t system`

Can paste the model and manufacturer into a search engine. 

`
Manufacturer: Micro-Star International Co., Ltd.
Product Name: GP72 6QE
`

Here is me getting 350 fps on this 200$ laptop from eBay.

<img width="1920" height="1080" alt="2025-10-13_14 37 49" src="https://github.com/user-attachments/assets/e91b64ac-a4f1-43e1-bf1a-bbc3a71143c1" />
