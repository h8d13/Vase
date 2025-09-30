# VaseOS
A testing suite to run VMs and perform system installations.

## Usage


### From an existing install

1. Get the code from Github

`git clone https://github.com/h8d13/VaseOS`

2. Check deps if not running from the USB

To check packages used by archinstall fork:

`$ sudo ./hade_box/install -d` then without `-d` to test TUI menu. 

It will output perhaps missing libs used in arch install and how to download them.

3. Install to a target drive or create custom ISO ! 

Overlay hade_box into an existing ISO or create your own installers.

4. Testing suite from an existing install

`$ sudo ./main` to install required.

5. Start your first VMs

`$ sudo ./main -s` to start the menu.

```
########################################
Zazulago VM Tooling: rdisk, then brick.
Display: sdl | GL: on
########################################
 r       : Refresh key
 rdisk   : Reset myvm1 60G
 dupk    : Permanent copy
 duck    : Temporary copy
 mayk    : Maybe save copy
 brick   : Boot ISO + Run
 vncd    : Boot ISO (VNC)
 vnck    : Run (VNC)
 std     : Run (standard VGA)
 cupkd   : Boot ISO w /dev/sde1
 cupk    : Run w /dev/sde1
 taild   : Headless w logs
 bootk   : Boot headless w/ logs
 macg    : Generate MAC + run
 conkd   : Boot ISO w /dev/sde1
 conk    : Run w /dev/sde1
 potk    : Delete key + encrypt
 exit    : Exit without encrypt
########################################
Choice (any key for default): exit
[-] Exiting without encryption
```

6. Single file for all conf

Found in root dir: `...`

7. Config file for logs

```
#FORMAT= # 1 start enabled / 0 start disabled
COLORS=1 # 0 Disables colors of all output
TIMING=1 # 0 Disables timing output of rcw
DEBUGS=1 # 0 Disables info outputs from program
TEELOG=1 # 0 Disables complete log file
LOGMEM=0 # 1 Enables keeping previous log
LOGCLR=0 # 1 Enables non standard ascii in log
CATART=1 # 0 Disables cli art sadface
```

### From a USB

1. Get the code from Github

`git clone https://github.com/h8d13/VaseOS`

2. Regular USB run

`$ sudo ./hade_box/install` to run the regular TUI menu.

