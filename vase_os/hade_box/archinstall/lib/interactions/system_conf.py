from __future__ import annotations

from archinstall.tui.curses_menu import SelectMenu, EditMenu
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType
from archinstall.tui.types import Alignment, FrameProperties, FrameStyle, Orientation, PreviewStyle

from ..args import arch_config_handler
from ..hardware import GfxDriver, SysInfo
from ..models.bootloader import Bootloader, GrubConfiguration

def select_kernel(preset: list[str] = []) -> list[str]:
	"""
	Asks the user to select a kernel for system.

	:return: The string as a selected kernel
	:rtype: string
	"""
	kernels = ['linux', 'linux-lts', 'linux-zen', 'linux-hardened']
	default_kernel = 'linux'

	items = [MenuItem(k, value=k) for k in kernels]

	group = MenuItemGroup(items, sort_items=True)
	group.set_default_by_value(default_kernel)
	group.set_focus_by_value(default_kernel)
	group.set_selected_by_value(preset)

	result = SelectMenu[str](
		group,
		allow_skip=True,
		allow_reset=True,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Kernel'),
		multi=True,
	).run()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Reset:
			return []
		case ResultType.Selection:
			return result.get_values()

def ask_for_bootloader(preset: Bootloader | None) -> Bootloader | None:
	return Bootloader.Grub

