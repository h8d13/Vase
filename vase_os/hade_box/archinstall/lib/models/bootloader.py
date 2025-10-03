from __future__ import annotations

from enum import Enum
from dataclasses import dataclass

class Bootloader(Enum):
	Grub = 'Grub'

	def json(self) -> str:
		return self.value

	@classmethod
	def get_default(cls) -> Bootloader:
		return Bootloader.Grub

	@classmethod
	def from_arg(cls, bootloader: str, skip_boot: bool) -> Bootloader:
		return Bootloader.Grub

@dataclass
class GrubConfiguration:
	"""Configuration options for GRUB bootloader"""
	enable_os_prober: bool = False
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
		if self.enable_os_prober:
			# If OS prober is enabled, always show menu
			return 'menu'
		elif self.hide_menu:
			# Hide menu only if OS prober is disabled
			return 'hidden'
		else:
			return 'menu'  # default to menu when OS prober disabled but not hiding
