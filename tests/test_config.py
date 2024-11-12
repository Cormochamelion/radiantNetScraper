"""
Tests for the config module.
"""

import configparser as cfp

from json import dump
from pytest import raises
from pytest_cases import parametrize_with_cases

import test_config_cases as case_module

from radiant_net_scraper import config


def prepare_config_files(config_paths_objs, config_dicts) -> None:
    """
    Dump the contents of config_dicts into JSON files at config_paths with
    corresponding names.
    """
    config_paths = {
        config_name: str(config_path)
        for config_name, config_path in config_paths_objs.items()
    }

    for config_name in config_dicts:
        data = config_dicts[config_name]

        # We may want to leave data empty during testing, dump would complain in
        # that case.
        if data:
            with open(
                str(config_paths[config_name]), mode="w", encoding="UTF-8"
            ) as outfile:
                dump(data, outfile)


class TestUpdateConfigWithFiles:
    """
    Tests for config._update_config_with_files.
    """

    @parametrize_with_cases(
        ["config_dicts", "hierarchy", "expected"],
        cases=case_module.TestUpdateConfigWithFilesCases.TestSuccessCases,
    )
    def test_success(self, tmpdir, config_dicts, hierarchy, expected):
        """
        Test that the function returns expected results.
        """
        config_paths = {
            "default": str(tmpdir.join("default.json")),
            "user": str(tmpdir.join("user.json")),
        }

        prepare_config_files(config_paths, config_dicts)

        config_obj = cfp.ConfigParser(allow_no_value=True)
        config._update_config_with_files(config_obj, config_paths, hierarchy)

        assert config_obj == expected

    @parametrize_with_cases(
        ["config_dicts", "hierarchy"],
        cases=case_module.TestUpdateConfigWithFilesCases.TestHierarchyErrorCases,
    )
    def test_hierarchy_error(self, tmpdir, config_dicts, hierarchy):
        """
        Test that an error gets raised when the hierarchy is misspecified.
        """
        config_paths = {
            "default": str(tmpdir.join("default.json")),
            "user": str(tmpdir.join("user.json")),
        }

        prepare_config_files(config_paths, config_dicts)

        config_obj = cfp.ConfigParser(allow_no_value=True)

        with raises(ValueError):
            config._update_config_with_files(config_obj, config_paths, hierarchy)


class TestUpdateConfigWithEnv:
    """
    Test config._update_config_with_env.
    """

    @parametrize_with_cases(
        ["config_obj", "env_dict", "env_config", "expected_config"],
        cases=case_module.TestUpdateConfigWithEnvCases.TestSuccessCases,
    )
    def test_success(
        self, monkeypatch, config_obj, env_dict, env_config, expected_config
    ):
        """
        Test that the function returns expected results.
        """
        for env_name, env_value in env_dict.items():
            monkeypatch.setenv(env_name, env_value)

        config._update_config_with_env(config_obj, env_config)

        assert config_obj == expected_config

    @parametrize_with_cases(
        ["config_obj", "env_dict", "env_config"],
        cases=case_module.TestUpdateConfigWithEnvCases.TestConfigPathErrorCases,
    )
    def test_config_path_error(self, monkeypatch, config_obj, env_dict, env_config):
        """
        Test that an error gets raised when the config path is misspecified.
        """
        for env_name, env_value in env_dict.items():
            monkeypatch.setenv(env_name, env_value)

        with raises(ValueError):
            config._update_config_with_env(config_obj, env_config)

    @parametrize_with_cases(
        ["config_obj", "env_dict", "env_config"],
        cases=case_module.TestUpdateConfigWithEnvCases.TestConfigSectionErrorCases,
    )
    def test_config_section_error(self, monkeypatch, config_obj, env_dict, env_config):
        """
        Test that an error gets raised when the specified path is not already present.
        """
        for env_name, env_value in env_dict.items():
            monkeypatch.setenv(env_name, env_value)

        with raises(ValueError):
            config._update_config_with_env(config_obj, env_config)


class TestInitConfig:
    """
    Test config._init_config.
    """

    def test_success(self, monkeypatch, tmpdir):
        """
        Test whether data gets read from files and env to produce an expected config
        object.
        """

        mock_paths = {
            "metaconfig": tmpdir.join("metaconfig.json"),
            "default_config": tmpdir.join("default_config.json"),
            "user_config": tmpdir.join("user_config.json"),
        }

        mock_data = {
            "metaconfig": {
                "env_variables": {"password": ["secrets", "password"]},
                "config_hierarchy": ["default", "user"],
            },
            "default_config": {
                "attributes": {"count": "1", "color": "yellow"},
                "secrets": {"password": None},
            },
            "user_config": {
                "attributes": {"count": "1", "color": "yellow"},
                "secrets": {"password": "illnevertell"},
            },
        }

        env_password = "0451"
        monkeypatch.setenv("password", env_password)

        for mock_type, mock_path in mock_paths.items():
            with open(mock_path, "w", encoding="UTF-8") as outfile:
                dump(mock_data[mock_type], outfile)

        def mock_metaconfig_path():
            return mock_paths["metaconfig"]

        def mock_config_paths():
            return {
                "default": mock_paths["default_config"],
                "user": mock_paths["user_config"],
            }

        expected = cfp.ConfigParser(allow_no_value=True)

        for data_key in ["default_config", "user_config"]:
            expected.read_dict(mock_data[data_key])

        expected["secrets"]["password"] = env_password

        monkeypatch.setattr(config, "get_metaconfig_path", mock_metaconfig_path)
        monkeypatch.setattr(config, "get_config_paths", mock_config_paths)

        # Monkeypatch the config object, so that our later modifications get reset as
        # well.
        monkeypatch.setattr(config.Config, "_config_obj", None)
        config._init_config()

        assert config.Config.get_config() == expected