def ask_for_grub_configuration(preset: GrubConfiguration | None = None) -> GrubConfiguration:
	"""
	Configure GRUB bootloader options
	"""
	if preset is None:
		preset = GrubConfiguration()

	config = GrubConfiguration()

	# Ask about OS prober
	os_prober_options = [
		MenuItem(text='Enabled', value=True, preview_action=lambda x: 'Installs os-prober package and enables detection.\nAfter first boot, run: sudo grub-mkconfig -o /boot/grub/grub.cfg'),
		MenuItem(text='Disabled', value=False, preview_action=lambda x: 'OS Prober will remain disabled (default).\nOnly your Arch Linux installation will appear in GRUB menu.')
	]

	group = MenuItemGroup(os_prober_options, sort_items=False)
	group.set_focus_by_value(preset.enable_os_prober)

	result = SelectMenu[bool](
		group,
		header='Enable OS Prober to detect other operating systems?\n',
		allow_skip=True,
		alignment=Alignment.CENTER,
		orientation=Orientation.HORIZONTAL,
		columns=2,
		frame=FrameProperties.min('Grub os-prober'),
		preview_size='auto',
		preview_style=PreviewStyle.BOTTOM,
		preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
	).run()

	match result.type_:
		case ResultType.Skip:
			config.enable_os_prober = preset.enable_os_prober
		case ResultType.Selection:
			config.enable_os_prober = result.get_value()

	# Only ask about hiding menu if OS prober is disabled
	if not config.enable_os_prober:
		hide_menu_options = [
			MenuItem(
				text='Enabled',
				value=False,
				preview_action=lambda x: 'GRUB menu will be visible during boot.\nUser can select boot options (and snapshots) and see timeout countdown.\nENTER key can skip the timeout and boot immediately.'
			),
			MenuItem(
				text='Disabled',
				value=True,
				preview_action=lambda x: 'GRUB menu will be hidden during boot.\nSystem boots directly to default entry.\nESC key during boot will reveal the menu if needed (snapshots + boot options.)'
			)
		]

		group = MenuItemGroup(hide_menu_options, sort_items=False)
		group.set_focus_by_value(preset.hide_menu)

		result = SelectMenu[bool](
			group,
			header='Hide GRUB menu at boot? (ESC key still opens it.)\n',
			allow_skip=True,
			alignment=Alignment.CENTER,
			orientation=Orientation.HORIZONTAL,
			columns=2,
			frame=FrameProperties.min('Grub Menu'),
			preview_size='auto',
			preview_style=PreviewStyle.BOTTOM,
			preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
		).run()

		match result.type_:
			case ResultType.Skip:
				config.hide_menu = preset.hide_menu
			case ResultType.Selection:
				config.hide_menu = result.get_value()
	else:
		# If OS prober is enabled, never hide menu
		config.hide_menu = False

		# Ask about remembering last selection (only useful with OS prober)
		remember_options = [
			MenuItem(
				text='Enabled',
				value=True,
				preview_action=lambda x: 'GRUB will remember your last boot choice.\nNext boot will default to the same OS you selected.\nUseful for dual-boot systems with a preferred OS.'
			),
			MenuItem(
				text='Disabled',
				value=False,
				preview_action=lambda x: 'GRUB will always boot the first entry by default.\nConsistent behavior regardless of previous selection.\nRecommended for single-user systems.'
			)
		]

		group = MenuItemGroup(remember_options, sort_items=False)
		group.set_focus_by_value(preset.remember_last_selection)

		result = SelectMenu[bool](
			group,
			header='Remember last selected OS for next boot?\n',
			allow_skip=True,
			alignment=Alignment.CENTER,
			orientation=Orientation.HORIZONTAL,
			columns=2,
			frame=FrameProperties.min('GRUB Memory'),
			preview_size='auto',
			preview_style=PreviewStyle.BOTTOM,
			preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
		).run()

		match result.type_:
			case ResultType.Skip:
				config.remember_last_selection = preset.remember_last_selection
			case ResultType.Selection:
				config.remember_last_selection = result.get_value()

	# Ask about timeout (unless menu is hidden)
	if not config.hide_menu:
		timeout_options = [
			MenuItem(text='3 seconds', value=3),
			MenuItem(text='5 seconds (default)', value=5),
			MenuItem(text='10 seconds', value=10),
			MenuItem(text='30 seconds', value=30)
		]

		group = MenuItemGroup(timeout_options, sort_items=False)
		group.set_focus_by_value(preset.timeout)

		result = SelectMenu[int](
			group,
			header='How long should GRUB wait before auto-booting?\n',
			allow_skip=True,
			alignment=Alignment.CENTER,
			frame=FrameProperties.min('GRUB Timeout'),
			preview_size='auto',
			preview_style=PreviewStyle.BOTTOM,
			preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
		).run()

		match result.type_:
			case ResultType.Skip:
				config.timeout = preset.timeout
			case ResultType.Selection:
				config.timeout = result.get_value()
	else:
		# When menu is hidden, use preset timeout
		config.timeout = preset.timeout

	# Ask about custom colors
	color_enable_options = [
		MenuItem(
			text='Enabled',
			value=True,
			preview_action=lambda x: 'Enable custom colors for GRUB menu.\nAllows you to set foreground/background colors for normal text and highlighted entries.\nMakes the boot menu more visually appealing.'
		),
		MenuItem(
			text='Disabled',
			value=False,
			preview_action=lambda x: 'Use default GRUB colors.\nStandard white text on black background.\nMinimal but functional appearance.'
		)
	]

	group = MenuItemGroup(color_enable_options, sort_items=False)
	group.set_focus_by_value(preset.enable_custom_colors)

	result = SelectMenu[bool](
		group,
		header='Enable custom colors for GRUB menu?\n',
		allow_skip=True,
		alignment=Alignment.CENTER,
		orientation=Orientation.HORIZONTAL,
		columns=2,
		frame=FrameProperties.min('GRUB Colors'),
		preview_size='auto',
		preview_style=PreviewStyle.BOTTOM,
		preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
	).run()

	match result.type_:
		case ResultType.Skip:
			config.enable_custom_colors = preset.enable_custom_colors
		case ResultType.Selection:
			config.enable_custom_colors = result.get_value()

	# If custom colors are enabled, ask for color scheme
	if config.enable_custom_colors:
		def create_color_preview(normal_colors: str, highlight_colors: str, description: str) -> str:
			"""Create a simple text-based color preview"""
			# Parse colors
			normal_fg, normal_bg = normal_colors.split('/')
			highlight_fg, highlight_bg = highlight_colors.split('/')

			preview = f"GRUB Colors:\n\n"
			preview += f"Normal text:      {normal_fg} on {normal_bg}\n"
			preview += f"Highlighted text: {highlight_fg} on {highlight_bg}\n\n"
			preview += description

			return preview

		color_schemes = [
			MenuItem(
				text='Default (Blue)',
				value=('light-blue/black', 'light-cyan/blue'),
				preview_action=lambda x: create_color_preview('light-blue/black', 'light-cyan/blue', 'Classic, easy to read theme')
			),
			MenuItem(
				text='Classic (White)',
				value=('white/black', 'black/light-gray'),
				preview_action=lambda x: create_color_preview('white/black', 'black/light-gray', 'High contrast, very readable')
			),
			MenuItem(
				text='Matrix (Green)',
				value=('light-green/black', 'black/light-green'),
				preview_action=lambda x: create_color_preview('light-green/black', 'black/light-green', 'Matrix/terminal style theme')
			),
			MenuItem(
				text='Ocean (Cyan)',
				value=('light-cyan/blue', 'blue/light-cyan'),
				preview_action=lambda x: create_color_preview('light-cyan/blue', 'blue/light-cyan', 'Cool ocean-inspired colors')
			),
			MenuItem(
				text='Sunset (Orange)',
				value=('yellow/red', 'red/yellow'),
				preview_action=lambda x: create_color_preview('yellow/red', 'red/yellow', 'Warm sunset-inspired colors')
			),
			MenuItem(
				text='Retro (Magenta)',
				value=('light-magenta/black', 'black/light-magenta'),
				preview_action=lambda x: create_color_preview('light-magenta/black', 'black/light-magenta', 'Retro 80s computer style')
			)
		]

		group = MenuItemGroup(color_schemes, sort_items=False)
		# Set default based on current preset colors
		current_scheme = (preset.color_normal, preset.color_highlight)
		for item in color_schemes:
			if item.value == current_scheme:
				group.set_focus_by_value(item.value)
				break
		else:
			group.set_focus_by_value(color_schemes[0].value)  # Default to first option

		result = SelectMenu[tuple[str, str]](
			group,
			header='Choose a color scheme for GRUB:\n',
			allow_skip=True,
			alignment=Alignment.CENTER,
			frame=FrameProperties.min('Color Scheme'),
			preview_size='auto',
			preview_style=PreviewStyle.BOTTOM,
			preview_frame=FrameProperties(('Preview'), h_frame_style=FrameStyle.MIN),
		).run()

		match result.type_:
			case ResultType.Skip:
				config.color_normal = preset.color_normal
				config.color_highlight = preset.color_highlight
			case ResultType.Selection:
				normal, highlight = result.get_value()
				config.color_normal = normal
				config.color_highlight = highlight
	else:
		# Use preset colors when custom colors are disabled
		config.color_normal = preset.color_normal
		config.color_highlight = preset.color_highlight

	# Ask about boot sound
	boot_sound_options = [
		MenuItem(
			text='Enabled',
			value=True,
			preview_action=lambda x: 'Enable boot sound (beep) when GRUB starts.\nPlays a simple tone: 480Hz for 440ms.\nHelps confirm that GRUB has loaded successfully.\nUseful for headless systems or debugging.'
		),
		MenuItem(
			text='Disabled',
			value=False,
			preview_action=lambda x: 'No boot sound when GRUB starts.\nSilent boot process.\nRecommended for most desktop systems.\nDefault behavior.'
		)
	]

	group = MenuItemGroup(boot_sound_options, sort_items=False)
	group.set_focus_by_value(preset.enable_boot_sound)

	result = SelectMenu[bool](
		group,
		header='Enable boot sound when GRUB starts?\n',
		allow_skip=True,
		alignment=Alignment.CENTER,
		orientation=Orientation.HORIZONTAL,
		columns=2,
		frame=FrameProperties.min('GRUB Boot Sound'),
		preview_size='auto',
		preview_style=PreviewStyle.BOTTOM,
		preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
	).run()

	match result.type_:
		case ResultType.Skip:
			config.enable_boot_sound = preset.enable_boot_sound
		case ResultType.Selection:
			config.enable_boot_sound = result.get_value()

	# If boot sound is enabled, ask for tune options
	if config.enable_boot_sound:
		tune_options = [
			MenuItem(
				text='Default Beep',
				value='480 440 1',
				preview_action=lambda x: 'Standard boot beep\n480Hz tone for 440ms, plays once\nClassic computer startup sound'
			),
			MenuItem(
				text='Short Beep',
				value='800 200 1',
				preview_action=lambda x: 'Quick startup beep\n800Hz tone for 200ms, plays once\nBrief confirmation sound'
			),
			MenuItem(
				text='Low Tone',
				value='220 500 1',
				preview_action=lambda x: 'Deep startup tone\n220Hz tone for 500ms, plays once\nLower pitched, longer duration'
			),
			MenuItem(
				text='High Tone',
				value='1000 300 1',
				preview_action=lambda x: 'High startup beep\n1000Hz tone for 300ms, plays once\nCrisp, high-pitched sound'
			),
			MenuItem(
				text='Double Beep',
				value='600 250 2',
				preview_action=lambda x: 'Two-tone startup\n600Hz tone for 250ms, plays twice\nDouble confirmation beep'
			),
			MenuItem(
				text='Triple Beep',
				value='440 150 3',
				preview_action=lambda x: 'Triple confirmation beep\n440Hz tone for 150ms, plays 3 times\nClear startup confirmation sequence'
			)
		]

		group = MenuItemGroup(tune_options, sort_items=False)
		# Set default based on current preset
		for item in tune_options:
			if item.value == preset.boot_sound_tune:
				group.set_focus_by_value(item.value)
				break
		else:
			group.set_focus_by_value(tune_options[0].value)  # Default to first option

		result = SelectMenu[str](
			group,
			header='Choose boot sound type:\n',
			allow_skip=True,
			alignment=Alignment.CENTER,
			frame=FrameProperties.min('Boot Sound'),
			preview_size='auto',
			preview_style=PreviewStyle.BOTTOM,
			preview_frame=FrameProperties(('Sound Info'), h_frame_style=FrameStyle.MIN),
		).run()

		match result.type_:
			case ResultType.Skip:
				config.boot_sound_tune = preset.boot_sound_tune
			case ResultType.Selection:
				config.boot_sound_tune = result.get_value()
	else:
		# Use preset tune when boot sound is disabled
		config.boot_sound_tune = preset.boot_sound_tune

	return config

