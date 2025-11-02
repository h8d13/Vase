import os
import time
from pathlib import Path

from archinstall import SysInfo
from archinstall.lib.applications.application_handler import application_handler
from archinstall.lib.args import arch_config_handler
from archinstall.lib.authentication.authentication_handler import auth_handler
from archinstall.lib.configuration import ConfigurationOutput
from archinstall.lib.disk.filesystem import FilesystemHandler
from archinstall.lib.disk.utils import disk_layouts
from archinstall.lib.global_menu import GlobalMenu
from archinstall.lib.installer import Installer, accessibility_tools_in_use, run_custom_user_commands
from archinstall.lib.interactions.general_conf import PostInstallationAction, ask_post_installation
from archinstall.lib.models import Bootloader
from archinstall.lib.models.device import (
	DiskLayoutType,
	EncryptionType,
	SnapshotType,
)
from archinstall.lib.models.users import User
from archinstall.lib.general import running_from_iso
from archinstall.lib.output import debug, error, info
from archinstall.lib.profile.profiles_handler import profile_handler
from archinstall.tui import Tui

def _check_for_saved_config() -> None:
	"""Check for saved config and offer to resume"""
	from archinstall.lib.configuration import has_saved_config, load_saved_config
	from archinstall.lib.args import ArchConfig
	from archinstall.tui.curses_menu import SelectMenu
	from archinstall.tui.menu_item import MenuItem, MenuItemGroup
	from archinstall.tui.result import ResultType
	from archinstall.tui.types import Alignment

	if not has_saved_config() or arch_config_handler.args.silent:
		return

	items = [
		MenuItem(text=('Resume from saved selections'), value='resume'),
		MenuItem(text=('Start fresh'), value='fresh'),
	]

	group = MenuItemGroup(items)
	group.focus_item = group.items[0]  # Focus on resume

	result = SelectMenu[str](
		group,
		header=('Saved configuration found in user_configuration.json.') + '\n' + ('What would you like to do?'),
		alignment=Alignment.CENTER,
		allow_skip=False,
	).run()

	if result.type_ == ResultType.Selection:
		choice = result.get_value()

		if choice == 'resume':
			cached_config = load_saved_config()
			if cached_config:
				try:
					new_config = ArchConfig.from_config(cached_config, arch_config_handler.args)
					arch_config_handler._config = new_config
					print('Saved selections loaded successfully')
				except Exception as e:
					print(f'Failed to load saved selections: {e}')
		elif choice == 'fresh':
			# Remove both saved config files
			config_file = Path.cwd() / 'vase_os' / 'hade_box' / 'user_configuration.json'
			creds_file = Path.cwd() / 'vase_os' / 'hade_box' / 'user_credentials.json'

			if config_file.exists():
				config_file.unlink()
			if creds_file.exists():
				creds_file.unlink()

def ask_user_questions() -> None:
	"""
	First, we'll ask the user for a bunch of user input.
	Not until we're satisfied with what we want to install
	will we continue with the actual installation steps.
	"""

	title_text = None
	# Version check removed - custom KDE-only installer

	with Tui():
		# Check for saved config and offer to resume
		_check_for_saved_config()

		global_menu = GlobalMenu(arch_config_handler.config)

		global_menu.set_enabled('parallel_downloads', True)

		global_menu.run(additional_title=title_text)

