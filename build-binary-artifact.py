# MIT License

# Copyright 2018 BorisFX, Inc

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:


# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
import sys, os
import string
import socket                   # for machine name
import getpass                  # for getuser
import platform
import fnmatch, glob
import tempfile
import time, datetime
import subprocess
import tarfile, zipfile

def write_manifest(name, args, extra):
    """Write a manifest file from the args."""
    with open(name, "w") as f:
        keys=["base-version",
              "name",
              "os",
              "bits",
              "author",
              "build-id",
              "build-branch",
              "build-date",
              "build-machine",
              "build-os",
              "note"]
        for k in keys:
            arg_key = k.translate(string.maketrans("-","_"))
            line = "%s: %s\n" % (k, getattr(args, arg_key))
            f.write(line)
            if not args.silent:
                sys.stdout.write(line)
        if extra is not None:
            f.write(extra)
            if not args.silent:
                sys.stdout.write(extra)

# http://stackoverflow.com/questions/24937495
# http://akiscode.com/articles/sha-1directoryhash.shtml
# Copyright (c) 2009 Stephen Akiki
# MIT Licensed
def hash_dir_contents(dirs, ignore_pattern=None, verbose=False):
    """Returns a hash (hex digest) of contents of the dir."""
    import hashlib, os
    SHAhash = hashlib.sha1()

    if type(dirs) == type(""):
        dirs = [dirs]

    for d in sorted(dirs):
        if not os.path.exists (d):
            raise IOError("Dir %s does not exist"%d)
        if os.path.isfile(d):
            if verbose:
                print "Updating SHA with top-level file %s"%(d)
            try:
                SHAhash.update(d)
            except Exception as e:
                raise RuntimeError("hash_dir_contents: exception %s processing %s"%(e, d))
        else:
            try:
                for root, dirs, files in os.walk(d):
                    relpath = os.path.relpath(root, d)
                    dirs.sort()           # make sure order is stable
                    for name in sorted(files):
                        if ignore_pattern and fnmatch.fnmatch(name, ignore_pattern):
                            # print "Ignoring %s" % name
                            continue
                        filepath = os.path.join(root,name)
                        # make this stable across OSes since it could be compared on a different OS
                        # (only used for hashing)
                        relfilepath = os.path.normpath(os.path.join(relpath, name)).replace('\\', '/')
                        SHAhash.update(relfilepath)
                        if verbose:
                            print "Updating SHA with file %s"%(relfilepath)
                        try:
                            f1 = open(filepath, 'rb')
                        except:
                            raise IOError("Can't open %s for hashing"%filepath)
                        while 1:
                            # Read file in as little chunks
                            buf = f1.read(16384)
                            if not buf:
                                break
                            SHAhash.update(buf)
                        f1.close()
            except Exception as e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                raise RuntimeError("hash_dir_contents: exception '%s' processing '%s'"%(e, d))
    return SHAhash.hexdigest()[0:16]

def make_tarfile(dirs, manifest, manifest_name, top_level_name, outdir, exclude=None):
    """Make a tarfile named <top_level_name>.tgz from all the files in dir
    Include the manifest, so the result looks like:
    tar filename: <top_level_name>.tgz
    contents:
      top_level_name/
        <manifest>
        dir/
          ...
    Note: exclude is not yet implemented.
    """
    tarfilename = os.path.join(outdir, "%s.tgz" % top_level_name)
    with tarfile.open(tarfilename, 'w:gz') as f:
        f.add(manifest, '%s/%s' % (top_level_name, manifest_name))
        for dir in dirs:
            f.add(dir, '%s/%s' % (top_level_name, dir))
    return tarfilename

