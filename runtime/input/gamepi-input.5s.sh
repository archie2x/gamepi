#!/bin/sh
# <swiftbar.title>Gamepi Input</swiftbar.title>
# <swiftbar.version>1.0</swiftbar.version>
# <swiftbar.desc>Connect keyboard and mouse to Gamepi over SSH</swiftbar.desc>
# <swiftbar.refreshOnOpen>true</swiftbar.refreshOnOpen>
exec @PYTHON@ @CONTROLLER@ "$@"
