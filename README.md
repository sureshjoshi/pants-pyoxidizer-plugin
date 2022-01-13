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
4. GUI

## Compilation Instructions

```bash
./pants --version
./pants package ::
```

## Next Steps

1. Take available PyOxidizer configuration or fallback to sane default
2. Save binary to flattened dist/
3. Add debug and release build flags