def make_zipfile(dirs, manifest, manifest_name, top_level_name, outdir, exclude=None):
    """Make a zipfile named <top_level_name>.zip from all the files in dir
    Include the manifest, so the result looks like:
    zip filename: <top_level_name>.zip
    contents:
      top_level_name/
        <manifest>
        dir/
          ...
    Exclude any filename in the exclude list
    """
    zipfilename = os.path.join(outdir, "%s.zip" % top_level_name)
    with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(manifest, '%s/%s' % (top_level_name, manifest_name))
        for dir in dirs:
            f.write(dir, '%s/%s' % (top_level_name, dir))
            for root, dirs, files in os.walk(dir):
                for file in files:
                    if exclude is None or file not in exclude:
                        name = os.path.join(root, file)
                        f.write(name, '%s/%s' % (top_level_name, name))
    return zipfilename

def fullname(args, hash):
    """Return the "full" name of the file, with the relevant args and date included.
    No file extension, just the interpolated name fields."""
    today = datetime.date.today()
    datestr = "%04d.%02d.%02d" % (today.year, today.month, today.day)
    if args.build_id != "":
        outname="%s-%s-%s-%s-%s" % (args.name, args.base_version, args.build_id, datestr, hash) # no ext
    else:
        outname="%s-%s-%s-%s" % (args.name, args.base_version, datestr, hash) # no ext

    return outname

def create_artifact(args):
    orig_cwd=os.getcwd()
    if args.chdir:
        os.chdir(args.chdir)
    hash = hash_dir_contents(sorted(args.dir), ignore_pattern="*-manifest.txt")
    outname = fullname(args, hash)
    manifest_name = '%s-manifest.txt' % args.name
    file, manifest = tempfile.mkstemp(prefix='%s-manifest'%args.name)
    os.close(file)
    extra = "fullname: %s\ncontent-hash: %s\n" % (outname, hash)
    write_manifest(manifest, args, extra)
    outdir_path = os.path.join(orig_cwd, args.outdir) # note: this is OK if args.outdir is absolut
    for d in args.dir:
        existing_manifest = os.path.join(d, manifest_name)
        if os.path.exists(existing_manifest):
            print "WARNING: %s already exists in source dir %s; deleting from source!" % (manifest_name, d)
            os.unlink(existing_manifest)
    if args.tar:
        resultfile = make_tarfile(args.dir, manifest, manifest_name, outname, outdir_path, args.exclude)
    else:
        resultfile = make_zipfile(args.dir, manifest, manifest_name, outname, outdir_path, args.exclude)
    os.unlink(manifest)
    if not args.silent:
        print "Wrote %s"%resultfile
    sys.stderr.write("Created binary artifact %s\n" %resultfile)

def print_artifact_name(args):
    orig_cwd=os.getcwd()
    if args.chdir:
        os.chdir(args.chdir)
    hash = hash_dir_contents(args.dir, ignore_pattern="*-manifest.txt")
    print fullname(args, hash)

def print_artifact_hash(args):
    orig_cwd=os.getcwd()
    if args.chdir:
        os.chdir(args.chdir)
    hash = hash_dir_contents(args.dir, ignore_pattern="*-manifest.txt")
    print hash

def validate_archive(args):
    """Validate that an unpacked archive has the correct hash.
    Looks in dir specified by args.dir (not args.chdir).
    Exits with status 1 if mismatch.
    """
    dir = args.dir[0]
    print "Validating archive in %s" % dir
    manifest = glob.glob("%s/*-manifest.txt" % dir)[0]
    if not manifest:
        print "No manifest found in %s; can't validate." % dir
        return
    manifest_contents = open(manifest, 'rb').read(1024*1024).splitlines()
    hashline = [x for x in manifest_contents if x.startswith("content-hash: ")]
    if hashline == []:
        print "Can't find hash line in manifest %s" % manifest
        return
    key, expected = hashline[0].split(': ')
    hash = hash_dir_contents(dir, ignore_pattern="*-manifest.txt")
    if hash != expected:
        print "Hash mismatch: actual %s, expected %s" % (hash, expected)
        sys.exit(1)
    print "Hash OK: %s."%hash

