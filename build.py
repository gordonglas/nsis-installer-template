# Build the Windows Nullsoft Installer.
# Run help to see usage:
#   `python build.py -h`

import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

# Holds data from build_config.json
class BuildConfig:
    installer_version = ''
    app_version = ''
    copyright_year = ''
    app_name = ''
    company_name = ''
    installer_filename = ''
    installer_icon_path = ''
    app_files_parent = ''
    license_txt_path = ''
    main_file = ''
    icon_path = ''
    create_desktop_shortcut = True
    create_start_menu_shortcut = True

# Get path containing this script,
# regardless of current working directory
def get_script_path() -> str:
    return os.path.dirname(os.path.realpath(__file__))

# Read build_config.json file into BuildConfig vars.
# Returns tuple of (error, BuildConfig).
def validate_build_config(config):
    error = ''
    cfg = BuildConfig()

    # Read config json file
    data = None
    with open(config, 'rb') as config_file:
        data = json.load(config_file)

    # installer_version
    if 'installer_version' not in data or data['installer_version'] == '':
        return f'"installer_version" not found in {config} or empty', cfg
    cfg.installer_version = data['installer_version']

    # app_version
    if 'app_version' not in data or data['app_version'] == '':
        return f'"app_version" not found in {config} or empty', cfg
    cfg.app_version = data['app_version']

    # copyright_year
    if 'copyright_year' not in data:
        return f'"copyright_year" not found in {config}', cfg
    cfg.copyright_year = data['copyright_year']
    # if copyright_year is empty, use current year
    if cfg.copyright_year == '':
        cfg.copyright_year = str(datetime.date.today().year)

    # app_name
    if 'app_name' not in data or data['app_name'] == '':
        return f'"app_name" not found in {config} or empty', cfg
    cfg.app_name = data['app_name']

    # company_name
    if 'company_name' not in data or data['company_name'] == '':
        return f'"company_name" not found in {config} or empty', cfg
    cfg.company_name = data['company_name']

    # installer_filename
    if 'installer_filename' not in data or data['installer_filename'] == '':
        return f'"installer_filename" not found in {config} or empty', cfg
    cfg.installer_filename = data['installer_filename']

    # installer_icon_path
    if 'installer_icon_path' not in data or data['installer_icon_path'] == '':
        return f'"installer_icon_path" not found in {config} or empty', cfg
    installer_icon_abs = os.path.abspath(data['installer_icon_path'])
    if os.path.islink(installer_icon_abs) or not os.path.isfile(installer_icon_abs):
        return f'"installer_icon_path" (defined in {config}) must be a file, whose path is absolute or relative to this script', cfg
    cfg.installer_icon_path = installer_icon_abs

    # 'app_files_parent' is the parent folder of the files/folders to install
    # to the user's machine during install.
    # It's either an absolute path, or relative path to this build script.
    if 'app_files_parent' not in data or data['app_files_parent'] == '':
        return f'"app_files_parent" not found in {config} or empty', cfg
    if os.path.islink(data['app_files_parent']) or not os.path.isdir(data['app_files_parent']):
        return f'"app_files_parent" (defined in {config}) must be a directory, whose path is absolute or relative to this script', cfg
    # os.path.abspath will convert slashes to backslashes for us, which we need for NSIS paths.
    cfg.app_files_parent = os.path.abspath(data['app_files_parent'])

    # license_txt_path is relative to app_files_parent in build_config.json,
    # but NSIS needs an absolute path.
    if 'license_txt_path' not in data or data['license_txt_path'] == '':
        return f'"license_txt_path" not found in {config} or empty', cfg
    license_abs = os.path.abspath(os.path.join(cfg.app_files_parent, data['license_txt_path']))
    if os.path.islink(license_abs) or not os.path.isfile(license_abs):
        return f'"license_txt_path" (defined in {config}) must be a file relative to app_files_parent', cfg
    cfg.license_txt_path = license_abs

    # main_file is usually the main exe that will run from the start menu
    # and desktop shortcuts. It's relative to app_files_parent.
    if 'main_file' not in data or data['main_file'] == '':
        return f'"main_file" not found in {config} or empty', cfg
    main_file_abs = os.path.abspath(os.path.join(cfg.app_files_parent, data['main_file']))
    if os.path.islink(main_file_abs) or not os.path.isfile(main_file_abs):
        return f'"main_file" (defined in {config}) must be a file relative to app_files_parent', cfg
    cfg.main_file = data['main_file'].replace('/', '\\')

    # icon_path is relative to app_files_parent.
    if 'icon_path' not in data or data['icon_path'] == '':
        return f'"icon_path" not found in {config} or empty', cfg
    icon_path_abs = os.path.abspath(os.path.join(cfg.app_files_parent, data['icon_path']))
    if os.path.islink(icon_path_abs) or not os.path.isfile(icon_path_abs):
        return f'"icon_path" (defined in {config}) must be a file relative to app_files_parent', cfg
    cfg.icon_path = data['icon_path'].replace('/', '\\')

    # create_desktop_shortcut determines if the installer will
    # create a desktop shortcut to the main_file or not.
    if 'create_desktop_shortcut' not in data or not (data['create_desktop_shortcut'] == True or data['create_desktop_shortcut'] == False):
        return f'"create_desktop_shortcut" not found in {config} or invalid. Valid values are true or false.', cfg
    cfg.create_desktop_shortcut = data['create_desktop_shortcut']

    # create_start_menu_shortcut determines if the installer will
    # create a start menu shortcut to the main_file or not.
    if 'create_start_menu_shortcut' not in data or not (data['create_start_menu_shortcut'] == True or data['create_start_menu_shortcut'] == False):
        return f'"create_start_menu_shortcut" not found in {config} or invalid. Valid values are true or false.', cfg
    cfg.create_start_menu_shortcut = data['create_start_menu_shortcut']

    return error, cfg

