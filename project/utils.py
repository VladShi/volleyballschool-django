from django.core.management.utils import get_random_secret_key
import os.path


def generate_secret_key_into_secret_key_file(path) -> None:
    """The function generates a file called secret_key.py
    in the "path" dir with the content:
    SECRET_KEY = '....random string....'
    You should add 'secret_key.py' path into .gitignore
    """
    filepath = os.path.join(path, 'secret_key.py')
    secret_file = open(filepath, "w")
    secret = "SECRET_KEY = " + "\"" + get_random_secret_key() + "\"" + "\n"
    secret_file.write(secret)
    secret_file.close()
