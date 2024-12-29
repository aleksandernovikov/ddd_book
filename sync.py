import hashlib
import os
import shutil
from pathlib import Path


def sync(source, dest):
    # imperative shell step 1, gather inputs
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)

    # step 2: call functional core
    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    # imperative shell step 3, apply outputs
    for action, *paths in actions:
        if action == "COPY":
            shutil.copyfile(*paths)
        if action == "MOVE":
            shutil.move(*paths)
        if action == "DELETE":
            os.remove(paths[0])


BLOCKSIZE = 65536


def hash_file(path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def read_paths_and_hashes(root):
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    return hashes


def determine_actions(source_hashes, dest_hashes, source_folder, dest_folder):
    for sha, filename in source_hashes.items():
        if sha not in dest_hashes:
            sourcepath = Path(source_folder) / filename
            destpath = Path(dest_folder) / filename
            yield "COPY", sourcepath, destpath

        elif dest_hashes[sha] != filename:
            olddestpath = Path(dest_folder) / dest_hashes[sha]
            newdestpath = Path(dest_folder) / filename
            yield "MOVE", olddestpath, newdestpath

    for sha, filename in dest_hashes.items():
        if sha not in source_hashes:
            yield "DELETE", dest_folder / filename


def determine_actions2(reader, filesystem, source_root, dest_root):
    source_hashes = reader(source_root)
    dest_hashes = reader(dest_root)

    source_root = Path(source_root)
    dest_root = Path(dest_root)

    for sha, filename in source_hashes.items():
        file_exists_in_dest = sha in dest_hashes
        filenames_match = dest_hashes.get(sha) == filename

        match (file_exists_in_dest, filenames_match):
            case (False, _):
                # Файл отсутствует в dest, копируем его
                source_path = source_root / filename
                dest_path = dest_root / filename
                filesystem.copy(source_path, dest_path)

            case (True, False):
                # Файл есть в dest, но с другим именем, перемещаем его
                old_dest_path = dest_root / dest_hashes[sha]
                new_dest_path = dest_root / filename
                filesystem.move(old_dest_path, new_dest_path)

    for sha, filename in dest_hashes.items():
        if sha not in source_hashes:
            filesystem.delete(dest_root / filename)


class FakeFileSystem(list):
    def copy(self, src, dest):
        self.append(('COPY', src, dest))

    def move(self, src, dest):
        self.append(('MOVE', src, dest))

    def delete(self, dest):
        self.append(('DELETE', dest))
