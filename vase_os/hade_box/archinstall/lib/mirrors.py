import time
import urllib.parse
from pathlib import Path
from typing import override

from archinstall.tui.curses_menu import EditMenu, SelectMenu, Tui
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties

from .general import SysCommand
from .menu.abstract_menu import AbstractSubMenu
from .menu.list_manager import ListManager
from .models.mirrors import (
	CustomRepository,
	CustomServer,
	MirrorConfiguration,
	MirrorRegion,
	MirrorStatusEntryV3,
	MirrorStatusListV3,
	SignCheck,
	SignOption,
)
from .models.packages import Repository
from .networking import fetch_data_from_url
from .output import FormattedOutput, debug

class CustomMirrorRepositoriesList(ListManager[CustomRepository]):
	def __init__(self, custom_repositories: list[CustomRepository]):
		self._actions = [
			('Add a custom repository'),
			('Change custom repository'),
			('Delete custom repository'),
		]

		super().__init__(
			custom_repositories,
			[self._actions[0]],
			self._actions[1:],
			'',
		)

	@override
	def selected_action_display(self, selection: CustomRepository) -> str:
		return selection.name

	@override
	def handle_action(
		self,
		action: str,
		entry: CustomRepository | None,
		data: list[CustomRepository],
	) -> list[CustomRepository]:
		if action == self._actions[0]:  # add
			new_repo = self._add_custom_repository()
			if new_repo is not None:
				data = [d for d in data if d.name != new_repo.name]
				data += [new_repo]
		elif action == self._actions[1] and entry:  # modify repo
			new_repo = self._add_custom_repository(entry)
			if new_repo is not None:
				data = [d for d in data if d.name != entry.name]
				data += [new_repo]
		elif action == self._actions[2] and entry:  # delete
			data = [d for d in data if d != entry]

		return data

	def _add_custom_repository(self, preset: CustomRepository | None = None) -> CustomRepository | None:
		edit_result = EditMenu(
			('Repository name'),
			alignment=Alignment.CENTER,
			allow_skip=True,
			default_text=preset.name if preset else None,
		).input()

		match edit_result.type_:
			case ResultType.Selection:
				name = edit_result.text()
			case ResultType.Skip:
				return preset
			case _:
				raise ValueError('Unhandled return type')

		header = f'("Name"): {name}'

		edit_result = EditMenu(
			('Url'),
			header=header,
			alignment=Alignment.CENTER,
			allow_skip=True,
			default_text=preset.url if preset else None,
		).input()

		match edit_result.type_:
			case ResultType.Selection:
				url = edit_result.text()
			case ResultType.Skip:
				return preset
			case _:
				raise ValueError('Unhandled return type')

		header += f'\n("Url"): {url}\n'
		prompt = f'{header}\n' + ('Select signature check')

		sign_chk_items = [MenuItem(s.value, value=s.value) for s in SignCheck]
		group = MenuItemGroup(sign_chk_items, sort_items=False)

		if preset is not None:
			group.set_selected_by_value(preset.sign_check.value)

		result = SelectMenu[SignCheck](
			group,
			header=prompt,
			alignment=Alignment.CENTER,
			allow_skip=False,
		).run()

		match result.type_:
			case ResultType.Selection:
				sign_check = SignCheck(result.get_value())
			case _:
				raise ValueError('Unhandled return type')

		header += f'("Signature check"): {sign_check.value}\n'
		prompt = f'{header}\n' + ('Select signature option')

		sign_opt_items = [MenuItem(s.value, value=s.value) for s in SignOption]
		group = MenuItemGroup(sign_opt_items, sort_items=False)

		if preset is not None:
			group.set_selected_by_value(preset.sign_option.value)

		result = SelectMenu(
			group,
			header=prompt,
			alignment=Alignment.CENTER,
			allow_skip=False,
		).run()

		match result.type_:
			case ResultType.Selection:
				sign_opt = SignOption(result.get_value())
			case _:
				raise ValueError('Unhandled return type')

		return CustomRepository(name, url, sign_check, sign_opt)

