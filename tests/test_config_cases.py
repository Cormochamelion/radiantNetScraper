"""
Cases to test the config module.
"""

import configparser as cfp


class TestUpdateConfigWithFilesCases:
    class TestSuccessCases:
        def case_basic(self):
            config_obj = cfp.ConfigParser(allow_no_value=True)

            config_obj.read_dict(
                {
                    "attributes": {"count": 200, "color": "yellow"},
                    "secrets": {"password": "illnevertell"},
                }
            )

            return (
                {
                    "default": {
                        "attributes": {"count": 1, "color": "yellow"},
                        "secrets": {"password": None},
                    },
                    "user": {
                        "attributes": {"count": 200},
                        "secrets": {"password": "illnevertell"},
                    },
                },
                ["default", "user"],
                config_obj,
            )

        def case_reversed_hierarchy(self):
            config_obj = cfp.ConfigParser(allow_no_value=True)

            config_obj.read_dict(
                {
                    "attributes": {"count": 1, "color": "yellow"},
                    "secrets": {"password": None},
                }
            )

            return (
                {
                    "default": {
                        "attributes": {"count": 1, "color": "yellow"},
                        "secrets": {"password": None},
                    },
                    "user": {
                        "attributes": {"count": 200},
                        "secrets": {"password": "illnevertell"},
                    },
                },
                ["user", "default"],
                config_obj,
            )

        def case_empty_default(self):
            config_obj = cfp.ConfigParser(allow_no_value=True)

            config_obj.read_dict(
                {
                    "attributes": {"count": 200},
                    "secrets": {"password": "illnevertell"},
                }
            )

            return (
                {
                    "default": {},
                    "user": {
                        "attributes": {"count": 200},
                        "secrets": {"password": "illnevertell"},
                    },
                },
                ["user", "default"],
                config_obj,
            )

    class TestHierarchyErrorCases:
        def case_basic(self):
            return (
                {
                    "default": {
                        "attributes": {"count": 1, "color": "yellow"},
                        "secrets": {"password": None},
                    },
                    "user": {
                        "attributes": {"count": 200},
                        "secrets": {"password": "illnevertell"},
                    },
                },
                ["default"],
            )


default_config_obj = cfp.ConfigParser(allow_no_value=True)
default_config_obj.read_dict(
    {
        "attributes": {"count": "1", "color": "yellow"},
        "secrets": {"password": None},
    }
)

default_env_dict = {"password": "illnevertell", "other_secret": "0451"}
default_env_config = {"password": ["secrets", "password"]}

default_expected_config = cfp.ConfigParser()
default_expected_config.read_dict(
    {
        "attributes": {"count": "1", "color": "yellow"},
        "secrets": {"password": "illnevertell"},
    }
)


class TestUpdateConfigWithEnvCases:

    class TestSuccessCases:
        def case_basic(self):
            return (
                default_config_obj,
                default_env_dict,
                default_env_config,
                default_expected_config,
            )

    class TestConfigPathErrorCases:
        def case_path_too_short(self):
            return (
                default_config_obj,
                default_env_dict,
                {"password": ["secrets"]},
            )

        def case_path_too_long(self):
            return (
                default_config_obj,
                default_env_dict,
                {"password": ["secrets", "passwords", "email"]},
            )

    class TestConfigSectionErrorCases:
        def case_basic(self):
            return (
                default_config_obj,
                default_env_dict,
                {"password": ["flowers", "password"]},
            )