def select_driver(options: list[GfxDriver] = [], preset: GfxDriver | None = None) -> GfxDriver | None:
	"""
	Some what convoluted function, whose job is simple.
	Select a graphics driver from a pre-defined set of popular options.

	(The template xorg is for beginner users, not advanced, and should
	there for appeal to the general public first and edge cases later)
	"""
	if not options:
		options = [driver for driver in GfxDriver]

	items = [MenuItem(o.value, value=o, preview_action=lambda x: x.value.packages_text()) for o in options]
	group = MenuItemGroup(items, sort_items=True)
	group.set_default_by_value(GfxDriver.AllOpenSource)

	if preset is not None:
		group.set_focus_by_value(preset)

	header = ''

	# Check for VM environment first
	if SysInfo.is_vm():
		virt_type = SysInfo.virtualization()
		if virt_type:
			header += f'Virtual machine detected ({virt_type}). The Virtual Machine (open-source) driver is recommended for VM environments to avoid graphics compatibility issues.\n\n'
		else:
			header += 'Virtual machine detected. The Virtual Machine (open-source) driver is recommended for VM environments to avoid graphics compatibility issues.\n\n'

		# Set VM driver as default for VMs
		group.set_default_by_value(GfxDriver.VMOpenSource)
		if preset is None:
			group.set_focus_by_value(GfxDriver.VMOpenSource)
	else:
		# Check for hybrid graphics first
		if SysInfo.has_intel_graphics() and SysInfo.has_nvidia_graphics():
			header += ('Hybrid graphics detected (Intel + Nvidia). For laptop power management and GPU switching, consider the Intel + Nvidia (hybrid) option.\n')
		elif SysInfo.has_amd_graphics() and SysInfo.has_nvidia_graphics():
			header += ('Multiple GPUs detected (AMD + Nvidia). You may want to choose based on your primary use case.\n')
		else:
			# Single GPU recommendations
			if SysInfo.has_amd_graphics():
				header += ('For the best compatibility with your AMD hardware, you may want to use either the all open-source or AMD / ATI options.') + '\n'
			if SysInfo.has_intel_graphics():
				header += ('For the best compatibility with your Intel hardware, you may want to use either the all open-source or Intel options.\n')
			if SysInfo.has_nvidia_graphics():
				header += ('For the best compatibility with your Nvidia hardware, you may want to use the Nvidia proprietary driver.\n')

	result = SelectMenu[GfxDriver](
		group,
		header=header,
		allow_skip=True,
		allow_reset=True,
		preview_size='auto',
		preview_style=PreviewStyle.BOTTOM,
		preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
	).run()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Reset:
			return None
		case ResultType.Selection:
			return result.get_value()