class CustomMirrorServersList(ListManager[CustomServer]):
	def __init__(self, custom_servers: list[CustomServer]):
		self._actions = [
			('Add a custom server'),
			('Change custom server'),
			('Delete custom server'),
		]

		super().__init__(
			custom_servers,
			[self._actions[0]],
			self._actions[1:],
			'',
		)

	@override
	def selected_action_display(self, selection: CustomServer) -> str:
		return selection.url

	@override
	def handle_action(
		self,
		action: str,
		entry: CustomServer | None,
		data: list[CustomServer],
	) -> list[CustomServer]:
		if action == self._actions[0]:  # add
			new_server = self._add_custom_server()
			if new_server is not None:
				data = [d for d in data if d.url != new_server.url]
				data += [new_server]
		elif action == self._actions[1] and entry:  # modify repo
			new_server = self._add_custom_server(entry)
			if new_server is not None:
				data = [d for d in data if d.url != entry.url]
				data += [new_server]
		elif action == self._actions[2] and entry:  # delete
			data = [d for d in data if d != entry]

		return data

	def _add_custom_server(self, preset: CustomServer | None = None) -> CustomServer | None:
		edit_result = EditMenu(
			('Server url'),
			alignment=Alignment.CENTER,
			allow_skip=True,
			default_text=preset.url if preset else None,
		).input()

		match edit_result.type_:
			case ResultType.Selection:
				uri = edit_result.text()
				return CustomServer(uri)
			case ResultType.Skip:
				return preset

		return None

class MirrorMenu(AbstractSubMenu[MirrorConfiguration]):
	def __init__(
		self,
		preset: MirrorConfiguration | None = None,
	):
		if preset:
			self._mirror_config = preset
		else:
			self._mirror_config = MirrorConfiguration()

		menu_optioons = self._define_menu_options()
		self._item_group = MenuItemGroup(menu_optioons, checkmarks=True)

		super().__init__(
			self._item_group,
			config=self._mirror_config,
			allow_reset=True,
		)

	def _define_menu_options(self) -> list[MenuItem]:
		return [
			MenuItem(
				text=('Reflector status'),
				action=lambda preset: preset,
				preview_action=self._prev_reflector_status,
			),
			MenuItem(
				text=('Mirror configuration'),
				action=configure_mirrors,
				value=self._mirror_config.mirror_regions,
				preview_action=self._prev_regions,
				key='mirror_regions',
			),
			MenuItem(
				text=('Optional repositories'),
				action=select_optional_repositories,
				value=[],
				preview_action=self._prev_additional_repos,
				key='optional_repositories',
			),
			MenuItem(
				text=('Add custom servers'),
				action=add_custom_mirror_servers,
				value=self._mirror_config.custom_servers,
				preview_action=self._prev_custom_servers,
				key='custom_servers',
			),
			MenuItem(
				text=('Add custom repository'),
				action=select_custom_mirror,
				value=self._mirror_config.custom_repositories,
				preview_action=self._prev_custom_mirror,
				key='custom_repositories',
			),
		]

	def _check_reflector_status(self) -> str:
		from .exceptions import SysCallError
		try:
			result = SysCommand('systemctl is-active reflector.service', environment_vars={'SYSTEMD_COLORS': '0'})
			status = result.decode().strip()
		except SysCallError as e:
			# systemctl is-active returns non-zero for inactive/failed services
			# but still outputs the status, so we can extract it
			status = str(e).split('\n')[0] if str(e) else 'unknown'
			# Try to extract from the exception output
			if 'inactive' in str(e).lower():
				status = 'inactive'
			elif 'failed' in str(e).lower():
				status = 'failed'
			elif 'activating' in str(e).lower():
				status = 'activating'
		except Exception:
			return 'N/A'

		if status in ['active', 'activating']:
			return 'Running...'
		elif status == 'inactive':
			return 'Done.'
		elif status in ['dead', 'failed']:
			return f'Error ({status})'
		else:
			return f'Status: {status}'

	def _prev_reflector_status(self, item: MenuItem) -> str:
		return self._check_reflector_status()

	def _prev_regions(self, item: MenuItem) -> str:
		regions = item.get_value()

		if not regions:
			return 'No regions selected'

		# After editing, show what's actually in the temp mirrorlist
		try:
			mirrorlist_path = mirror_list_handler._local_mirrorlist
			if mirrorlist_path.exists():
				with mirrorlist_path.open('r') as f:
					content = f.read()

				# Check if temp file has content for selected regions
				has_content = any(f'## {region.name}' in content for region in regions)
				if has_content:
					# Show actual temp mirrorlist content (reflects edits)
					lines = content.strip().split('\n')
					output = ''
					for line in lines:
						if line.startswith('## '):
							region_name = line.replace('## ', '')
							# Only show if it's one of the selected regions
							if any(r.name == region_name for r in regions):
								output += f'{region_name}\n'
						elif line.startswith('Server = '):
							url = line.replace('Server = ', '')
							output += f' - {url}\n'
						elif line == '':
							output += '\n'
					return output.strip()
		except Exception:
			pass

		# Fallback: show from region objects
		output = ''
		for region in regions:
			output += f'{region.name}\n'
			for url in region.urls:
				output += f' - {url}\n'
			output += '\n'

		return output

	def _prev_additional_repos(self, item: MenuItem) -> str | None:
		if item.value:
			repositories: list[Repository] = item.value
			repos = ', '.join([repo.value for repo in repositories])
			return f'Additional repositories: {repos}'
		return None

	def _prev_custom_mirror(self, item: MenuItem) -> str | None:
		if not item.value:
			return None

		custom_mirrors: list[CustomRepository] = item.value
		output = FormattedOutput.as_table(custom_mirrors)
		return output.strip()

	def _prev_custom_servers(self, item: MenuItem) -> str | None:
		if not item.value:
			return None

		custom_servers: list[CustomServer] = item.value
		output = '\n'.join([server.url for server in custom_servers])
		return output.strip()

	@override
	def run(self, additional_title: str | None = None) -> MirrorConfiguration:
		super().run(additional_title=additional_title)
		return self._mirror_config

