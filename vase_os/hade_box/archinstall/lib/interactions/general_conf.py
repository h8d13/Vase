from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import assert_never

from archinstall.tui.curses_menu import EditMenu, SelectMenu, Tui
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties, Orientation

from ..locale.utils import list_timezones
from ..output import warn

class PostInstallationAction(Enum):
	EXIT = ('Exit archinstall')
	REBOOT = ('Reboot system')
	CHROOT = ('Chroot into installation for post-installation configurations')

def ask_ntp(preset: bool = True) -> bool:
	header = ('Would you like to use automatic time synchronization (NTP) with the default time servers?\n') + '\n'
	header += (
		'Hardware time and other post-configuration steps might be required in order for NTP to work.\nFor more information, please check the Arch wiki'
		+ '\n'
	)

	preset_val = MenuItem.yes() if preset else MenuItem.no()
	group = MenuItemGroup.yes_no()
	group.focus_item = preset_val

	result = SelectMenu[bool](
		group,
		header=header,
		allow_skip=True,
		alignment=Alignment.CENTER,
		columns=2,
		orientation=Orientation.HORIZONTAL,
	).run()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Selection:
			return result.item() == MenuItem.yes()
		case _:
			raise ValueError('Unhandled return type')

def ask_hostname(preset: str | None = None) -> str | None:
	result = EditMenu(
		('Hostname'),
		alignment=Alignment.CENTER,
		allow_skip=True,
		default_text=preset,
	).input()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Selection:
			hostname = result.text()
			if len(hostname) < 1:
				return None
			return hostname
		case ResultType.Reset:
			raise ValueError('Unhandled result type')

def ask_for_a_timezone(preset: str | None = None) -> str | None:
	default = 'UTC'
	timezones = list_timezones()

	items = [MenuItem(tz, value=tz) for tz in timezones]
	group = MenuItemGroup(items, sort_items=True)
	group.set_selected_by_value(preset)
	group.set_default_by_value(default)

	result = SelectMenu[str](
		group,
		allow_reset=True,
		allow_skip=True,
		frame=FrameProperties.min('Timezone'),
		alignment=Alignment.CENTER,
	).run()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Reset:
			return default
		case ResultType.Selection:
			return result.get_value()

def select_language(preset: str | None = None) -> str | None:
	from ..locale.locale_menu import select_kb_layout

	# We'll raise an exception in an upcoming version.
	# from ..exceptions import Deprecated
	# raise Deprecated("select_language() has been deprecated, use select_kb_layout() instead.")

	# No need to translate this i feel, as it's a short lived message.
	warn('select_language() is deprecated, use select_kb_layout() instead. select_language() will be removed in a future version')

	return select_kb_layout(preset)

def add_number_of_parallel_downloads(preset: int | None = None) -> int | None:
	max_recommended = 10
	
	header = ('This option enables the number of parallel downloads that can occur during package downloads') + '\n'
	header += ('Enter the number of parallel downloads to be enabled.\n\nNote:\n')
	header += (' - Maximum recommended value : {} ( Allows {} parallel downloads at a time )').format(max_recommended, max_recommended) + '\n'
	header += (' - Disable/Default : 0 ( Disables parallel downloading, allows only 1 download at a time )\n')

	def validator(s: str | None) -> str | None:
		if s is not None:
			try:
				value = int(s)
				if value >= 0:
					return None
			except Exception:
				pass

		return ('Invalid download number')

	result = EditMenu(
		('Number downloads'),
		header=header,
		allow_skip=True,
		allow_reset=True,
		validator=validator,
		default_text=str(preset) if preset is not None else None,
	).input()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Reset:
			return 0
		case ResultType.Selection:
			downloads: int = int(result.text())
		case _:
			assert_never(result.type_)

	pacman_conf_path = Path('/etc/pacman.conf')
	with pacman_conf_path.open() as f:
		pacman_conf = f.read().split('\n')

	with pacman_conf_path.open('w') as fwrite:
		for line in pacman_conf:
			if 'ParallelDownloads' in line:
				fwrite.write(f'ParallelDownloads = {downloads}\n')
			else:
				fwrite.write(f'{line}\n')

	return downloads

def ask_post_installation(elapsed_time: float | None = None) -> PostInstallationAction:
	header = ('Installation completed')
	if elapsed_time is not None:
		minutes = int(elapsed_time // 60)
		seconds = int(elapsed_time % 60)
		header += f' in {minutes}m {seconds}s'
	header += '\n\n'
	header += ('What would you like to do next?') + '\n'

	items = [MenuItem(action.value, value=action) for action in PostInstallationAction]
	group = MenuItemGroup(items)

	result = SelectMenu[PostInstallationAction](
		group,
		header=header,
		allow_skip=False,
		alignment=Alignment.CENTER,
	).run()

	match result.type_:
		case ResultType.Selection:
			return result.get_value()
		case _:
			raise ValueError('Post installation action not handled')

def ask_additional_packages_to_install(preset: list[str] = []) -> list[str]:
	"""
	Simple comma-separated package input with validation.
	Validates packages against pacman database.
	"""
	header = 'Enter additional packages to install (comma-separated)\n\n'
	header += 'Examples: vim, htop, firefox, neofetch\n'
	header += 'Package names will be validated against pacman database.\n'

	preset_text = ', '.join(preset) if preset else ''

	def validator(text: str | None) -> str | None:
		"""Validate comma-separated package names against pacman database"""
		if not text or not text.strip():
			return None  # Empty is valid (no packages)

		# Split and clean package names
		packages = [pkg.strip() for pkg in text.split(',') if pkg.strip()]

		# Check for invalid characters in package names first
		# Valid: alphanumeric, dash, underscore, plus, dot
		import re
		for pkg in packages:
			if not re.match(r'^[a-zA-Z0-9._+-]+$', pkg):
				return f'Invalid package name format: {pkg}'

		# Validate packages exist in pacman database
		from ..general import SysCommand
		invalid_packages = []

		for pkg in packages:
			try:
				# Check if package exists in pacman database (local + sync)
				# pacman -Ss returns 1 if package not found
				result = SysCommand(f'pacman -Ss "^{pkg}$"')
				if not result.exit_code == 0 or not result.decode().strip():
					invalid_packages.append(pkg)
			except Exception:
				invalid_packages.append(pkg)

		if invalid_packages:
			return f'Package(s) not found: {", ".join(invalid_packages)}'

		return None  # Valid

	result = EditMenu(
		'Additional packages',
		header=header,
		alignment=Alignment.CENTER,
		allow_skip=True,
		allow_reset=True,
		validator=validator,
		default_text=preset_text,
	).input()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Reset:
			return []
		case ResultType.Selection:
			text = result.text()
			if not text or not text.strip():
				return []
			# Split, clean, and return list
			packages = [pkg.strip() for pkg in text.split(',') if pkg.strip()]
			return packages

def ask_abort() -> None:
	prompt = ('Do you really want to abort?') + '\n'
	group = MenuItemGroup.yes_no()

	result = SelectMenu[bool](
		group,
		header=prompt,
		allow_skip=False,
		alignment=Alignment.CENTER,
		columns=2,
		orientation=Orientation.HORIZONTAL,
	).run()

	if result.item() == MenuItem.yes():
		exit(0)
