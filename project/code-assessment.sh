#!/bin/bash

declare -a FAILURES

add_fail() {
    FAILURES+=("$1")
}

black --check /pyats/project/src || add_fail black
pylint /pyats/project/src || add_fail pylint
flake8 /pyats/project/src || add_fail flake8
pydocstyle /pyats/project/src || add_fail pydocstyle
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