from typing import TYPE_CHECKING, override

from archinstall.default_profiles.profile import GreeterType, Profile, ProfileType

if TYPE_CHECKING:
	pass

class PlasmaMinimalProfile(Profile):
	def __init__(self) -> None:
		super().__init__(
			'KDE Plasma (Minimal)',
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
			'plasma-desktop',
			'konsole',
			'plasma-workspace',
			'xdg-utils',
		]

	@property
	@override
	def default_greeter_type(self) -> GreeterType:
		return GreeterType.Sddm
