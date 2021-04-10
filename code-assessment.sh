#!/usr/bin/env bash

declare -a FAILURES

add_fail() {
    FAILURES+=("$1")
}

black --check . || add_fail black
pylint app || add_fail pylint
flake8 app || add_fail flake8
pydocstyle app || add_fail pydocstyle
if [[ ${#FAILURES[@]} -ne 0 ]]; then
    cat <<RESULT
===================================================
= Code assessment is failed! Please fix errors!!! =
===================================================
Failed tool(s):
RESULT
    for var in "${FAILURES[@]}"; do
        echo "- ${var}"
    done
    exit 11
fi

