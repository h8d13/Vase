from __future__ import annotations

from typing import override

from archinstall.default_profiles.profile import GreeterType, Profile
from archinstall.tui.curses_menu import SelectMenu
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties, Orientation

from ..hardware import GfxDriver
from ..interactions.system_conf import select_driver
from ..menu.abstract_menu import AbstractSubMenu
from ..models.profile import ProfileConfiguration

class ProfileMenu(AbstractSubMenu[ProfileConfiguration]):
	def __init__(
		self,
		preset: ProfileConfiguration | None = None,
	):
		if preset:
			self._profile_config = preset
		else:
			self._profile_config = ProfileConfiguration()

		menu_optioons = self._define_menu_options()
		self._item_group = MenuItemGroup(menu_optioons, checkmarks=True)

		super().__init__(
			self._item_group,
			self._profile_config,
			allow_reset=True,
		)
		
		# Set checkmark status: Type is auto-selected, Greeter is auto-determined by desktop env,
		# only Graphics Driver can be user-modified
		for item in self._item_group._menu_items:
			if item.value is not None:
				if item.key == 'gfx_driver':
					# Only graphics driver can be modified by user choice
					if item.value == GfxDriver.AllOpenSource:
						item.default_value = item.value
						item._value_modified = False  # Default
					else:
						item.default_value = GfxDriver.AllOpenSource
						item._value_modified = True   # User modified
				else:
					# Type and Greeter are auto-determined, always default
					item.default_value = item.value
					item._value_modified = False

	def _define_menu_options(self) -> list[MenuItem]:
		return [
			MenuItem(
				text=('Type'),
				action=self._select_profile,
				value=self._profile_config.profile,
				preview_action=self._preview_profile,
				key='profile',
			),
			MenuItem(
				text=('Graphics drivers'),
				action=self._select_gfx_driver,
				value=self._profile_config.gfx_driver if self._profile_config.profile and self._profile_config.profile.is_graphic_driver_supported() else None,
				preview_action=self._prev_gfx,
				enabled=self._profile_config.profile.is_graphic_driver_supported() if self._profile_config.profile else False,
				dependencies=['profile'],
				key='gfx_driver',
			),
			MenuItem(
				text=('X11 packages'),
				action=self._select_x11_packages,
				value=getattr(self._profile_config, 'x11_packages', None),
				preview_action=lambda item: ', '.join(item.value) if item.value else 'None',
				enabled='KDE Plasma' in self._profile_config.profile.current_selection_names() if self._profile_config.profile else False,
				dependencies=['profile'],
				key='x11_packages',
			),
			MenuItem(
				text=('Greeter (SDDM for KDE)'),
				action=lambda x: select_greeter(preset=x),
				value=self._profile_config.greeter if self._profile_config.profile and self._profile_config.profile.is_greeter_supported() else None,
				enabled=self._profile_config.profile.is_graphic_driver_supported() if self._profile_config.profile else False,
				preview_action=self._prev_greeter,
				dependencies=['profile'],
				key='greeter',
			),
		]

	@override
	def run(self, additional_title: str | None = None) -> ProfileConfiguration | None:
		from archinstall.lib.profile.profiles_handler import profile_handler
		from archinstall.lib.hardware import SysInfo
		
		# Preload graphics detection for faster access to Graphics driver menu
		# This caches the lspci detection so it's already available when needed
		SysInfo.has_nvidia_graphics()
		SysInfo.has_amd_graphics() 
		SysInfo.has_intel_graphics()
		
		# If no profile is set and there's only one option, auto-select it
		if not self._profile_config.profile:
			top_level_profiles = profile_handler.get_top_level_profiles()
			if len(top_level_profiles) == 1:
				profile = self._select_profile(None)
				if profile:
					self._profile_config.profile = profile
					# Mark auto-selected profile as default since it was auto-selected
					profile_item = self._item_group.find_by_key('profile')
					profile_item.value = profile
					profile_item.set_as_default()
					
					# Only mark gfx_driver and greeter as default if they were just auto-set
					# Don't override user's previous choices by checking if they were previously unset
					gfx_item = self._item_group.find_by_key('gfx_driver')
					if gfx_item.value is not None and not gfx_item._value_modified:
						gfx_item.set_as_default()
						
					greeter_item = self._item_group.find_by_key('greeter')
					if greeter_item.value is not None and not greeter_item._value_modified:
						greeter_item.set_as_default()
		
		super().run(additional_title=additional_title)
		return self._profile_config
	
	def has_modifications(self) -> bool:
		"""Check if any submenu items have been modified"""
		try:
			return (
				self._item_group.find_by_key('profile')._value_modified or
				self._item_group.find_by_key('gfx_driver')._value_modified
				# greeter is auto-determined, not user-modifiable
			)
		except ValueError:
			return False

	def _select_profile(self, preset: Profile | None) -> Profile | None:
		profile = select_profile(preset)

		if profile is not None:
			gfx_item = self._item_group.find_by_key('gfx_driver')
			if not profile.is_graphic_driver_supported():
				gfx_item.enabled = False
				gfx_item.value = None
			else:
				gfx_item.enabled = True
				# Only set default graphics driver if user hasn't already chosen one
				if gfx_item.value is None:
					gfx_item.value = GfxDriver.AllOpenSource

			greeter_item = self._item_group.find_by_key('greeter')
			if not profile.is_greeter_supported():
				greeter_item.enabled = False
				greeter_item.value = None
			else:
				greeter_item.enabled = True
				# Set default if not already chosen
				if greeter_item.value is None:
					greeter_item.value = profile.default_greeter_type

			x11_item = self._item_group.find_by_key('x11_packages')
			if 'KDE Plasma' in profile.current_selection_names():
				x11_item.enabled = True
			else:
				x11_item.enabled = False
				x11_item.value = None

		else:
			self._item_group.find_by_key('gfx_driver').value = None
			self._item_group.find_by_key('greeter').value = None
			self._item_group.find_by_key('x11_packages').value = None

		return profile

	def _select_gfx_driver(self, preset: GfxDriver | None = None) -> GfxDriver | None:
		driver = preset
		profile: Profile | None = self._item_group.find_by_key('profile').value

		if profile:
			if profile.is_graphic_driver_supported():
				driver = select_driver(preset=preset)

			if driver and 'Sway' in profile.current_selection_names():
				if driver.is_nvidia():
					header = ('The proprietary Nvidia driver is not supported by Sway.') + '\n'
					header += ('It is likely that you will run into issues, are you okay with that?') + '\n'

					group = MenuItemGroup.yes_no()
					group.focus_item = MenuItem.no()
					group.default_item = MenuItem.no()

					result = SelectMenu[bool](
						group,
						header=header,
						allow_skip=False,
						columns=2,
						orientation=Orientation.HORIZONTAL,
						alignment=Alignment.CENTER,
					).run()

					if result.item() == MenuItem.no():
						return preset

		return driver

	def _prev_gfx(self, item: MenuItem) -> str | None:
		if item.value:
			driver = item.get_value().value
			packages = item.get_value().packages_text()
			return f'Driver: {driver}\n{packages}'
		return None

	def _prev_greeter(self, item: MenuItem) -> str | None:
		if item.value:
			return f'Greeter: {item.value.value}'
		return None

	def _preview_profile(self, item: MenuItem) -> str | None:
		profile: Profile | None = item.value
		text = ''

		if profile:
			if (sub_profiles := profile.current_selection) is not None:
				text += ('Selected profiles: ')
				text += ', '.join([p.name for p in sub_profiles]) + '\n'

			if packages := profile.packages_text(include_sub_packages=True):
				text += f'{packages}'

			if text:
				return text

		return None

	def _select_x11_packages(self, preset: list[str] | None) -> list[str] | None:
		header = 'Select X11 packages to install:\n'
		header += 'Usually useful for older hardware, alongside Wayland.\n'

		# Get current profile to determine DE-specific packages
		profile: Profile | None = self._item_group.find_by_key('profile').value
		available_packages = []

		if profile:
			selection_names = profile.current_selection_names()
			if 'KDE Plasma' in selection_names:
				available_packages.append('plasma-x11-session')
				available_packages.extend(['xorg-xinit', 'xorg-xrandr', 'xorg-xauth'])
		
		# Can add common ones here that apply to several DE
		# Currently for GNOME leave wayland only.

		items = [
			MenuItem(
				text=pkg,
				value=pkg
			)
			for pkg in available_packages
		]

		group = MenuItemGroup(items)

		if preset:
			group.set_selected_by_value(preset)

		result = SelectMenu[str](
			group,
			multi=True,
			header=header,
			allow_skip=True,
			allow_reset=True,
			frame=FrameProperties.min('X11 packages'),
		).run()

		if result.type_ == ResultType.Skip:
			return preset
		elif result.type_ == ResultType.Selection:
			return result.get_values()
		elif result.type_ == ResultType.Reset:
			return None

		return None

