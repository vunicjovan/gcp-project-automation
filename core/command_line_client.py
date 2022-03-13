import logging
import sys
from argparse import ArgumentParser

from statics import ARGUMENTS

# Basic log message configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="gcp-automated-setup - %(levelname)s - %(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


class CommandLineClient:
    """
    Represents a client for communication with command line.
    Automatically parses the default arguments and performs safety checks.
    """

    def _set_arguments(self):
        """
        Sets arguments provided by global ARGUMENTS dictionary to argument parser.
        """

        [self.parser.add_argument(f"--{a}", help=h) for a, h in ARGUMENTS.items()]

    def __init__(self):
        """
        Initializes argument parser and sets its arguments.
        """

        self.parser = ArgumentParser()
        self._set_arguments()

    def fetch_args(self):
        """
        Parses arguments from the command line.
        Notifies user if any of the required arguments were not entered.
        If checks for the required arguments successfully pass, returns
        parsed arguments in a form of dictionary.

        :return: Parsed arguments as dictionary (argument: value)
        :rtype: dict
        """

        args = vars(self.parser.parse_args())

        # If external configuration file is used, other args are redundant
        config_file = args.get("config_file")

        if config_file:
            logging.info(f"Using an external configuration file: {config_file}")
            args = {"config_file": config_file}
        else:
            logging.info("Using command line arguments for project configuration")

            # If using command line arguments, required ones must be set
            if not all(
                [
                    args.get("auth"),
                    args.get("gcp_project_id"),
                    args.get("android_package"),
                ]
            ):
                logging.warning(
                    "You need to specify --auth, --gcp_project_id and --android_package "
                    "arguments if not using an external configuration file"
                )
                sys.exit(1)
            elif (
                any(
                    [
                        args.get("ios_app_name"),
                        args.get("app_store_id"),
                        args.get("ios_config_path"),
                    ],
                )
                and not args.get("ios_bundle_id")
            ):
                logging.warning(
                    "You need to specify --ios_bundle_id argument if using any of the "
                    "following arguments: --ios_app_name, --app_store_id or --ios_config_path"
                )
                sys.exit(1)

        return {argument: value for argument, value in args.items()}
