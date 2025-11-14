from pathlib import Path

from archinstall.lib.args import arch_config_handler
from archinstall.lib.disk.device_handler import device_handler
from archinstall.lib.menu.menu_helper import MenuHelper
from archinstall.lib.models.bootloader import Bootloader
from archinstall.lib.models.device import (
	BDevice,
	BtrfsMountOption,
	DeviceModification,
	DiskLayoutConfiguration,
	DiskLayoutType,
	FilesystemType,
	ModificationStatus,
	PartitionFlag,
	PartitionModification,
	PartitionType,
	SectorSize,
	Size,
	SubvolumeModification,
	Unit,
	_DeviceInfo,
)
from archinstall.lib.output import debug
from archinstall.tui.curses_menu import SelectMenu
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties, Orientation, PreviewStyle

from ..output import FormattedOutput

def select_devices(preset: list[BDevice] | None = []) -> list[BDevice]:
	def _preview_device_selection(item: MenuItem) -> str | None:
		device = item.get_value()
		dev = device_handler.get_device(device.path)

		if dev and dev.partition_infos:
			return FormattedOutput.as_table(dev.partition_infos)
		return None

	if preset is None:
		preset = []

	devices = device_handler.devices
	options = [d.device_info for d in devices]
	presets = [p.device_info for p in preset]

	group = MenuHelper(options).create_menu_group()
	group.set_selected_by_value(presets)
	group.set_preview_for_all(_preview_device_selection)

	result = SelectMenu[_DeviceInfo](
		group,
		alignment=Alignment.CENTER,
		search_enabled=False,
		multi=True,
		preview_style=PreviewStyle.BOTTOM,
		preview_size='auto',
		preview_frame=FrameProperties.max('Partitions'),
		allow_skip=True,
	).run()

	match result.type_:
		case ResultType.Reset:
			return []
		case ResultType.Skip:
			return preset
		case ResultType.Selection:
			selected_device_info = result.get_values()
			selected_devices = []

			for device in devices:
				if device.device_info in selected_device_info:
					selected_devices.append(device)

			return selected_devices

def select_disk_config(preset: DiskLayoutConfiguration | None = None) -> DiskLayoutConfiguration | None:
	"""
	Simplified disk configuration - default layout only (single disk).
	Removed multi-disk and manual partitioning options.
	"""
	preset_devices = [mod.device for mod in preset.device_modifications] if preset else []
	devices = select_devices(preset_devices)

	if not devices:
		return None

	# Only support single disk
	if len(devices) > 1:
		from archinstall.tui.curses_menu import SelectMenu
		from archinstall.tui.menu_item import MenuItem, MenuItemGroup
		from archinstall.tui.types import Alignment

		items = [MenuItem('Continue')]
		group = MenuItemGroup(items)
		SelectMenu(
			group,
			header='Only single disk installations are supported.\nPlease select one device.',
			alignment=Alignment.CENTER,
		).run()
		return None

	# New single disk only since adding disks post-install is trivial
	device_modification = suggest_single_disk_layout(
		devices[0],
		filesystem_type=None,
	)

	if device_modification:
		return DiskLayoutConfiguration(
			config_type=DiskLayoutType.Default,
			device_modifications=[device_modification],
		)

	return None

def _select_boot_size(sector_size: SectorSize) -> Size:
	"""Prompt user to select boot partition size"""
	items = [
		MenuItem('512 MiB', value=Size(512, Unit.MiB, sector_size)),
		MenuItem('1 GiB', value=Size(1, Unit.GiB, sector_size)),
		MenuItem('2 GiB', value=Size(2, Unit.GiB, sector_size)),
		MenuItem('4 GiB', value=Size(4, Unit.GiB, sector_size)),
		MenuItem('8 GiB', value=Size(8, Unit.GiB, sector_size)),
	]

	group = MenuItemGroup(items, sort_items=False)
	group.set_default_by_value(Size(1, Unit.GiB, sector_size))

	result = SelectMenu[Size](
		group,
		header='Select boot partition size:\n',
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Boot size'),
		allow_skip=False,
	).run()

	match result.type_:
		case ResultType.Selection:
			return result.get_value()
		case _:
			return Size(1, Unit.GiB, sector_size)

def _select_separate_esp(using_gpt: bool) -> bool:
	"""Prompt user if they want ESP on a separate partition (GPT only)"""
	if not using_gpt:
		return False

	prompt = ('Would you like to use a separate ESP partition?\n')
	prompt += ('Merged: /boot/efi is the ESP (simpler, default)\n')
	prompt += ('Separate: /efi for ESP (grub kernels on /), /boot for systemd-boot\n')

	items = [
		MenuItem('Standard (recommended)', value=False),
		MenuItem('Separate ESP (advanced)', value=True),
	]

	group = MenuItemGroup(items, sort_items=False)
	group.set_default_by_value(False)

	result = SelectMenu[bool](
		group,
		header=prompt,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('ESP Configuration'),
		allow_skip=False,
	).run()

	match result.type_:
		case ResultType.Selection:
			return result.get_value()
		case _:
			return False