def cmd(cmd, name):
    """Run shell command; if it fails, return None."""
    try:
        # Use Popen here in case we care about stderr, e.g. for debugging this code.
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        stat = proc.returncode
        if stat == 0:
            return stdout.strip()
        else:
            return None
    except Exception as e:
        # Don't print here; wait to see if user specifies it on cmd line
        return None


def main(argv=None):
    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                          argparse.RawDescriptionHelpFormatter):
        pass

    try:
        parser = argparse.ArgumentParser(description="""Binary Artifact builder
    Make a zip/tarfile called NAME-VER-BUILD-DATE-HASH.tgz from all the files in dirs.
        Include a generated manifest, so the result looks like:
        filename: NAME-VER-BUILD-DATE-HASH.tgz/.zip
        contents:
          NAME-VER-BUILD-DATE-HASH/
            NAME-manifest.txt
            dir1/
            dir2/
              ...""",
                                         formatter_class=CustomFormatter)
        parser.add_argument('--base-version', '-B', required=True,
                            help="""Base version for manifest""")
        parser.add_argument('--name', '-n', required=True,
                            help="""Artifact name (human readable). E.g. 'mocha-bcc-mac'.""")
        parser.add_argument('--bits', '-b', type=int, default=64,
                            help="""bits (32 or 64)""")
        parser.add_argument('--build-id', '-i',
                            default=cmd("git rev-parse --short=10 HEAD", 'build-id'),
                            help="""Build ID""")
        parser.add_argument('--build-branch', '--branch',
                            default=cmd("git rev-parse --abbrev-ref HEAD", 'build-branch'),
                            help="""Build branch""")
        parser.add_argument('--build-date', '--date', '-D',
                            default=time.ctime(),
                            help="""Build date""")
        parser.add_argument('--build-machine', '--machine', '-m',
                            default=socket.gethostname(),
                            help="""Build machine""")
        parser.add_argument('--os', '-o',
                            default=platform.uname()[0],
                            help="""Build machine OS""")
        parser.add_argument('--build-os', '-O',
                            default=' '.join([platform.uname()[i] for i in (0,2,3,4)]),
                            help="""Build machine OS""")
        parser.add_argument('--note', '-N',
                            help="""Note to put in manifest (one line)""")
        parser.add_argument('--author', '-a',
                            default=getpass.getuser(),
                            help="""Person (username/email) building the archive""")
        parser.add_argument('--chdir', '-C',
                            help="""Change to this dir before starting to archive files.\n"""
                            """Useful if dir is in a subdir or elsewhere on disk and you don't\n"""
                            """want the intervening dir names in the final archive.""")
        parser.add_argument('--outdir',
                            default='.',
                            help="""Directory in which to create the output zip/tar file.""")
        parser.add_argument('--silent', '-s', action='store_true',
                            help="""Skip printing the manifest file contents on stdout""")
        parser.add_argument('--tar', '-T', action='store_true',
                            help="""Create a tar (tgz) file instead of zip""")
        parser.add_argument('--name-only', action='store_true',
                            help="""Don't build the archive; just return the name of the tar/zip file. (Requires hashing contents.)""")
        parser.add_argument('--hash-only', action='store_true',
                            help="""Don't build the archive; just return the hash of the given dir.""")
        parser.add_argument('--validate', action='store_true',
                            help="""Validate an unpacked archive by checking its hash against the manifest.""")
        parser.add_argument('--exclude', action='append',
                            help="""Exclude this filename from the archive. May be repeated.""")
        parser.add_argument('dir', nargs='+',
                            help="""dirs to collect into the binary artifact""")
        args = parser.parse_args(argv)

        if args.build_branch is None:
            print "Warning: Can't get default value for --build-branch; using None."
        if args.build_id is None:
            print "Warning: Can't get default value for --build-id; using None."

        if args.validate:
            validate_archive(args)
        elif args.hash_only:
            print_artifact_hash(args)
        elif args.name_only:
            print_artifact_name(args)
        else:
            create_artifact(args)
        return 0
    except RuntimeError as e:
        print e
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
