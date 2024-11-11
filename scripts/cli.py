"""Frida gadget injector for Android APK"""
import os
import sys
import shutil
import subprocess
from shutil import which
from pathlib import Path
import click
from androguard.core.apk import APK
from .logger import logger
from .__version__ import __version__
from .frida_github import FridaGithub
from .uber_apk_signer_github import UberApkSignerGithub
from . import INSTALLED_FRIDA_VERSION


p = Path(__file__)
ROOT_DIR = p.parent.resolve()
TEMP_DIR = ROOT_DIR.joinpath('temp')
FILE_DIR = ROOT_DIR.joinpath('files')

APKTOOL = which("apktool")
if not APKTOOL:
    raise FileNotFoundError(
        "Please download the 'apktool' and set it to your PATH environment.")

def run_apktool(option: list, apk_path: str):
    """Run apktool with option

    Args:
        option (list|str): option of apktool
        apk_path (str): path of apk file

    """

    pipe = subprocess.PIPE
    cmd = [APKTOOL] + option + [apk_path]
    with subprocess.Popen(cmd, stdin=pipe, stdout=sys.stdout, stderr=sys.stderr) as process:
        process.communicate(b"\n")
        if process.returncode != 0:
            if 'b' in option:
                recommend_options = []
                if '--use-aapt2' not in option:
                    recommend_options += ['--use-aapt2']
                if '--no-res' not in option:
                    recommend_options += ['--no-res']

                if recommend_options:
                    logger.error("It seems like you're facing issues with Apktool.\n"
                                 "I would suggest considering the '%s' options or opting for a hands-on approach "
                                 "by using the '--skip-recompile' option.", ", ".join(recommend_options))
                else:
                    logger.error("Try recompile the APK manually using the "
                                 "'--skip-recompile' option.")

            if 'd' in option:
                logger.error("Try decompile the APK manually using the '--skip-decompile' option.")

            raise subprocess.CalledProcessError(process.returncode, cmd,
                                                sys.stdout, sys.stderr)
        return True

def download_gadget(arch: str):
    """Download the frida gadget library

    Args:
        arch (str): architecture of the device
    """
    logger.debug("Auto-detected your frida version: %s", INSTALLED_FRIDA_VERSION)
    frida_github = FridaGithub(INSTALLED_FRIDA_VERSION)
    assets = frida_github.get_assets()
    file = f'frida-gadget-{INSTALLED_FRIDA_VERSION}-android-{arch}.so.xz'
    for asset in assets:
        if asset['name'] == file:
            logger.debug("Downloading the frida gadget library(%s) for %s",
                         INSTALLED_FRIDA_VERSION,
                         arch)
            so_gadget_path = str(FILE_DIR.joinpath(file[:-3]))
            return frida_github.download_gadget_so(asset['browser_download_url'], so_gadget_path)

    raise FileNotFoundError(f"'{file}' not found in the github releases")

def download_signer():
    """Download the Uber Apk Signer
    """
    signer_github = UberApkSignerGithub()
    assets = signer_github.get_assets()
    file = f'uber-apk-signer-{signer_github.signer_version}.jar'
    signer_path = str(FILE_DIR.joinpath(file))
    if os.path.exists(signer_path):
        return signer_path

    logger.debug("Downloading the %s file for signing", file)    
    return signer_github.download_signer_jar(assets, signer_path)

