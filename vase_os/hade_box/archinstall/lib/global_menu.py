from __future__ import annotations

from typing import override

from archinstall.lib.disk.disk_menu import DiskLayoutConfigurationMenu
from archinstall.lib.models.application import ApplicationConfiguration, Audio, AudioConfiguration, BluetoothConfiguration
from archinstall.lib.models.authentication import AuthenticationConfiguration
from archinstall.lib.models.device import DiskLayoutConfiguration, DiskLayoutType, EncryptionType, FilesystemType, PartitionModification
from archinstall.tui.menu_item import MenuItem, MenuItemGroup

from .applications.application_menu import ApplicationMenu
from .args import ArchConfig, SwapConfiguration
from .authentication.authentication_menu import AuthenticationMenu
from .configuration import save_config, ConfigurationOutput
from .hardware import SysInfo
from .interactions.general_conf import (
	add_number_of_parallel_downloads,
	ask_for_a_timezone,
	ask_hostname,
	ask_ntp,
)
from .interactions.network_menu import ask_to_configure_network
from .interactions.system_conf import ask_for_grub_configuration, select_kernel
from .locale.locale_menu import LocaleMenu
from .menu.abstract_menu import CONFIG_KEY, AbstractMenu
from .mirrors import MirrorMenu
from .models.bootloader import Bootloader
from .models.locale import LocaleConfiguration
from .models.mirrors import MirrorConfiguration
from .models.network import NetworkConfiguration, NicType
from .models.packages import Repository
from .models.profile import ProfileConfiguration
from .output import FormattedOutput
from .pacman.config import PacmanConfig

