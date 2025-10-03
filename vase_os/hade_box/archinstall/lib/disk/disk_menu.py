from dataclasses import dataclass
from typing import override, TYPE_CHECKING

from archinstall.lib.models.device import (
	BtrfsOptions,
	DiskLayoutConfiguration,
	DiskLayoutType,
	SnapshotConfig,
	SnapshotType,
)

if TYPE_CHECKING:
	from ..args import SwapConfiguration
from archinstall.tui.curses_menu import SelectMenu
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties

from ..interactions.disk_conf import select_disk_config
from ..menu.abstract_menu import AbstractSubMenu
from ..output import FormattedOutput, info

@dataclass
class DiskMenuConfig:
	disk_config: DiskLayoutConfiguration | None
	btrfs_snapshot_config: SnapshotConfig | None
	swap_config: 'SwapConfiguration | None' = None

class DiskLayoutConfigurationMenu(AbstractSubMenu[DiskLayoutConfiguration]):
	def __init__(self, disk_layout_config: DiskLayoutConfiguration | None, swap_config: 'SwapConfiguration | None' = None):
		from ..args import SwapConfiguration

		# Convert swap_config to SwapConfiguration if needed
		if swap_config is not None:
			if isinstance(swap_config, dict):
				# Handle dict from JSON deserialization
				swap_config = SwapConfiguration(
					swap_type=swap_config.get('swap_type', 'zram'),
					size=swap_config.get('size', '4G')
				)
			# else assume it's already a SwapConfiguration object
		else:
			swap_config = SwapConfiguration()

		if not disk_layout_config:
			self._disk_menu_config = DiskMenuConfig(
				disk_config=None,
				btrfs_snapshot_config=None,
				swap_config=swap_config,
			)
		else:
			snapshot_config = disk_layout_config.btrfs_options.snapshot_config if disk_layout_config.btrfs_options else None

			self._disk_menu_config = DiskMenuConfig(
				disk_config=disk_layout_config,
				btrfs_snapshot_config=snapshot_config,
				swap_config=swap_config,
			)

		menu_optioons = self._define_menu_options()
		self._item_group = MenuItemGroup(menu_optioons, sort_items=False, checkmarks=True)

		super().__init__(
			self._item_group,
			self._disk_menu_config,
			allow_reset=True,
		)

	def _define_menu_options(self) -> list[MenuItem]:
		return [
			MenuItem(
				text='Swap configuration',
				action=self._select_swap_config,
				value=self._disk_menu_config.swap_config,
				preview_action=self._prev_swap_config,
				key='swap_config',
			),
			MenuItem(
				text=('Partitioning'),
				action=self._select_disk_layout_config,
				value=self._disk_menu_config.disk_config,
				preview_action=self._prev_disk_layouts,
				key='disk_config',
			),
			MenuItem(
				text='Btrfs snapshots',
				action=self._select_btrfs_snapshots,
				value=self._disk_menu_config.btrfs_snapshot_config,
				preview_action=self._prev_btrfs_snapshots,
				dependencies=[self._check_dep_btrfs],
				key='btrfs_snapshot_config',
			),
		]

	@override
	def run(self, additional_title: str | None = None) -> DiskLayoutConfiguration | None:
		result = super().run(additional_title=additional_title)

		# Sync the current menu values to our config
		swap_item = self._item_group.find_by_key('swap_config')
		if swap_item:
			self._disk_menu_config.swap_config = swap_item.value

		if self._disk_menu_config.disk_config:
			# Handle swap partition creation if needed
			if self._disk_menu_config.swap_config and self._disk_menu_config.swap_config.swap_type == 'partition':
				self._ensure_swap_partition_exists()


			# Only set btrfs_options if the configuration actually has btrfs volumes
			if self._disk_menu_config.disk_config.has_default_btrfs_vols():
				self._disk_menu_config.disk_config.btrfs_options = BtrfsOptions(snapshot_config=self._disk_menu_config.btrfs_snapshot_config)
			else:
				self._disk_menu_config.disk_config.btrfs_options = None
			return self._disk_menu_config.disk_config

		return None

	def _check_dep_btrfs(self) -> bool:
		disk_layout_conf: DiskLayoutConfiguration | None = self._menu_item_group.find_by_key('disk_config').value

		if disk_layout_conf:
			return disk_layout_conf.has_default_btrfs_vols()

		return False

	def _select_disk_layout_config(self, preset: DiskLayoutConfiguration | None) -> DiskLayoutConfiguration | None:
		disk_config = select_disk_config(preset)

		if disk_config != preset:
			# Clear snapshot configuration if switching to non-btrfs filesystem
			if not disk_config or not disk_config.has_default_btrfs_vols():
				self._disk_menu_config.btrfs_snapshot_config = None

		return disk_config

	def _select_btrfs_snapshots(self, preset: SnapshotConfig | None) -> SnapshotConfig | None:
		preset_type = preset.snapshot_type if preset else None

		group = MenuItemGroup.from_enum(
			SnapshotType,
			sort_items=False,
			preset=preset_type,
		)

		result = SelectMenu[SnapshotType](
			group,
			allow_reset=True,
			allow_skip=True,
			frame=FrameProperties.min('Snapshot type'),
			alignment=Alignment.CENTER,
		).run()

		match result.type_:
			case ResultType.Skip:
				return preset
			case ResultType.Reset:
				return None
			case ResultType.Selection:
				return SnapshotConfig(snapshot_type=result.get_value())

	def _prev_disk_layouts(self, item: MenuItem) -> str | None:
		if not item.value:
			return None

		disk_layout_conf = item.get_value()

		device_mods = [d for d in disk_layout_conf.device_modifications if d.partitions]

		if device_mods:
			output_partition = '{}: {}\n'.format(('Configuration'), disk_layout_conf.config_type.display_msg())
			output_btrfs = ''

			# Add swap configuration info if relevant
			swap_info = self._get_swap_info_for_preview()
			if swap_info:
				output_partition += f'\n{swap_info}\n'

			for mod in device_mods:
				# Show actual partitions plus swap if configured
				partitions_to_show = list(mod.partitions)

				# Get the current swap config from the menu item to ensure we have the latest value
				swap_item = self._item_group.find_by_key('swap_config')
				current_swap_config = swap_item.value if swap_item else self._disk_menu_config.swap_config

				# Add swap partition for preview if configured as partition type and not already present
				if (current_swap_config and
					current_swap_config.swap_type == 'partition' and
					not any(p.is_swap() for p in mod.partitions)):
					# Create a properly positioned swap partition for preview
					swap_partition = self._create_swap_partition(current_swap_config, mod.partitions)
					if swap_partition:
						# Insert swap as second partition (after boot) for preview
						boot_index = -1
						for i, part in enumerate(partitions_to_show):
							if part.is_boot() or part.is_efi():
								boot_index = i
								break

						if boot_index >= 0:
							# Insert after boot partition
							partitions_to_show.insert(boot_index + 1, swap_partition)
						else:
							# No boot partition, add at end
							partitions_to_show.append(swap_partition)

				# create partition table
				partition_table = FormattedOutput.as_table(partitions_to_show)

				output_partition += f'{mod.device_path}: {mod.device.device_info.model}\n'
				output_partition += '{}: {}\n'.format(('Wipe'), mod.wipe)
				output_partition += partition_table + '\n'

				# create btrfs table
				btrfs_partitions = [p for p in mod.partitions if p.btrfs_subvols]
				for partition in btrfs_partitions:
					output_btrfs += FormattedOutput.as_table(partition.btrfs_subvols) + '\n'

			output = output_partition + output_btrfs
			return output.rstrip()

		return None

	def _prev_btrfs_snapshots(self, item: MenuItem) -> str | None:
		if not item.value:
			return None

		snapshot_config: SnapshotConfig = item.value
		return ('Snapshot type: {}').format(snapshot_config.snapshot_type.value)

	def _select_swap_config(self, preset: 'SwapConfiguration | None') -> 'SwapConfiguration':
		from ..interactions.system_conf import ask_for_swap, ask_for_swap_size
		from ..args import SwapConfiguration

		if not preset:
			preset = SwapConfiguration()
		elif isinstance(preset, dict):
			# Handle dict from JSON deserialization
			preset = SwapConfiguration(
				swap_type=preset.get('swap_type', 'zram'),
				size=preset.get('size', '4G')
			)

		# Use the existing swap configuration UI
		swap_type = ask_for_swap(preset.swap_type)

		# Ask for size for all swap types except 'none'
		size = preset.size
		if swap_type != 'none':
			size = ask_for_swap_size(preset.size)

		# Create new SwapConfiguration with the selected type and size
		new_config = SwapConfiguration(swap_type=swap_type, size=size)

		# If partition type selected, automatically create partition when disk config exists
		if swap_type == 'partition' and self._disk_menu_config.disk_config:
			self._auto_create_swap_partition(new_config)

		return new_config

	def _ensure_swap_partition_exists(self) -> None:
		"""Ensure a swap partition exists when partition swap is selected"""
		from ..models.device import PartitionModification, PartitionFlag, FilesystemType, Size, Unit, ModificationStatus, SectorSize, PartitionType
		from ..output import info

		disk_config = self._disk_menu_config.disk_config
		swap_config = self._disk_menu_config.swap_config

		if not disk_config or not disk_config.device_modifications or not swap_config:
			return

		# Check if swap partition already exists in any device
		for device_mod in disk_config.device_modifications:
			if any(p.is_swap() for p in device_mod.partitions):
				info('Swap partition already exists in disk configuration')
				return  # Swap partition already exists

		# No swap partition found, create one on the first available device
		info('Creating swap partition as configured')

		# Parse the swap size first to know how much space we need
		size_str = swap_config.size or '4G'
		try:
			import re
			match = re.match(r'(\d+)([KMGT]?)', size_str.upper())
			if match:
				value, unit_str = match.groups()
				value = int(value)
				unit_map = {'': Unit.B, 'K': Unit.KiB, 'M': Unit.MiB, 'G': Unit.GiB, 'T': Unit.TiB}
				unit = unit_map.get(unit_str, Unit.GiB)
			else:
				value, unit = 4, Unit.GiB
		except:
			value, unit = 4, Unit.GiB

		for device_mod in disk_config.device_modifications:
			info(f'Device {device_mod.device_path} has {len(device_mod.partitions)} existing partitions')

			# Check partition count limits for MBR
			if len(device_mod.partitions) >= 4 and hasattr(device_mod.device.disk, 'type') and device_mod.device.disk.type == 'msdos':
				info('Cannot add swap partition: MBR partition limit (4) reached')
				continue

			# Shrink the last partition to make room for swap
			if device_mod.partitions:
				last_partition = device_mod.partitions[-1]
				swap_size = Size(value, unit, SectorSize.default())

				# Check if last partition is large enough to shrink
				if last_partition.length > swap_size:
					info(f'Shrinking last partition by {swap_size.value} {swap_size.unit.value} to make room for swap')
					last_partition.length = last_partition.length - swap_size
				else:
					info(f'Last partition too small to shrink for swap ({last_partition.length.value} {last_partition.length.unit.value} < {swap_size.value} {swap_size.unit.value})')
					continue

			# Calculate proper start position after existing partitions
			if device_mod.partitions:
				info(f'Calculating position after {len(device_mod.partitions)} existing partitions')
				# Find the end of the last partition by converting everything to sectors first
				last_end_sectors = 0
				sector_size = SectorSize.default()

				for i, partition in enumerate(device_mod.partitions):
					# Convert both start and length to sectors for accurate calculation
					start_sectors = partition.start.convert(Unit.sectors, sector_size).value
					length_sectors = partition.length.convert(Unit.sectors, sector_size).value
					partition_end_sectors = start_sectors + length_sectors
					info(f'Partition {i}: start={start_sectors}, length={length_sectors}, end={partition_end_sectors}')

					if partition_end_sectors > last_end_sectors:
						last_end_sectors = partition_end_sectors

				# Calculate swap partition size in sectors using already parsed values
				swap_size_sectors = Size(value, unit, sector_size).convert(Unit.sectors, sector_size).value

				# Get disk size in sectors
				device_size_sectors = device_mod.device.device_info.total_size
				if hasattr(device_size_sectors, 'convert'):
					device_size_sectors = device_size_sectors.convert(Unit.sectors, sector_size).value
				else:
					# Convert bytes to sectors
					device_size_sectors = device_size_sectors // sector_size.value

				# Add padding and check if swap partition fits
				padding_sectors = Size(1, Unit.MiB, sector_size).convert(Unit.sectors, sector_size).value
				proposed_start = last_end_sectors + padding_sectors
				proposed_end = proposed_start + swap_size_sectors

				if proposed_end > device_size_sectors:
					info(f'Swap partition would exceed disk boundary: proposed_end={proposed_end}, disk_end={device_size_sectors}')
					# Try to fit swap at the end of disk with minimal padding
					available_sectors = device_size_sectors - last_end_sectors - 2048  # 1MB safety margin
					if available_sectors >= swap_size_sectors:
						start_position = Size(device_size_sectors - swap_size_sectors - 1024, Unit.sectors, sector_size)  # 512KB safety margin
						info(f'Repositioned swap to fit: start={start_position.value} sectors')
					else:
						info(f'Cannot fit {swap_size_sectors} sector swap partition, only {available_sectors} sectors available')
						continue
				else:
					start_position = Size(proposed_start, Unit.sectors, sector_size)
					info(f'Calculated swap start position: {proposed_start} sectors')
			else:
				# No existing partitions, start at 1MB
				start_position = Size(1, Unit.MiB, SectorSize.default())
				info('No existing partitions, starting swap at 1MB')

			# Skip space validation if wiping disk - we'll have full disk available after wipe
			if not device_mod.wipe:
				# Only validate space if not wiping (preserving existing partitions)
				device_size_bytes = device_mod.device.device_info.total_size
				# Convert device size to bytes if it's a Size object
				if hasattr(device_size_bytes, 'convert'):
					device_size_bytes = device_size_bytes.convert(Unit.B, SectorSize.default()).value

				required_size = start_position.convert(Unit.B, SectorSize.default()).value + Size(value, unit, SectorSize.default()).convert(Unit.B, SectorSize.default()).value
				if required_size > device_size_bytes:
					info(f'Cannot add swap partition: insufficient space on {device_mod.device_path}')
					continue
			else:
				info(f'Disk will be wiped - skipping space validation')

			# Create swap partition - we want it as partition 2 (after boot)
			# Find the boot partition (should be first)
			boot_partition = None
			boot_index = -1
			for i, part in enumerate(device_mod.partitions):
				if part.is_boot() or part.is_efi():
					boot_partition = part
					boot_index = i
					break

			if boot_partition:
				# Calculate swap position after boot partition
				boot_end = boot_partition.start + boot_partition.length
				swap_start = boot_end  # Start right after boot partition

				# Create swap partition
				swap_partition = PartitionModification(
					status=ModificationStatus.Create,
					type=PartitionType.Primary,
					start=swap_start,
					length=Size(value, unit, SectorSize.default()),
					fs_type=FilesystemType.LinuxSwap,
					mountpoint=None,
					flags=[PartitionFlag.SWAP],
				)

				# Adjust subsequent partitions to start after swap
				swap_end = swap_start + swap_partition.length
				for i in range(boot_index + 1, len(device_mod.partitions)):
					part = device_mod.partitions[i]
					if part.status == ModificationStatus.Create:
						# Move this partition to start after swap
						old_start = part.start
						part.start = swap_end
						swap_end = part.start + part.length
						info(f'Moved partition {i} from {old_start.value} to {part.start.value} sectors')

				# Insert swap as second partition (after boot)
				device_mod.partitions.insert(boot_index + 1, swap_partition)
				info(f'Added {size_str} swap partition as partition 2 after boot partition')
			else:
				# No boot partition found, fallback to adding at end
				start_position = Size(last_end_sectors, Unit.sectors, sector_size)
				swap_partition = PartitionModification(
					status=ModificationStatus.Create,
					type=PartitionType.Primary,
					start=start_position,
					length=Size(value, unit, SectorSize.default()),
					fs_type=FilesystemType.LinuxSwap,
					mountpoint=None,
					flags=[PartitionFlag.SWAP],
				)
				device_mod.partitions.append(swap_partition)
				info(f'No boot partition found, added swap at end: {size_str} swap partition at sector {start_position.value}')

			break

	def _auto_create_swap_partition(self, swap_config: 'SwapConfiguration') -> None:
		"""Automatically create a swap partition when partition swap is selected"""
		# Only create if disk config exists and has partitions
		if self._disk_menu_config.disk_config and self._disk_menu_config.disk_config.device_modifications:
			self._ensure_swap_partition_exists()
		else:
			info('Disk configuration not ready yet - swap partition will be added later')

	def _prev_swap_config(self, item: MenuItem) -> str | None:
		if not item.value:
			return None

		swap_config = item.value

		# Handle different types of swap config
		if isinstance(swap_config, dict):
			swap_type = swap_config.get('swap_type', 'zram')
			size = swap_config.get('size', '4G')
		else:
			swap_type = swap_config.swap_type
			size = swap_config.size or '4G'

		if swap_type == 'zram':
			return 'Compressed swap in RAM using zram.\nFast performance, no disk wear.\nRecommended for most systems.'
		elif swap_type == 'swapfile':
			return f'Traditional swap file on filesystem.\nSize: {size}\nEasy to resize later.'
		elif swap_type == 'partition':
			return f'Dedicated swap partition on disk.\nSize: {size}\nTraditional Linux approach.\nWill appear in partition table when disk is configured.'
		elif swap_type == 'none':
			return 'No swap configured.\nOnly recommended for systems with abundant RAM.'

		return None

	def _create_swap_partition(self, swap_config: 'SwapConfiguration', existing_partitions: list) -> 'PartitionModification | None':
		"""Create a swap partition positioned as partition 2 (after boot partition)"""
		from ..models.device import PartitionModification, PartitionFlag, FilesystemType, Size, Unit, ModificationStatus, SectorSize, PartitionType

		if not swap_config:
			return None

		# Parse the swap size (default to 4GB)
		size_str = swap_config.size or '4G'
		try:
			# Extract number and unit from size string like "4G"
			import re
			match = re.match(r'(\d+)([KMGT]?)', size_str.upper())
			if match:
				value, unit_str = match.groups()
				value = int(value)
				unit_map = {'': Unit.B, 'K': Unit.KiB, 'M': Unit.MiB, 'G': Unit.GiB, 'T': Unit.TiB}
				unit = unit_map.get(unit_str, Unit.GiB)
			else:
				value, unit = 4, Unit.GiB
		except:
			value, unit = 4, Unit.GiB

		sector_size = SectorSize.default()

		# Find the boot partition (should be first)
		boot_partition = None
		for partition in existing_partitions:
			if partition.is_boot() or partition.is_efi():
				boot_partition = partition
				break

		if boot_partition:
			# Position swap right after boot partition
			boot_end = boot_partition.start + boot_partition.length
			start_position = boot_end  # Start right after boot partition
		else:
			# No boot partition found, fallback to calculating position after all existing partitions
			if existing_partitions:
				# Find the end of the last partition
				last_end_sectors = 0
				for partition in existing_partitions:
					if partition.start:
						start_sectors = partition.start.convert(Unit.sectors, sector_size).value
						length_sectors = partition.length.convert(Unit.sectors, sector_size).value
						partition_end_sectors = start_sectors + length_sectors
						if partition_end_sectors > last_end_sectors:
							last_end_sectors = partition_end_sectors

				# Add padding
				padding_sectors = Size(1, Unit.MiB, sector_size).convert(Unit.sectors, sector_size).value
				start_position = Size(last_end_sectors + padding_sectors, Unit.sectors, sector_size)
			else:
				# No existing partitions, start at 1MB
				start_position = Size(1, Unit.MiB, SectorSize.default())

		return PartitionModification(
			status=ModificationStatus.Create,
			type=PartitionType.Primary,
			start=start_position,
			length=Size(value, unit, SectorSize.default()),
			fs_type=FilesystemType.LinuxSwap,
			mountpoint=None,
			flags=[PartitionFlag.SWAP],
		)

	def _get_swap_info_for_preview(self) -> str | None:
		"""Get swap information to show in disk configuration preview"""
		# Get the current swap config from the menu item to ensure we have the latest value
		swap_item = self._item_group.find_by_key('swap_config')
		swap_config = swap_item.value if swap_item else self._disk_menu_config.swap_config

		if not swap_config or swap_config.swap_type == 'none':
			return None

		if swap_config.swap_type == 'partition':
			# Don't show swap info here - it will appear directly in the partition table
			return None
		elif swap_config.swap_type == 'swapfile':
			return f"Swap: {swap_config.size} file"
		elif swap_config.swap_type == 'zram':
			return "Swap: zram (compressed RAM)"

		return None

	def _create_preview_swap_partition(self) -> 'PartitionModification | None':
		"""Create a temporary swap partition for preview purposes"""
		from ..models.device import PartitionModification, PartitionFlag, FilesystemType, Size, Unit, ModificationStatus, SectorSize, PartitionType

		# Get the current swap config from the menu item to ensure we have the latest value
		swap_item = self._item_group.find_by_key('swap_config')
		swap_config = swap_item.value if swap_item else self._disk_menu_config.swap_config

		if not swap_config:
			return None

		# Parse the swap size (default to 4GB)
		size_str = swap_config.size or '4G'
		try:
			# Extract number and unit from size string like "4G"
			import re
			match = re.match(r'(\d+)([KMGT]?)', size_str.upper())
			if match:
				value, unit_str = match.groups()
				value = int(value)
				unit_map = {'': Unit.B, 'K': Unit.KiB, 'M': Unit.MiB, 'G': Unit.GiB, 'T': Unit.TiB}
				unit = unit_map.get(unit_str, Unit.GiB)
			else:
				value, unit = 4, Unit.GiB
		except:
			value, unit = 4, Unit.GiB

		# Create preview swap partition - calculate actual position like the real creation logic

		# Use the same logic as _ensure_swap_partition_exists for accurate preview
		disk_config = self._disk_menu_config.disk_config
		start_position = Size(1, Unit.MiB, SectorSize.default())  # Default fallback

		if disk_config and disk_config.device_modifications:
			for device_mod in disk_config.device_modifications:
				# Calculate proper start position after existing partitions (same as real logic)
				if device_mod.partitions:
					# Find the end of the last partition by converting everything to sectors first
					last_end_sectors = 0
					sector_size = SectorSize.default()

					for partition in device_mod.partitions:
						if partition.start:
							# Convert both start and length to sectors for accurate calculation
							start_sectors = partition.start.convert(Unit.sectors, sector_size).value
							length_sectors = partition.length.convert(Unit.sectors, sector_size).value
							partition_end_sectors = start_sectors + length_sectors

							if partition_end_sectors > last_end_sectors:
								last_end_sectors = partition_end_sectors

					# Convert back to a Size object and add padding
					padding_sectors = Size(1, Unit.MiB, sector_size).convert(Unit.sectors, sector_size).value
					start_position = Size(last_end_sectors + padding_sectors, Unit.sectors, sector_size)
				else:
					# No existing partitions, start at 1MB (same as real logic)
					start_position = Size(1, Unit.MiB, SectorSize.default())
				break  # Use first device for preview

		return PartitionModification(
			status=ModificationStatus.Create,
			type=PartitionType.Primary,
			start=start_position,
			length=Size(value, unit, SectorSize.default()),
			fs_type=FilesystemType.LinuxSwap,
			mountpoint=None,
			flags=[PartitionFlag.SWAP],
		)

