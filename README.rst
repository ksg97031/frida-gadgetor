frida-gadget
============

|Codacy-Grade| |Docker| |LICENCE|


| ``frida-gadget`` is a tool for patching Android applications to integrate the `Frida Gadget <https://frida.re/docs/gadget/>`_.
| This tool automates the process of downloading the Frida gadget library and injecting the ``loadLibrary`` code into the main activity.


Installation
------------

|Py-Versions| |PyPI-Downloads|

.. code:: sh

    pip install frida-gadget --upgrade

Prerequirement
----------------

| You should install ``apktool`` and add it to your ``PATH`` environment variable.
|   

.. code:: sh

   # Install Apktool on macOS
   brew install apktool
    
   # Add Apktool to your PATH environment variable
   export PATH=$PATH:$HOME/.brew/bin 

| For other operating systems, such as ``Windows``, you can refer to the `Install Guide <https://ibotpeaches.github.io/Apktool/install/>`_.

Usage
------------

.. code:: sh

    $ frida-gadget --help
      Usage: cli.py [OPTIONS] APK_PATH

        Patch an APK with the Frida gadget library
    
      Options:
        --arch TEXT                Target architecture of the device. (options: arm64, x86_64, arm, x86)
        --config TEXT              Upload the Frida configuration file.
        --custom-gadget-name TEXT  Custom name for the Frida gadget.
        --no-res                   Do not decode resources.
        --main-activity TEXT       Specify the main activity if desired. (e.g., com.example.MainActivity)
        --sign                     Automatically sign the APK using uber-apk-signer.
        --skip-decompile           Skip decompilation if desired.
        --skip-recompile           Skip recompilation if desired.
        --use-aapt2                Use aapt2 instead of aapt.
        --version                  Show version and exit.
        --help                     Show this message and exit.

How do I begin?
~~~~~~~~~~~~~~~~~~~~~~
| Simply provide the APK file with the target architecture.
|

.. code:: sh

    $ frida-gadget handtrackinggpu.apk --sign
      [INFO] Auto-detected frida version: 16.1.3
      [INFO] APK: '[REDACTED]/demo-apk/handtrackinggpu.apk'
      [INFO] Auto-detected architecture via ADB: arm64-v8a # Alternatively, specify the architecture with --arch arm64
      [INFO] Gadget Architecture(--arch): arm64(default)
      [DEBUG] Decompiling the target APK using apktool
      [DEBUG] Downloading the frida gadget library for arm64
      [DEBUG] Checking internet permission and extractNativeLibs settings
      [DEBUG] Adding 'android.permission.INTERNET' permission to AndroidManifest.xml
      [DEBUG] Searching for the main activity in the smali files
      [DEBUG] Found the main activity at '[REDACTED]/frida-gadget/tests/demo-apk/handtrackinggpu/smali/com/google/mediapipe/apps/handtrackinggpu/MainActivity.smali'
      [DEBUG] Locating the onCreate method and injecting the loadLibrary code
      [DEBUG] Recompiling the new APK using apktool
      ...
      I: Building apk file...
      I: Copying unknown files/dir...
      I: Built apk into: [REDACTED]/demo-apk/handtrackinggpu/dist/handtrackinggpu.apk
      [INFO] Success
      ...
      

How to Identify?
~~~~~~~~~~~~~~~~~~
| Observe the main activity; the injected `loadLibrary` code will be visible.

.. image:: https://github.com/ksg97031/frida-gadget/blob/trunk/images/decompile.png
   :width: 600

| Furthermore, the Frida gadget library has been injected into your APK.

.. code:: sh

    $ unzip -l [REDACTED]/demo-apk/handtrackinggpu/dist/handtrackinggpu.apk | grep libfrida-gadget
      21133848  09-15-2021 02:28   lib/arm64-v8a/libfrida-gadget-16.1.3-android-arm64.so 

With Docker
~~~~~~~
| Use the ``-v`` flag to bind the current directory to the ``/workspace/mount`` directory inside the Docker container.  
| Ensure that your APK file is in the current directory, or replace ``$APK_DIRECTORY`` with the path to your APK file's location.
|

.. code:: sh

    APK_DIRECTORY=$PWD
    APK_FILENAME=example.apk
    docker run -v $APK_DIRECTORY/:/workspace/mount ksg97031/frida-gadget mount/$APK_FILENAME --arch arm64 --sign

    ...
    # The patched APK will be located at $APK_DIRECTORY/example/dist/example.apk

How to know device architecture?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
| Connect your device and run the following command:
|

.. code:: sh

    adb shell getprop ro.product.cpu.abi

