#!/bin/sh

cd $(git rev-parse --show-toplevel)/.git/hooks
ln -s ../../hooks/pre-commit
ln -s ../../hooks/pre-push

