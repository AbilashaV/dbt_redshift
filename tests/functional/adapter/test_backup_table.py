import pytest

from dbt.tests.util import run_dbt


_MODELS = {
    "backup_is_false.sql": "{{ config(materialized='table', backup=False) }} select 1 as my_col",
    "backup_is_true.sql": "{{ config(materialized='table', backup=True) }} select 1 as my_col",
    "backup_is_undefined.sql": "{{ config(materialized='table') }} select 1 as my_col",
    "backup_is_true_view.sql": "{{ config(materialized='view', backup=True) }} select 1 as my_col",
    "syntax_with_distkey.sql": "{{ config(materialized='table', backup=False, dist='my_col') }} select 1 as my_col",
    "syntax_with_sortkey.sql": "{{ config(materialized='table', backup=False, sort='my_col') }} select 1 as my_col",
}


class BackupTableBase:

    @pytest.fixture(scope="class", autouse=True)
    def run_dbt_results(self, project):
        run_dbt(["run"])

    @pytest.fixture(scope="class")
    def models(self):
        return _MODELS


class TestBackupTableModel(BackupTableBase):

    @pytest.mark.parametrize(
        "model_ddl,backup_expected",
        [
            ("backup_is_false", False),
            ("backup_is_true", True),
            ("backup_is_undefined", True),
            ("backup_is_true_view", True),
        ],
        indirect=["model_ddl"]
    )
    def test_setting_reflects_config_option(self, model_ddl: str, backup_expected: bool):
        backup_will_occur = "backup no" not in model_ddl.lower()
        assert backup_will_occur == backup_expected

    @pytest.mark.parametrize(
        "model_ddl,search_phrase",
        [
            ("syntax_with_distkey", "diststyle key distkey"),
            ("syntax_with_sortkey", "compound sortkey"),
        ],
        indirect=["model_ddl"]
    )
    def test_properly_formed_ddl(self, model_ddl, search_phrase):
        assert model_ddl.find("backup no") < model_ddl.find(search_phrase)


class TestBackupTableProject(BackupTableBase):

    @pytest.fixture(scope="class")
    def project_config_update(self):
        return {"models": {"backup": False}}

    @pytest.mark.parametrize(
        "model_ddl,backup_expected",
        [
            ("backup_is_true", True),
            ("backup_is_undefined", False)
        ],
        indirect=["model_ddl"]
    )
    def test_setting_defaults_to_project_option(self, model_ddl: str, backup_expected: bool):
        backup_will_occur = "backup no" not in model_ddl.lower()
        assert backup_will_occur == backup_expected
