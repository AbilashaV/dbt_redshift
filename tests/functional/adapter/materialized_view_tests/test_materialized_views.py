import pytest

from dbt.contracts.results import RunStatus
from dbt.contracts.relation import RelationType
from dbt.tests.adapter.materialized_view.base import (
    run_model,
    assert_model_exists_and_is_correct_type,
    insert_record,
    get_row_count,
)
from dbt.tests.adapter.materialized_view.on_configuration_change import (
    assert_proper_scenario,
)

from tests.functional.adapter.materialized_view_tests.fixtures import (
    RedshiftBasicBase,
    RedshiftOnConfigurationChangeBase,
)


class TestBasic(RedshiftBasicBase):
    def test_relation_is_materialized_view_on_initial_creation(self, project):
        assert_model_exists_and_is_correct_type(
            project, "base_materialized_view", RelationType.MaterializedView
        )

    def test_relation_is_materialized_view_when_rerun(self, project):
        run_model("base_materialized_view")
        assert_model_exists_and_is_correct_type(
            project, "base_materialized_view", RelationType.MaterializedView
        )

    def test_relation_is_materialized_view_on_full_refresh(self, project):
        run_model("base_materialized_view", full_refresh=True)
        assert_model_exists_and_is_correct_type(
            project, "base_materialized_view", RelationType.MaterializedView
        )

    def test_relation_is_materialized_view_on_update(self, project):
        run_model("base_materialized_view", run_args=["--vars", "quoting: {identifier: True}"])
        assert_model_exists_and_is_correct_type(
            project, "base_materialized_view", RelationType.MaterializedView
        )

    @pytest.mark.skip("This test will fail because we're mocking with a view for now")
    def test_updated_base_table_data_only_shows_in_materialized_view_after_rerun(self, project):
        # poll database
        table_start = get_row_count(project, "base_table")
        view_start = get_row_count(project, "base_materialized_view")

        # insert new record in table
        new_record = (2,)
        insert_record(project, new_record, "base_table", ["base_column"])

        # poll database
        table_mid = get_row_count(project, "base_table")
        view_mid = get_row_count(project, "base_materialized_view")

        # refresh the materialized view
        run_model("base_materialized_view")

        # poll database
        table_end = get_row_count(project, "base_table")
        view_end = get_row_count(project, "base_materialized_view")

        # new records were inserted in the table but didn't show up in the view until it was refreshed
        assert table_start < table_mid == table_end
        assert view_start == view_mid < view_end


class OnConfigurationChangeCommon(RedshiftOnConfigurationChangeBase):
    def test_full_refresh_takes_precedence_over_any_configuration_changes(
        self,
        configuration_changes_apply,
        configuration_changes_refresh,
        replace_message,
        configuration_change_message,
    ):
        results, logs = run_model("base_materialized_view", full_refresh=True)
        assert_proper_scenario(
            self.on_configuration_change,
            results,
            logs,
            RunStatus.Success,
            messages_in_logs=[replace_message],
            messages_not_in_logs=[configuration_change_message],
        )

    def test_model_is_refreshed_with_no_configuration_changes(
        self, refresh_message, configuration_change_message
    ):
        results, logs = run_model("base_materialized_view")
        assert_proper_scenario(
            self.on_configuration_change,
            results,
            logs,
            RunStatus.Success,
            messages_in_logs=[refresh_message, configuration_change_message],
        )


class TestOnConfigurationChangeApply(OnConfigurationChangeCommon):
    def test_model_applies_changes_with_small_configuration_changes(
        self, configuration_changes_apply, alter_message, update_auto_refresh_message
    ):
        results, logs = run_model("base_materialized_view")
        assert_proper_scenario(
            self.on_configuration_change,
            results,
            logs,
            RunStatus.Success,
            messages_in_logs=[alter_message, update_auto_refresh_message],
        )

    def test_model_rebuilds_with_large_configuration_changes(
        self, configuration_changes_refresh, alter_message, replace_message
    ):
        results, logs = run_model("base_materialized_view")
        assert_proper_scenario(
            self.on_configuration_change,
            results,
            logs,
            RunStatus.Success,
            messages_in_logs=[alter_message, replace_message],
        )

    def test_model_only_rebuilds_with_large_configuration_changes(
        self,
        configuration_changes_apply,
        configuration_changes_refresh,
        alter_message,
        replace_message,
        update_auto_refresh_message,
    ):
        results, logs = run_model("base_materialized_view")
        assert_proper_scenario(
            self.on_configuration_change,
            results,
            logs,
            RunStatus.Success,
            messages_in_logs=[alter_message, replace_message],
            messages_not_in_logs=[update_auto_refresh_message],
        )


class TestOnConfigurationChangeSkip(OnConfigurationChangeCommon):
    on_configuration_change = "skip"

    def test_model_is_skipped_with_configuration_changes(
        self, configuration_changes_apply, configuration_change_skip_message
    ):
        results, logs = run_model("base_materialized_view")
        assert_proper_scenario(
            self.on_configuration_change,
            results,
            logs,
            RunStatus.Success,
            messages_in_logs=[configuration_change_skip_message],
        )


class TestOnConfigurationChangeFail(OnConfigurationChangeCommon):
    on_configuration_change = "fail"

    def test_run_fails_with_configuration_changes(
        self, configuration_changes_apply, configuration_change_fail_message
    ):
        results, logs = run_model("base_materialized_view", expect_pass=False)
        assert_proper_scenario(
            self.on_configuration_change,
            results,
            logs,
            RunStatus.Error,
            messages_in_logs=[configuration_change_fail_message],
        )
