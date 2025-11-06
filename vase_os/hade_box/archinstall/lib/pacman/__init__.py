import time
from collections.abc import Callable
from pathlib import Path

from ..exceptions import RequirementError
from ..general import SysCommand
from ..output import error, info, warn
from .config import PacmanConfig

class Pacman:
	def __init__(self, target: Path, silent: bool = False):
		self.synced = False
		self.silent = silent
		self.target = target

	@staticmethod
	def run(args: str, default_cmd: str = 'pacman') -> SysCommand:
		"""
		A centralized function to call `pacman` from.
		It also protects us from colliding with other running pacman sessions (if used locally).
		The grace period is set to 10 minutes before exiting hard if another pacman instance is running.
		"""
		pacman_db_lock = Path('/var/lib/pacman/db.lck')

		if pacman_db_lock.exists():
			warn('Pacman is already running, waiting maximum 10 minutes for it to terminate.')

		started = time.time()
		while pacman_db_lock.exists():
			time.sleep(0.25)

			if time.time() - started > (60 * 10):
				error('Pre-existing pacman lock never exited. Please clean up any existing pacman sessions before using archinstall.')
				exit(1)

		return SysCommand(f'{default_cmd} {args}')

	def ask(self, error_message: str, bail_message: str, func: Callable, *args, **kwargs) -> None:  # type: ignore[no-untyped-def, type-arg]
		pacman_conf = Path('/etc/pacman.conf')
		pacman_conf_backup = Path('/etc/pacman.conf.backup')
		mirrorlist = Path('/etc/pacman.d/mirrorlist')
		mirrorlist_backup = Path('/etc/pacman.d/mirrorlist.original')
		backup_attempted = False

		while True:
			try:
				func(*args, **kwargs)
				break
			except Exception as err:
				error(f'{error_message}: {err}')

				# Display extracted error messages if available
				if hasattr(err, 'error_messages') and err.error_messages:
					warn('Detected errors in command output:')
					for err_msg in err.error_messages[:10]:  # Limit to 10 messages
						warn(f'  {err_msg}')

				# Check if error is mirror-related (no servers configured)
				if 'no servers configured' in str(err).lower() and mirrorlist_backup.exists() and not backup_attempted:
					warn('No servers configured - attempting to restore mirrorlist from backup...')
					try:
						import shutil
						shutil.copy(mirrorlist_backup, mirrorlist)
						info('Restored mirrorlist backup, retrying...')
						backup_attempted = True
						continue
					except Exception as restore_err:
						error(f'Failed to restore mirrorlist: {restore_err}')

				# Try to restore backup config if it exists and not already attempted
				if pacman_conf_backup.exists() and not backup_attempted:
					warn('Attempting to restore default pacman.conf from backup...')
					try:
						import shutil
						shutil.copy(pacman_conf_backup, pacman_conf)
						info('Restored backup pacman.conf, retrying...')
						backup_attempted = True
						continue
					except Exception as restore_err:
						error(f'Failed to restore backup config: {restore_err}')

				# Ultimate fallback: prompt user
				if not self.silent and input('Would you like to re-try this download? (Y/n): ').lower().strip() in 'y':
					continue

				raise RequirementError(f'{bail_message}: {err}')

	def sync(self) -> None:
		if self.synced:
			return
		self.ask(
			'Could not sync a new package database',
			'Could not sync mirrors',
			self.run,
			'-Syy',
			default_cmd='pacman',
		)
		self.synced = True

	def strap(self, packages: str | list[str]) -> None:
		self.sync()
		if isinstance(packages, str):
			packages = [packages]

		info(f'Installing packages: {packages}')

		self.ask(
			'Could not strap in packages',
			'Pacstrap failed. See logs/install.log or above message for error details',
			SysCommand,
			f'pacstrap -C /etc/pacman.conf -K {self.target} {" ".join(packages)} --needed --noconfirm',
			peek_output=True,
		)

__all__ = [
	'Pacman',
	'PacmanConfig',
]
