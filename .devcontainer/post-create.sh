#!/bin/sh
# Kept in a file so postCreateCommand is a single word: Zed joins the
# arguments of lifecycle commands without quoting them.
set -eu
pipx install uv
uv sync --all-groups
uv run prek install
