#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
flutter create . --platforms=android,ios,windows,macos,linux
flutter pub get
flutter analyze
echo "PetroNexa Flutter platforms generated and source analysed."
