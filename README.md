# Simple NSIS Installer Template

A simple Nullsoft Installer Template you can use as a starting point for your Windows Installer.

When I say simple, I mean it makes some assumptions:
* Currently does checks for Windows 10 and above, and the OS architecture is 64-bit. If these requirements aren't met, it closes after showing the user a message. If you don't want this, you can comment it out in `installer.nsi`.
* It assumes the app you're installing is 64-bit, and installs files under `"$PROGRAMFILES64\${COMPANY_NAME}\${APP_NAME}"` where COMPANY_NAME and APP_NAME are defined in `build_config.json` and `$PROGRAMFILES64` is the 64-bit Program Files folder. If you need to install under the 32-bit Program Files folder (or both conditionally) you'll need to make changes.
* Requires admin permission to install. This seems to be the most common scenaro, but if you need to change it, you can change `RequestExecutionLevel admin`, `SetShellVarContext all` and the install path.
* Doesn't have code-signing support. If you need it, you'll have to add it yourself to the build script.

Some features:
* You can easily specify what files/folders get installed by specifying the path to their parent folder in the `app_files_parent` field within `build_config.json`, documented below.
* Only files/folders that are installed will be deleted during uninstall. This protects the user's machine/files.
* You can pass `/BYPASS=TRUE` to the installer to bypass the OS version check and the architecture check at runtime. This is for futureproofing.

# How to build the installer

[Nullsoft Install System](https://sourceforge.net/projects/nsis/) version 3.09 or above is required. Once installed, add it's `bin` folder to your PATH environment variable.

[Python3](https://www.python.org/downloads/) is required for the build script. I used version 3.11.3, but previous versions of 3 may work.

Since this is a template, you should always clone a new copy of this repo for each installer you need.

```
git clone git@github.com:gordonglas/nsis-installer-template.git awesome-game-installer
```

Update variables in `build_config.json`

Build with the python3 build script `build.py`:

```
python build.py
```

You can also pass the build config file as a parameter if you want to maintain multiple configurations in the same repo:

```
python build.py -c build_config.json
```

The build script uses variables in `build_config.json` to configure and build the installer. When a user runs the installer, it will add the entry in `Add/Remove Programs`, so the user can uninstall in the usual way.

# build_config.json fields

Note: The build.py script will validate a lot of this for you, but it's nice to have it listed somewhere:

* `installer_version` and `app_version` - The version number for the installer and your app, respectively.
* `copyright_year` - Leave blank for current year, or set it to a specific year.
* `app_name` - The name or your app.
* `company_name` - Used as part of the install path to keep your app separate from other companies.
* `installer_filename` - The installer exe name.
* `installer_icon_path` - The icon for the installer, whose path is absolute or relative to the build script.
* `app_files_parent` - Parent folder of the files/folders you want to be installed on the user's machine, whose path is absolute or relative to the build script.
* `license_txt_path` - The license text file. Relative to app_files_parent. (Yes it must be under app_files_parent, so it also gets installed.)
* `main_file` - Usually the main exe that will run from the start menu and desktop shortcuts. Relative to app_files_parent.
* `icon_path` - Your app's icon. Relative to app_files_parent. (Yes it must be under app_files_parent, so it gets installed and `Add/Remove Programs` can properly show it.)
* `create_desktop_shortcut` - `true` or `false` to have the installer create a desktop shortcut to `main_file`.
* `create_start_menu_shortcut` - `true` or `false` to have the installer create a start menu shortcut to `main_file`.
