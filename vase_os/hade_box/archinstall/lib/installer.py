import glob
import os
import platform
import re
import shlex
import shutil
import subprocess
import textwrap
import time
from collections.abc import Callable
from pathlib import Path
from subprocess import CalledProcessError
from types import TracebackType
from typing import Any

from archinstall.lib.disk.device_handler import device_handler
from archinstall.lib.disk.utils import get_lsblk_by_mountpoint, get_lsblk_info
from archinstall.lib.models.device import (
	DiskEncryption,
	DiskLayoutConfiguration,
	EncryptionType,
	FilesystemType,
	PartitionModification,
	SectorSize,
	Size,
	SnapshotType,
	SubvolumeModification,
	Unit,
)
from archinstall.lib.models.packages import Repository
from archinstall.lib.packages import installed_package
from archinstall.tui.curses_menu import Tui

from .args import arch_config_handler
from .exceptions import DiskError, HardwareIncompatibilityError, RequirementError, ServiceException, SysCallError
from .general import SysCommand, run
from .hardware import GfxDriver, SysInfo
from .locale.utils import verify_keyboard_layout, verify_x11_keyboard_layout
from .models.bootloader import Bootloader, GrubConfiguration
from .models.locale import LocaleConfiguration
from .models.mirrors import MirrorConfiguration
from .models.network import Nic
from .models.users import User
from .output import debug, error, info, log, logger, warn
from .pacman import Pacman
from .pacman.config import PacmanConfig
from .storage import storage

# Any package that the Installer() is responsible for (optional and the default ones)
__packages__ = ['base', 'base-devel', 'linux-firmware', 'linux', 'linux-lts', 'linux-zen', 'linux-hardened']

# Additional packages that are installed if the user is running the Live ISO with accessibility tools enabled
__accessibility_packages__ = ['brltty', 'espeakup', 'alsa-utils']

