from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from archinstall.default_profiles.profile import GreeterType, Profile

if TYPE_CHECKING:
	from archinstall.lib.profile.profiles_handler import ProfileSerialization
	from ..hardware import GfxDriver

class _ProfileConfigurationSerialization(TypedDict):
	profile: ProfileSerialization
	gfx_driver: str | None
	greeter: str | None
	plasma_x11_session: bool | None
	x11_packages: list[str] | None

@dataclass
class ProfileConfiguration:
	profile: Profile | None = None
	gfx_driver: GfxDriver | None = None
	greeter: GreeterType | None = None
	plasma_x11_session: bool = False
	x11_packages: list[str] | None = None

	def json(self) -> _ProfileConfigurationSerialization:
		from ..profile.profiles_handler import profile_handler

		return {
			'profile': profile_handler.to_json(self.profile),
			'gfx_driver': self.gfx_driver.value if self.gfx_driver else None,
			'greeter': self.greeter.value if self.greeter else None,
			'plasma_x11_session': self.plasma_x11_session,
			'x11_packages': self.x11_packages,
		}

	@classmethod
	def parse_arg(cls, arg: _ProfileConfigurationSerialization) -> 'ProfileConfiguration':
		from ..hardware import GfxDriver
		from ..profile.profiles_handler import profile_handler

		profile = profile_handler.parse_profile_config(arg['profile'])
		greeter = arg.get('greeter', None)
		gfx_driver = arg.get('gfx_driver', None)
		plasma_x11_session = arg.get('plasma_x11_session', False)
		x11_packages = arg.get('x11_packages', None)

		return ProfileConfiguration(
			profile,
			GfxDriver(gfx_driver) if gfx_driver else None,
			GreeterType(greeter) if greeter else None,
			plasma_x11_session,
			x11_packages,
		)
