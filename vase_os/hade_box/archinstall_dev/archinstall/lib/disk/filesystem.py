from __future__ import annotations

import time
from pathlib import Path

from archinstall.tui.curses_menu import Tui

from ..interactions.general_conf import ask_abort
from ..models.device import (
	DiskLayoutConfiguration,
	DiskLayoutType,
	FilesystemType,
	PartitionModification,
	SectorSize,
	Size,
	Unit,
)
from ..output import debug, info
from .device_handler import device_handler

class FilesystemHandler:
	def __init__(self, disk_config: DiskLayoutConfiguration):
		self._disk_config = disk_config

	def perform_filesystem_operations(self, show_countdown: bool = True) -> None:
		device_mods = [d for d in self._disk_config.device_modifications if d.partitions]

		if not device_mods:
			debug('No modifications required')
			return

		device_paths = ', '.join([str(mod.device.device_info.path) for mod in device_mods])

		if show_countdown:
			self._final_warning(device_paths)

		# Setup the blockdevice and filesystem.
		# Once that's done, we'll hand over to perform_installation()

		# make sure all devices are unmounted
		for mod in device_mods:
			device_handler.umount_all_existing(mod.device_path)

		# Additional safety: ensure any swap partitions are disabled before partitioning
		for mod in device_mods:
			for partition in mod.partitions:
				if partition.is_swap() and partition.dev_path:
					try:
						from ..general import SysCommand
						SysCommand(['swapoff', str(partition.dev_path)])
						info(f'Disabled swap on {partition.dev_path}')
					except Exception:
						pass  # Ignore if swap wasn't enabled

		for mod in device_mods:
			device_handler.partition(mod)

		device_handler.udev_sync()

		# Force kernel to re-read partition table and clear cached data
		from ..general import SysCommand
		import time
		for mod in device_mods:
			try:
				# Re-read partition table
				SysCommand(['partprobe', str(mod.device_path)])
				debug(f'Ran partprobe on {mod.device_path}')
			except Exception as e:
				debug(f'partprobe failed (non-critical): {e}')

			try:
				# Flush device buffers
				SysCommand(['blockdev', '--flushbufs', str(mod.device_path)])
				debug(f'Flushed buffers on {mod.device_path}')
			except Exception as e:
				debug(f'blockdev --flushbufs failed (non-critical): {e}')

		# Brief delay for kernel to process partition table changes
		time.sleep(1)

		for mod in device_mods:
			self._format_partitions(mod.partitions)

			for part_mod in mod.partitions:
				if part_mod.fs_type == FilesystemType.Btrfs and part_mod.is_create_or_modify():
					device_handler.create_btrfs_volumes(part_mod)

	def _format_partitions(
		self,
		partitions: list[PartitionModification],
	) -> None:
		"""
		Format can be given an overriding path, for instance /dev/null to test
		the formatting functionality and in essence the support for the given filesystem.
		"""

		# don't touch existing partitions
		create_or_modify_parts = [p for p in partitions if p.is_create_or_modify()]

		self._validate_partitions(create_or_modify_parts)

		for part_mod in create_or_modify_parts:
			device_handler.format(part_mod.safe_fs_type, part_mod.safe_dev_path)

			# synchronize with udev before using lsblk
			device_handler.udev_sync()

			lsblk_info = device_handler.fetch_part_info(part_mod.safe_dev_path)

			part_mod.partn = lsblk_info.partn
			part_mod.partuuid = lsblk_info.partuuid
			part_mod.uuid = lsblk_info.uuid

	def _validate_partitions(self, partitions: list[PartitionModification]) -> None:
		checks = {
			# verify that all partitions have a path set (which implies that they have been created)
			lambda x: x.dev_path is None: ValueError('When formatting, all partitions must have a path set'),
			# file system type must be set
			lambda x: x.fs_type is None: ValueError('File system type must be set for modification'),
		}

		for check, exc in checks.items():
			found = next(filter(check, partitions), None)
			if found is not None:
				raise exc

	def _final_warning(self, device_paths: str) -> bool:
		# Issue a final warning before we continue with something un-revertable.
		# We mention the drive one last time, and count from 5 to 0.
		out =(' ! Formatting {} in ').format(device_paths)
		Tui.print(out, row=0, endl='', clear_screen=True)

		try:
			countdown = '\n5...4...3...2...1\n'
			for c in countdown:
				Tui.print(c, row=0, endl='')
				time.sleep(0.25)
		except KeyboardInterrupt:
			with Tui():
				ask_abort()

		return True
