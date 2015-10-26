# -*- coding: utf-8 -*-
import tarfile
import zipfile
import shutil
import os

def is_archive(filename):
    """
    Returns true if filename is an archive and false otherwise.
    """
    if zipfile.is_zipfile(filename):
        return True
    else:
        try:
            tarfile.open(filename)
            return True
        except:
            pass
    ext = os.path.splitext(filename)[1]
    if ext == '.zip' or ext == '.gz' or \
       ext == '.tar' or ext == '.bz2' or \
       ext == '.tgz':
        return True
    return False

def unpack(input_filename, extract_dir):
    """
    Unpacks the input_filename archive to the extract_dir directory.
    """
    if zipfile.is_zipfile(input_filename):
        unzip(input_filename, extract_dir)
    else:
        untar(input_filename, extract_dir)

def pack(output_filename, source_dir):
    """
    Packs the source_dir directory in the output_filename archive.
    """
    ext = os.path.splitext(output_filename)[1][1:]
    if ext == 'zip':
        pack_zip(output_filename, source_dir)
    elif ext == 'gz' or ext == 'tgz' or ext == 'bz2' or ext == 'tar':
        pack_tar(output_filename, source_dir, ext)
    
def untar(input_filename, extract_dir):
    """
    Extracts the input_filename archive to the extract_dir directory.
    """
    try:
        tar_ds = tarfile.open(input_filename)
    except tarfile.TarError:
        raise "%s is not a tar file" % (input_filename)
    tar_ds.extractall(path=extract_dir)
    tar_ds.close()

def unzip(input_filename, extract_dir):
    """
    Extracts the input_filename archive to the extract_dir directory.
    """
    if not zipfile.is_zipfile(input_filename):
        raise "%s is not a zip file" % (input_filename)
    zip_ds = zipfile.ZipFile(input_filename)
    zip_ds.extractall(path=extract_dir)
    zip_ds.close()

def pack_tar(output_filename, source_dir, type='gz'):
    """
    Creates a tar archive in output_filename from the source_dir directory.
    """
    if type == 'tgz':
        type = 'gz'
    elif type == 'tar':
        type = ''
    tar_ds = tarfile.open(output_filename, 'w:' + type)
    tar_ds.add(source_dir, arcname=os.path.basename(source_dir))
    tar_ds.close()

def pack_zip(output_filename, source_dir):
    """
    Creates a zip archive in output_filename from the source_dir directory.
    """
    previous_dir = os.getcwd()
    os.chdir(os.path.dirname(source_dir))
    zip_ds = zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(os.path.basename(source_dir)):
        for file in files:
            zip_ds.write(os.path.join(root, file))
    zip_ds.close()
    os.chdir(previous_dir)
