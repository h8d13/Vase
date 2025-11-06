import re

class RequirementError(Exception):
	pass

class DiskError(Exception):
	pass

class UnknownFilesystemFormat(Exception):
	pass

class SysCallError(Exception):
	def __init__(self, message: str, exit_code: int | None = None, worker_log: bytes = b'') -> None:
		super().__init__(message)
		self.message = message
		self.exit_code = exit_code
		self.worker_log = worker_log
		self.error_messages = self._extract_errors(worker_log)

	@staticmethod
	def _extract_errors(worker_log: bytes) -> list[str]:
		"""Extract error messages from command output"""
		if not worker_log:
			return []

		try:
			output = worker_log.decode('utf-8', errors='ignore')
		except Exception:
			return []

		errors = []
		# Match lines containing error patterns (case-insensitive)
		error_patterns = [
			r'(?i)^.*\berror\b.*$',           # Lines with "error"
			r'(?i)^.*\bfailed\b.*$',          # Lines with "failed"
			r'(?i)^==>.*ERROR.*$',            # Arch-style hook errors
			r'(?i)^ERROR:.*$',                # Standard ERROR: prefix
			r'(?i)^.*\b(dkms|hook).*failed.*$',  # DKMS/hook failures
		]

		for line in output.split('\n'):
			line = line.strip()
			if any(re.match(pattern, line) for pattern in error_patterns):
				# Avoid duplicate messages
				if line and line not in errors:
					errors.append(line)

		return errors[:20]  # Limit to first 20 error messages

class HardwareIncompatibilityError(Exception):
	pass

class ServiceException(Exception):
	pass

class PackageError(Exception):
	pass

class Deprecated(Exception):
	pass

class DownloadTimeout(Exception):
	"""
	Download timeout exception raised by DownloadTimer.
	"""
