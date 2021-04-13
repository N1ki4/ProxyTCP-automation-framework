#!/bin/bash

declare -a FAILURES

add_fail() {
    FAILURES+=("$1")
}

black --check project || add_fail black
pylint project || add_fail pylint
flake8 project || add_fail flake8
pydocstyle project || add_fail pydocstyle
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