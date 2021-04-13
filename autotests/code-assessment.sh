#!/bin/bash

declare -a FAILURES

add_fail() {
    FAILURES+=("$1")
}

black --check autotests || add_fail black
pylint autotests || add_fail pylint
flake8 autotests || add_fail flake8
pydocstyle autotests || add_fail pydocstyle
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