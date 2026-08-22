from importlib.metadata import metadata

_metadata = metadata("boids")

__project_name__ = _metadata["Name"]
__version__ = _metadata["Version"]
__authors__ = _metadata.get_all("Author-email")
__description__ = _metadata.get("Summary", "")

__urls__ = dict(item.split(", ") for item in _metadata.get_all("Project-URL"))


def print_metadata(pygame=None):
    print(
        f"{__project_name__} {__version__}\n"
        f"{__description__}\n"
        f"Authored by: {__authors__}\n"
        f"Repository: {__urls__["Repository"]}\n"
        f"Changelog: {__urls__["Changelog"]}\n"
        f"Issues: {__urls__["Issues"]}",
    )
    if pygame:
        print(f"pygame-ce {pygame.ver}")
    print()