class GlobalMenu(AbstractMenu[None]):
	def __init__(self, arch_config: ArchConfig) -> None:
		self._arch_config = arch_config
		menu_optioons = self._get_menu_options()

		self._item_group = MenuItemGroup(
			menu_optioons,
			sort_items=False,
			checkmarks=True,
		)

		super().__init__(self._item_group, config=arch_config)
		
		# Mark items with default values AFTER config sync
		self._mark_defaults()

	def _mark_defaults(self) -> None:
		"""Mark menu items with default values"""
		items_with_defaults = [
			'locale_config',  # Default locale configuration
			'profile_config', # Default profile with graphics driver
			'app_config',     # Pipewire audio
			'hostname',      # 'archlinux'
			'kernels',       # 'linux'
			'network_config', # NetworkManager
			'parallel_downloads', # 0
			'timezone',      # 'UTC'
			'ntp',          # True
			'removable_media', # False
		]
		
		for key in items_with_defaults:
			try:
				item = self._item_group.find_by_key(key)
				if key == 'profile_config':
					# Profile config gets populated later, mark as default even if None initially
					item._value_modified = False
					item.default_value = item.value
				elif key == 'app_config':
					# App config default configuration (Bluetooth disabled, Audio PipeWire)
					default_config = ApplicationConfiguration(
						bluetooth_config=BluetoothConfiguration(enabled=False),
						audio_config=AudioConfiguration(audio=Audio.PIPEWIRE)
					)
					item._value_modified = False
					item.default_value = default_config
					# Set value to default if currently None
					if item.value is None:
						item.value = default_config
				elif item.value is not None:
					item.set_as_default()
			except ValueError:
				# Item not found, skip
				pass

	def _get_menu_options(self) -> list[MenuItem]:
		menu_options = [
			# Language menu removed - English only
			MenuItem(
				text=('Locales'),
				action=self._locale_selection,
				preview_action=self._prev_locale,
				key='locale_config',
			),
			MenuItem(
				text=('Authentication'),
				action=self._select_authentication,
				preview_action=self._prev_authentication,
				mandatory=True,
				key='auth_config',
			),
			MenuItem(
				text=('Disk configuration'),
				action=self._select_disk_config,
				preview_action=self._prev_disk_config,
				mandatory=True,
				key='disk_config',
			),
			MenuItem(
				text=('Grub2 configuration'),
				action=lambda preset: ask_for_grub_configuration(preset),
				preview_action=self._prev_grub_config,
				value=None,
				key='grub_config',
			),
			MenuItem(
				text=('Kernels'),
				value=['linux'],
				action=select_kernel,
				preview_action=self._prev_kernel,
				mandatory=True,
				key='kernels',
			),
			MenuItem(
				text=('Profile'),
				action=self._select_profile,
				preview_action=self._prev_profile,
				key='profile_config',
				mandatory=True,
				value=None,  # Will be populated by config sync
			),
			MenuItem(
				text=('Applications'),
				action=self._select_applications,
				value=None,
				preview_action=self._prev_applications,
				key='app_config',
			),
			MenuItem(
				text=('Hostname'),
				value='archlinux',
				action=ask_hostname,
				preview_action=self._prev_hostname,
				key='hostname',
			),
			MenuItem(
				text=('Network configuration'),
				action=ask_to_configure_network,
				value=NetworkConfiguration(NicType.NM),
				preview_action=self._prev_network_config,
				key='network_config',
			),
			MenuItem(
				text=('Parallel Downloads'),
				action=add_number_of_parallel_downloads,
				value=10,
				preview_action=self._prev_parallel_dw,
				key='parallel_downloads',
			),
			MenuItem(
				text=('Timezone'),
				action=ask_for_a_timezone,
				value='UTC',
				preview_action=self._prev_tz,
				key='timezone',
			),
			MenuItem(
				text=('Automatic time sync (NTP)'),
				action=ask_ntp,
				value=True,
				preview_action=self._prev_ntp,
				key='ntp',
			),
			MenuItem(
				text=('Mirrors and repos'),
				action=self._mirror_configuration,
				preview_action=self._prev_mirror_config,
				mandatory=True,
				key='mirror_config',
			),
			MenuItem(
				text=('Live medium'),
				value=self._arch_config.removable_media,
				preview_action=self._prev_removable_media,
				key='removable_media',
			),
			MenuItem(
				text='',
			),
			MenuItem(
				text=('Install'),
				preview_action=self._prev_install_invalid_config,
				key=f'{CONFIG_KEY}_install',
			),
			MenuItem(
				text=('Abort'),
				action=self._handle_abort,
				key=f'{CONFIG_KEY}_abort',
			),
		]

		return menu_options

	def _safe_config(self) -> None:
		# data: dict[str, Any] = {}
		# for item in self._item_group.items:
		# 	if item.key is not None:
		# 		data[item.key] = item.value

		self.sync_all_to_config()
		save_config(self._arch_config)

	def _missing_configs(self) -> list[str]:
		item: MenuItem = self._item_group.find_by_key('auth_config')
		auth_config: AuthenticationConfiguration | None = item.value

		def check(s: str) -> bool:
			item = self._item_group.find_by_key(s)
			return item.has_value()

		def has_superuser() -> bool:
			if auth_config and auth_config.users:
				return any([u.sudo for u in auth_config.users])
			return False

		missing = set()

		if not has_superuser():
			missing.add(
				('At least 1 user with sudo privileges must be specified'),
			)

		for item in self._item_group.items:
			if item.mandatory:
				assert item.key is not None
				if not check(item.key):
					missing.add(item.text)

		return list(missing)

	@override
	def _is_config_valid(self) -> bool:
		"""
		Checks the validity of the current configuration.
		"""
		if len(self._missing_configs()) != 0:
			return False
		return self._validate_bootloader() is None

	def _select_applications(self, preset: ApplicationConfiguration | None) -> ApplicationConfiguration | None:
		# If no preset, use default values
		if preset is None:
			preset = ApplicationConfiguration()
		
		app_config = ApplicationMenu(preset).run()
		
		# Get the parent item to manually control its status
		app_item = self._item_group.find_by_key('app_config')
		
		# Check if bluetooth is enabled (the only thing that matters)
		bluetooth_enabled = (app_config.bluetooth_config is not None and 
		                     app_config.bluetooth_config.enabled)
		
		# Force the correct modified state
		app_item._value_modified = bluetooth_enabled
		
		return app_config

	def _select_authentication(self, preset: AuthenticationConfiguration | None) -> AuthenticationConfiguration | None:
		auth_config = AuthenticationMenu(preset).run()
		return auth_config

	def _update_lang_text(self) -> None:
		"""
		The options for the global menu are generated with a static text;
		each entry of the menu needs to be updated with the new translation
		"""
		new_options = self._get_menu_options()

		for o in new_options:
			if o.key is not None:
				self._item_group.find_by_key(o.key).text = o.text

	def _locale_selection(self, preset: LocaleConfiguration) -> LocaleConfiguration:
		locale_menu = LocaleMenu(preset)
		locale_config = locale_menu.run()
		
		# If any submenu items were modified, mark parent as modified
		if locale_menu.has_modifications():
			locale_item = self._item_group.find_by_key('locale_config')
			locale_item.mark_as_modified()
		
		return locale_config

	def _prev_locale(self, item: MenuItem) -> str | None:
		if not item.value:
			return None

		config: LocaleConfiguration = item.value
		return config.preview()

	def _prev_network_config(self, item: MenuItem) -> str | None:
		if item.value:
			network_config: NetworkConfiguration = item.value
			output = f'Network configuration:\n{network_config.type.display_msg()}'

			return output
		return None

	def _prev_authentication(self, item: MenuItem) -> str | None:
		if item.value:
			auth_config: AuthenticationConfiguration = item.value
			output = ''

			if auth_config.root_enc_password:
				output += f'Root password: {auth_config.root_enc_password.hidden()}\n'

			if auth_config.users:
				output += FormattedOutput.as_table(auth_config.users) + '\n'

			return output

		return None

	def _prev_applications(self, item: MenuItem) -> str | None:
		output = ''
		
		if item.value:
			app_config: ApplicationConfiguration = item.value

			if app_config.bluetooth_config:
				output += f'Bluetooth: '
				output += ('Enabled') if app_config.bluetooth_config.enabled else ('Disabled')
			else:
				output += f'Bluetooth: ("Disabled") (default)'
			output += '\n'

			if app_config.audio_config:
				audio_config = app_config.audio_config
				output += f'Audio: {audio_config.audio.value}'
			else:
				output += f'Audio: {Audio.PIPEWIRE.value} (default)'
			output += '\n'
		else:
			# Show defaults when no configuration is set
			output += f'Bluetooth:("Disabled") (default)\n'
			output += f'Audio: {Audio.PIPEWIRE.value} (default)\n'

		return output.rstrip('\n')

	def _prev_tz(self, item: MenuItem) -> str | None:
		if item.value:
			return f'Timezone: {item.value}'
		return None

	def _prev_ntp(self, item: MenuItem) -> str | None:
		if item.value is not None:
			output = f'NTP: '
			output += ('Enabled') if item.value else ('Disabled')
			return output
		return None

	def _prev_disk_config(self, item: MenuItem) -> str | None:
		disk_layout_conf: DiskLayoutConfiguration | None = item.value

		if disk_layout_conf:
			output = ('Configuration type: {}').format(disk_layout_conf.config_type.display_msg()) + '\n'

			# Display swap configuration
			swap_config = getattr(self._config, 'swap', None)
			if swap_config:
				if isinstance(swap_config, SwapConfiguration):
					if swap_config.swap_type == 'none':
						output += ('Swap: Disabled') + '\n'
					elif swap_config.swap_type == 'zram':
						output += ('Swap: ZRAM ({})\n').format(swap_config.size)
					elif swap_config.swap_type == 'swapfile':
						output += ('Swap: Swapfile ({})\n').format(swap_config.size)
					else:
						output += ('Swap: {}').format(swap_config.swap_type) + '\n'

			if disk_layout_conf.btrfs_options:
				btrfs_options = disk_layout_conf.btrfs_options
				if btrfs_options.snapshot_config:
					output += ('Btrfs snapshot type: {}').format(btrfs_options.snapshot_config.snapshot_type.value) + '\n'

			return output

		return None

	def _prev_hostname(self, item: MenuItem) -> str | None:
		if item.value is not None:
			return f'Hostname: {item.value}'
		return None

	def _prev_parallel_dw(self, item: MenuItem) -> str | None:
		if item.value is not None:
			return f'Parallel Downloads: {item.value}'
		return None

	def _prev_kernel(self, item: MenuItem) -> str | None:
		if item.value:
			kernel = ', '.join(item.value)
			return f'Kernel: {kernel}'
		return None

	def _prev_grub_config(self, item: MenuItem) -> str | None:
		if item.value:
			from .models.bootloader import GrubConfiguration
			config: GrubConfiguration = item.value
			output = f'OS Prober: {"Enabled" if config.enable_os_prober else "Disabled"}\n'
			if config.enable_os_prober:
				output += f'Remember last OS: {"Yes" if config.remember_last_selection else "No"}\n'
			else:
				output += f'Menu visibility: {"Hidden (ESC to show)" if config.hide_menu else "Visible"}'

			# Only show timeout if menu is visible
			if not config.hide_menu:
				output += f'\nTimeout: {config.timeout} seconds'

			return output
		return None

	def _validate_bootloader(self) -> str | None:
		"""
		Checks the selected bootloader is valid for the selected filesystem
		type of the boot partition.

		Returns [`None`] if the bootloader is valid, otherwise returns a
		string with the error message.

		XXX: The caller is responsible for wrapping the string with the translation
			shim if necessary.
		"""
		bootloader: Bootloader | None = None
		root_partition: PartitionModification | None = None
		boot_partition: PartitionModification | None = None
		efi_partition: PartitionModification | None = None

		bootloader = Bootloader.Grub

		if disk_config := self._item_group.find_by_key('disk_config').value:
			for layout in disk_config.device_modifications:
				if root_partition := layout.get_root_partition():
					break
			for layout in disk_config.device_modifications:
				if boot_partition := layout.get_boot_partition():
					break
			if SysInfo.has_uefi():
				for layout in disk_config.device_modifications:
					if efi_partition := layout.get_efi_partition():
						break
		else:
			return 'No disk layout selected'

		if root_partition is None:
			return 'Root partition not found'

		if boot_partition is None:
			return 'Boot partition not found'

		if SysInfo.has_uefi():
			if efi_partition is None:
				return 'EFI system partition (ESP) not found'

			if efi_partition.fs_type not in [FilesystemType.Fat12, FilesystemType.Fat16, FilesystemType.Fat32]:
				return 'ESP must be formatted as a FAT filesystem'

		return None

	def _prev_install_invalid_config(self, item: MenuItem) -> str | None:
		if missing := self._missing_configs():
			text = ('Missing configurations:\n')
			for m in missing:
				text += f'- {m}\n'
			return text[:-1]  # remove last new line

		if error := self._validate_bootloader():
			return (f'Invalid configuration: {error}')

		return None

	def _prev_profile(self, item: MenuItem) -> str | None:
		profile_config: ProfileConfiguration | None = item.value

		if profile_config and profile_config.profile:
			output = ('Profiles') + ': '
			if profile_names := profile_config.profile.current_selection_names():
				output += ', '.join(profile_names) + '\n'
			else:
				output += profile_config.profile.name + '\n'

			if profile_config.gfx_driver:
				output += ('Graphics drivers') + ': ' + profile_config.gfx_driver.value + '\n'

			if profile_config.x11_packages:
				output += ('X11 packages') + ': ' + ', '.join(profile_config.x11_packages) + '\n'

			if profile_config.greeter:
				output += ('Greeter') + ': ' + profile_config.greeter.value + '\n'

			return output

		return None

	def _select_disk_config(
		self,
		preset: DiskLayoutConfiguration | None = None,
	) -> DiskLayoutConfiguration | None:
		# Get current swap config from the configuration
		# This might be boolean, dict, or SwapConfiguration object
		swap_config = getattr(self._config, 'swap', None)

		# Create disk menu with swap configuration integrated
		# The DiskLayoutConfigurationMenu constructor will handle conversion
		disk_menu = DiskLayoutConfigurationMenu(preset, swap_config)
		disk_config = disk_menu.run()

		# Update swap configuration from disk menu results
		if disk_menu._disk_menu_config.swap_config:
			self._config.swap = disk_menu._disk_menu_config.swap_config

		# Immediately sync the updated disk config to the main config
		# This ensures the swap partition is included in the saved configuration
		if disk_config:
			self._config.disk_config = disk_config

		return disk_config

	def _select_profile(self, current_profile: ProfileConfiguration | None) -> ProfileConfiguration | None:
		from .profile.profile_menu import ProfileMenu

		profile_menu = ProfileMenu(preset=current_profile)
		profile_config = profile_menu.run()
		
		# If any submenu items were modified, mark parent as modified
		if profile_menu.has_modifications():
			profile_item = self._item_group.find_by_key('profile_config')
			profile_item.mark_as_modified()
		
		return profile_config

	def _mirror_configuration(self, preset: MirrorConfiguration | None = None) -> MirrorConfiguration:
		mirror_configuration = MirrorMenu(preset=preset).run()

		if mirror_configuration.optional_repositories:
			# enable the repositories in the config
			pacman_config = PacmanConfig(None)
			pacman_config.enable(mirror_configuration.optional_repositories)
			pacman_config.apply()

		return mirror_configuration

	def _prev_mirror_config(self, item: MenuItem) -> str | None:
		if not item.value:
			return None

		mirror_config: MirrorConfiguration = item.value

		output = ''
		if mirror_config.mirror_regions:
			title = ('Selected mirror regions')
			divider = '-' * len(title)
			regions = mirror_config.region_names
			output += f'{title}\n{divider}\n{regions}\n\n'

		if mirror_config.custom_servers:
			title = ('Custom servers')
			divider = '-' * len(title)
			servers = mirror_config.custom_server_urls
			output += f'{title}\n{divider}\n{servers}\n\n'

		if mirror_config.optional_repositories:
			title = ('Optional repositories')
			divider = '-' * len(title)
			repos = ', '.join([r.value for r in mirror_config.optional_repositories])
			output += f'{title}\n{divider}\n{repos}\n\n'

		if mirror_config.custom_repositories:
			title = ('Custom repositories')
			table = FormattedOutput.as_table(mirror_config.custom_repositories)
			output += f'{title}:\n\n{table}'

		return output.strip()

	def _prev_removable_media(self, item: MenuItem) -> str | None:
		if item.value is not None:
			status = 'Enabled' if item.value else 'Disabled'
			output = f'Live medium: {status}\n\n'
			if item.value:
				output += 'Portable USB/SD installation with:\n'
				output += '• Hardware-agnostic boot\n'
				output += '• Reduced flash writes\n'
				output += '• Optimized I/O scheduler'
			else:
				output += 'Standard fixed drive installation'
			return output
		return None

	def _handle_abort(self, preset: None) -> None:
		"""Handle abort with option to save selections"""
		from ..tui.curses_menu import SelectMenu
		from ..tui.menu_item import MenuItem, MenuItemGroup
		from ..tui.result import ResultType
		from ..tui.types import Alignment
		from .configuration import auto_save_config

		# Sync current selections to config
		self.sync_all_to_config()

		items = [
			MenuItem(text=('Save selections and abort'), value='save_abort'),
			MenuItem(text=('Abort without saving'), value='abort_only'),
			MenuItem(text=('Cancel abort'), value='cancel'),
		]

		group = MenuItemGroup(items)
		group.focus_item = group.items[0]  # Focus on save option

		result = SelectMenu[str](
			group,
			header=('You are about to abort the installation.'),
			alignment=Alignment.CENTER,
			allow_skip=False,
		).run()

		if result.type_ == ResultType.Selection:
			choice = result.get_value()

			if choice == 'save_abort':
				success, saved_files = auto_save_config(self._arch_config)
				if success:
					# Check if credentials are actually present (not just empty JSON)
					config_output = ConfigurationOutput(self._arch_config)
					creds_json = config_output.user_credentials_to_json()
					has_creds = creds_json and creds_json.strip() != '{}'
					creds_status = "✓" if has_creds else "✗ (empty)"
					print(f'Saved: user_configuration.json ✓, user_credentials.json {creds_status} - Resume by running installer again.')
				else:
					print('Failed to save selections.')
				exit(1)
			elif choice == 'abort_only':
				exit(1)
			# If 'cancel', just return to menu

		return None

	def sync_all_to_config(self) -> None:
		for item in self._menu_item_group._menu_items:
			if item.key:
				setattr(self._config, item.key, item.value)

	def _sync_from_config(self) -> None:
		for item in self._menu_item_group._menu_items:
			if item.key:
				config_value = getattr(self._config, item.key, None)
				if config_value is not None:
					item.value = config_value
