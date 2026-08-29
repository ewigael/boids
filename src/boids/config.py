"""Configuration class"""

from importlib.resources import files
import tomllib


class GenericSubConfig:
    """Recursive configuration container base class"""

    def __init__(self, data, specific_sub_configs=None):
        self.subs = []
        self.specific_sub_configs = specific_sub_configs

        self.recursive_build(data, specific_sub_configs)

    def recursive_build(self, data, specific_sub_configs):
        for k, v in data.items():
            self.subs.append(k)
            if isinstance(v, dict):
                cls = (specific_sub_configs or {}).get(k, GenericSubConfig)
                v = cls(v, specific_sub_configs)
            setattr(self, k, v)

    def overlay_data(self, data):
        for k, v in data.items():
            if isinstance(v, dict):
                sub = getattr(self, k, None)
                if sub is None:
                    cls = (self.specific_sub_configs or {}).get(k, GenericSubConfig)
                    v = cls(v, self.specific_sub_configs)
                    self.subs.append(k)
                    setattr(self, k, v)
                else:
                    sub.overlay_data(v)
            else:
                if k not in self.subs:
                    self.subs.append(k)
                setattr(self, k, v)

    def asdict(self):
        result = {}

        for k in self.subs:
            v = getattr(self, k)
            if isinstance(v, GenericSubConfig):
                v = v.asdict()
            result[k] = v

        return result


class EntitiesSubConfig(GenericSubConfig):
    @property
    def sensor_range_squared(self):
        return self.sensor_range**2


class Config(GenericSubConfig):
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

        super().__init__(data, self.specific_sub_configs)

    def overlay(self, path):
        with path.open("rb") as f:
            data = tomllib.load(f)
        self.overlay_data(data)


config = Config()