def insert_loadlibary(decompiled_path, main_activity, load_library_name):
    """Inject loadlibary code to main activity

    Args:
        decompiled_path (str): decomplied path of apk file
        main_activity (str): main activity of apk file
        load_library_name (str): name of load library
    """
    logger.debug('Searching for the main activity in the smali files')
    target_smali = None

    target_relative_path = main_activity.replace(".", os.sep)
    for directory in decompiled_path.iterdir():
        if directory.is_dir() and directory.name.startswith("smali"):
            target_smali = directory.joinpath(target_relative_path + ".smali")
            if target_smali.exists():
                break

    if not target_smali or not target_smali.exists():
        raise FileNotFoundError(f"The target class file {target_smali} was not found.")

    logger.debug("Found the main activity at '%s'", str(target_smali))
    text = target_smali.read_text()

    text = text.replace(
        "invoke-virtual {v0, v1}, Ljava/lang/Runtime;->exit(I)V", "")
    text = text.split("\n")

    logger.debug(
        'Locating the entrypoint method and injecting the loadLibrary code')
    status = False
    entrypoints = [" onCreate(", "<init>"]
    for entrypoint in entrypoints:
        idx = 0
        while idx != len(text):
            line = text[idx].strip()
            if line.startswith('.method') and entrypoint in line:
                if ".locals" not in text[idx + 1]:
                    idx += 1
                    continue

                if load_library_name.startswith('lib'):
                    load_library_name = load_library_name[3:]
                text.insert(idx + 2,
                            "    invoke-static {v0}, "
                            "Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V")
                text.insert(idx + 2,
                            f"    const-string v0, "
                            f"\"{load_library_name}\"")
                status = True
                break
            idx += 1

        if status:
            break

    if not status:
        logger.error(
            "Cannot find the appropriate position in the main activity.")
        logger.error(
            "Please report the issue at %s with the following information:", 
            'https://github.com/ksg97031/frida-gadget/issues')
        logger.error("APK Name: <Your APK Name>")
        logger.error("APK Version: <Your APK Version>")
        logger.error("APKTOOL Version: <Your APKTOOL Version>")
        sys.exit(-1)

    # Replace the smali file with the new one
    target_smali.write_text("\n".join(text))

def modify_manifest(decompiled_path):
    """Modify manifest permssions

    Args:
        decompiled_path (str): decomplied path of apk file
    """
    # Add internet permission
    logger.debug("Checking internet permission and extractNativeLibs settings")
    android_manifest = decompiled_path.joinpath("AndroidManifest.xml")
    txt = android_manifest.read_text(encoding="utf-8")
    pos = txt.index('</manifest>')
    permission = 'android.permission.INTERNET'

    if permission not in txt:
        logger.debug(
            "Adding 'android.permission.INTERNET' permission to AndroidManifest.xml")
        permissions_txt = f"<uses-permission android:name='{permission}'/>"
        txt = txt[:pos] + permissions_txt + txt[pos:]

    # Set extractNativeLibs to true
    if ':extractNativeLibs="false"' in txt:
        logger.debug('Editing the extractNativeLibs="true"')
        txt = txt.replace(':extractNativeLibs="false"',
                            ':extractNativeLibs="true"')
    android_manifest.write_text(txt, encoding="utf-8")

def inject_gadget_into_apk(apk_path:str, arch:str, decompiled_path:str, main_activity:str = None, config:str = None):
    """Inject frida gadget into an APK

    Args:
        apk (APK): path of apk file
        arch (str): architecture of the device
        decompiled_path (str): decomplied path of apk file

    Raises:
        FileNotFoundError: file not found
        NotImplementedError: not implemented
    """
    apk = APK(apk_path)
    gadget_path = download_gadget(arch) # Download gadget library
    gadget_name = Path(gadget_path).name
    if not main_activity:
        main_activity = apk.get_main_activity()

    if not main_activity:
        if len(apk.get_activities()) == 1:
            logger.warn("The main activity was not found.\n"
                        "Using the first activity from the manifest file.")
            main_activity = apk.get_activities()[0]
        else:
            logger.error("The main activity was not found.\n"
                        "Please specify the main activity using the --main-activity option.\n"
                        "Select the activity from %s", apk.get_activities())
            sys.exit(-1)
    # Apply permission to android manifest
    modify_manifest(decompiled_path)

    # Search the main activity from smali files
    load_library_name = gadget_name[:-3]
    insert_loadlibary(decompiled_path, main_activity, load_library_name)

    # Copy the frida gadget library to the lib directory
    lib = decompiled_path.joinpath('lib')
    if not lib.exists():
        lib.mkdir()
    arch_dirnames = {'arm': 'armeabi-v7a', 'x86':'x86', 'arm64': 'arm64-v8a', 'x86_64':'x86_64'}
    if arch not in arch_dirnames:
        raise NotImplementedError(f"The architecture '{arch}' is not supported.")

    arch_dirname = arch_dirnames[arch]
    lib = lib.joinpath(arch_dirname)
    if not lib.exists():
        lib.mkdir()

    lib_library_name = gadget_name
    if not lib_library_name.startswith('lib'):
        lib_library_name = 'lib' + gadget_name
    shutil.copy(gadget_path, lib.joinpath(lib_library_name))


    # Upload gadget config file
    upload_files = {'config': config}

    for file_type, file_path in upload_files.items():
        if file_path:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error("Frida %s file not found: %s", file_type, file_path)
                sys.exit(-1)
            else:
                target_name = f"lib{load_library_name}.{file_type}.so"
                if file_path.name == target_name:
                    logger.info("Uploading Frida %s file: %s", file_type, file_path.name)
                else:
                    logger.info("Renaming and uploading Frida %s file: %s -> %s", file_type, file_path.name, target_name)
                shutil.copy(file_path, lib.joinpath(target_name))

