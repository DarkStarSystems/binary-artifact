# Build-binary-artifact

`build-binary-artifact.py` is a simple binary artifact generator. It
creates zip files with specific filename formats, a content signature,
and a manifest for trackability.

`build-binary-artifact.py` is basically a glorified zip creator. To
use it normally:

```
build-binary-artifact.py --name foo --base-version 1.0 --build-id 1 <FILE_OR_DIR>...
```

That creates a file `foo-1.0-1-2018.10.11-<sha>.zip` where the SHA is
the signature of the dir's contents. `base-version` is the version of
the thing you're packaging. The created zip file just contains the dir
itself, and a `foo-manifest` file for tracking, containing all the
metadata (name, version, build date, build machine, git SHA if
available, etc.)

Why is it better than just using zip? Mainly because it names the
resulting file uniquely, which makes everything totally trackable. And
on the target system you can check the manifest file from where you
unzipped it to see what's actually there, find out when/where/who
built it, etc.

It's scriptable so it's easy to include in any build tool.

To use the resulting binary artifact files: they're just standard Zip
files, so unzip and do whatever you'd normally do.

## Getting Started

Download this repo and copy `build-binary-artifact.py` somewhere on
your path.

### Usage:

```
usage: build-binary-artifact.py [-h] --base-version BASE_VERSION --name NAME
                                [--bits BITS] [--build-id BUILD_ID]
                                [--build-branch BUILD_BRANCH]
                                [--build-date BUILD_DATE]
                                [--build-machine BUILD_MACHINE] [--os OS]
                                [--build-os BUILD_OS] [--note NOTE]
                                [--author AUTHOR] [--chdir CHDIR]
                                [--outdir OUTDIR] [--silent] [--tar]
                                [--name-only] [--hash-only] [--validate]
                                [--exclude EXCLUDE]
                                dir [dir ...]

Binary Artifact builder
    Make a zip/tarfile called NAME-VER-BUILD-DATE-HASH.tgz from all the files in dirs.
        Include a generated manifest, so the result looks like:
        filename: NAME-VER-BUILD-DATE-HASH.tgz/.zip
        contents:
          NAME-VER-BUILD-DATE-HASH/
            NAME-manifest.txt
            dir1/
            dir2/
              ...

positional arguments:
  dir                   dirs to collect into the binary artifact

optional arguments:
  -h, --help            show this help message and exit
  --base-version BASE_VERSION, -B BASE_VERSION
                        Base version for manifest (default: None)
  --name NAME, -n NAME  Artifact name (human readable). E.g. 'libfoo-mac'.
                        (default: None)
  --bits BITS, -b BITS  bits (32 or 64) (default: 64)
  --build-id BUILD_ID, -i BUILD_ID
                        Build ID (default: git SHA)
  --build-branch BUILD_BRANCH, --branch BUILD_BRANCH
                        Build branch (default: git branch)
  --build-date BUILD_DATE, --date BUILD_DATE, -D BUILD_DATE
                        Build date (default: now)
  --build-machine BUILD_MACHINE, --machine BUILD_MACHINE, -m BUILD_MACHINE
                        Build machine (default: machine name)
  --os OS, -o OS        Build machine OS (default: current OS)
  --build-os BUILD_OS, -O BUILD_OS
                        Build machine OS (default: current OS)
  --note NOTE, -N NOTE  Note to put in manifest (one line) (default: None)
  --author AUTHOR, -a AUTHOR
                        Person (username/email) building the archive (default:
                        guessed username)
  --chdir CHDIR, -C CHDIR
                        Change to this dir before starting to archive files.
                        Useful if dir is in a subdir or elsewhere on disk and
                        you don't want the intervening dir names in the final
                        archive. (default: None)
  --outdir OUTDIR       Directory in which to create the output zip/tar file.
                        (default: .)
  --silent, -s          Skip printing the manifest file contents on stdout
                        (default: False)
  --tar, -T             Create a tar (tgz) file instead of zip (default:
                        False)
  --name-only           Don't build the archive; just return the name of the
                        tar/zip file. (Requires hashing contents.) (default:
                        False)
  --hash-only           Don't build the archive; just return the hash of the
                        given dir. (default: False)
  --validate            Validate an unpacked archive by checking its hash
                        against the manifest. (default: False)
  --exclude EXCLUDE     Exclude this filename from the archive. May be
                        repeated. (default: None)
  --top-dir-name TOP_DIR_NAME, -t TOP_DIR_NAME
                        Top dir of the resulting zip: Default=None means use
                        the full name of the zip. A string means use that name
                        as the top dir. '.' means no top dir; put the manifest
                        and contents at top level. (default: None)
```
The following arguments are required: `--base-version`/`-B`, `--name`/`-n`, `dir`.

If `git` is available, the tool tries to inspect the dir and infer
`build-branch` and `build-id` from git. It defaults `build-machine`
from the current machine name, `build-date` defaults to now, and
`build-os` defaults to the current OS.

`build-binary-artifact.py` has three additional modes besides creating
the artifact:
 * `validate`: verifies an existing unpacked archive by checking the
   content hash against the manifest
 * `name-only`: don't build, just return the filename. This is useful
   for build systems that want to know the names of targets before
   they're created.
 * `hash-only`: don't build, just return the content hash.

### Example:

This packages build-binary-artifact itself (the git working dir) as a
binary artifact. It excludes the `.git` folder.

```
% ls
binary-artifact

% python binary-artifact/build-binary-artifact.py --base-version 1.0 \
   --build-id 1 --exclude .git --name build-binary-artifact binary-artifact
Created binary artifact ./build-binary-artifact-1.0-1-2018.10.17-99b6130f5a6f51a3.zip
base-version: 1.0
name: build-binary-artifact
os: Windows
bits: 64
author: garyo
build-id: 1
build-branch: None
build-date: Wed Oct 17 10:29:54 2018
build-machine: tower1
build-os: Windows 10 10.0.17134 AMD64
note: None
fullname: build-binary-artifact-1.0-1-2018.10.17-99b6130f5a6f51a3
content-hash: 99b6130f5a6f51a3
Wrote .\build-binary-artifact-1.0-1-2018.10.17-99b6130f5a6f51a3.zip
%
```

### Prerequisites

Python 2.7 or 3.6+

### Installing

Eventually this tool will be installable via `pip install build-binary-artifact`
but for now, just download the repo.

## Running the tests

TBD


## Contributing

Pull requests and issues gratefully accepted!

## Authors

* [Gary Oberbrunner](https://github.com/garyo) at Boris FX, Inc. (current maintainer)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