def _esp_partition(sector_size: SectorSize) -> PartitionModification:
	"""Create a separate ESP partition (512 MiB, mounted at /efi)"""
	flags = [PartitionFlag.ESP]
	start = Size(1, Unit.MiB, sector_size)
	size = Size(512, Unit.MiB, sector_size)

	return PartitionModification(
		status=ModificationStatus.Create,
		type=PartitionType.Primary,
		start=start,
		length=size,
		mountpoint=Path('/efi'),
		fs_type=FilesystemType.Fat32,
		flags=flags,
	)

def _boot_partition(sector_size: SectorSize, using_gpt: bool, size: Size | None = None, separate_esp: bool = False, filesystem_type: FilesystemType | None = None) -> PartitionModification:
	"""Create boot partition. If separate_esp=True, this is a regular boot partition using user's chosen FS, otherwise it's the ESP (FAT32)"""
	if size is None:
		size = Size(1, Unit.GiB, sector_size)

	flags = [PartitionFlag.BOOT]
	start = Size(1, Unit.MiB, sector_size)

	# Determine filesystem type and flags based on separate_esp setting
	if separate_esp:
		# When using separate ESP, /boot uses the same filesystem as root (user's choice)
		fs_type = filesystem_type if filesystem_type else FilesystemType.Ext4
		# Add XBOOTLDR flag for systemd-boot when using separate ESP
		if using_gpt:
			if arch_config_handler.config.bootloader == Bootloader.Systemd:
				flags.append(PartitionFlag.XBOOTLDR)
	else:
		# Standard mode: /boot is the ESP (FAT32)
		fs_type = FilesystemType.Fat32
		if using_gpt:
			flags.append(PartitionFlag.ESP)

	return PartitionModification(
		status=ModificationStatus.Create,
		type=PartitionType.Primary,
		start=start,
		length=size,
		mountpoint=Path('/boot'),
		fs_type=fs_type,
		flags=flags,
	)

def select_main_filesystem_format() -> FilesystemType:
	items = [
		MenuItem('ext4', value=FilesystemType.Ext4),
		MenuItem('btrfs', value=FilesystemType.Btrfs),
		MenuItem('xfs', value=FilesystemType.Xfs),
		MenuItem('f2fs', value=FilesystemType.F2fs),
	]

	group = MenuItemGroup(items, sort_items=False)
	result = SelectMenu[FilesystemType](
		group,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Filesystem'),
		allow_skip=False,
	).run()

	match result.type_:
		case ResultType.Selection:
			return result.get_value()
		case _:
			raise ValueError('Unhandled result type')

def select_mount_options() -> list[str]:
	prompt = ('Would you like to use compression or disable CoW?') + '\n'
	compression = ('Use compression')
	disable_cow = ('Disable Copy-on-Write')

	items = [
		MenuItem(compression, value=BtrfsMountOption.compress.value),
		MenuItem(disable_cow, value=BtrfsMountOption.nodatacow.value),
	]
	group = MenuItemGroup(items, sort_items=False)
	result = SelectMenu[str](
		group,
		header=prompt,
		alignment=Alignment.CENTER,
		columns=2,
		orientation=Orientation.HORIZONTAL,
		search_enabled=False,
		allow_skip=True,
	).run()

	match result.type_:
		case ResultType.Skip:
			return []
		case ResultType.Selection:
			return [result.get_value()]
		case _:
			raise ValueError('Unhandled result type')

def process_root_partition_size(total_size: Size, sector_size: SectorSize) -> Size:
	# root partition size processing
	total_device_size = total_size.convert(Unit.GiB)
	if total_device_size.value > 500:
		# maximum size
		return Size(value=50, unit=Unit.GiB, sector_size=sector_size)
	elif total_device_size.value < 320:
		# minimum size
		return Size(value=32, unit=Unit.GiB, sector_size=sector_size)
	else:
		# 10% of total size
		length = total_device_size.value // 10
		return Size(value=length, unit=Unit.GiB, sector_size=sector_size)

