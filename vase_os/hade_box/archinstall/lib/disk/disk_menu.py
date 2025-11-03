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
		swap_item = MenuItem(
			text='Swap configuration',
			action=self._select_swap_config,
			value=self._disk_menu_config.swap_config,
			preview_action=self._prev_swap_config,
			key='swap_config',
		)
		# Mark the default swap config as default (zram) to show 'D' instead of checkmark
		swap_item.set_as_default()

		return [
			MenuItem(
				text=('Partitioning'),
				action=self._select_disk_layout_config,
				value=self._disk_menu_config.disk_config,
				preview_action=self._prev_disk_layouts,
				key='disk_config',
			),
			swap_item,
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

			for mod in device_mods:
				# Show actual partitions plus swap if configured
				partitions_to_show = list(mod.partitions)

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
		return new_config

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