def configure_mirrors(preset: list[MirrorRegion]) -> list[MirrorRegion]:
	"""Main mirror configuration - choose between system mirrorlist or manual selection"""
	from .args import arch_config_handler

	# First, ask user how they want to configure mirrors
	items = [
		MenuItem('Use system mirrorlist (automatic/reflector)', value='system'),
		MenuItem('Manual region selection', value='manual'),
	]
	group = MenuItemGroup(items, sort_items=False)

	result = SelectMenu[str](
		group,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Mirror configuration method'),
		allow_skip=True,
	).run()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Selection:
			choice = result.get_value()

			if choice == 'system':
				# Use system mirrorlist - force reload from global
				mirror_list_handler._status_mappings = None  # Clear cached mappings

				system_mirrorlist = Path('/etc/pacman.d/mirrorlist')
				if not system_mirrorlist.exists():
					if not arch_config_handler.args.silent:
						Tui.print('System mirrorlist not found, falling back to manual selection')
						input('\nPress ENTER to continue...')
					return select_mirror_regions(preset)

				temp_mirrorlist = mirror_list_handler._local_mirrorlist

				# Check if they're the same file
				if system_mirrorlist.resolve() != temp_mirrorlist.resolve():
					import shutil
					shutil.copy(system_mirrorlist, temp_mirrorlist)

				# Reload handler to parse the system mirrorlist
				mirror_list_handler.load_local_mirrors()

				# Return regions parsed from system mirrorlist
				return mirror_list_handler.get_mirror_regions()

			elif choice == 'manual':
				# Manual region selection
				return select_mirror_regions(preset)

	return preset

def select_mirror_regions(preset: list[MirrorRegion]) -> list[MirrorRegion]:
	from .args import arch_config_handler
	from .output import info

	# Only load mirrors if not already loaded
	if mirror_list_handler._status_mappings is None:
		if arch_config_handler.args.offline:
			Tui.print('Loading mirror regions (offline mode)...', clear_screen=True)
		else:
			Tui.print('Loading mirror regions (fetching from archlinux.org, may timeout and fallback to local)...', clear_screen=True)
		mirror_list_handler.load_mirrors()

	available_regions = mirror_list_handler.get_mirror_regions()

	if not available_regions:
		return []

	# Check if we fell back to local mirrors (couldn't fetch remote)
	fell_back_to_local = not mirror_list_handler._fetched_remote

	preset_regions = [region for region in available_regions if region in preset]

	items = [MenuItem(region.name, value=region) for region in available_regions]
	group = MenuItemGroup(items, sort_items=True)

	group.set_selected_by_value(preset_regions)

	result = SelectMenu[MirrorRegion](
		group,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Mirror regions'),
		allow_reset=True,
		allow_skip=True,
		multi=True,
	).run()

	selected_regions: list[MirrorRegion] = []

	match result.type_:
		case ResultType.Skip:
			selected_regions = preset_regions
		case ResultType.Reset:
			selected_regions = []
		case ResultType.Selection:
			selected_regions = result.get_values()

	# After region selection, offer to edit/filter mirrors for selected regions
	if selected_regions and not arch_config_handler.args.silent:
		result = SelectMenu(
			MenuItemGroup([
				MenuItem('Filter/reorder mirrors for selected regions', value='edit'),
				MenuItem('Use selected regions as-is', value='continue'),
			], sort_items=False),
			alignment=Alignment.CENTER,
			allow_skip=False,
		).run()

		if result.type_ == ResultType.Selection:
			choice = result.get_value()

			if choice == 'edit':
				# Edit only mirrors from selected regions
				edited_regions = edit_mirrorlist_for_regions(selected_regions)
				if edited_regions:
					selected_regions = edited_regions
			elif choice == 'continue':
				# Write full mirrorlist from selected regions to temp file
				_write_mirrorlist_from_regions(selected_regions)

			# Reload after any changes
			mirror_list_handler.load_local_mirrors()

	return selected_regions

