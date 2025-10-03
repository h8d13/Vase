from typing import TYPE_CHECKING

from archinstall.lib.models.authentication import AuthenticationConfiguration

if TYPE_CHECKING:
	from archinstall.lib.installer import Installer

class AuthenticationHandler:
	def setup_auth(
		self,
		install_session: 'Installer',
		auth_config: AuthenticationConfiguration,
		hostname: str,
	) -> None:
		# KDE installer - no U2F setup needed
		pass

auth_handler = AuthenticationHandler()
