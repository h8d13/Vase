from dataclasses import dataclass, field
from typing import Any, TypedDict

from archinstall.lib.models.users import Password, User

class AuthenticationSerialization(TypedDict):
	pass

@dataclass
class AuthenticationConfiguration:
	root_enc_password: Password | None = None
	users: list[User] = field(default_factory=list)

	@staticmethod
	def parse_arg(args: dict[str, Any]) -> 'AuthenticationConfiguration':
		auth_config = AuthenticationConfiguration()

		if enc_password := args.get('root_enc_password'):
			auth_config.root_enc_password = Password(enc_password=enc_password)

		return auth_config

	def json(self) -> AuthenticationSerialization:
		config: AuthenticationSerialization = {}
		return config
