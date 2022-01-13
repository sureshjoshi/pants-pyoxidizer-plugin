def make_exe():
    print('Printing from make_exe inside of pyoxidizer.bzl')
    dist = default_python_distribution()
    policy = dist.make_python_packaging_policy()

    # Note: Adding this for pydanic (unable to load from memory) - cannot find .so files
    # https://github.com/indygreg/PyOxidizer/issues/438
    policy.resources_location_fallback = "filesystem-relative:prefix" 
    python_config = dist.make_python_interpreter_config()
    python_config.run_command = "import main; main.say_hello()"
    #python_config.run_module = "main"
    exe = dist.to_python_executable(
        name="hellofastapi",
        packaging_policy=policy,
        config=python_config,
    )
    exe.add_python_resources(exe.pip_download(["pydantic", "fastapi", "uvicorn"]))
    # exe.add_in_memory_python_resources(dist.read_package_root(
    #     path=".",
    #     packages=["hello"],
    # ))
    #exe.add_python_resources(exe.pip_install({wheel_relpaths}))
    return exe

register_target("exe", make_exe)
#register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
#register_target("install", make_install, depends=["exe"], default=True)
#register_target("msi_installer", make_msi, depends=["exe"])
resolve_targets()