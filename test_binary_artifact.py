#! /usr/bin/env python

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

import pytest
import sys, os, os.path, subprocess
import zipfile

@pytest.fixture
def cd_tmp(tmpdir):
    # Invoke this fixture last so paths work out
    dir = os.getcwd()
    print(f'Changing to tmp dir {tmpdir} from {dir}')
    os.chdir(tmpdir)
    yield
    print(f'Changing back to {dir}')
    os.chdir(dir)

@pytest.fixture
def create_artifact():
    topdir = os.getcwd()        # save original top dir to get build-binary-artifact.py
    def _create_artifact(*args, **kwargs):
        cmd_with_args=(sys.executable, os.path.join(topdir, 'build-binary-artifact.py'),
                       *args);
        subprocess.check_output(cmd_with_args)
    return _create_artifact

@pytest.fixture
def get_artifact_name():
    topdir = os.getcwd()
    def _get_artifact_name(*args, **kwargs):
        cmd_with_args=(sys.executable, os.path.join(topdir, 'build-binary-artifact.py'),
                       '--name-only', *args);
        output = subprocess.check_output(cmd_with_args)
        print(f'Artifact name={output}')
        return output.rstrip()
    return _get_artifact_name

@pytest.fixture
def create_test_dir(tmpdir):
    srcdir = tmpdir.mkdir('src')
    subdir = tmpdir.mkdir('src/sub')
    p = srcdir.join('file1.txt')
    p.write('content')
    p = srcdir.join('file2.txt')
    p.write('file 2 content')
    p = subdir.join('subfile1.txt')
    p.write('sub/subfile1 content')
    p = srcdir.join('.hidden.txt')
    p.write('hidden content')

def test_simple(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', 'src')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open(name + '/foo-manifest.txt') as manifest:
            assert(b'base-version: 1.0' in manifest.read())
        with zfile.open(name + '/src/file1.txt') as file1:
            assert(b'content' in file1.read())
        with zfile.open(name + '/src/file2.txt') as file1:
            assert(b'file 2 content' in file1.read())
        with zfile.open(name + '/src/sub/subfile1.txt') as file1:
            assert(b'sub/subfile1 content' in file1.read())
        with pytest.raises(KeyError):
            zfile.open(name + '/src/.hidden.txt') # shouldn't exist

def test_chdir(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', '--chdir', 'src', '.')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open(name + '/foo-manifest.txt') as manifest:
            assert(b'base-version: 1.0' in manifest.read())
        with zfile.open(name + '/file1.txt') as file1:
            assert(b'content' in file1.read())

def test_note(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', 'src', '--note', 'hi there')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open(name + '/foo-manifest.txt') as manifest:
            manifest_contents = manifest.read()
            assert(b'base-version: 1.0' in manifest_contents)
            assert(b'note: hi there' in manifest_contents)
        with zfile.open(name + '/src/file1.txt') as file1:
            assert(b'content' in file1.read())

def test_topdir(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', '--top-dir-name', 'xyz', 'src')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open('xyz' + '/foo-manifest.txt') as manifest:
            assert(b'base-version: 1.0' in manifest.read())
        with zfile.open('xyz' + '/src/file1.txt') as file1:
            assert(b'content' in file1.read())

def test_no_topdir(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', '--top-dir-name', '.', 'src')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open('foo-manifest.txt') as manifest:
            assert(b'base-version: 1.0' in manifest.read())
        with zfile.open('src/file1.txt') as file1:
            assert(b'content' in file1.read())

def test_hidden(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', '--include-hidden', 'src')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open(name + '/foo-manifest.txt') as manifest:
            assert(b'base-version: 1.0' in manifest.read())
        with zfile.open(name + '/src/file1.txt') as file1:
            assert(b'content' in file1.read())
        with zfile.open(name + '/src/.hidden.txt') as file1:
            assert(b'hidden content' in file1.read())

def test_exclude(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', '--exclude', 'file2.txt', 'src')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open(name + '/foo-manifest.txt') as manifest:
            assert(b'base-version: 1.0' in manifest.read())
        with zfile.open(name + '/src/file1.txt') as file1:
            assert(b'content' in file1.read())
        with pytest.raises(KeyError):
            zfile.open(name + '/src/file2.txt')

def test_no_recurse(tmpdir, create_test_dir, create_artifact, get_artifact_name, cd_tmp):
    args = ('--name', 'foo', '-B', '1.0', '--no-recurse', 'src')
    name = get_artifact_name(*args).decode('utf-8')
    create_artifact(*args)
    zip_path = os.path.join(tmpdir, name + '.zip')
    assert(os.path.exists(zip_path))
    with zipfile.ZipFile(zip_path) as zfile:
        with zfile.open(name + '/foo-manifest.txt') as manifest:
            assert(b'base-version: 1.0' in manifest.read())
        with zfile.open(name + '/src/file1.txt') as file1:
            assert(b'content' in file1.read())
        with zfile.open(name + '/src/file2.txt') as file1:
            assert(b'file 2 content' in file1.read())
        with pytest.raises(KeyError):
            zfile.open(name + '/src/.hidden.txt') # shouldn't exist
        with pytest.raises(KeyError):
            zfile.open(name + '/src/sub/subfile1.txt') # shouldn't exist


# end of file
