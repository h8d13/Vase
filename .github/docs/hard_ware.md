# hard_ware

## System info: 

The easiet way if you are intrested in digging a bit deeper (and you should): 

`sudo dmidecode -t <type>` 

  | Filter    | Shows                                    |
  |-----------|------------------------------------------|
  | system    | Motherboard info, manufacturer, SKU      |
  | baseboard | Detailed mobo specs (better than system) |
  | bios      | BIOS version, vendor, date               |
  | processor | CPU model, cores, threads, speed         |
  | memory    | RAM sticks, speed, type, slots           |
  | cache     | CPU cache levels (L1/L2/L3)              |
  | slot      | PCIe slots (x16, x8, x4, x1)             |
  | connector | Physical ports/connectors                |
  | chassis   | Case/chassis type and info               |


Can paste the model and manufacturer into a search engine. 

`
Manufacturer: Micro-Star International Co., Ltd.
Product Name: GP72 6QE
`

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

Here is me getting 350 fps on this 200$ laptop from eBay.

<img width="1920" height="1080" alt="2025-10-13_14 37 49" src="https://github.com/user-attachments/assets/e91b64ac-a4f1-43e1-bf1a-bbc3a71143c1" />

With a Intel iGPU and Nvidia 950M. Specsheet here [MSI](https://www.msi.com/Laptop/GP72-6QE-Leopard-Pro/Specification)

### NVIDIA Table :(

- GTX 600/700 (Kepler) → needs nvidia-470xx-dkms (AUR)
- GTX 400/500 (Fermi) → needs nvidia-390xx-dkms (AUR)
- GTX 200/8800 (Tesla) → needs nvidia-340xx-dkms (AUR)
- Older than GTX 200 → No longer supported.

> For these above use Nouveau then install from AUR appropriately. [WikiNVIDIA](https://wiki.archlinux.org/title/NVIDIA)

## Kernels

During install you pick one or several kernels, that can be found in your Grub boot screen: (Zen, hardened, lts or default)

Depending on hardware again, performance might differ from one mainline to another variant. 

Mainline standard balanced.
Zen for desktop/gaming.
Hardened for dev systems.
LTS more stable version. (6.12.x)

For example when you build nvidia drivers they are built against your current kernel-headers making this just as important as the drivers selection part.

Another example is network cards that might need LTS or latest (e.g. Realtek drivers)
Why is why I recommend trying to trace through your hardware from model or pieces.

---

# Testing dumps

Done with browser opened and a few apps to make system 'in-use'. Usually a Youtube Video and a code editor.

----

- Integrated graphics: 1000-5000
- Mid-range: 5000-15000
- High-end: 15000-30000+

```
CPU: AMD Ryzen 5 5600X 6-Core 12-Threads Processor

    OpenGL Information
    GL_VENDOR:      NVIDIA Corporation
    GL_RENDERER:    NVIDIA GeForce RTX 4060 Ti/PCIe/SSE2
    GL_VERSION:     4.6.0 NVIDIA 580.95.05
    Surface Config: buf=32 r=8 g=8 b=8 a=8 depth=24 stencil=0 samples=0
    Surface Size:   800x600 windowed
=======================================================
[build] use-vbo=false: FPS: 6594 FrameTime: 0.152 ms
[build] use-vbo=true: FPS: 17829 FrameTime: 0.056 ms
[texture] texture-filter=nearest: FPS: 17437 FrameTime: 0.057 ms
[texture] texture-filter=linear: FPS: 17360 FrameTime: 0.058 ms
[texture] texture-filter=mipmap: FPS: 17728 FrameTime: 0.056 ms
[shading] shading=gouraud: FPS: 17967 FrameTime: 0.056 ms
[shading] shading=blinn-phong-inf: FPS: 17133 FrameTime: 0.058 ms
[shading] shading=phong: FPS: 16930 FrameTime: 0.059 ms
[shading] shading=cel: FPS: 16886 FrameTime: 0.059 ms
[bump] bump-render=high-poly: FPS: 17360 FrameTime: 0.058 ms
[bump] bump-render=normals: FPS: 16982 FrameTime: 0.059 ms
[bump] bump-render=height: FPS: 17052 FrameTime: 0.059 ms
[effect2d] kernel=0,1,0;1,-4,1;0,1,0;: FPS: 17317 FrameTime: 0.058 ms
[effect2d] kernel=1,1,1,1,1;1,1,1,1,1;1,1,1,1,1;: FPS: 17612 FrameTime: 0.057 ms
[pulsar] light=false:quads=5:texture=false: FPS: 16804 FrameTime: 0.060 ms
[desktop] blur-radius=5:effect=blur:passes=1:separable=true:windows=4: FPS: 7500 FrameTime: 0.133 ms
[desktop] effect=shadow:windows=4: FPS: 8425 FrameTime: 0.119 ms
[buffer] columns=200:interleave=false:update-dispersion=0.9:update-fraction=0.5:update-method=map: FPS: 1745 FrameTime: 0.573 ms
[buffer] columns=200:interleave=false:update-dispersion=0.9:update-fraction=0.5:update-method=subdata: FPS: 3180 FrameTime: 0.315 ms
[buffer] columns=200:interleave=true:update-dispersion=0.9:update-fraction=0.5:update-method=map: FPS: 2095 FrameTime: 0.477 ms
[ideas] speed=duration: FPS: 10210 FrameTime: 0.098 ms
[jellyfish] <default>: FPS: 14311 FrameTime: 0.070 ms
[terrain] <default>: FPS: 3126 FrameTime: 0.320 ms
[shadow] <default>: FPS: 11447 FrameTime: 0.087 ms
[refract] <default>: FPS: 6893 FrameTime: 0.145 ms
[conditionals] fragment-steps=0:vertex-steps=0: FPS: 17542 FrameTime: 0.057 ms
[conditionals] fragment-steps=5:vertex-steps=0: FPS: 17277 FrameTime: 0.058 ms
[conditionals] fragment-steps=0:vertex-steps=5: FPS: 17518 FrameTime: 0.057 ms
[function] fragment-complexity=low:fragment-steps=5: FPS: 17871 FrameTime: 0.056 ms
[function] fragment-complexity=medium:fragment-steps=5: FPS: 17940 FrameTime: 0.056 ms
[loop] fragment-loop=false:fragment-steps=5:vertex-steps=5: FPS: 17528 FrameTime: 0.057 ms
[loop] fragment-steps=5:fragment-uniform=false:vertex-steps=5: FPS: 17746 FrameTime: 0.056 ms
[loop] fragment-steps=5:fragment-uniform=true:vertex-steps=5: FPS: 17276 FrameTime: 0.058 ms
=======================================================
                                  glmark2 Score: 13896 
=======================================================
```

CS2: Workshop map de_dust [FPS Bench](https://steamcommunity.com/sharedfiles/filedetails/?id=3240880604)

Settings: Low 1240x 1024 - 5:4 ratio

```
[VProf] -- Performance report --
[VProf] Summary of 60388 frames and 115 1-second intervals.  (4771 frames excluded from analysis.)
[VProf] FPS: Avg=534.8, P1=182.0
[VProf] 
[VProf]                         All frames         Active frames       1s max (all)      1s max (active)  
[VProf]                           Avg    P99        N    Avg    P99      P50    P95        N    P50    P95
[VProf] ---------------------- ------ ------   ------ ------ ------   ------ ------   ------ ------ ------
[VProf]             FrameTotal   1.87   5.49    60388   1.87   5.49     5.83  17.83      115   5.83  17.83
[VProf]       Client Rendering   1.22   1.81    60388   1.22   1.81     1.95  12.19      115   1.95  12.19
[VProf]         Frame Boundary   0.77   1.45    60388   0.77   1.45     1.59  10.27      115   1.59  10.27
[VProf]      Client Simulation   0.21   0.95    60388   0.21   0.95     1.16   2.21      115   1.16   2.21
[VProf]      Server Simulation   0.19   1.79     7204   1.56   2.83     2.04   3.66      115   2.04   3.66
[VProf]            Server Game   0.15   1.45     7204   1.26   2.12     1.71   3.14      115   1.71   3.14
[VProf]    ClientSimulateFrame   0.14   0.31    60388   0.14   0.31     0.33   0.88      115   0.33   0.88
[VProf]   Present_RenderDevice   0.08   0.41    60388   0.08   0.41     0.40   5.57      115   0.40   5.57
[VProf]             Prediction   0.08   0.61    60388   0.08   0.61     0.65   1.10      115   0.65   1.10
[VProf]           UserCommands   0.08   0.76     7204   0.63   0.95     0.86   1.48      115   0.86   1.48
[VProf]     ClientSimulateTick   0.07   0.77     7204   0.60   0.92     0.88   1.62      115   0.88   1.62
[VProf]       Server Animation   0.03   0.33     7204   0.26   0.91     0.35   1.28      115   0.35   1.28
[VProf]       Client_Animation   0.03   0.28     7204   0.24   0.53     0.32   0.79      115   0.32   0.79
[VProf]                   NPCs   0.02   0.28     7204   0.16   0.50     0.35   0.78      115   0.35   0.78
[VProf] Server Send Networking   0.02   0.17     7204   0.15   0.36     0.22   0.67      115   0.22   0.67
[VProf]             Networking   0.02   0.16     7207   0.13   0.25     0.27   0.81      115   0.27   0.81
[VProf]    Server PackEntities   0.01   0.13     7204   0.11   0.33     0.19   0.60      115   0.19   0.60
[VProf]         SoundOperators   0.00   0.00       18   0.31   2.93     0.00   0.15       13   0.13   1.53
```
