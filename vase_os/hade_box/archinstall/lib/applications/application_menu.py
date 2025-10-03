from typing import override

from archinstall.lib.menu.abstract_menu import AbstractSubMenu
from archinstall.lib.models.application import ApplicationConfiguration, Audio, AudioConfiguration, BluetoothConfiguration
from archinstall.tui.curses_menu import SelectMenu
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties, Orientation

class ApplicationMenu(AbstractSubMenu[ApplicationConfiguration]):
	def __init__(
		self,
		preset: ApplicationConfiguration | None = None,
	):
		if preset:
			self._app_config = preset
		else:
			self._app_config = ApplicationConfiguration()

		menu_optioons = self._define_menu_options()
		self._item_group = MenuItemGroup(menu_optioons, checkmarks=True)

		super().__init__(
			self._item_group,
			config=self._app_config,
			allow_reset=True,
		)

	@override
	def run(self, additional_title: str | None = None) -> ApplicationConfiguration:
		super().run(additional_title=additional_title)
		return self._app_config

	def _define_menu_options(self) -> list[MenuItem]:
		# Bluetooth: disabled by default, show D when disabled, V when enabled
		bluetooth_item = MenuItem(
			text=('Bluetooth'),
			action=select_bluetooth,
			value=self._app_config.bluetooth_config,
			preview_action=self._prev_bluetooth,
			key='bluetooth_config',
		)
		bluetooth_item.default_value = BluetoothConfiguration(enabled=False)
		if bluetooth_item.value is None:
			bluetooth_item.value = bluetooth_item.default_value
			bluetooth_item._value_modified = False
		else:
			# Check if current value matches default
			is_enabled = bluetooth_item.value.enabled
			bluetooth_item._value_modified = is_enabled  # Only modified if enabled
		
		# Audio: always PipeWire, always show D (never modified)
		audio_item = MenuItem(
			text=('Audio'),
			action=select_audio,
			value=self._app_config.audio_config,
			preview_action=self._prev_audio,
			key='audio_config',
		)
		audio_item.default_value = AudioConfiguration(audio=Audio.PIPEWIRE)
		if audio_item.value is None:
			audio_item.value = audio_item.default_value
		audio_item._value_modified = False  # Always show D since only one option
		
		return [bluetooth_item, audio_item]

	def _prev_bluetooth(self, item: MenuItem) -> str | None:
		if item.value is not None:
			bluetooth_config: BluetoothConfiguration = item.value

			output = 'Bluetooth: '
			output += ('Enabled') if bluetooth_config.enabled else ('Disabled')
			return output
		return None

	def _prev_audio(self, item: MenuItem) -> str | None:
		if item.value is not None:
			config: AudioConfiguration = item.value
			return f'Audio: {config.audio.value}'
		return None

def select_bluetooth(preset: BluetoothConfiguration | None) -> BluetoothConfiguration | None:
	group = MenuItemGroup.yes_no()
	group.focus_item = MenuItem.no()

	if preset is not None:
		group.set_selected_by_value(preset.enabled)

	header = ('Would you like to configure Bluetooth?') + '\n'

	result = SelectMenu[bool](
		group,
		header=header,
		alignment=Alignment.CENTER,
		columns=2,
		orientation=Orientation.HORIZONTAL,
		allow_skip=True,
	).run()

	match result.type_:
		case ResultType.Selection:
			enabled = result.item() == MenuItem.yes()
			return BluetoothConfiguration(enabled)
		case ResultType.Skip:
			return preset
		case _:
			raise ValueError('Unhandled result type')

def select_audio(preset: AudioConfiguration | None = None) -> AudioConfiguration | None:
	"""
	KDE installer - PipeWire only
	"""
	# Always return PipeWire configuration for KDE
	return AudioConfiguration(audio=Audio.PIPEWIRE)
