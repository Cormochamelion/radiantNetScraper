"""
Read config from both default, site & user dirs as well as from the environment to
construct a config object.
"""

import configparser as cfp
from importlib.metadata import metadata
from importlib.resources import files
from json import load
from os import environ
from os.path import exists
from platformdirs import site_config_dir, user_config_dir


def get_config_paths() -> dict[str, str]:
    """
    Get a dict of paths in which the app looks for configuration files.
    """
    scraper_meta = metadata("radiant_net_scraper")

    config_file_name = "config.json"

    return {
        "default": str(
            files("radiant_net_scraper.data").joinpath("default_config.json")
        ),
        "site": site_config_dir(scraper_meta["Name"], scraper_meta["Author"])
        + f"/{config_file_name}",
        "user": user_config_dir(scraper_meta["Name"], scraper_meta["Author"])
        + f"/{config_file_name}",
    }


def _update_config_with_files(
    config: cfp.ConfigParser, config_files: dict[str, str], config_hierarchy: list[str]
) -> None:
    """
    Update a config object in place with parameters read from default, site, and user
    config files. The hierarchy is determined by the `config_hierarchy` arg, where
    configurations later in the list will overwrite earlier ones.
    """
    config_data = {}

    for config_type, config_file in config_files.items():
        if exists(config_file):
            with open(config_file, encoding="UTF-8") as infile:
                config_data[config_type] = load(infile)

    if not "default" in config_files:
        default_config_file = config_files["default"]
        raise FileNotFoundError(
            f"Could not load default config params from {default_config_file}. This "
            f"probably indicates an issue with the install of the package, the file "
            f"should always be present."
        )

    hierarchy_set = set(config_hierarchy)
    config_key_set = set(config_files.keys())

    if not hierarchy_set == config_key_set:
        hierarchy_str = ", ".join(hierarchy_set)
        config_key_str = ", ".join(config_key_set)

        raise ValueError(
            f"The config hierarchy ({hierarchy_str}) does not contain the same keys as "
            f"the config ({config_key_str}). This is not sane, I refuse to proceed."
        )

    # Read config in order of the hierarchy.
    for hierarchy_key in config_hierarchy:
        # If there is no file at one of the optional config paths, its key is absent.
        if hierarchy_key in config_data:
            config.read_dict(config_data[hierarchy_key])


def _update_config_with_env(
    config: cfp.ConfigParser, env_var_config: dict[str, list]
) -> None:
    """
    Update a config object in place with pre-defined env variables. The env variables
    are specified as a dict where the key specifies the name of the env var and the
    value a list of length two specifying what the env var represents. The first value
    in the list gives the config section into which the value belongs and the second
    the key of the value in the config section.
    """
    for env_name, env_path in env_var_config.items():
        update_value = environ.get(env_name)

        if not len(env_path) == 2:
            raise ValueError(
                f"Malformed config path to read env var {env_name} into. "
                f"It needs to have exactly two values ([*section*, *id*]). "
                f"Actual values: {env_path}."
            )

        section_name, value_key = env_path

        if not section_name in config:
            config_section_names = ", ".join(config)
            raise ValueError(
                f"Section {section_name} for which env var {env_name} should be read "
                f"does not exist as part of the config ({config_section_names})."
            )

        # Only update if the env var was set.
        if update_value:
            section = config[section_name]
            section[value_key] = update_value


def get_metaconfig_path() -> str:
    """
    Get the path to where the metaconfiguration file can be found.
    """
    return str(files("radiant_net_scraper.data").joinpath("metaconfig.json"))


def _init_config() -> cfp.ConfigParser:
    """
    Inintialize the config object by reading from config files and the environment.
    """
    metaconfig_path = get_metaconfig_path()

    with open(metaconfig_path, "r", encoding="UTF-8") as infile:
        metaconfig = load(infile)

    config_files = get_config_paths()

    config = cfp.ConfigParser(allow_no_value=True)

    _update_config_with_files(config, config_files, metaconfig["config_hierarchy"])

    _update_config_with_env(config, metaconfig["env_variables"])

    return config


class Config:
    """
    Singleton wrapper to defer the creation of the config object from module load to
    when it is first needed.
    """

    _config_obj = None

    @classmethod
    def get_config(cls) -> cfp.ConfigParser:
        """
        Get the class-internal config object, intantiate if not already present.
        """
        if cls._config_obj is None:
            cls._config_obj = _init_config()

        return cls._config_obj