"""Configuration class"""

from importlib.resources import files
import tomllib


class GenericSubConfig:
    """Recursive configuration container base class"""

    def __init__(self, data):
        for k, v in data.items():
            if isinstance(v, dict):
                v = GenericSubConfig(v)
            setattr(self, k, v)


class EntitiesSubConfig(GenericSubConfig):
    @property
    def sensor_range_squared(self):
        return self.sensor_range**2


class Config:
    """Top level configuration class.

    Sections requiring custom behavior (ie. @property) can be assigned a specific
    config class by populating `specific_sub_configs`
    """

    specific_sub_configs = {
        "entities": EntitiesSubConfig,
    }

    def __init__(self):
        default_config_file = files("boids").joinpath("default_conf.toml")
        with default_config_file.open("rb") as f:
            data = tomllib.load(f)
            print(data)

        for k, v in data.items():
            if k in self.specific_sub_configs:
                v = self.specific_sub_configs[k](v)
            elif isinstance(v, dict):
                v = GenericSubConfig(v)
            setattr(self, k, v)
            print(k, v)


config = Config()