def ask_for_swap(preset: str = 'zram') -> str:
	swap_options = [
		MenuItem(
			text='Swap on zram (compressed RAM)',
			value='zram',
			preview_action=lambda x: 'Compressed swap in RAM using zram.\nFast performance, no disk wear.\nSize: typically 25-50% of RAM.\nBest for most desktop/laptop systems.\nRecommended for SSDs.'
		),
		MenuItem(
			text='Swap file on disk',
			value='swapfile',
			preview_action=lambda x: 'Traditional swap file on main filesystem.\nEasy to resize later.\nGood for systems with limited RAM.\nWorks with any filesystem type.\nSlightly slower than partition.'
		),
		MenuItem(
			text='Swap partition on disk',
			value='partition',
			preview_action=lambda x: 'Dedicated swap partition on disk.\nSlightly faster than swap file.\nFixed size, harder to resize.\nTraditional Linux approach.\nGood for systems with spinning disks.'
		),
		MenuItem(
			text='No swap',
			value='none',
			preview_action=lambda x: 'Disable swap entirely.\nRelies only on physical RAM.\nOnly recommended for systems with abundant RAM (16GB+).\nCan cause out-of-memory issues under heavy load.'
		)
	]

	prompt = 'Select swap configuration:\n'

	group = MenuItemGroup(swap_options, sort_items=False)
	group.set_focus_by_value(preset)

	result = SelectMenu[str](
		group,
		header=prompt,
		allow_skip=True,
		alignment=Alignment.CENTER,
		frame=FrameProperties.min('Swap Configuration'),
		preview_size='auto',
		preview_style=PreviewStyle.BOTTOM,
		preview_frame=FrameProperties(('Info'), h_frame_style=FrameStyle.MIN),
	).run()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Selection:
			return result.get_value()
		case ResultType.Reset:
			raise ValueError('Unhandled result type')


