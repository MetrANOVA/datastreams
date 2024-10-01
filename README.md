# techex-demo
Repo for docker compose and default configs working towards techex demo 12/2024

# Purpose
We intend to use this repo to set up a Docker Compose that should result in a set of containers that are deployable to a single VM or set of VMs.

# Docker Compose Profiles

We'll use docker compose's "profile" feature to separate components that we might want to deploy in different contexts.

For instance, we may want to have a "collector" profile, as differentiated from a "storage" profile. These would then spin up separate stacks that can be deployed to different VMs.



