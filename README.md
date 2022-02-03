# NOTE 1: pants-pyoxidizer-plugin was accepted into the [Pants repo](https://github.com/pantsbuild/pants/pull/14183) as an experimental plugin on Feb 3, 2022

So this repo is being archived. All future bug fixes will occur in the Pants repo.

# NOTE 2: Additional Pants plugins are being prototyped at: https://github.com/sureshjoshi/pants-plugins

Bug fixes, feature requests, or additional plugins may be requested there.

# pants-pyoxidizer-plugin

Please note: This is my first time writing a Pants Plugin - so this should not be used as an example of the "right" way to do it, or even A way to do it. I'm flailing around and committing periodically - monkeys on a keyboard approach.

## Gameplan

1. ~~Scaffold a Pants plugin that does basically nothing~~
2. ~~Refer to Docker plugin for inspiration on how to approach PyOx~~
3. ~~Oxidize Pants emitted wheel or pex~~
4. Oxidize source through Pants python_sources

## Examples/Libraries to test

These are some typical workflows, which also highlight some unique circumstances in [PyOx's packaging](https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_packaging_additional_files.html)

1. ~~Hello World~~
2. ~~FastAPI~~ -> Installing Classified Resources on the Filesystem
3. ~~Numpy~~ -> Installing Unclassified Files on the Filesystem
4. ~~GUI~~ -> Works on MacOS with Kivy using the patch/workaround mentioned below

## Compilation Instructions

```bash
./pants --version
./pants package ::
```

## Next Steps

1. ~~Take available PyOxidizer configuration or fallback to sane default~~
2. ~~Save binary to flattened dist/~~ -> Probably won't do until upstream
3. ~~Add debug and release build flags~~ -> Added to pants.toml as args (applies for all targets, not individuals)

## Workarounds

There are some workarounds for existing libraries - which are unrelated to Pants, but specifically related to PyOxidizer.

### Missing sys.argv[0]

Some libraries require the calling filename, which PyOxidizer does not provide. While not a stable workaround, a hack could be placing this code at the top of the main module. This code is placed in the `hellokivy` and `hellotyper` examples.

```python
import sys

# Patch missing sys.argv[0] which is None for some reason when using PyOxidizer
# https://github.com/indygreg/PyOxidizer/issues/307
if sys.argv[0] is None:
    sys.argv[0] = sys.executable
    print(f"Patched sys.argv to {sys.argv}")
```