# Run a command, wait for it to finish, then display its output
def run_command(cmd):
    error = ''
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    if process.stdout == None:
        error = 'Popen failed'
        return error

    for line in process.stdout:
        ln = line.decode()
        if ln.startswith("Error "):
            error = ln
        sys.stdout.write(ln)

    return error

def error_quit(error, orig_cwd) -> int:
    print(error)
    os.chdir(orig_cwd)
    return 1

def main() -> int:
    parser = argparse.ArgumentParser(description='Configures and builds a Windows Installer.\
                                     Requires makensis.exe in your PATH.')
    parser.add_argument('-c', '--config',
                        help='build-config file (default: build_config.json)',
                        default='build_config.json')
    args = parser.parse_args()
    config = args.config

    orig_cwd = os.getcwd()
    script_path = get_script_path()
    os.chdir(script_path)

    # Read build_config.json file into vars
    (error, cfg) = validate_build_config(config)
    if error != '':
        return error_quit(error, orig_cwd)

    # Create bin folder under NsisInstaller folder
    Path("NsisInstaller/bin").mkdir(parents=True, exist_ok=True)

    # Use BuildConfig to form statements for InstallerVars.nsh.
    vars_nsh = os.path.abspath('NsisInstaller/inc/InstallerVars.nsh')

    with open(vars_nsh, 'w') as vars_nsh_handle:
        vars_nsh_handle.write('; generated by build.py\n')
        vars_nsh_handle.write(f'!define INSTALLER_VERSION "{cfg.installer_version}"\n')
        vars_nsh_handle.write(f'!define APP_VERSION "{cfg.app_version}"\n')
        vars_nsh_handle.write(f'!define COPYRIGHT_YEAR "{cfg.copyright_year}"\n')
        vars_nsh_handle.write(f'!define APP_NAME "{cfg.app_name}"\n')
        vars_nsh_handle.write(f'!define COMPANY_NAME "{cfg.company_name}"\n')
        vars_nsh_handle.write(f'!define INSTALLER_FILENAME "{cfg.installer_filename}"\n')
        vars_nsh_handle.write(f'!define INSTALLER_ICON_PATH "{cfg.installer_icon_path}"\n')
        vars_nsh_handle.write(f'!define LICENSE_TXT_PATH "{cfg.license_txt_path}"\n')
        vars_nsh_handle.write(f'!define MAIN_FILE "{cfg.main_file}"\n')
        vars_nsh_handle.write(f'!define ICON_PATH "{cfg.icon_path}"\n')
        vars_nsh_handle.write(f'!define CREATE_DESKTOP_SHORTCUT "{str(cfg.create_desktop_shortcut).upper()}"\n')
        vars_nsh_handle.write(f'!define CREATE_START_MENU_SHORTCUT "{str(cfg.create_start_menu_shortcut).upper()}"\n')

    # Use files and dirs under app_files_parent to form statements for InstallFiles.nsh.
    # Directories will be used for NSIS 'CreateDirectory' statements.
    # Files will be used for NSIS 'File' statements.
    # Form opposite NSIS 'Delete' and 'RMDir' statements for UninstallFiles.nsh.

    install_files_nsh = os.path.abspath('NsisInstaller/inc/InstallFiles.nsh')
    uninstall_files_nsh = os.path.abspath('NsisInstaller/inc/UninstallFiles.nsh')

    # 'os.scandir' doesn't guarantee any order of files/dirs enumerated,
    # also NSIS 'CreateDirectory' statements need to come before NSIS File statements in InstallFiles.nsh,
    # while NSIS RmDir statements need to come after NSIS Delete statements in UninstallFiles.nsh,
    # so we will make a full pass while caching dirs and files separately.

    # Don't need to use recursion to traverse all sub-folders.
    # Instead, insert sub-folders into a queue and loop through them as we pop them off the queue.
    dirs = []
    files = []
    dirs_queue = []
    dir_prefix = ''
    while True:
        #print(f'entries under {app_files_parent}\\{dir_prefix}')
        with os.scandir(f'{cfg.app_files_parent}\\{dir_prefix}') as itr:
            for entry in itr:
                #file_type = ''
                if entry.is_symlink():
                    continue
                elif entry.is_file(follow_symlinks=False):
                    #file_type = 'f'
                    files.append(f'{dir_prefix}{entry.name}')
                elif entry.is_dir(follow_symlinks=False):
                    #file_type = 'd'
                    dirs.append(f'{dir_prefix}{entry.name}')
                    dirs_queue.append(f'{dir_prefix}{entry.name}')
                #print(f'  {file_type}  {entry.name}')

        if len(dirs_queue) == 0:
            break

        # Process next subfolder in the queue
        dir_prefix = f'{dirs_queue.pop(0)}\\'

    # Write NSIS commands to "InstallFiles.nsh"
    with open(install_files_nsh, 'w') as install_nsh_handle:
        install_nsh_handle.write('; generated by build.py\n')
        # CreateDirectory statements first
        for dir in dirs:
            install_nsh_handle.write(f'CreateDirectory "$INSTDIR\\{dir}"\n')
        # Files last
        for file in files:
            install_nsh_handle.write(f'File "/oname=$INSTDIR\\{file}" "{cfg.app_files_parent}\\{file}"\n')

    # Write NSIS commands to "UninstallFiles.nsh"
    with open(uninstall_files_nsh, 'w') as uninstall_nsh_handle:
        uninstall_nsh_handle.write('; generated by build.py\n')
        # Delete files first
        for file in files:
            uninstall_nsh_handle.write(f'Delete "$INSTDIR\\{file}"\n')
        # RMDir last, but in reverse order, since "dirs" is in hierarchical order.
        # Never use /r switch in RMDir, because we don't want to delete files
        # the user might have added under our folders.
        for dir in reversed(dirs):
            uninstall_nsh_handle.write(f'RMDir "$INSTDIR\\{dir}"\n')

    cmd = "makensis.exe NsisInstaller/installer.nsi"
    print('Build NsisInstaller...')
    print(cmd)
    error = run_command(cmd)
    if error != '':
        print('Build failed. Quitting.')
        os.chdir(orig_cwd)
        return 1

    os.chdir(orig_cwd)
    return 0

if __name__ == '__main__':
    sys.exit(main())