def ask_for_swap_size(preset: str = '4G') -> str:
	"""Ask user for swap size in GiB"""
	# Get total RAM and calculate recommendations
	total_ram_kb = SysInfo.mem_total()
	total_ram_gb = total_ram_kb / (1024 * 1024)

	# Generate swap size recommendations based on RAM
	if total_ram_gb <= 2:
		recommended = "4G"
	elif total_ram_gb <= 4:
		recommended = "4G"
	elif total_ram_gb <= 8:
		recommended = "4G"
	elif total_ram_gb <= 16:
		recommended = "8G"
	else:
		recommended = "8G"

	if preset == '4G' and recommended != '4G':
		preset = recommended

	prompt = f'Enter desired swap size:'

	result = EditMenu(
		prompt,
		header=f'Configuration (detected RAM: {total_ram_gb:.1f}GB, recommended: {recommended})',
		alignment=Alignment.CENTER,
		allow_skip=True,
		validator=_validate_swap_size,
		default_text=preset,
	).input()

	match result.type_:
		case ResultType.Skip:
			return preset
		case ResultType.Selection:
			if result.text() and result.text().strip():
				return result.text().strip()
			else:
				return preset

	return preset

def _validate_swap_size(size_str: str) -> str | None:
	"""Validate swap size format"""
	import re
	if not size_str:
		return "Size cannot be empty"

	# Allow formats like: 2G, 4G, 8G, 1024M, etc.
	pattern = r'^\d+[KMGT]?$'
	if re.match(pattern, size_str.upper()):
		return None  # Valid
	else:
		return "Invalid size format. Use formats like: 2G, 4G, 8G, 1024M"