def get_default_btrfs_subvols() -> list[SubvolumeModification]:
	# https://btrfs.wiki.kernel.org/index.php/FAQ
	# https://unix.stackexchange.com/questions/246976/btrfs-subvolume-uuid-clash
	# https://github.com/classy-giraffe/easy-arch/blob/main/easy-arch.sh
	return [
		SubvolumeModification(Path('@'), Path('/')),
		SubvolumeModification(Path('@home'), Path('/home')),
		SubvolumeModification(Path('@log'), Path('/var/log')),
		SubvolumeModification(Path('@pkg'), Path('/var/cache/pacman/pkg')),
	]

def suggest_single_disk_layout(
	device: BDevice,
	filesystem_type: FilesystemType | None = None,
	separate_home: bool | None = None,
) -> DeviceModification:
	if not filesystem_type:
		filesystem_type = select_main_filesystem_format()

	sector_size = device.device_info.sector_size
	total_size = device.device_info.total_size
	available_space = total_size
	min_size_to_allow_home_part = Size(40, Unit.GiB, sector_size)

	if filesystem_type == FilesystemType.Btrfs:
		# Always use default btrfs subvolume structure for proper snapshot integration
		using_subvolumes = True
		mount_options = select_mount_options()
	else:
		using_subvolumes = False
		mount_options = []

	device_modification = DeviceModification(device, wipe=True)

	using_gpt = device_handler.partition_table.is_gpt()

	if using_gpt:
		available_space = available_space.gpt_end()

	available_space = available_space.align()

	# Used for reference: https://wiki.archlinux.org/title/partitioning

	# Ask if user wants separate ESP (GPT only)
	use_separate_esp = _select_separate_esp(using_gpt)

	# Create ESP partition if using separate ESP mode
	if use_separate_esp:
		esp_partition = _esp_partition(sector_size)
		device_modification.add_partition(esp_partition)
		# Boot partition comes after ESP
		next_start = esp_partition.start + esp_partition.length
	else:
		next_start = Size(1, Unit.MiB, sector_size)

	# When using GRUB with separate ESP, /boot partition is optional
	# GRUB can install to ESP and load kernels from root
	bootloader = arch_config_handler.config.bootloader
	skip_boot_partition = (use_separate_esp and bootloader == Bootloader.Grub)

	boot_partition = None
	if not skip_boot_partition:
		# Ask for boot partition size
		boot_size = _select_boot_size(sector_size)
		boot_partition = _boot_partition(sector_size, using_gpt, boot_size, separate_esp=use_separate_esp, filesystem_type=filesystem_type)
		# Adjust boot partition start if ESP came first
		if use_separate_esp:
			boot_partition.start = next_start
		device_modification.add_partition(boot_partition)

	if separate_home is False or using_subvolumes or total_size < min_size_to_allow_home_part:
		using_home_partition = False
	elif separate_home:
		using_home_partition = True
	else:
		prompt = ('Would you like to create a separate partition for /home?') + '\n'
		group = MenuItemGroup.yes_no()
		group.set_focus_by_value(MenuItem.yes().value)
		result = SelectMenu(
			group,
			header=prompt,
			orientation=Orientation.HORIZONTAL,
			columns=2,
			alignment=Alignment.CENTER,
			allow_skip=False,
		).run()

		using_home_partition = result.item() == MenuItem.yes()

	# root partition starts right after boot partition (or ESP if no boot partition)
	if boot_partition:
		root_start = boot_partition.start + boot_partition.length
	elif use_separate_esp:
		root_start = esp_partition.start + esp_partition.length
	else:
		root_start = Size(1, Unit.MiB, sector_size)

	# Set a size for / (/root)
	if using_home_partition:
		root_length = process_root_partition_size(total_size, sector_size)
	else:
		root_length = available_space - root_start

	root_partition = PartitionModification(
		status=ModificationStatus.Create,
		type=PartitionType.Primary,
		start=root_start,
		length=root_length,
		mountpoint=Path('/') if not using_subvolumes else None,
		fs_type=filesystem_type,
		mount_options=mount_options,
	)

	device_modification.add_partition(root_partition)

	if using_subvolumes:
		root_partition.btrfs_subvols = get_default_btrfs_subvols()
	elif using_home_partition:
		# If we don't want to use subvolumes,
		# But we want to be able to reuse data between re-installs..
		# A second partition for /home would be nice if we have the space for it
		home_start = root_partition.start + root_partition.length
		home_length = available_space - home_start

		flags = []
		if using_gpt:
			flags.append(PartitionFlag.LINUX_HOME)

		home_partition = PartitionModification(
			status=ModificationStatus.Create,
			type=PartitionType.Primary,
			start=home_start,
			length=home_length,
			mountpoint=Path('/home'),
			fs_type=filesystem_type,
			mount_options=mount_options,
			flags=flags,
		)
		device_modification.add_partition(home_partition)

	return device_modification

	return [root_device_modification, home_device_modification]