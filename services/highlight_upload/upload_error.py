"""
Custom exception for upload errors.
"""


class UploadError(Exception):
    """Custom exception for upload errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

