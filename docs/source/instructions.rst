Installation and Configuration Instructions
===========================================

This section provides detailed instructions on how to install and configure the necessary tools for running CARLA, SUMO, and their co-simulation.

System Requirements
-------------------

Before starting the installation, ensure your system meets the following requirements:

- **Operating System**: Ubuntu 20.04 or later is recommended.
- **CPU**: Multi-core processor (Intel i5 or better).
- **RAM**: At least 16 GB of RAM.
- **Graphics**: NVIDIA GPU with CUDA support (for CARLA).
- **Disk Space**: At least 50 GB of free disk space.

Installing CARLA
----------------

1. **Download CARLA**:

   Visit the `CARLA official website <https://carla.org/>`_.
   Download the latest release compatible with your operating system.

2. **Extract CARLA**:

   Extract the downloaded file to a desired directory.

   Example:

   .. code-block:: bash

      tar -xvf CARLA_0.9.13.tar.gz -C ~/carla

3. **Install Dependencies**:

   CARLA requires several dependencies, which can be installed with the following command:

   .. code-block:: bash

      sudo apt-get update
      sudo apt-get install clang-8 lld-8 python3-pip python3-dev
      pip3 install --user pygame numpy

4. **Running CARLA**:

   Navigate to the CARLA directory and run the simulator:

   .. code-block:: bash

      cd ~/carla
      ./CarlaUE4.sh

Installing SUMO
---------------

1. **Add SUMO PPA**:

   Add the SUMO PPA to your package manager and update:

   .. code-block:: bash

      sudo add-apt-repository ppa:sumo/stable
      sudo apt-get update

2. **Install SUMO**:

   Install SUMO and its dependencies:

   .. code-block:: bash

      sudo apt-get install sumo sumo-tools sumo-doc

3. **Verify Installation**:

   Check if SUMO is correctly installed by running:

   .. code-block:: bash

      sumo --version

   This should display the installed version of SUMO.

Setting Up Co-Simulation
------------------------

CARLA ships the SUMO bridge in its own package, in the folder ``Co-Simulation/Sumo``. No other repository is needed. The steps below follow the `CARLA-SUMO co-simulation guide <https://carla.readthedocs.io/en/latest/adv_sumo/>`_.

1. **Configure Environment**:

   Set the paths to CARLA and SUMO. You can add the following to your ``~/.bashrc`` file:

   .. code-block:: bash

      export CARLA_ROOT=~/carla
      export SUMO_HOME=/usr/share/sumo

   The bridge also needs the CARLA Python client. Install the version that matches the server, for example:

   .. code-block:: bash

      pip3 install carla==0.9.15

2. **Start CARLA and Load Town04**:

   Start the CARLA server in one terminal, then load the Town04 map from a second terminal:

   .. code-block:: bash

      cd $CARLA_ROOT
      ./CarlaUE4.sh

   .. code-block:: bash

      cd $CARLA_ROOT/PythonAPI/util
      python3 config.py --map Town04

3. **Run Co-Simulation**:

   Run the synchronization script with the Town04 example that comes with CARLA:

   .. code-block:: bash

      cd $CARLA_ROOT/Co-Simulation/Sumo
      python3 run_synchronization.py examples/Town04.sumocfg --sumo-gui

   Press ``Ctrl+C`` in this terminal to stop the co-simulation. The folder ``examples`` also holds configurations for Town01 and Town05.
