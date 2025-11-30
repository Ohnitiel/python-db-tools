from cryptography.fernet import Fernet

from .extras import find_root_dir


class SecurityManager:
    """
    Manages the encryption and decryption of passwords.
    """

    def __init__(self: "SecurityManager"):
        """
        Initializes a new SecurityManager object.
        """
        self.key_path = find_root_dir(["pyproject.toml"]) / ".config" / ".key"
        self.key = self._load_key()

    def _load_key(self: "SecurityManager") -> bytes:
        """
        Loads the encryption key from the .key file.
        If the file does not exist, a new key is generated and saved to the file.

        Returns:
            The encryption key.
        """
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                return f.read()
        else:
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
            return key

    def encrypt_password(self: "SecurityManager", password: str) -> str:
        """
        Encrypts a password.

        Args:
            password: The password to encrypt.

        Returns:
            The encrypted password.
        """
        fernet = Fernet(self.key)
        encrypted_password = fernet.encrypt(password.encode())
        return encrypted_password.decode()

    def decrypt_password(self: "SecurityManager", encrypted_password: str) -> str:
        """
        Decrypts a password.

        Args:
            encrypted_password: The encrypted password.

        Returns:
            The decrypted password.
        """
        fernet = Fernet(self.key)
        decrypted_password = fernet.decrypt(encrypted_password.encode())
        return decrypted_password.decode()
