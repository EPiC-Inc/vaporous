from pathlib import Path

class FileHandler():
	__slots__ = ("base",)

	def __init__(self, base):
		self.base = Path(base)
