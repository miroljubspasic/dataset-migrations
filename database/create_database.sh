#!/usr/bin/env sh

sqlite3 -batch "$PWD/data/database.sqlite" <"$PWD/initdb.sql"
