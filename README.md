# I made boids!

A Boids simulation implementation in Python using pygame-ce for gui

[See Changelog>](CHANGELOG.md)

## Installation

Download the repository and install the package with pip:

```bash
# clone repository
git clone https://github.com/ewigael/boids.git
# move to source
cd boids
# install package
pip install .
```

## About

A boid in its simplest form is a simulated entity with position and velocity,
governed by three simple rules:
- **separation** - stay away from its neighbors
- **alignment** - match speed and direction of its neighbors
- **cohesion** - move toward the center of the group

From these rules, given a little time, they organise to form flocks!

New behaviors appearing spontaneously from seemingly simple or unrelated rules is called Emergence, and it's everywhere in the Universe.

Boids algorithms are used to simulate bird flocks, schools of fish, [waddles of penguins](https://en.wiktionary.org/wiki/Appendix:English_collective_nouns#The_main_list)... But also enemy AI in video games or even drones

## Usage

Installing the package exposes the ```boids``` executable

### Key Bindings

Coming soon

### Cli Options

Coming soon

Use ```boids -h``` for a full list of cli options