def sign_apk(apk_path:str):
    """Run uber apk signer with option

    Args:
        apk_path (str): path of apk file

    """
    signer_path = download_signer() # Download apk signer

    pipe = subprocess.PIPE
    cmd = ['java', '-jar', signer_path, '--apks', apk_path]
    with subprocess.Popen(cmd, stdin=pipe, stdout=sys.stdout, stderr=sys.stderr) as process:
        process.communicate(b"\n")
        if process.returncode != 0:
            logger.error("The APK signing process failed.")

            raise subprocess.CalledProcessError(process.returncode, cmd, sys.stdout, sys.stderr)
        return True



def print_version(ctx, _, value):
    """Print version and exit"""
    if not value or ctx.resilient_parsing:
        return
    print(f"frida-gadget version {__version__}")
    ctx.exit()

# pylint: disable=too-many-arguments
@click.command()
@click.option('--arch', default="arm64", help="Target architecture of the device. (options: arm64, x86_64, arm, x86)")
@click.option('--config', help="Upload the Frida configuration file.")
@click.option('--no-res', is_flag=True, help="Do not decode resources.")
@click.option('--main-activity', default=None, help="Specify the main activity if desired.")
@click.option('--sign', is_flag=True, help="Automatically sign the APK using uber-apk-signer.")
@click.option('--skip-decompile', is_flag=True, help="Skip decompilation if desired.")
@click.option('--skip-recompile', is_flag=True, help="Skip recompilation if desired.")
@click.option('--use-aapt2', is_flag=True, help="Use aapt2 instead of aapt.")
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help="Show version and exit.")
@click.argument('apk_path', type=click.Path(exists=True), required=True)
def run(apk_path: str, arch: str, config: str, no_res:bool, main_activity: str,
        sign:bool, skip_decompile:bool, skip_recompile:bool, use_aapt2:bool):
    """Patch an APK with the Frida gadget library"""
    apk_path = Path(apk_path)

    logger.info("APK: '%s'", apk_path)
    logger.info("Gadget Architecture(--arch): %s%s", arch, "(default)" if arch == "arm64" else "")

    arch = arch.lower()
    supported_archs = ['arm', 'arm64', 'x86', 'x86_64']
    if arch not in supported_archs:
        logger.error(
            "The --arch option only supports the following architectures: %s",
            ", ".join(supported_archs)
        )
        sys.exit(-1)

    # Make temp directory for decompile
    decompiled_path = TEMP_DIR.joinpath(str(apk_path.resolve())[:-4])
    if not skip_decompile:
        logger.debug('Decompiling the target APK using apktool\n"%s"', decompiled_path)
        if decompiled_path.exists():
            shutil.rmtree(decompiled_path)
        decompiled_path.mkdir()

        # APK decompile with apktool
        decompile_option = ['d', '-o', str(decompiled_path.resolve()), '-f']
        if no_res:
            decompile_option += ['--no-res']
        run_apktool(decompile_option, str(apk_path.resolve()))
    else:
        if not decompiled_path.exists():
            logger.error("Decompiled directory not found: %s", decompiled_path)
            sys.exit(-1)

    # Process if decompile is success
    inject_gadget_into_apk(apk_path, arch, decompiled_path, main_activity, config)

    # Rebuild with apktool, print apk_path if process is success
    if not skip_recompile:
        logger.debug('Recompiling the new APK using apktool\n"%s"', decompiled_path)

        recompile_option = ['b']
        if use_aapt2:
            recompile_option += ['--use-aapt2']

        run_apktool(recompile_option, str(decompiled_path.resolve()))
        apk_path = decompiled_path.joinpath('dist', apk_path.name)
        if not apk_path.exists():
            logger.error("APK not found: %s", apk_path)
        else:
            logger.info("Success")

        if sign:
            logger.debug('Starting APK signing using uber-apk-signer')
            sign_apk(str(apk_path))

    logger.info(apk_path)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    run()
