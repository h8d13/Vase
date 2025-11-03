from typing import TYPE_CHECKING

from archinstall.lib.general import SysCommand
from archinstall.lib.models.authentication import AuthenticationConfiguration
from archinstall.lib.output import info

if TYPE_CHECKING:
	from archinstall.lib.installer import Installer

class AuthenticationHandler:
	def setup_auth(
		self,
		install_session: 'Installer',
		auth_config: AuthenticationConfiguration,
		hostname: str,
	) -> None:
		# Lock root account if requested
		if auth_config.lock_root:
			info('Locking root account')
			SysCommand(f'arch-chroot -S {install_session.target} passwd -l root')

auth_handler = AuthenticationHandler()
