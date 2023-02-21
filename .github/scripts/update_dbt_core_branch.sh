#!/bin/bash -e
set -e

git_branch=$1
target_req_file="dev-requirements.txt"
core_req_sed_pattern="s/dbt-core.git.*#egg=dbt-core/dbt-core.git@${git_branch}#egg=dbt-core/g"
postgres_req_sed_pattern="s/dbt-core.git.*#egg=dbt-postgres/dbt-core.git@${git_branch}#egg=dbt-postgres/g"
tests_req_sed_pattern="s/dbt-core.git.*#egg=dbt-tests/dbt-core.git@${git_branch}#egg=dbt-tests/g"
if [[ "$OSTYPE" == darwin* ]]; then
 # mac ships with a different version of sed that requires a delimiter arg
 sed -i "" "$core_req_sed_pattern" $target_req_file
 sed -i "" "$postgres_req_sed_pattern" $target_req_file
 sed -i "" "$tests_req_sed_pattern" $target_req_file
else
 sed -i "$core_req_sed_pattern" $target_req_file
 sed -i "$postgres_req_sed_pattern" $target_req_file
 sed -i "$tests_req_sed_pattern" $target_req_file
fi
core_version=$(curl "https://raw.githubusercontent.com/dbt-labs/dbt-core/${git_branch}/core/dbt/version.py" | grep "__version__ = *"|cut -d'=' -f2)
bumpversion --allow-dirty --new-version "$core_version" major
