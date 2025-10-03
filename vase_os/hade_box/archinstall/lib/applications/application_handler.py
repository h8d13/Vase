from typing import TYPE_CHECKING

from archinstall.applications.audio import AudioApp
from archinstall.applications.bluetooth import BluetoothApp
from archinstall.lib.models.application import ApplicationConfiguration
from archinstall.lib.models.users import User

if TYPE_CHECKING:
	from archinstall.lib.installer import Installer

class ApplicationHandler:
	def __init__(self) -> None:
		pass

	def install_applications(self, install_session: 'Installer', app_config: ApplicationConfiguration | None, users: list['User'] | None = None) -> None:
		# Install bluetooth if enabled (default is disabled)
		if app_config and app_config.bluetooth_config and app_config.bluetooth_config.enabled:
			BluetoothApp().install(install_session)

		# Always install PipeWire (only audio option for KDE)
		from archinstall.lib.models.application import Audio, AudioConfiguration
		AudioApp().install(
			install_session,
			AudioConfiguration(audio=Audio.PIPEWIRE),
			users,
		)

application_handler = ApplicationHandler()
