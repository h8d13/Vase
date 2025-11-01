from typing import TYPE_CHECKING, override

from archinstall.default_profiles.profile import GreeterType, Profile, ProfileType

if TYPE_CHECKING:
	pass

class PlasmaFullProfile(Profile):
	def __init__(self) -> None:
		super().__init__(
			'KDE Plasma (Full)',
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
		# Full KDE experience: plasma meta + all kde-applications (189 packages)
		return super().packages + [
			'plasma',  # Full Plasma desktop meta package
			'kde-applications',  # All KDE applications (utilities, graphics, multimedia, games, etc)
		]

	@property
	@override
	def default_greeter_type(self) -> GreeterType:
		return GreeterType.Sddm
