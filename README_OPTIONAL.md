Optional dependencies and installation notes
=========================================

This project includes several optional Python packages that enable
enhanced features (face recognition, local TTS, Whisper transcription,
interactive charts). These dependencies are not required to run the
core demo in a minimal environment and are listed in
`requirements_optional.txt`.

macOS notes
-----------

`face_recognition` depends on `dlib` which often requires system
libraries (a C++ toolchain, cmake, etc.). On macOS you can prepare
the system with Homebrew:

  brew install cmake pkg-config openblas

Then install the optional requirements in a virtualenv (recommended):

  ./install_optional.sh

What the install script does
---------------------------

- Creates (or reuses) a virtualenv at `.venv_optional`.
- Activates it and upgrades pip.
- Installs packages from `requirements_optional.txt`.

If you encounter build failures for `dlib`/`face_recognition`, consult
their upstream docs for platform-specific steps. For a simpler setup
consider using a prebuilt wheel on macOS or running on a Linux CI where
many packages have prebuilt binaries.
