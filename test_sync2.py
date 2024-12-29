from pathlib import Path

from sync import FakeFileSystem, determine_actions2


def test_when_a_file_exists_in_the_source_but_not_the_destination():
    source = {'sha1': 'my-file'}
    dest = {}
    filesystem = FakeFileSystem()

    reader = {'/source': source, '/dest': dest}
    determine_actions2(reader.pop, filesystem, '/source', '/dest')
    assert filesystem == [('COPY', Path('/source/my-file'), Path('/dest/my-file'))]


def test_when_a_file_has_been_renamed_in_the_source():
    source = {'sha1': 'renamed-file'}
    dest = {'sha1': 'original-file'}

    filesystem = FakeFileSystem()
    reader = {'/source': source, '/dest': dest}
    determine_actions2(reader.pop, filesystem, '/source', '/dest')
    assert filesystem == [('MOVE', Path('/dest/original-file'), Path('/dest/renamed-file'))]
