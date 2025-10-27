from typing import override

from archinstall.default_profiles.profile import GreeterType, Profile, ProfileType


class MinimalProfile(Profile):
	def __init__(self) -> None:
		super().__init__(
			'Minimal (Server/CLI)',
			ProfileType.DesktopEnv,
			packages=[],
			services=[],
			support_gfx_driver=False,
		)

	@property
	@override
	def default_greeter_type(self) -> GreeterType | None:
		# No display manager needed for CLI-only install
		return None
