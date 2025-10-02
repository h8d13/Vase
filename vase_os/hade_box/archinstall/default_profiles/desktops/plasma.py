from typing import TYPE_CHECKING, override

from archinstall.default_profiles.profile import GreeterType, Profile, ProfileType

if TYPE_CHECKING:
	pass

class PlasmaProfile(Profile):
	def __init__(self) -> None:
		super().__init__(
			'KDE Plasma',
			ProfileType.DesktopEnv,
			packages=[
				'xorg-server',
			],
			services=['sddm'],
			support_gfx_driver=True,
		)

	@property
	@override
	def packages(self) -> list[str]:
		return super().packages + [
			'plasma-meta',
			'konsole',
			'kate',
			'dolphin',
			'ark',
			'plasma-workspace',
		]

	@property
	@override
	def default_greeter_type(self) -> GreeterType:
		return GreeterType.Sddm
