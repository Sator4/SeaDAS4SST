import os
from pathlib import Path
import subprocess


class OCSSW:
    def __init__(self, root: os.PathLike | str) -> None:
        """
        Initialize the OCSSW class with the given root directory.

        Args:
            root (os.PathLike | str): The root directory of the OCSSW installation.
                It can be either a string representing the path or an instance of os.PathLike.

        Raises:
            Exception: If the root directory does not exist.

        """
        if type(root) == str:
            self.root = Path(root)
        else:
            self.root = root
        if not os.path.exists(self.root):
            raise Exception(
                """
                The OCSSW root directory does not exist.
                """
            )

    def l2gen(self, config: dict) -> None:
        """
        Generate a level 2 file using the given configuration.

        This function takes a dictionary `config` containing the configuration parameters for generating the level 2 file.
        It sets up the necessary environment variables and arguments for the `l2gen` command.
        The `l2gen` command is executed using the `subprocess.run` function with the specified arguments and environment variables.

        Parameters:
            config (dict): A dictionary containing the configuration parameters for generating the level 2 file.
                The dictionary should have the following keys:
                    - `k1` (str): The value for the `k1` parameter.
                    - `k2` (str): The value for the `k2` parameter.
                    - ...

        Returns:
            None

        """
        args = []
        env = {
            "OCDATAROOT": str(os.path.join(self.root, "share")),
            "OCVARROOT": str(os.path.join(self.root, 'var'))
        }
        args.append(os.path.join(self.root, 'bin/l2gen'))
        for k, v in config.items():
            args.append(f'{k}="{v}"')
        print(*args, sep='\n')
        print(env)
        subprocess.run(args=args, env=env)
        # albedo, ик каналы от 3.7 до 12 микрометров