def add_custom_mirror_servers(preset: list[CustomServer] = []) -> list[CustomServer]:
	custom_mirrors = CustomMirrorServersList(preset).run()
	return custom_mirrors

def select_custom_mirror(preset: list[CustomRepository] = []) -> list[CustomRepository]:
	custom_mirrors = CustomMirrorRepositoriesList(preset).run()
	return custom_mirrors

def _write_mirrorlist_from_regions(regions: list[MirrorRegion]) -> None:
	"""Write full mirrorlist from selected regions to temp file"""
	mirrorlist_path = mirror_list_handler._local_mirrorlist

	with mirrorlist_path.open('w') as f:
		for region in regions:
			f.write(f'## {region.name}\n')
			for mirror in region.urls:
				f.write(f'Server = {mirror}\n')
			f.write('\n')

def edit_mirrorlist_for_regions(regions: list[MirrorRegion]) -> list[MirrorRegion] | None:
	"""Edit mirrorlist for specific regions only, returns updated regions with edited mirrors"""
	# Extract mirrors from selected regions
	mirrors = []
	for region in regions:
		mirrors.extend(region.urls)

	if not mirrors:
		Tui.print('No mirrors found in selected regions')
		return None

	edited_mirrors = _edit_mirrors(mirrors, regions)

	# If mirrors were edited, rebuild regions with new mirror list
	if edited_mirrors:
		# Create updated regions with new mirror URLs
		updated_regions = []
		for region in regions:
			# Filter edited mirrors that belong to this region
			region_mirrors = [m for m in edited_mirrors if m in region.urls]
			if region_mirrors:
				# Create new region with updated URLs
				updated_region = MirrorRegion(region.name, region_mirrors)
				updated_regions.append(updated_region)
		return updated_regions

	return None

def edit_mirrorlist(preset: None = None) -> None:
	"""Interactive mirrorlist editor to reorder and filter mirrors

	Uses mirrors from selected regions if available, otherwise from temp mirrorlist
	"""
	from .args import arch_config_handler

	# Get selected regions from config
	config = arch_config_handler.config
	selected_regions = config.mirror_config.mirror_regions if config.mirror_config else []

	if selected_regions:
		# Use mirrors from selected regions
		mirrors = []
		for region in selected_regions:
			mirrors.extend(region.urls)

		if not mirrors:
			Tui.print('No mirrors found in selected regions')
			return None

		_edit_mirrors(mirrors, selected_regions)
	else:
		# Fallback to reading temp mirrorlist
		mirrorlist_path = mirror_list_handler._local_mirrorlist

		with mirrorlist_path.open('r') as f:
			lines = f.readlines()

		# Extract active mirrors (uncommented Server lines)
		mirrors = []
		for line in lines:
			if line.strip().startswith('Server = '):
				url = line.strip().replace('Server = ', '')
				mirrors.append(url)

		if not mirrors:
			Tui.print('No mirrors found in mirrorlist')
			return None

		_edit_mirrors(mirrors, None)

	return None

