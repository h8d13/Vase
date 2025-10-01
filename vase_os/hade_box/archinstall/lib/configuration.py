import json
import readline
import stat
from pathlib import Path

from archinstall.tui.curses_menu import SelectMenu, Tui
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties, Orientation, PreviewStyle

from .args import ArchConfig
from .crypt import encrypt
from .general import JSON, UNSAFE_JSON
from .output import debug, logger, warn
from .utils.util import get_password, prompt_dir


class ConfigurationOutput:
	def __init__(self, config: ArchConfig):
		"""
		Configuration output handler to parse the existing
		configuration data structure and prepare for output on the
		console and for saving it to configuration files

		:param config: Archinstall configuration object
		:type config: ArchConfig
		"""

		self._config = config
		self._default_save_path = logger.directory
		self._user_config_file = Path('vase_os/hade_box/user_configuration.json')
		self._user_creds_file = Path('vase_os/hade_box/user_credentials.json')

	@property
	def user_configuration_file(self) -> Path:
		return self._user_config_file

	@property
	def user_credentials_file(self) -> Path:
		return self._user_creds_file

	def user_config_to_json(self) -> str:
		out = self._config.safe_json()
		return json.dumps(out, indent=4, sort_keys=True, cls=JSON)

	def user_credentials_to_json(self) -> str:
		out = self._config.unsafe_json()
		return json.dumps(out, indent=4, sort_keys=True, cls=UNSAFE_JSON)

	def write_debug(self) -> None:
		debug(' -- Chosen configuration --')
		debug(self.user_config_to_json())

	def confirm_config(self) -> bool:
		header = f'The specified configuration will be applied. WILL ERASE DATA ON DISK depending on how you set up.\n'
		header += 'Would you like to continue?'

		with Tui():
			group = MenuItemGroup.yes_no()
			group.focus_item = MenuItem.yes()
			group.set_preview_for_all(lambda x: self.user_config_to_json())

			result = SelectMenu[bool](
				group,
				header=header,
				alignment=Alignment.CENTER,
				columns=2,
				orientation=Orientation.HORIZONTAL,
				allow_skip=False,
				preview_size='auto',
				preview_style=PreviewStyle.BOTTOM,
				preview_frame=FrameProperties.max('Configuration'),
			).run()

			if result.item() != MenuItem.yes():
				return False

		return True

	def _is_valid_path(self, dest_path: Path) -> bool:
		dest_path_ok = dest_path.exists() and dest_path.is_dir()
		if not dest_path_ok:
			warn(
				f'Destination directory {dest_path.resolve()} does not exist or is not a directory\n.',
				'Configuration files can not be saved',
			)
		return dest_path_ok

	def save_user_config(self, dest_path: Path) -> None:
		if self._is_valid_path(dest_path):
			target = dest_path / self._user_config_file
			target.write_text(self.user_config_to_json())
			target.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

	def save_user_creds(
		self,
		dest_path: Path,
		password: str | None = None,
	) -> None:
		data = self.user_credentials_to_json()

		if password:
			data = encrypt(password, data)

		if self._is_valid_path(dest_path):
			target = dest_path / self._user_creds_file
			target.write_text(data)
			target.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

	def save(
		self,
		dest_path: Path | None = None,
		creds: bool = False,
		password: str | None = None,
	) -> None:
		save_path = dest_path or self._default_save_path

		if self._is_valid_path(save_path):
			self.save_user_config(save_path)
			if creds:
				self.save_user_creds(save_path, password=password)