def select_greeter(
	profile: Profile | None = None,
	preset: GreeterType | None = None,
) -> GreeterType | None:
	if not profile or profile.is_greeter_supported():
		items = [MenuItem(greeter.value, value=greeter) for greeter in GreeterType]
		group = MenuItemGroup(items, sort_items=True)

		default: GreeterType | None = None
		if preset is not None:
			default = preset
		elif profile is not None:
			default_greeter = profile.default_greeter_type
			default = default_greeter if default_greeter else None

		group.set_default_by_value(default)

		result = SelectMenu[GreeterType](
			group,
			allow_skip=True,
			frame=FrameProperties.min('Greeter'),
			alignment=Alignment.CENTER,
		).run()

		match result.type_:
			case ResultType.Skip:
				return preset
			case ResultType.Selection:
				return result.get_value()
			case ResultType.Reset:
				raise ValueError('Unhandled result type')

	return None

def select_profile(
	current_profile: Profile | None = None,
	header: str | None = None,
	allow_reset: bool = True,
) -> Profile | None:
	from archinstall.lib.profile.profiles_handler import profile_handler

	top_level_profiles = profile_handler.get_top_level_profiles()
	
	# If there's only one profile type available, auto-select it
	if len(top_level_profiles) == 1:
		profile_selection = top_level_profiles[0]
		select_result = profile_selection.do_on_select()
		
		if not select_result:
			return None
			
		match select_result:
			case select_result.NewSelection:
				profile_handler.reset_top_level_profiles(exclude=[profile_selection])
				return profile_selection
			case select_result.ResetCurrent:
				profile_handler.reset_top_level_profiles()
				return None
			case select_result.SameSelection:
				return profile_selection

	if header is None:
		header = ('This is a list of pre-programmed default_profiles') + '\n'

	items = [MenuItem(p.name, value=p) for p in top_level_profiles]
	group = MenuItemGroup(items, sort_items=False)
	group.set_selected_by_value(current_profile)

	result = SelectMenu[Profile](
		group,
		header=header,
		allow_reset=allow_reset,
		allow_skip=True,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Main profile'),
	).run()

	match result.type_:
		case ResultType.Reset:
			return None
		case ResultType.Skip:
			return current_profile
		case ResultType.Selection:
			profile_selection = result.get_value()
			select_result = profile_selection.do_on_select()

			if not select_result:
				return None

			# we're going to reset the currently selected profile(s) to avoid
			# any stale data laying around
			match select_result:
				case select_result.NewSelection:
					profile_handler.reset_top_level_profiles(exclude=[profile_selection])
					current_profile = profile_selection
				case select_result.ResetCurrent:
					profile_handler.reset_top_level_profiles()
					current_profile = None
				case select_result.SameSelection:
					pass

			return current_profile
