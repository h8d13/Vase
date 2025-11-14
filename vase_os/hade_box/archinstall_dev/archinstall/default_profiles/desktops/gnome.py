from typing import override

from archinstall.default_profiles.profile import GreeterType, Profile, ProfileType

class GnomeProfile(Profile):
	def __init__(self) -> None:
		super().__init__(
			'GNOME',
			ProfileType.DesktopEnv,
			packages=[
				'xorg-server',
			],
			services=[],
			support_gfx_driver=True,
		)

	@property
	@override
	def packages(self) -> list[str]:
		return super().packages + [
			'gnome',
			'gnome-tweaks',
			'gnome-shell-extensions',
			'gnome-browser-connector',
			'xdg-utils',
		]

	@property
	@override
	def default_greeter_type(self) -> GreeterType:
		return GreeterType.Gdm