def save_config(config: ArchConfig) -> None:
	def preview(item: MenuItem) -> str | None:
		match item.value:
			case 'user_config':
				serialized = config_output.user_config_to_json()
				return f'{config_output.user_configuration_file}\n{serialized}'
			case 'user_creds':
				if maybe_serial := config_output.user_credentials_to_json():
					return f'{config_output.user_credentials_file}\n{maybe_serial}'
				return ('No configuration')
			case 'all':
				output = [str(config_output.user_configuration_file)]
				config_output.user_credentials_to_json()
				output.append(str(config_output.user_credentials_file))
				return '\n'.join(output)
		return None

	config_output = ConfigurationOutput(config)

	items = [
		MenuItem(
			('Save user configuration (including disk layout)'),
			value='user_config',
			preview_action=preview,
		),
		MenuItem(
			('Save user credentials'),
			value='user_creds',
			preview_action=preview,
		),
		MenuItem(
			('Save all'),
			value='all',
			preview_action=preview,
		),
	]

	group = MenuItemGroup(items)
	result = SelectMenu[str](
		group,
		allow_skip=True,
		preview_frame=FrameProperties.max('Configuration'),
		preview_size='auto',
		preview_style=PreviewStyle.RIGHT,
	).run()

	match result.type_:
		case ResultType.Skip:
			return
		case ResultType.Selection:
			save_option = result.get_value()
		case _:
			raise ValueError('Unhandled return type')

	readline.set_completer_delims('\t\n=')
	readline.parse_and_bind('tab: complete')

	dest_path = prompt_dir(
		('Directory'),
		('Enter a directory for the configuration(s) to be saved (tab completion enabled)') + '\n',
		allow_skip=True,
	)

	if not dest_path:
		return

	header = ('Do you want to save the configuration file(s) to {}?').format(dest_path)

	group = MenuItemGroup.yes_no()
	group.focus_item = MenuItem.yes()

	result = SelectMenu(
		group,
		header=header,
		allow_skip=False,
		alignment=Alignment.CENTER,
		columns=2,
		orientation=Orientation.HORIZONTAL,
	).run()

	match result.type_:
		case ResultType.Selection:
			if result.item() == MenuItem.no():
				return

	debug(f'Saving configuration files to {dest_path.absolute()}')

	header = ('Do you want to encrypt the user_credentials.json file?')

	group = MenuItemGroup.yes_no()
	group.focus_item = MenuItem.no()

	result = SelectMenu(
		group,
		header=header,
		allow_skip=False,
		alignment=Alignment.CENTER,
		columns=2,
		orientation=Orientation.HORIZONTAL,
	).run()

	enc_password: str | None = None
	match result.type_:
		case ResultType.Selection:
			if result.item() == MenuItem.yes():
				password = get_password(
					text=('Credentials file encryption password'),
					allow_skip=True,
				)

				if password:
					enc_password = password.plaintext

	match save_option:
		case 'user_config':
			config_output.save_user_config(dest_path)
		case 'user_creds':
			config_output.save_user_creds(dest_path, password=enc_password)
		case 'all':
			config_output.save(dest_path, creds=True, password=enc_password)


def _get_hade_box_path() -> Path | None:
	"""Find and return the hade_box root directory"""
	current_path = Path(__file__).resolve()
	while current_path.parent != current_path:
		if (current_path / 'vase_os' / 'hade_box').exists():
			return current_path / 'vase_os' / 'hade_box'
		if current_path.name == 'hade_box':
			return current_path
		current_path = current_path.parent
	return None


def auto_save_config(config: ArchConfig) -> tuple[bool, list[str]]:
	"""Auto-save config and credentials to hade_box folder without prompting
	Returns: (success, list of saved files)
	"""
	try:
		config_output = ConfigurationOutput(config)
		hade_box_path = _get_hade_box_path() or Path.cwd()
		saved_files = []

		# Always save user config
		config_output.save_user_config(hade_box_path)
		saved_files.append('user_configuration.json')

		# Only save credentials if there are any (not just empty JSON)
		creds_json = config_output.user_credentials_to_json()
		if creds_json and creds_json.strip() != '{}':
			config_output.save_user_creds(hade_box_path, password=None)
			saved_files.append('user_credentials.json')

		return True, saved_files
	except Exception as e:
		print(f'Failed to auto-save config: {e}')
		return False, []


def has_saved_config() -> bool:
	"""Check if there's a saved config in hade_box folder"""
	hade_box_path = _get_hade_box_path()
	if not hade_box_path:
		return False
	config_file = hade_box_path / 'user_configuration.json'
	return config_file.exists()


def load_saved_config() -> dict | None:
	"""Load saved config and credentials from hade_box folder"""
	try:
		hade_box_path = _get_hade_box_path()
		if not hade_box_path:
			return None

		config_data = {}

		# Load main config
		config_file = hade_box_path / 'user_configuration.json'
		if config_file.exists():
			with open(config_file, 'r') as f:
				config_data.update(json.load(f))

		# Load credentials if they exist (follows same pattern as args.py)
		creds_file = hade_box_path / 'user_credentials.json'
		if creds_file.exists():
			with open(creds_file, 'r') as f:
				creds_data = json.load(f)
				config_data.update(creds_data)

		return config_data if config_data else None

	except Exception as e:
		print(f'Failed to load saved config: {e}')
	return None