def _edit_mirrors(mirrors: list[str], regions: list[MirrorRegion] | None = None) -> list[str] | None:
	"""Core mirror editing logic - filters and reorders given list of mirrors, returns final list"""
	mirrorlist_path = mirror_list_handler._local_mirrorlist

	# Loop to allow multiple operations
	while True:
		items = [
			MenuItem('Keep only HTTPS mirrors', value='https_only'),
			MenuItem('Reorder mirrors interactively', value='reorder'),
			MenuItem('Preview current selection', value='preview'),
			MenuItem('Done - save and continue', value='done'),
		]

		result = SelectMenu(
			MenuItemGroup(items, sort_items=False),
			header=f'Mirror editing ({len(mirrors)} mirrors)',
			alignment=Alignment.CENTER,
			allow_skip=False,
		).run()

		if result.type_ == ResultType.Selection:
			choice = result.get_value()

			if choice == 'https_only':
				# Filter to HTTPS only
				https_mirrors = [m for m in mirrors if m.startswith('https://')]
				if https_mirrors:
					mirrors = https_mirrors
					Tui.print(f'Filtered to {len(mirrors)} HTTPS mirrors')
				else:
					Tui.print('No HTTPS mirrors found, keeping all')

			elif choice == 'reorder':
				# Interactive mirror reordering
				mirror_items = [MenuItem(url, value=url) for url in mirrors]
				group = MenuItemGroup(mirror_items, sort_items=False)

				result = SelectMenu(
					group,
					header='Select mirrors (SPACEBAR). First selected = highest priority! ESC to cancel.',
					alignment=Alignment.CENTER,
					allow_reset=False,
					allow_skip=True,
					multi=True,
				).run()

				if result.type_ == ResultType.Selection:
					selected_mirrors = result.get_values()
					if selected_mirrors:
						mirrors = selected_mirrors

			elif choice == 'preview':
				# Show current mirror selection
				preview_text = f'Current mirror selection ({len(mirrors)} mirrors):\n\n'
				for idx, mirror in enumerate(mirrors, 1):
					preview_text += f'{idx}. {mirror}\n'
				Tui.print(preview_text)
				input('\nPress ENTER to continue...')

			elif choice == 'done':
				# Write final mirrorlist with region structure preserved
				with mirrorlist_path.open('w') as f:
					if regions:
						# Write mirrors grouped by region
						for region in regions:
							region_mirrors = [m for m in mirrors if m in region.urls]
							if region_mirrors:
								f.write(f'## {region.name}\n')
								for mirror in region_mirrors:
									f.write(f'Server = {mirror}\n')
								f.write('\n')
					else:
						# No region structure, write flat list
						f.write('# Custom mirrorlist\n')
						for mirror in mirrors:
							f.write(f'Server = {mirror}\n')
				return mirrors  # Return edited mirrors

def select_optional_repositories(preset: list[Repository]) -> list[Repository]:
	"""
	Allows the user to select additional repositories (multilib, and testing) if desired.

	:return: The string as a selected repository
	:rtype: Repository
	"""

	repositories = [Repository.Multilib, Repository.Testing]
	items = [MenuItem(r.value, value=r) for r in repositories]
	group = MenuItemGroup(items, sort_items=True)
	group.set_selected_by_value(preset)

	result = SelectMenu[Repository](
		group,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Additional repositories'),
		allow_reset=True,
		allow_skip=True,
		multi=True,
	).run()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Reset:
			return []
		case ResultType.Selection:
			return result.get_values()

