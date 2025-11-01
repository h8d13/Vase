from __future__ import annotations

import sys
from enum import Enum
from dataclasses import dataclass

from ..hardware import SysInfo
from ..output import warn

class Bootloader(Enum):
	Grub = 'Grub'
	Systemd = 'Systemd-boot'

	def has_uki_support(self) -> bool:
		"""Check if bootloader supports Unified Kernel Images"""
		match self:
			case Bootloader.Systemd:
				return True
			case _:
				return False

	def json(self) -> str:
		return self.value

	@classmethod
	def get_default(cls) -> Bootloader:
		"""Get default bootloader based on system capabilities"""
		if SysInfo.has_uefi():
			return Bootloader.Grub
		else:
			return Bootloader.Grub

	@classmethod
	def from_arg(cls, bootloader: str, skip_boot: bool) -> Bootloader:
		"""Parse bootloader from user input"""
		# Support old configuration files
		bootloader = bootloader.capitalize()

		bootloader_options = [e.value for e in Bootloader]

		if bootloader not in bootloader_options:
			values = ', '.join(bootloader_options)
			warn(f'Invalid bootloader value "{bootloader}". Allowed values: {values}')
			sys.exit(1)

		return Bootloader(bootloader)

@dataclass
class GrubConfiguration:
	"""Configuration options for GRUB bootloader"""
	hide_menu: bool = False  # Only hide if OS prober is disabled
	remember_last_selection: bool = False  # Remember last selected OS
	timeout: int = 5
	enable_custom_colors: bool = False
	color_normal: str = "light-blue/black"
	color_highlight: str = "light-cyan/blue"
	enable_boot_sound: bool = False
	boot_sound_tune: str = "480 440 1"  # frequency duration repeat

	def get_timeout_style(self) -> str:
		"""Return the appropriate timeout style based on configuration"""
		if self.hide_menu:
			# Hide menu only if OS prober is disabled
			return 'hidden'
		else:
			return 'menu'  # default to menu when OS prober disabled but not hiding