def perform_installation(mountpoint: Path) -> None:
	"""
	Performs the installation steps on a block device.
	Only requirement is that the block devices are
	formatted and setup prior to entering this function.
	"""
	start_time = time.time()
	checkpoint_time = start_time

	# Display environment detection (visible output)
	from archinstall.lib.output import log
	if running_from_iso():
		log('Running from Arch Linux ISO / USB Medium', fg='yellow')
	else:
		log('Running from a Arch Linux Host System', fg='yellow')

	info('Starting installation...')

	config = arch_config_handler.config

	if not config.disk_config:
		error('No disk configuration provided')
		return

	disk_config = config.disk_config
	run_mkinitcpio = True
	locale_config = config.locale_config
	optional_repositories = config.mirror_config.optional_repositories if config.mirror_config else []
	# mountpoint is already provided as a parameter, no need to get it from disk_config

	with Installer(
		mountpoint,
		disk_config,
		kernels=config.kernels,
	) as installation:
		# Mount all the drives to the desired mountpoint
		installation.mount_ordered_layout()

		installation.sanity_check()

		if mirror_config := config.mirror_config:
			installation.set_mirrors(mirror_config, on_target=False)

		installation.minimal_installation(
			optional_repositories=optional_repositories,
			mkinitcpio=run_mkinitcpio,
			hostname=arch_config_handler.config.hostname,
			locale_config=locale_config,
		)

		if mirror_config := config.mirror_config:
			installation.set_mirrors(mirror_config, on_target=True)

		if config.swap.swap_type != 'none':
			installation.setup_swap(config.swap.swap_type, config.swap.size)

		# Install audio drivers before profile to avoid package conflicts
		if app_config := config.app_config:
			application_handler.install_applications(installation, app_config)

		# Install profile after audio so graphics driver is set before bootloader
		if profile_config := config.profile_config:
			profile_handler.install_profile_config(installation, profile_config)

		if config.bootloader:
			if config.bootloader == Bootloader.Grub and SysInfo.has_uefi():
				installation.add_additional_packages('grub')

			installation.add_bootloader(config.bootloader, config.grub_config, config.uki_enabled)

		# If user selected to copy the current ISO network configuration
		# Perform a copy of the config
		network_config = config.network_config

		if network_config:
			network_config.install_network_config(
				installation,
				config.profile_config,
			)

		if config.auth_config:
			if config.auth_config.users:
				installation.create_users(config.auth_config.users)
				auth_handler.setup_auth(installation, config.auth_config, config.hostname)

		mandatory_package = ['git']
		installation.add_additional_packages(mandatory_package)

		if timezone := config.timezone:
			installation.set_timezone(timezone)

		if config.ntp:
			installation.activate_time_synchronization()

		if accessibility_tools_in_use():
			installation.enable_espeakup()

		if config.auth_config and config.auth_config.root_enc_password:
			root_user = User('root', config.auth_config.root_enc_password, False)
			installation.set_user_password(root_user)

		if (profile_config := config.profile_config) and profile_config.profile:
			profile_config.profile.post_install(installation)

		# If the user provided a list of services to be enabled, pass the list to the enable_service function.
		# Note that while it's called enable_service, it can actually take a list of services and iterate it.
		if servies := config.services:
			installation.enable_service(servies)

		if disk_config.has_default_btrfs_vols():
			btrfs_options = disk_config.btrfs_options
			snapshot_config = btrfs_options.snapshot_config if btrfs_options else None
			snapshot_type = snapshot_config.snapshot_type if snapshot_config else None
			if snapshot_type and snapshot_type != SnapshotType.NoSnapshots:
				installation.setup_btrfs_snapshot(snapshot_type, config.bootloader)

		# If the user provided custom commands to be run post-installation, execute them now.
		if cc := config.custom_commands:
			run_custom_user_commands(cc, installation)

		# Apply removable media optimizations if enabled
		if config.removable_media:
			installation.apply_removable_media_optimizations()

		installation.genfstab()

		debug(f'Disk states after installing:\n{disk_layouts()}')

		# Calculate installation time
		elapsed_time = time.time() - start_time

		if not arch_config_handler.args.silent:
			with Tui():
				action = ask_post_installation(elapsed_time)

			match action:
				case PostInstallationAction.EXIT:
					pass
				case PostInstallationAction.REBOOT:
					os.system('reboot')
				case PostInstallationAction.CHROOT:
					try:
						installation.drop_to_shell()
					except Exception:
						pass

def guided() -> None:
	if not arch_config_handler.args.silent:
		ask_user_questions()

	# Store pandora script path for later (will be copied to target during installation)
	import os
	if pandora_script := os.environ.get('PANDORA_SCRIPT'):
		arch_config_handler.config.pandora_script = pandora_script

	config = ConfigurationOutput(arch_config_handler.config)
	config.write_debug()

	if arch_config_handler.args.dry_run:
		exit(0)

	if not arch_config_handler.args.silent:
		aborted = False
		with Tui():
			if not config.confirm_config():
				debug('Installation aborted')
				aborted = True

		if aborted:
			return guided()

	if arch_config_handler.config.disk_config:
		fs_handler = FilesystemHandler(arch_config_handler.config.disk_config)
		fs_handler.perform_filesystem_operations()

	perform_installation(arch_config_handler.args.mountpoint)

guided()