class Installer:
	def __init__(
		self,
		target: Path,
		disk_config: DiskLayoutConfiguration,
		base_packages: list[str] = [],
		kernels: list[str] | None = None,
	):
		"""
		`Installer()` is the wrapper for most basic installation steps.
		It also wraps :py:func:`~archinstall.Installer.pacstrap` among other things.
		"""

		self._base_packages = base_packages or __packages__[:3]
		self.kernels = kernels or ['linux']
		self._disk_config = disk_config

		self._disk_encryption = disk_config.disk_encryption or DiskEncryption(EncryptionType.NoEncryption)
		self.target: Path = target

		self.init_time = time.strftime('%Y-%m-%d_%H-%M-%S')
		self.milliseconds = int(str(time.time()).split('.')[1])
		self._helper_flags: dict[str, str | bool | None] = {
			'base': False,
			'bootloader': None,
		}

		# Store graphics driver configuration for kernel parameter detection
		self._gfx_driver: GfxDriver | None = None

		for kernel in self.kernels:
			self._base_packages.append(kernel)

		# If using accessibility tools in the live environment, append those to the packages list
		if accessibility_tools_in_use():
			self._base_packages.extend(__accessibility_packages__)

		self.post_base_install: list[Callable] = []  # type: ignore[type-arg]

		storage['installation_session'] = self

		self._modules: list[str] = []
		self._binaries: list[str] = []
		self._files: list[str] = []

		# systemd, sd-vconsole and sd-encrypt will be replaced by udev, keymap and encrypt
		# if HSM is not used to encrypt the root volume. Check mkinitcpio() function for that override.
		self._hooks: list[str] = [
			'base',
			'systemd',
			'autodetect',
			'microcode',
			'modconf',
			'kms',
			'keyboard',
			'sd-vconsole',
			'block',
			'filesystems',
			'fsck',
		]
		self._kernel_params: list[str] = []
		self._fstab_entries: list[str] = []

		self._zram_enabled = False
		self._disable_fstrim = False

		self.pacman = Pacman(self.target, arch_config_handler.args.silent)

	def __enter__(self) -> 'Installer':
		return self

	def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> bool | None:
		if exc_type is not None:
			error(str(exc_value))

			# We avoid printing /mnt/<log path> because that might confuse people if they note it down
			# and then reboot, and a identical log file will be found in the ISO medium anyway.
			Tui.print(str('[!] A log file has been created here: {}').format(logger.path))

			# Return None to propagate the exception
			return None

		self.sync()

		if not (missing_steps := self.post_install_check()):
			msg = f'Installation completed without any errors.\nLog files temporarily available at {logger.directory}.\nYou may reboot when ready.\n'
			log(msg, fg='green')
			return True
		else:
			warn('Some required steps were not successfully installed/configured before leaving the installer:')

			for step in missing_steps:
				warn(f' - {step}')

			warn(f'Detailed error logs can be found at: {logger.directory}')

			return False

	def sync(self) -> None:
		info('Syncing the system...')
		SysCommand('sync')

	def remove_mod(self, mod: str) -> None:
		if mod in self._modules:
			self._modules.remove(mod)

	def append_mod(self, mod: str) -> None:
		if mod not in self._modules:
			self._modules.append(mod)

	def _verify_service_stop(self) -> None:
		"""
		Certain services might be running that affects the system during installation.
		One such service is "reflector.service" which updates /etc/pacman.d/mirrorlist
		We need to wait for it before we continue since we opted in to use a custom mirror/region.
		"""
		if not arch_config_handler.args.skip_ntp:
			info('Waiting for time sync (timedatectl show) to complete.')
			started_wait = time.time()
			notified = False
			while True:
				if not notified and time.time() - started_wait > 5:
					notified = True
					warn('Time synchronization not completing, while you wait - check the docs for workarounds: https://archinstall.readthedocs.io/')
				time_val = SysCommand('timedatectl show --property=NTPSynchronized --value').decode()
				if time_val and time_val.strip() == 'yes':
					break
				time.sleep(1)
		else:
			info('Skipping waiting for automatic time sync (this can cause issues if time is out of sync during installation)')

		# Skip reflector wait if mirrors were already configured in TUI
		# (pacman -Sy was already run in install script before TUI launch)
		if arch_config_handler.config.mirror_config:
			info('Mirrors already configured, skipping reflector wait.')
		else:
			info('Waiting for automatic mirror selection (reflector) to complete.')
			while self._service_state('reflector') not in ('dead', 'failed', 'exited'):
				time.sleep(1)
		# info('Waiting for pacman-init.service to complete.')
		# while self._service_state('pacman-init') not in ('dead', 'failed', 'exited'):
		# 	time.sleep(1)

		if not arch_config_handler.args.skip_wkd:
			# Check if keyring is already initialized
			keyring_dir = Path('/etc/pacman.d/gnupg')
			keyring_initialized = keyring_dir.exists() and any(keyring_dir.iterdir())

			if keyring_initialized:
				info('Keyring already initialized, skipping WKD sync')
			else:
				info('Waiting for Arch Linux keyring sync (archlinux-keyring-wkd-sync) to complete.')
				# Wait for the timer to kick in (10 second timeout)
				timer_waited = 0
				while self._service_started('archlinux-keyring-wkd-sync.timer') is None:
					if timer_waited >= 10:
						warn('Keyring timer did not start after 10s, skipping')
						break
					time.sleep(1)
					timer_waited += 1
				else:
					# Wait for the service to complete (30 second timeout)
					if self._wait_for_service('archlinux-keyring-wkd-sync.service', timeout=30):
						info('Keyring sync completed.')
					else:
						warn('Keyring sync timed out after 30s, continuing with existing keyring')

	def _verify_boot_part(self) -> None:
		"""
		Check that mounted /boot device has at minimum size for installation
		The reason this check is here is to catch pre-mounted device configuration and potentially
		configured one that has not gone through any previous checks (e.g. --silence mode)

		NOTE: this function should be run AFTER running the mount_ordered_layout function
		"""
		boot_mount = self.target / 'boot'
		lsblk_info = get_lsblk_by_mountpoint(boot_mount)

		if len(lsblk_info) > 0:
			if lsblk_info[0].size < Size(200, Unit.MiB, SectorSize.default()):
				raise DiskError(
					f'The boot partition mounted at {boot_mount} is not large enough to install a boot loader. '
					f'Please resize it to at least 200MiB and re-run the installation.',
				)

	def sanity_check(self) -> None:
		# self._verify_boot_part()
		self._verify_service_stop()

	def set_graphics_driver(self, gfx_driver: GfxDriver) -> None:
		"""
		Set the graphics driver for hardware-specific kernel parameters.
		This should be called when installing the graphics driver. Pre-cached
		"""
		self._gfx_driver = gfx_driver
		debug(f'Graphics driver set to {gfx_driver.value} for kernel parameter configuration')

	def mount_ordered_layout(self) -> None:
		debug('Mounting ordered layout')

		# mount all regular partitions
		self._mount_partition_layout()

	def _mount_partition_layout(self) -> None:
		debug('Mounting partition layout')

		# do not mount any PVs part
		pvs = []

		sorted_device_mods = self._disk_config.device_modifications.copy()

		# move the device with the root partition to the beginning of the list
		for mod in self._disk_config.device_modifications:
			if any(partition.is_root() for partition in mod.partitions):
				sorted_device_mods.remove(mod)
				sorted_device_mods.insert(0, mod)
				break

		for mod in sorted_device_mods:
			not_pv_part_mods = [p for p in mod.partitions if p not in pvs]

			# partitions have to mounted in the right order on btrfs the mountpoint will
			# be empty as the actual subvolumes are getting mounted instead so we'll use
			# '/' just for sorting
			sorted_part_mods = sorted(not_pv_part_mods, key=lambda x: x.mountpoint or Path('/'))

			for part_mod in sorted_part_mods:
				self._mount_partition(part_mod)

	def _mount_partition(self, part_mod: PartitionModification) -> None:
		if not part_mod.dev_path:
			return

		# it would be none if it's btrfs as the subvolumes will have the mountpoints defined
		if part_mod.mountpoint:
			target = self.target / part_mod.relative_mountpoint
			device_handler.mount(part_mod.dev_path, target, options=part_mod.mount_options)
		elif part_mod.fs_type == FilesystemType.Btrfs:
			self._mount_btrfs_subvol(
				part_mod.dev_path,
				part_mod.btrfs_subvols,
				part_mod.mount_options,
			)
		elif part_mod.is_swap():
			device_handler.swapon(part_mod.dev_path)

	def _mount_btrfs_subvol(
		self,
		dev_path: Path,
		subvolumes: list[SubvolumeModification],
		mount_options: list[str] = [],
	) -> None:
		for subvol in sorted(subvolumes, key=lambda x: x.relative_mountpoint):
			mountpoint = self.target / subvol.relative_mountpoint
			options = mount_options + [f'subvol={subvol.name}']
			device_handler.mount(dev_path, mountpoint, options=options)

	def add_swapfile(self, size: str = '4G', enable_resume: bool = True, file: str = '/swapfile') -> None:
		if file[:1] != '/':
			file = f'/{file}'
		if len(file.strip()) <= 0 or file == '/':
			raise ValueError(f'The filename for the swap file has to be a valid path, not: {self.target}{file}')

		SysCommand(f'dd if=/dev/zero of={self.target}{file} bs={size} count=1')
		SysCommand(f'chmod 0600 {self.target}{file}')
		SysCommand(f'mkswap {self.target}{file}')

		self._fstab_entries.append(f'{file} none swap defaults 0 0')

		if enable_resume:
			resume_uuid = SysCommand(f'findmnt -no UUID -T {self.target}{file}').decode()
			resume_offset = (
				SysCommand(
					f'filefrag -v {self.target}{file}',
				)
				.decode()
				.split('0:', 1)[1]
				.split(':', 1)[1]
				.split('..', 1)[0]
				.strip()
			)

			self._hooks.append('resume')
			self._kernel_params.append(f'resume=UUID={resume_uuid}')
			self._kernel_params.append(f'resume_offset={resume_offset}')

	def post_install_check(self, *args: str, **kwargs: str) -> list[str]:
		return [step for step, flag in self._helper_flags.items() if flag is False]

	def set_mirrors(
		self,
		mirror_config: MirrorConfiguration,
		on_target: bool = False,
	) -> None:
		"""
		Set the mirror configuration for the installation.

		:param mirror_config: The mirror configuration to use.
		:type mirror_config: MirrorConfiguration

		:on_target: Whether to set the mirrors on the target system or the live system.
		:param on_target: bool
		"""
		debug('Setting mirrors on ' + ('target' if on_target else 'live system'))

		root = self.target if on_target else Path('/')
		mirrorlist_config = root / 'etc/pacman.d/mirrorlist'
		pacman_config = root / 'etc/pacman.conf'

		repositories_config = mirror_config.repositories_config()
		if repositories_config:
			debug(f'Pacman config: {repositories_config}')

			with open(pacman_config, 'a') as fp:
				fp.write(repositories_config)

		regions_config = mirror_config.regions_config(speed_sort=True)
		if regions_config:
			debug(f'Mirrorlist:\n{regions_config}')
			mirrorlist_config.write_text(regions_config)

		custom_servers = mirror_config.custom_servers_config()
		if custom_servers:
			debug(f'Custom servers:\n{custom_servers}')

			content = mirrorlist_config.read_text()
			mirrorlist_config.write_text(f'{custom_servers}\n\n{content}')

	def genfstab(self, flags: str = '-pU') -> None:
		fstab_path = self.target / 'etc' / 'fstab'
		info(f'Updating {fstab_path}')

		try:
			# Use -f flag to restrict output to mountpoints under target, preventing host system mounts
			gen_fstab = SysCommand(f'genfstab {flags} -f {self.target} {self.target}').output()
		except SysCallError as err:
			raise RequirementError(f'Could not generate fstab, strapping in packages most likely failed (disk out of space?)\n Error: {err}')

		with open(fstab_path, 'ab') as fp:
			fp.write(gen_fstab)

		if not fstab_path.is_file():
			raise RequirementError('Could not create fstab file')

		with open(fstab_path, 'a') as fp:
			for entry in self._fstab_entries:
				fp.write(f'{entry}\n')

	def apply_removable_media_optimizations(self) -> None:
		"""
		Apply optimizations for removable media.
		Based on: https://wiki.archlinux.org/title/Install_Arch_Linux_on_a_removable_medium

		Optimizations include:
		1. mkinitcpio hooks reordering for hardware portability
		2. Systemd journal to RAM (volatile storage)
		3. BFQ I/O scheduler for better USB/SSD performance
		"""
		info('[PAN_DORA] Applying removable media optimizations...')

		# 1. Configure mkinitcpio for portable boot
		info('[PAN_DORA] Configuring mkinitcpio for portable boot...')
		mkinitcpio_conf = self.target / 'etc/mkinitcpio.conf'
		if mkinitcpio_conf.exists():
			config = mkinitcpio_conf.read_text()
			# Move block and keyboard hooks BEFORE autodetect for hardware portability
			config = re.sub(
				r'^HOOKS=.*$',
				'HOOKS=(base udev block keyboard autodetect microcode modconf kms keymap consolefont filesystems fsck)',
				config,
				flags=re.MULTILINE
			)
			mkinitcpio_conf.write_text(config)

			# Regenerate initramfs
			try:
				SysCommand(f'arch-chroot {self.target} mkinitcpio -P')
				info('[PAN_DORA] ✓ mkinitcpio configured for portable boot')
			except SysCallError as err:
				warn(f'[PAN_DORA] Failed to regenerate initramfs: {err}')
		else:
			warn('[PAN_DORA] ✗ /etc/mkinitcpio.conf not found')

		# 2. Configure systemd journal to RAM (reduce writes)
		info('[PAN_DORA] Configuring systemd journal for volatile storage...')
		journald_dir = self.target / 'etc/systemd/journald.conf.d'
		journald_dir.mkdir(parents=True, exist_ok=True)

		journald_conf = journald_dir / 'usbstick.conf'
		journald_conf.write_text('[Journal]\nStorage=volatile\nRuntimeMaxUse=30M\n')
		info('[PAN_DORA] ✓ Journal configured for RAM storage (volatile)')

		# 3. Set BFQ scheduler for better USB performance
		info('[PAN_DORA] Configuring BFQ I/O scheduler...')
		udev_rules_dir = self.target / 'etc/udev/rules.d'
		udev_rules_dir.mkdir(parents=True, exist_ok=True)

		udev_rule = udev_rules_dir / '60-ioschedulers.rules'
		udev_rule.write_text(
			'# Set BFQ scheduler for better performance on removable media\n'
			'ACTION=="add|change", KERNEL=="sd[a-z]|mmcblk[0-9]*", '
			'ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="bfq"\n'
		)
		info('[PAN_DORA] ✓ BFQ scheduler configured for SSDs/USB')

		info('[PAN_DORA] Removable media optimizations complete!')

	def set_hostname(self, hostname: str) -> None:
		(self.target / 'etc/hostname').write_text(hostname + '\n')

	def set_locale(self, locale_config: LocaleConfiguration) -> bool:
		modifier = ''
		lang = locale_config.sys_lang
		encoding = locale_config.sys_enc

		# This is a temporary patch to fix #1200
		if '.' in locale_config.sys_lang:
			lang, potential_encoding = locale_config.sys_lang.split('.', 1)

			# Override encoding if encoding is set to the default parameter
			# and the "found" encoding differs.
			if locale_config.sys_enc == 'UTF-8' and locale_config.sys_enc != potential_encoding:
				encoding = potential_encoding

		# Make sure we extract the modifier, that way we can put it in if needed.
		if '@' in locale_config.sys_lang:
			lang, modifier = locale_config.sys_lang.split('@', 1)
			modifier = f'@{modifier}'
		# - End patch

		locale_gen = self.target / 'etc/locale.gen'
		locale_gen_lines = locale_gen.read_text().splitlines(True)

		# A locale entry in /etc/locale.gen may or may not contain the encoding
		# in the first column of the entry; check for both cases.
		entry_re = re.compile(rf'#{lang}(\.{encoding})?{modifier} {encoding}')

		lang_value = None
		for index, line in enumerate(locale_gen_lines):
			if entry_re.match(line):
				uncommented_line = line.removeprefix('#')
				locale_gen_lines[index] = uncommented_line
				locale_gen.write_text(''.join(locale_gen_lines))
				lang_value = uncommented_line.split()[0]
				break

		if lang_value is None:
			error(f"Invalid locale: language '{locale_config.sys_lang}', encoding '{locale_config.sys_enc}'")
			return False

		try:
			SysCommand(f'arch-chroot {self.target} locale-gen')
		except SysCallError as e:
			error(f'Failed to run locale-gen on target: {e}')
			return False

		(self.target / 'etc/locale.conf').write_text(f'LANG={lang_value}\n')
		return True

	def set_timezone(self, zone: str) -> bool:
		if not zone:
			return True
		if not len(zone):
			return True  # Redundant

		if (Path('/usr') / 'share' / 'zoneinfo' / zone).exists():
			(Path(self.target) / 'etc' / 'localtime').unlink(missing_ok=True)
			SysCommand(f'arch-chroot {self.target} ln -s /usr/share/zoneinfo/{zone} /etc/localtime')
			return True

		else:
			warn(f'Time zone {zone} does not exist, continuing with system default')

		return False

	def activate_time_synchronization(self) -> None:
		info('Activating systemd-timesyncd for time synchronization using Arch Linux and ntp.org NTP servers')
		self.enable_service('systemd-timesyncd')

	def enable_espeakup(self) -> None:
		info('Enabling espeakup.service for speech synthesis (accessibility)')
		self.enable_service('espeakup')

	def enable_periodic_trim(self) -> None:
		info('Enabling periodic TRIM')
		# fstrim is owned by util-linux, a dependency of both base and systemd.
		self.enable_service('fstrim.timer')

	def enable_service(self, services: str | list[str]) -> None:
		if isinstance(services, str):
			services = [services]

		for service in services:
			info(f'Enabling service {service}')

			try:
				SysCommand(f'systemctl --root={self.target} enable {service}')
			except SysCallError as err:
				raise ServiceException(f'Unable to start service {service}: {err}')

	def run_command(self, cmd: str, *args: str, **kwargs: str) -> SysCommand:
		return SysCommand(f'arch-chroot {self.target} {cmd}')

	def arch_chroot(self, cmd: str, run_as: str | None = None) -> SysCommand:
		if run_as:
			cmd = f'su - {run_as} -c {shlex.quote(cmd)}'

		return self.run_command(cmd)

	def drop_to_shell(self) -> None:
		subprocess.check_call(f'arch-chroot {self.target}', shell=True)

	def configure_nic(self, nic: Nic) -> None:
		conf = nic.as_systemd_config()

		with open(f'{self.target}/etc/systemd/network/10-{nic.iface}.network', 'a') as netconf:
			netconf.write(str(conf))

	def mkinitcpio(self, flags: list[str]) -> bool:

		with open(f'{self.target}/etc/mkinitcpio.conf', 'r+') as mkinit:
			content = mkinit.read()
			content = re.sub('\nMODULES=(.*)', f'\nMODULES=({" ".join(self._modules)})', content)
			content = re.sub('\nBINARIES=(.*)', f'\nBINARIES=({" ".join(self._binaries)})', content)
			content = re.sub('\nFILES=(.*)', f'\nFILES=({" ".join(self._files)})', content)

			# Since no encryption is supported, use traditional hooks
			# * systemd -> udev
			# * sd-vconsole -> keymap
			self._hooks = [hook.replace('systemd', 'udev').replace('sd-vconsole', 'keymap consolefont') for hook in self._hooks]

			content = re.sub('\nHOOKS=(.*)', f'\nHOOKS=({" ".join(self._hooks)})', content)
			mkinit.seek(0)
			mkinit.write(content)

		try:
			info('Running mkinitcpio quietly...')
			SysCommand(f'arch-chroot {self.target} mkinitcpio {" ".join(flags)}')
			info('mkinitcpio completed successfully')
			return True
		except SysCallError as e:
			if e.worker_log:
				log(e.worker_log.decode())
			return False

	def _get_microcode(self) -> Path | None:
		if not SysInfo.is_vm():
			if vendor := SysInfo.cpu_vendor():
				return vendor.get_ucode()
		return None

	def _prepare_fs_type(
		self,
		fs_type: FilesystemType,
		mountpoint: Path | None,
	) -> None:
		if (pkg := fs_type.installation_pkg) is not None:
			self._base_packages.append(pkg)
		if (module := fs_type.installation_module) is not None:
			self._modules.append(module)
		if (binary := fs_type.installation_binary) is not None:
			self._binaries.append(binary)

		# https://github.com/archlinux/archinstall/issues/1837
		if fs_type.fs_type_mount == 'btrfs':
			self._disable_fstrim = True

		# There is not yet an fsck tool for NTFS. If it's being used for the root filesystem, the hook should be removed.
		if fs_type.fs_type_mount == 'ntfs3' and mountpoint == self.target:
			if 'fsck' in self._hooks:
				self._hooks.remove('fsck')

	def minimal_installation(
		self,
		optional_repositories: list[Repository] = [],
		mkinitcpio: bool = True,
		hostname: str | None = None,
		locale_config: LocaleConfiguration | None = LocaleConfiguration.default(),
	) -> None:
		for mod in self._disk_config.device_modifications:
			for part in mod.partitions:
				if part.fs_type is None:
					continue

				self._prepare_fs_type(part.fs_type, part.mountpoint)

		if ucode := self._get_microcode():
			(self.target / 'boot' / ucode).unlink(missing_ok=True)
			self._base_packages.append(ucode.stem)
		else:
			debug('Archinstall will not install any ucode.')

		debug(f'Optional repositories: {optional_repositories}')

		# This action takes place on the host system as pacstrap copies over package repository lists.
		pacman_conf = PacmanConfig(self.target)
		pacman_conf.enable(optional_repositories)
		pacman_conf.apply()

		self.pacman.strap(self._base_packages)
		self._helper_flags['base-strapped'] = True

		pacman_conf.persist()

		# Periodic TRIM may improve the performance and longevity of SSDs whilst
		# having no adverse effect on other devices. Most distributions enable
		# periodic TRIM by default.
		#
		# https://github.com/archlinux/archinstall/issues/880
		# https://github.com/archlinux/archinstall/issues/1837
		# https://github.com/archlinux/archinstall/issues/1841
		if not self._disable_fstrim:
			self.enable_periodic_trim()

		# TODO: Support locale and timezone
		# os.remove(f'{self.target}/etc/localtime')
		# sys_command(f'arch-chroot {self.target} ln -s /usr/share/zoneinfo/{localtime} /etc/localtime')
		# sys_command('arch-chroot /mnt hwclock --hctosys --localtime')
		if hostname:
			self.set_hostname(hostname)

		if locale_config:
			self.set_locale(locale_config)
			self.set_keyboard_language(locale_config.kb_layout)

		# TODO: Use python functions for this
		SysCommand(f'arch-chroot {self.target} chmod 700 /root')

		if mkinitcpio and not self.mkinitcpio(['-P']):
			error('Error generating initramfs (continuing anyway)')

		self._helper_flags['base'] = True

		# Run registered post-install hooks
		for function in self.post_base_install:
			info(f'Running post-installation hook: {function}')
			function(self)

	def setup_btrfs_snapshot(
		self,
		snapshot_type: SnapshotType,
		bootloader: Bootloader | None = None,
	) -> None:
		if snapshot_type == SnapshotType.Snapper:
			debug('Setting up Btrfs snapper')
			self.pacman.strap('snapper')

			snapper: dict[str, str] = {
				'root': '/',
				'home': '/home',
			}

			for config_name, mountpoint in snapper.items():
				command = [
					'arch-chroot',
					str(self.target),
					'snapper',
					'--no-dbus',
					'-c',
					config_name,
					'create-config',
					mountpoint,
				]

				try:
					SysCommand(command, peek_output=True)
				except SysCallError as err:
					raise DiskError(f'Could not setup Btrfs snapper: {err}')

			self.enable_service('snapper-timeline.timer')
			self.enable_service('snapper-cleanup.timer')

			if bootloader and bootloader == Bootloader.Grub:
				self.pacman.strap('grub-btrfs')
				self.pacman.strap('inotify-tools')
				self._configure_grub_btrfsd_snapper()
				self.enable_service('grub-btrfsd.service')

		elif snapshot_type == SnapshotType.Timeshift:
			debug('Setting up Btrfs timeshift')

			self.pacman.strap('cronie')
			self.pacman.strap('timeshift')

			self.enable_service('cronie.service')

			if bootloader and bootloader == Bootloader.Grub:
				self.pacman.strap('grub-btrfs')
				self.pacman.strap('inotify-tools')
				self._configure_grub_btrfsd()
				self.enable_service('grub-btrfsd.service')

	def setup_swap(self, kind: str = 'zram', size: str = '4G') -> None:
		# Normalize the kind value
		if not isinstance(kind, str):
			kind = str(kind)
		kind = kind.lower().strip()

		# Default to zram for empty string or unrecognized values
		if kind == 'zram' or kind == '' or kind not in ['swapfile', 'partition', 'none']:
			if kind not in ['zram', '']:
				info('Unrecognized swap type, defaulting to zram')
			info('Setting up swap on zram')
			self.pacman.strap('zram-generator')

			# We could use the default example below, but maybe not the best idea: https://github.com/archlinux/archinstall/pull/678#issuecomment-962124813
			# zram_example_location = '/usr/share/doc/zram-generator/zram-generator.conf.example'
			# shutil.copy2(f"{self.target}{zram_example_location}", f"{self.target}/usr/lib/systemd/zram-generator.conf")
			# Parse size to MB for zram-size (e.g., "4G" -> 4096)
			size_mb = 4096  # default
			try:
				import re
				match = re.match(r'(\d+)([KMGT]?)', size.upper())
				if match:
					value, unit = match.groups()
					value = int(value)
					# Convert to MB
					if unit == 'G':
						size_mb = value * 1024
					elif unit == 'M':
						size_mb = value
					elif unit == 'K':
						size_mb = max(1, value // 1024)
					elif unit == 'T':
						size_mb = value * 1024 * 1024
			except Exception:
				pass

			with open(f'{self.target}/etc/systemd/zram-generator.conf', 'w') as zram_conf:
				zram_conf.write('[zram0]\n')
				zram_conf.write(f'zram-size = {size_mb}\n')

			self.enable_service('systemd-zram-setup@zram0.service')
			self._zram_enabled = True

		elif kind == 'swapfile':
			info(f'Setting up swapfile ({size})')
			swapfile_path = f'{self.target}/swapfile'

			# Create swapfile with specified size
			self.arch_chroot(f'fallocate -l {size} /swapfile')
			self.arch_chroot('chmod 600 /swapfile')
			self.arch_chroot('mkswap /swapfile')

			# Add swapfile to fstab
			self._fstab_entries.append('/swapfile none swap defaults 0 0')

		elif kind == 'partition':
			info('Configuring swap partitions for fstab')
			# Swap partitions are already activated during partition mounting
			# but they need to be added to fstab for automatic mounting on boot
			swap_partitions = []
			for layout in self._disk_config.device_modifications:
				for part_mod in layout.partitions:
					if part_mod.is_swap():
						swap_partitions.append(part_mod)

			if swap_partitions:
				info(f'Adding {len(swap_partitions)} swap partition(s) to fstab')
				for swap_part in swap_partitions:
					# Add swap partition to fstab for permanent mounting
					self._fstab_entries.append(f'{swap_part.dev_path} none swap defaults 0 0')
					info(f'Added swap partition {swap_part.dev_path} to fstab')
			else:
				warn('No swap partitions found in disk configuration.')
				info('Make sure to create a swap partition in the disk layout, or use "zram" or "swapfile" options instead.')

		elif kind == 'none':
			info('No swap configured')
			# Explicitly disable any swap setup
			pass

	def _get_efi_partition(self) -> PartitionModification | None:
		for layout in self._disk_config.device_modifications:
			if partition := layout.get_efi_partition():
				return partition
		return None

	def _get_boot_partition(self) -> PartitionModification | None:
		for layout in self._disk_config.device_modifications:
			if boot := layout.get_boot_partition():
				return boot
		return None

	def _get_root(self) -> PartitionModification | None:
		for mod in self._disk_config.device_modifications:
			if root := mod.get_root_partition():
				return root
		return None

	def _configure_grub_btrfsd(self) -> None:
		# See https://github.com/Antynea/grub-btrfs?tab=readme-ov-file#-using-timeshift-with-systemd
		debug('Configuring grub-btrfsd service')

		# https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#id-1.14.3
		systemd_dir = self.target / 'etc/systemd/system/grub-btrfsd.service.d'
		systemd_dir.mkdir(parents=True, exist_ok=True)

		override_conf = systemd_dir / 'override.conf'

		config_content = textwrap.dedent(
			"""
			[Service]
			ExecStart=
			ExecStart=/usr/bin/grub-btrfsd --syslog --timeshift-auto
			"""
		)

		override_conf.write_text(config_content)
		override_conf.chmod(0o644)

	def _configure_grub_btrfsd_snapper(self) -> None:
		debug('Configuring grub-btrfsd service for snapper')

		# https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#id-1.14.3
		systemd_dir = self.target / 'etc/systemd/system/grub-btrfsd.service.d'
		systemd_dir.mkdir(parents=True, exist_ok=True)

		override_conf = systemd_dir / 'override.conf'

		config_content = textwrap.dedent(
			"""
			[Service]
			ExecStart=
			ExecStart=/usr/bin/grub-btrfsd --syslog /.snapshots
			"""
		)

		override_conf.write_text(config_content)
		override_conf.chmod(0o644)

	def _get_kernel_params_partition(
		self,
		root_partition: PartitionModification,
		id_root: bool = True,
		partuuid: bool = True,
	) -> list[str]:
		kernel_parameters = []

		if id_root:
			if partuuid:
				debug(f'Identifying root partition by PARTUUID: {root_partition.partuuid}')
				kernel_parameters.append(f'root=PARTUUID={root_partition.partuuid}')
			else:
				debug(f'Identifying root partition by UUID: {root_partition.uuid}')
				kernel_parameters.append(f'root=UUID={root_partition.uuid}')

		return kernel_parameters

	def _get_kernel_params(
		self,
		root: PartitionModification,
		id_root: bool = True,
		partuuid: bool = True,
	) -> list[str]:
		kernel_parameters = []

		if isinstance(root, PartitionModification):
			kernel_parameters = self._get_kernel_params_partition(root, id_root, partuuid)

		# Zswap should be disabled when using zram.
		# https://github.com/archlinux/archinstall/issues/881
		if self._zram_enabled:
			kernel_parameters.append('zswap.enabled=0')

		if id_root:
			for sub_vol in root.btrfs_subvols:
				if sub_vol.is_root():
					kernel_parameters.append(f'rootflags=subvol={sub_vol.name}')
					break

			kernel_parameters.append('rw')

		kernel_parameters.append(f'rootfstype={root.safe_fs_type.fs_type_mount}')
		kernel_parameters.extend(self._kernel_params)

		debug(f'kernel parameters: {" ".join(kernel_parameters)}')

		return kernel_parameters

	def _create_bls_entries(
		self,
		boot_partition: PartitionModification,
		root: PartitionModification,
		entry_name: str,
	) -> None:
		# Loader entries are stored in $BOOT/loader:
		# https://uapi-group.org/specifications/specs/boot_loader_specification/#mount-points
		entries_dir = self.target / boot_partition.relative_mountpoint / 'loader/entries'
		# Ensure that the $BOOT/loader/entries/ directory exists before trying to create files in it
		entries_dir.mkdir(parents=True, exist_ok=True)

		entry_template = textwrap.dedent(
			f"""\
			# Created by: archinstall
			# Created on: {self.init_time}
			title   Arch Linux ({{kernel}}{{variant}})
			linux   /vmlinuz-{{kernel}}
			initrd  /initramfs-{{kernel}}{{variant}}.img
			options {' '.join(self._get_kernel_params(root))}
			""",
		)

		for kernel in self.kernels:
			for variant in ('', '-fallback'):
				# Setup the loader entry
				name = entry_name.format(kernel=kernel, variant=variant)
				entry_conf = entries_dir / name
				entry_conf.write_text(entry_template.format(kernel=kernel, variant=variant))

	#def _configure_hw_environment(self) -> None:
		#"""Configure /etc/environment with hardware-specific variables."""
		#if not self._gfx_driver:
			#return

		#env_vars = {}

		### CHANGE ME NVIDIA-specific environment variables
		### https://wiki.archlinux.org/title/NVIDIA
		#if self._gfx_driver.is_nvidia():
			#debug(f'Adding NVIDIA environment variables for {self._gfx_driver.value}')

			#if self._gfx_driver == GfxDriver.NvidiaProprietary:
				# Essential for NVIDIA + Wayland
				#env_vars['GBM_BACKEND'] = 'nvidia-drm'
				#env_vars['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
				# Hardware video decoding
				#env_vars['LIBVA_DRIVER_NAME'] = 'nvidia'
				#info('Added proprietary NVIDIA environment variables for Wayland support')

			#elif self._gfx_driver == GfxDriver.IntelNvidiaHybrid:
				# For hybrid setups - PRIME offloading
				#env_vars['__NV_PRIME_RENDER_OFFLOAD'] = '1'
				#env_vars['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
				#info('Added hybrid Intel/NVIDIA environment variables for PRIME offloading')

			#elif self._gfx_driver == GfxDriver.NvidiaOpenKernel:
				# Open kernel module with Wayland support
				#env_vars['GBM_BACKEND'] = 'nvidia-drm'
				#env_vars['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
				#debug('Added open kernel NVIDIA environment variables')

			# Troubleshooting LIBGL_ALWAYS_SOFTWARE=true which can make old card work on newer drivers. 
			# This can also be useful for a VM if not doing GPU passthrough
			# Intel/AMD Usually require little to no configuration or just for debug<3

			### INTEL https://wiki.archlinux.org/title/Intel_graphics
			# ANV_DEBUG=video_decode,video_encode
			### AMD https://wiki.archlinux.org/title/AMDGPU
			# RADV_PERFTEST=rt - Enable hardware raytracing (RDNA2+)
   			# RADV_PERFTEST=video_decode,video_encode - Force video accel on older GPUs
  			# RADV_PERFTEST=emulate_rt - Emulate raytracing for GFX8-10

		# Write environment variables to /etc/environment
		#if env_vars:
			#self._write_environment_file(env_vars)

	#def _write_environment_file(self, env_vars: dict[str, str]) -> None:
		#"""Write environment variables to /etc/environment."""
		#env_file = self.target / 'etc/environment'

		# Ensure /etc directory exists
		#env_file.parent.mkdir(parents=True, exist_ok=True)

		# Read existing content if file exists
		#existing_content = ''
		#if env_file.exists():
			#existing_content = env_file.read_text()

		# Prepare new content
		#new_lines = [
			#'# Hade_box - ENVIRONMENT MANAGER AUTO-GENERATED',
			#'# Hardware-specific environment variables',
			#'# Generated by archinstall for graphics optimization'
		#]

		#for key, value in env_vars.items():
			# Check if the key already exists in the file
			#if f'{key}=' not in existing_content:
				#new_lines.append(f'{key}={value}')

		# Only append if we have new variables to add
		#if len(new_lines) > 3:  # More than just the comments
			# Append to file
			#with env_file.open('a') as f:
				#f.write('\n'.join(new_lines) + '\n')

			#info(f'Added {len(new_lines) - 3} environment variables to /etc/environment')
			#debug(f'Environment variables: {env_vars}')
		#else:
			#debug('All environment variables already exist in /etc/environment')

	def _add_grub_bootloader(
		self,
		boot_partition: PartitionModification,
		root: PartitionModification,
		efi_partition: PartitionModification | None,
		grub_config: GrubConfiguration | None = None,
	) -> None:
		debug('Installing grub bootloader')

		self.pacman.strap('grub')

		# Install os-prober if enabled
		if grub_config and grub_config.enable_os_prober:
			debug('Installing os-prober for multi-OS detection')
			self.pacman.strap('os-prober')

		grub_default = self.target / 'etc/default/grub'
		config = grub_default.read_text()

		kernel_parameters = ' '.join(self._get_kernel_params(root, False, False))

		config = re.sub(r'(GRUB_CMDLINE_LINUX=")("\n)', rf'\1{kernel_parameters}\2', config, count=1)
		# This line usually appends zswap.enabled=0 and rootfstype=
		# This affects both recovery options AND normal boot.

		# Debug graphics driver state before GRUB configuration
		#debug(f'GRUB configuration - Graphics driver state: {self._gfx_driver}')
		#if self._gfx_driver:
			#debug(f'Graphics driver: {self._gfx_driver.value}, is_nvidia: {self._gfx_driver.is_nvidia()}')

		#### CHANGE ME Add hardware-specific parameters to GRUB_CMDLINE_LINUX_DEFAULT
		#if self._gfx_driver and self._gfx_driver.is_nvidia():
			#debug('Adding NVIDIA parameters to GRUB_CMDLINE_LINUX_DEFAULT')

			# Build the hardware-specific parameters string
			#hw_params = []

			# These are now included iin nvidia-utils but could help compat by setting explicitly. 
			#if self._gfx_driver == GfxDriver.NvidiaProprietary:
				#hw_params.append('nvidia-drm.modeset=1')
				#hw_params.append('nvidia-drm.fbdev=1')
				#hw_params.append('nvidia.NVreg_PreserveVideoMemoryAllocations=1')
				# i915.modeset=1
				
			# Find and update GRUB_CMDLINE_LINUX_DEFAULT
			#if 'GRUB_CMDLINE_LINUX_DEFAULT=' in config:
				# Extract existing parameters and append new ones
				#def append_params(match):
					#existing_params = match.group(2).strip()
					#if existing_params:
						# Add space before new params if existing params don't end with space
						#separator = ' ' if not existing_params.endswith(' ') else ''
						#return f'{match.group(1)}{existing_params}{separator}{" ".join(hw_params)}{match.group(3)}'
					#else:
						# No existing params, just add new ones
						#return f'{match.group(1)}{" ".join(hw_params)}{match.group(3)}'
				
				#config = re.sub(
					#r'(GRUB_CMDLINE_LINUX_DEFAULT=")(.*?)(")',
					#append_params,
					#config,
					#count=1
				#)
				#info(f'Added NVIDIA parameters to GRUB_CMDLINE_LINUX_DEFAULT: {" ".join(hw_params)}')
			#else:
				# If GRUB_CMDLINE_LINUX_DEFAULT doesn't exist, create it
				#config += f'\n# Hardware-specific parameters\nGRUB_CMDLINE_LINUX_DEFAULT="{" ".join(hw_params)}"\n'

		# Apply GRUB configuration
		if grub_config:
			# Configure OS prober - uncomment line if enabled, leave default (commented) if disabled
			if grub_config.enable_os_prober:
				if 'GRUB_DISABLE_OS_PROBER=' in config:
					config = re.sub(
						r'#?\s*GRUB_DISABLE_OS_PROBER=.*',
						'\nGRUB_DISABLE_OS_PROBER=false',
						config
					)
				else:
					config += '\n# Enable detection of other operating systems\nGRUB_DISABLE_OS_PROBER=false\n'

			# Configure menu visibility
			timeout_style = grub_config.get_timeout_style()
			if 'GRUB_TIMEOUT_STYLE=' in config:
				config = re.sub(
					r'^(\s*#?\s*GRUB_TIMEOUT_STYLE=.*)$',
					f'GRUB_TIMEOUT_STYLE={timeout_style}',
					config,
					flags=re.MULTILINE
				)
			else:
				config += f'\n# Menu visibility\nGRUB_TIMEOUT_STYLE={timeout_style}\n'

			# Set timeout (only if different from default 5)
			if grub_config.timeout != 5:
				if 'GRUB_TIMEOUT=' in config:
					# Add newline before replacement to ensure proper line separation
					config = re.sub(
						r'#?\s*GRUB_TIMEOUT=.*',
						f'\nGRUB_TIMEOUT={grub_config.timeout}',
						config
					)
				else:
					config += f'\n# Boot timeout\nGRUB_TIMEOUT={grub_config.timeout}\n'

			# Configure remember last selection
			if grub_config.remember_last_selection:
				# Set GRUB_DEFAULT=saved
				if 'GRUB_DEFAULT=' in config:
					config = re.sub(
						r'#?\s*GRUB_DEFAULT=.*',
						'\nGRUB_DEFAULT=saved',
						config
					)
				else:
					config += '\n# Remember last\nGRUB_DEFAULT=saved\n'

				# Enable GRUB_SAVEDEFAULT
				if 'GRUB_SAVEDEFAULT=' in config:
					config = re.sub(
						r'#?\s*GRUB_SAVEDEFAULT=.*',
						'\nGRUB_SAVEDEFAULT=true',
						config
					)
				else:
					config += 'GRUB_SAVEDEFAULT=true\n'

			# Configure custom colors
			if grub_config.enable_custom_colors:
				# Enable and set color normal
				if 'GRUB_COLOR_NORMAL=' in config:
					config = re.sub(
						r'#?\s*GRUB_COLOR_NORMAL=.*',
						f'\nGRUB_COLOR_NORMAL="{grub_config.color_normal}"',
						config
					)
				else:
					config += f'\n# Custom colors\nGRUB_COLOR_NORMAL="{grub_config.color_normal}"\n'

				# Enable and set color highlight
				if 'GRUB_COLOR_HIGHLIGHT=' in config:
					config = re.sub(
						r'#?\s*GRUB_COLOR_HIGHLIGHT=.*',
						f'GRUB_COLOR_HIGHLIGHT="{grub_config.color_highlight}"',
						config
					)
				else:
					config += f'GRUB_COLOR_HIGHLIGHT="{grub_config.color_highlight}"\n'

			# Configure boot sound
			if grub_config.enable_boot_sound:
				# Enable boot sound with tune
				if 'GRUB_INIT_TUNE=' in config:
					config = re.sub(
						r'#?\s*GRUB_INIT_TUNE=.*',
						f'\nGRUB_INIT_TUNE="{grub_config.boot_sound_tune}"',
						config
					)
				else:
					config += f'\n# Boot sound\nGRUB_INIT_TUNE="{grub_config.boot_sound_tune}"\n'

		grub_default.write_text(config)

		info(f'GRUB boot partition: {boot_partition.dev_path}')

		boot_dir = Path('/boot')

		command = [
			'arch-chroot',
			str(self.target),
			'grub-install',
			#'--debug',
		]
		# This produces very very verbose info kinda pollutes log too
		if SysInfo.has_uefi():
			if not efi_partition:
				raise ValueError('Could not detect efi partition')

			info(f'GRUB EFI partition: {efi_partition.dev_path}')

			self.pacman.strap('efibootmgr')

			boot_dir_arg = []
			if boot_partition.mountpoint and boot_partition.mountpoint != boot_dir:
				boot_dir_arg.append(f'--boot-directory={boot_partition.mountpoint}')
				boot_dir = boot_partition.mountpoint

			add_options = [
				f'--target={platform.machine()}-efi',
				f'--efi-directory={efi_partition.mountpoint}',
				*boot_dir_arg,
				'--bootloader-id=GRUB',
				'--removable',
			]

			command.extend(add_options)

			try:
				SysCommand(command, peek_output=True)
			except SysCallError:
				try:
					SysCommand(command, peek_output=True)
				except SysCallError as err:
					raise DiskError(f'Could not install GRUB to {self.target}{efi_partition.mountpoint}: {err}')
		else:
			info(f'GRUB boot partition: {boot_partition.dev_path}')

			parent_dev_path = device_handler.get_parent_device_path(boot_partition.safe_dev_path)

			add_options = [
				'--target=i386-pc',
				'--recheck',
				str(parent_dev_path),
			]

			try:
				SysCommand(command + add_options, peek_output=True)
			except SysCallError as err:
				raise DiskError(f'Failed to install GRUB boot on {boot_partition.dev_path}: {err}')

		try:
			SysCommand(
				f'arch-chroot {self.target} grub-mkconfig -o {boot_dir}/grub/grub.cfg',
			)
		except SysCallError as err:
			raise DiskError(f'Could not configure GRUB: {err}')

		# Configure hardware-specific environment variables after GRUB configuration
		#self._configure_hw_environment()

		self._helper_flags['bootloader'] = 'grub'

	def add_bootloader(self, bootloader: Bootloader, grub_config: GrubConfiguration | None = None) -> None:
		"""
		Adds a bootloader to the installation instance.
		Only GRUB bootloader is supported.

		:param bootloader: Type of bootloader to be added
		:param grub_config: Optional GRUB configuration settings
		"""

		efi_partition = self._get_efi_partition()
		boot_partition = self._get_boot_partition()
		root = self._get_root()

		if boot_partition is None:
			raise ValueError(f'Could not detect boot at mountpoint {self.target}')

		if root is None:
			raise ValueError(f'Could not detect root at mountpoint {self.target}')

		info(f'Adding bootloader {bootloader.value} to {boot_partition.dev_path}')

		self._add_grub_bootloader(boot_partition, root, efi_partition, grub_config)

	def add_additional_packages(self, packages: str | list[str]) -> None:
		return self.pacman.strap(packages)

	def enable_sudo(self, user: User, group: bool = False) -> None:
		info(f'Enabling sudo permissions for {user.username}')

		sudoers_dir = self.target / 'etc/sudoers.d'

		# Creates directory if not exists
		if not sudoers_dir.exists():
			sudoers_dir.mkdir(parents=True)
			# Guarantees sudoer confs directory recommended perms
			sudoers_dir.chmod(0o440)
			# Appends a reference to the sudoers file, because if we are here sudoers.d did not exist yet
			with open(self.target / 'etc/sudoers', 'a') as sudoers:
				sudoers.write('@includedir /etc/sudoers.d\n')

		# We count how many files are there already so we know which number to prefix the file with
		num_of_rules_already = len(os.listdir(sudoers_dir))
		file_num_str = f'{num_of_rules_already:02d}'  # We want 00_user1, 01_user2, etc

		# Guarantees that username str does not contain invalid characters for a linux file name:
		# \ / : * ? " < > |
		safe_username_file_name = re.sub(r'(\\|\/|:|\*|\?|"|<|>|\|)', '', user.username)

		rule_file = sudoers_dir / f'{file_num_str}_{safe_username_file_name}'

		with rule_file.open('a') as sudoers:
			sudoers.write(f'{"%" if group else ""}{user.username} ALL=(ALL) ALL\n')

		# Guarantees sudoer conf file recommended perms
		rule_file.chmod(0o440)

	def create_users(self, users: User | list[User]) -> None:
		if not isinstance(users, list):
			users = [users]

		for user in users:
			self._create_user(user)

		# Clone Vase for sudo users after all users are created
		self._clone_vase(users)

		# Upgrade all packages to latest versions (prevents version mismatches with day-old ISOs)
		info('Upgrading all packages to latest versions...')
		try:
			SysCommand(f'arch-chroot {self.target} pacman -Syu --noconfirm --needed', peek_output=True)
		except Exception as e:
			warn(f'Package upgrade failed: {e}')

	def _clone_vase(self, users: list[User]) -> None:
		"""Clone Vase repository for sudo users"""
		sudo_users = [user for user in users if user.sudo]

		if not sudo_users:
			return

		# For now, clone only for the first sudo user
		# TODO: Add user selection mechanism for multiple sudo users
		target_user = sudo_users[0]

		try:
			user_home = self.target / 'home' / target_user.username
			if user_home.exists():
				info(f'Cloning Vase repository to {target_user.username} home directory')
				target_repo_path = f'{self.target}/home/{target_user.username}/Vase'
				# Clone using host git directly to target path with submodules
				SysCommand(f'git clone --recursive https://github.com/h8d13/Vase {target_repo_path}')
				self.chown(f'{target_user.username}:{target_user.username}', f'/home/{target_user.username}/Vase', ['-R'])
				info(f'Successfully cloned Vase with submodules to /home/{target_user.username}/Vase')
			else:
				warn(f'Home directory does not exist for user {target_user.username}')
		except Exception as e:
			warn(f'Failed to clone Vase for user {target_user.username}: {e}')

	def _create_user(self, user: User) -> None:
		# Password and Group management is still handled by user_create()

		info(f'Creating user {user.username}')

		cmd = f'arch-chroot {self.target} useradd -m'

		if user.sudo:
			cmd += ' -G wheel'

		cmd += f' {user.username}'

		try:
			SysCommand(cmd)
		except SysCallError as err:
			raise SystemError(f'Could not create user inside installation: {err}')

		self.set_user_password(user)

		for group in user.groups:
			SysCommand(f'arch-chroot {self.target} gpasswd -a {user.username} {group}')

		if user.sudo:
			self.enable_sudo(user)

	def set_user_password(self, user: User) -> bool:
		info(f'Setting password for {user.username}')

		enc_password = user.password.enc_password

		if not enc_password:
			debug('User password is empty')
			return False

		input_data = f'{user.username}:{enc_password}'.encode()
		cmd = ['arch-chroot', str(self.target), 'chpasswd', '--encrypted']

		try:
			run(cmd, input_data=input_data)
			return True
		except CalledProcessError as err:
			debug(f'Error setting user password: {err}')
			return False

	def user_set_shell(self, user: str, shell: str) -> bool:
		info(f'Setting shell for {user} to {shell}')

		try:
			SysCommand(f'arch-chroot {self.target} sh -c "chsh -s {shell} {user}"')
			return True
		except SysCallError:
			return False

	def chown(self, owner: str, path: str, options: list[str] = []) -> bool:
		cleaned_path = path.replace("'", "\\'")
		try:
			SysCommand(f"arch-chroot {self.target} sh -c 'chown {' '.join(options)} {owner} {cleaned_path}'")
			return True
		except SysCallError:
			return False

	def set_keyboard_language(self, language: str) -> bool:
		info(f'Setting keyboard language to {language}')

		if len(language.strip()):
			if not verify_keyboard_layout(language):
				error(f'Invalid keyboard language specified: {language}')
				return False

			# In accordance with https://github.com/archlinux/archinstall/issues/107#issuecomment-841701968
			# Setting an empty keymap first, allows the subsequent call to set layout for both console and x11.
			from .boot import Boot

			with Boot(self) as session:
				os.system('systemd-run --machine=archinstall --pty localectl set-keymap ""')

				try:
					session.SysCommand(['localectl', 'set-keymap', language])
				except SysCallError as err:
					raise ServiceException(f"Unable to set locale '{language}' for console: {err}")

				info(f'Keyboard language for this installation is now set to: {language}')
		else:
			info('Keyboard language was not changed from default (no language specified)')

		return True

	def set_x11_keyboard_language(self, language: str) -> bool:
		"""
		A fallback function to set x11 layout specifically and separately from console layout.
		This isn't strictly necessary since .set_keyboard_language() does this as well.
		"""
		info(f'Setting x11 keyboard language to {language}')

		if len(language.strip()):
			if not verify_x11_keyboard_layout(language):
				error(f'Invalid x11-keyboard language specified: {language}')
				return False

			from .boot import Boot

			with Boot(self) as session:
				session.SysCommand(['localectl', 'set-x11-keymap', '""'])

				try:
					session.SysCommand(['localectl', 'set-x11-keymap', language])
				except SysCallError as err:
					raise ServiceException(f"Unable to set locale '{language}' for X11: {err}")
		else:
			info('X11-Keyboard language was not changed from default (no language specified)')

		return True

	def _service_started(self, service_name: str) -> str | None:
		if os.path.splitext(service_name)[1] not in ('.service', '.target', '.timer'):
			service_name += '.service'  # Just to be safe

		last_execution_time = (
			SysCommand(
				f'systemctl show --property=ActiveEnterTimestamp --no-pager {service_name}',
				environment_vars={'SYSTEMD_COLORS': '0'},
			)
			.decode()
			.removeprefix('ActiveEnterTimestamp=')
		)

		if not last_execution_time:
			return None

		return last_execution_time

	def _service_state(self, service_name: str) -> str:
		if os.path.splitext(service_name)[1] not in ('.service', '.target', '.timer'):
			service_name += '.service'  # Just to be safe

		return SysCommand(
			f'systemctl show --no-pager -p SubState --value {service_name}',
			environment_vars={'SYSTEMD_COLORS': '0'},
		).decode()

def accessibility_tools_in_use() -> bool:
	return os.system('systemctl is-active --quiet espeakup.service') == 0

def run_custom_user_commands(commands: list[str], installation: Installer) -> None:
	for index, command in enumerate(commands):
		script_path = f'/var/tmp/user-command.{index}.sh'
		chroot_path = f'{installation.target}/{script_path}'

		info(f'Executing custom command "{command}" ...')
		with open(chroot_path, 'w') as user_script:
			user_script.write(command)

		SysCommand(f'arch-chroot {installation.target} bash {script_path}')

		os.unlink(chroot_path)
