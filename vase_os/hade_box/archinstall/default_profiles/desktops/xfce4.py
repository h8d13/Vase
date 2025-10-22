from typing import override

from archinstall.default_profiles.profile import GreeterType, Profile, ProfileType


class Xfce4Profile(Profile):
	def __init__(self) -> None:
		super().__init__(
			'Xfce4',
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
			'xfce4',
			'xfce4-goodies',
			'pavucontrol',
			'gvfs',
			'xarchiver',
		]

	@property
	@override
	def default_greeter_type(self) -> GreeterType:
		return GreeterType.Lightdm