class MirrorListHandler:
	def __init__(
		self,
		local_mirrorlist: Path = Path('/etc/pacman.d/mirrorlist'),
	) -> None:
		from .general import running_from_iso

		# Check if running from ISO or host system
		self._running_from_iso = running_from_iso()

		# If running from host, use temp copy to avoid modifying host's mirrorlist
		if not self._running_from_iso:
			import shutil
			self._temp_mirrorlist = Path('/tmp/archinstall_mirrorlist')
			shutil.copy(local_mirrorlist, self._temp_mirrorlist)
			self._local_mirrorlist = self._temp_mirrorlist
		else:
			self._local_mirrorlist = local_mirrorlist

		self._status_mappings: dict[str, list[MirrorStatusEntryV3]] | None = None
		self._fetched_remote = False

	def _mappings(self) -> dict[str, list[MirrorStatusEntryV3]]:
		if self._status_mappings is None:
			self.load_mirrors()

		assert self._status_mappings is not None
		return self._status_mappings

	def get_mirror_regions(self) -> list[MirrorRegion]:
		available_mirrors = []
		mappings = self._mappings()

		for region_name, status_entry in mappings.items():
			urls = [entry.server_url for entry in status_entry]
			region = MirrorRegion(region_name, urls)
			available_mirrors.append(region)

		return available_mirrors

	def load_mirrors(self) -> None:
		from .args import arch_config_handler

		if arch_config_handler.args.offline:
			self._fetched_remote = False
			self.load_local_mirrors()
		else:
			self._fetched_remote = self.load_remote_mirrors()
			if not self._fetched_remote:
				self.load_local_mirrors()

	def load_remote_mirrors(self) -> bool:
		url = 'https://archlinux.org/mirrors/status/json/'
		attempts = 3

		for attempt_nr in range(attempts):
			try:
				mirrorlist = fetch_data_from_url(url)
				self._status_mappings = self._parse_remote_mirror_list(mirrorlist)
				return True
			except Exception as e:
				debug(f'Error while fetching mirror list: {e}')
				time.sleep(attempt_nr + 1)

		debug('Unable to fetch mirror list remotely, falling back to local mirror list')
		return False

	def load_local_mirrors(self) -> None:
		with self._local_mirrorlist.open('r') as fp:
			mirrorlist = fp.read()
			self._status_mappings = self._parse_locale_mirrors(mirrorlist)

	def get_status_by_region(self, region: str, speed_sort: bool) -> list[MirrorStatusEntryV3]:
		mappings = self._mappings()
		region_list = mappings[region]
		# Filter out mirrors where speed test failed (speed == 0)
		working_mirrors = [mirror for mirror in region_list if mirror.speed > 0]
		return sorted(working_mirrors, key=lambda mirror: (mirror.score, mirror.speed))

	def _parse_remote_mirror_list(self, mirrorlist: str) -> dict[str, list[MirrorStatusEntryV3]]:
		mirror_status = MirrorStatusListV3.model_validate_json(mirrorlist)

		sorting_placeholder: dict[str, list[MirrorStatusEntryV3]] = {}

		for mirror in mirror_status.urls:
			# We filter out mirrors that have bad criteria values
			if any(
				[
					mirror.active is False,  # Disabled by mirror-list admins
					mirror.last_sync is None,  # Has not synced recently
					# mirror.score (error rate) over time reported from backend:
					# https://github.com/archlinux/archweb/blob/31333d3516c91db9a2f2d12260bd61656c011fd1/mirrors/utils.py#L111C22-L111C66
					(mirror.score is None or mirror.score >= 100),
				]
			):
				continue

			if mirror.country == '':
				# TODO: This should be removed once RFC!29 is merged and completed
				# Until then, there are mirrors which lacks data in the backend
				# and there is no way of knowing where they're located.
				# So we have to assume world-wide
				mirror.country = 'Worldwide'

			if mirror.url.startswith('http'):
				sorting_placeholder.setdefault(mirror.country, []).append(mirror)

		sorted_by_regions: dict[str, list[MirrorStatusEntryV3]] = dict(
			{region: unsorted_mirrors for region, unsorted_mirrors in sorted(sorting_placeholder.items(), key=lambda item: item[0])}
		)

		return sorted_by_regions

	def _parse_locale_mirrors(self, mirrorlist: str) -> dict[str, list[MirrorStatusEntryV3]]:
		lines = mirrorlist.splitlines()

		# remove empty lines
		# lines = [line for line in lines if line]

		mirror_list: dict[str, list[MirrorStatusEntryV3]] = {}

		current_region = ''

		for line in lines:
			line = line.strip()

			if line.startswith('## '):
				current_region = line.replace('## ', '').strip()
				mirror_list.setdefault(current_region, [])

			if line.startswith('Server = '):
				if not current_region:
					current_region = 'Local'
					mirror_list.setdefault(current_region, [])

				url = line.removeprefix('Server = ')

				mirror_entry = MirrorStatusEntryV3(
					url=url.removesuffix('$repo/os/$arch'),
					protocol=urllib.parse.urlparse(url).scheme,
					active=True,
					country=current_region or 'Worldwide',
					# The following values are normally populated by
					# archlinux.org mirror-list endpoint, and can't be known
					# from just the local mirror-list file.
					country_code='WW',
					isos=True,
					ipv4=True,
					ipv6=True,
					details='Locally defined mirror',
				)

				mirror_list[current_region].append(mirror_entry)

		return mirror_list

mirror_list_handler = MirrorListHandler()
