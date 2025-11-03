from typing import override

from archinstall.lib.interactions.manage_users_conf import ask_for_additional_users
from archinstall.lib.menu.abstract_menu import AbstractSubMenu
from archinstall.lib.models.authentication import AuthenticationConfiguration
from archinstall.lib.models.users import Password, User
from archinstall.lib.output import FormattedOutput
from archinstall.lib.utils.util import get_password
from archinstall.tui.curses_menu import SelectMenu
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties, Orientation

class AuthenticationMenu(AbstractSubMenu[AuthenticationConfiguration]):
	def __init__(self, preset: AuthenticationConfiguration | None = None):
		if preset:
			self._auth_config = preset
		else:
			self._auth_config = AuthenticationConfiguration()

		menu_optioons = self._define_menu_options()
		self._item_group = MenuItemGroup(menu_optioons, checkmarks=True)

		super().__init__(
			self._item_group,
			config=self._auth_config,
			allow_reset=True,
		)

		# Mark lock_root as default after sync (False = unlocked is default)
		lock_root_item = self._item_group.find_by_key('lock_root')
		lock_root_item.set_as_default()

	@override
	def run(self, additional_title: str | None = None) -> AuthenticationConfiguration:
		super().run(additional_title=additional_title)
		return self._auth_config

	def _define_menu_options(self) -> list[MenuItem]:
		# Create lock root menu item - don't set value, let it sync from config
		# Then mark the synced value as default to show 'D' for False
		lock_root_item = MenuItem(
			text=('Lock root account'),
			action=self._toggle_lock_root,
			preview_action=self._prev_lock_root,
			key='lock_root',
		)

		return [
			MenuItem(
				text=('Root password'),
				action=select_root_password,
				preview_action=self._prev_root_pwd,
				key='root_enc_password',
			),
			MenuItem(
				text=('User account'),
				action=self._create_user_account,
				preview_action=self._prev_users,
				key='users',
			),
			lock_root_item,
		]

	def _create_user_account(self, preset: list[User] | None = None) -> list[User]:
		preset = [] if preset is None else preset
		users = ask_for_additional_users(defined_users=preset)
		return users

	def _prev_users(self, item: MenuItem) -> str | None:
		users: list[User] | None = item.value

		if users:
			return FormattedOutput.as_table(users)
		return None

	def _prev_root_pwd(self, item: MenuItem) -> str | None:
		if item.value is not None:
			password: Password = item.value
			return f'Root password: {password.hidden()}'
		return None

	def _toggle_lock_root(self, preset: bool) -> bool:
		"""Toggle lock root account setting"""
		return not preset

	def _prev_lock_root(self, item: MenuItem) -> str | None:
		if item.value:
			return 'Root account will be locked (sudo users only)'
		return 'Root account will remain unlocked'

def select_root_password(preset: str | None = None) -> Password | None:
	password = get_password(text='Root password', allow_skip=True)
	return password


