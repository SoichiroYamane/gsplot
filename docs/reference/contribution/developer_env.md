# Setting up gsplot for developer 🛠️

This document describes how to set up gsplot for development.

```{Warning}
An admonition note!
```

## Flow of setting up gsplot for development

1. [Fork the gsplot repository](fork_the_gsplot_repository)
2. [Clone the forked repository](clone_the_forked_repository)
3. [Create an environment](create_an_environment)
4. [Draw the test plot](draw_the_test_plot)

(fork_the_gsplot_repository)=

### 1. Fork the gsplot repository

(clone_the_forked_repository)=

### 2. Clone the forked repository

```bash
git clone xxxx
```

(create_an_environment)=

### 3.Create an environment

gsplot provides three ways to create an environment: Poetry, Local, and Docker. You can choose any of them according to your preference.

::::{tab-set}

:::{tab-item} Poetry

```bash
cd gsplot
poetry install
poetry shell
```

:::

:::{tab-item} Local

```bash
cd gsplot
pip install -e .
```

:::

:::{tab-item} Docker

```{important}
Ensure you have docker and X11 installed on your system. For MAC users, you can install [XQuartz](<https://www.xquartz.org/>), and it needs to allow connections from the network in the security settings in order to show an interactive plot.
```

```bash
cd gsplot
docker-composer up -d --build
docker-composer exec gsplot bash
cd opt
poetry shell
```

:::

::::

(draw_the_test_plot)=

### 4. Draw the test plot

Our repository has a demo folder that contains a quick start script. You can run the script to draw a test plot.

```bash
python demo/test_plot/gsplot_demo.py
```

After running the script, you will see a plot like this:

```{image} ../../../demo/test_plot/SC_cal.png
:alt: SC_cal.png
:class: bg-primary
:width: 1500px
:align: center
```
