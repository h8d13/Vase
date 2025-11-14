from typing import override

from archinstall.default_profiles.profile import GreeterType, Profile, ProfileType

class MinimalProfile(Profile):
	def __init__(self) -> None:
		super().__init__(
			'Minimal (Server/CLI)',
			ProfileType.Minimal,
			packages=[],
			services=[],
			support_gfx_driver=False,
			support_greeter=True,
		)

	@property
	@override
	def default_greeter_type(self) -> GreeterType | None:
		# Default to no display manager for CLI-only install
		return GreeterType.NoGreeter