| This command will output the architecture of your device, such as ``arm64-v8a``, ``armeabi-v7a``, ``x86``, or ``x86_64``.
|
| - Most modern Android emulators use the ``x86_64`` architecture.
| - Newer high-end devices typically use ``arm64-v8a``.
| - Older or lower-end devices might use ``armeabi-v7a``.
| - Some specific emulators or devices may still use ``x86``.

Contributing
-----------------
.. image:: CONTRIBUTORS.svg
   :target: ./CONTRIBUTORS.svg


.. |Coverage-Status| image:: https://img.shields.io/coveralls/github/ksg97031/frida-gadget/master?logo=coveralls
   :target: https://coveralls.io/github/ksg97031/frida-gadget
.. |Branch-Coverage-Status| image:: https://codecov.io/gh/ksg97031/frida-gadget/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/ksg97031/frida-gadget
.. |Codacy-Grade| image:: https://app.codacy.com/project/badge/Grade/a1e2ef93fd3842e4b9e92971c135ed3f
   :target: https://app.codacy.com/gh/ksg97031/frida-gadget/dashboard
.. |CII Best Practices| image:: https://bestpractices.coreinfrastructure.org/projects/3264/badge
   :target: https://bestpractices.coreinfrastructure.org/projects/3264
.. |GitHub-Status| image:: https://img.shields.io/github/tag/ksg97031/frida-gadget.svg?maxAge=86400&logo=github&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/releases
.. |GitHub-Forks| image:: https://img.shields.io/github/forks/ksg97031/frida-gadget.svg?logo=github&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/network
.. |GitHub-Stars| image:: https://img.shields.io/github/stars/ksg97031/frida-gadget.svg?logo=github&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/stargazers
.. |GitHub-Commits| image:: https://img.shields.io/github/commit-activity/y/ksg97031/frida-gadget.svg?logo=git&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/graphs/commit-activity
.. |GitHub-Issues| image:: https://img.shields.io/github/issues-closed/ksg97031/frida-gadget.svg?logo=github&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/issues?q=
.. |GitHub-PRs| image:: https://img.shields.io/github/issues-pr-closed/ksg97031/frida-gadget.svg?logo=github&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/pulls
.. |GitHub-Contributions| image:: https://img.shields.io/github/contributors/ksg97031/frida-gadget.svg?logo=github&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/graphs/contributors
.. |GitHub-Updated| image:: https://img.shields.io/github/last-commit/ksg97031/frida-gadget/master.svg?logo=github&logoColor=white&label=pushed
   :target: https://github.com/ksg97031/frida-gadget/pulse
.. |Gift-Casper| image:: https://img.shields.io/badge/dynamic/json.svg?color=ff69b4&label=gifts%20received&prefix=%C2%A3&query=%24..sum&url=https%3A%2F%2Fcaspersci.uk.to%2Fgifts.json
   :target: https://cdcl.ml/sponsor
.. |PyPI-Downloads| image:: https://static.pepy.tech/badge/frida-gadget
   :target: https://pepy.tech/project/frida-gadget
.. |Py-Versions| image:: https://img.shields.io/pypi/pyversions/frida-gadget
   :target: https://pypi.org/project/frida-gadget
.. |Conda-Forge-Status| image:: https://img.shields.io/conda/v/conda-forge/frida-gadget.svg?label=conda-forge&logo=conda-forge
   :target: https://anaconda.org/conda-forge/frida-gadget
.. |Docker| image:: https://img.shields.io/badge/docker-pull-blue.svg?logo=docker&logoColor=white
   :target: https://github.com/ksg97031/frida-gadget/pkgs/container/frida-gadget
.. |Libraries-Dependents| image:: https://img.shields.io/librariesio/dependent-repos/pypi/frida-gadget.svg?logo=koding&logoColor=white
    :target: https://github.com/ksg97031/frida-gadget/network/dependents
.. |OpenHub-Status| image:: https://www.openhub.net/p/frida-gadget/widgets/project_thin_badge?format=gif
   :target: https://www.openhub.net/p/frida-gadget?ref=Thin+badge
.. |awesome-python| image:: https://awesome.re/mentioned-badge.svg
   :target: https://github.com/vinta/awesome-python
.. |LICENCE| image:: https://img.shields.io/pypi/l/frida-gadget.svg
   :target: https://raw.githubusercontent.com/ksg97031/frida-gadget/master/LICENCE
.. |DOI| image:: https://img.shields.io/badge/DOI-10.5281/zenodo.595120-blue.svg
   :target: https://doi.org/10.5281/zenodo.595120
.. |binder-demo| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/ksg97031/frida-gadget/master?filepath=DEMO.ipynb
