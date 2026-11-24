# Project Leonida — Initial Research Snapshot

- Research date: 2026-11-24
- Time basis: GitHub timestamps in UTC
- Primary source: https://github.com/ProjectLeonida/Leonida
- Confidence: high for repository identity and cited commit/PR metadata; medium for project interpretation; low for inferred affiliation between separate map repositories.

## Repository identity

The canonical primary repository is [ProjectLeonida/Leonida](https://github.com/ProjectLeonida/Leonida). GitHub repository metadata resolves the historical `ItsNotRexed/Leonida` path to the ProjectLeonida organisation repository. Default branch is `main`; the live branch listing showed `main` as protected. The GitHub integration used for this research had read access and no push permission.

## Project status (maintainer-reported)

The project's README describes a static recompilation of the Xbox Series GTA VI build, with the code running natively on x86-64 and GPU programs translated to SPIR-V/Vulkan. It explicitly says the project is early and the game does not boot yet. The README documents 26,503 shader translations and full SPIR-V validation in specific reruns, large-scale model/texture/audio extraction, a partially implemented D3D12-to-Vulkan runtime, and ongoing ray-tracing work. These are maintainer-reported milestones, not independently reproduced by this research.

## Repository and dependency evidence

The primary README points to a custom Git mirror and uses a recursive clone because of the `third_party/rpf9-explorer` submodule. These are project/dependency references. No other GitHub map/GIS repository was established as a first-party ProjectLeonida subproject from the material reviewed here.

## Separate map/GIS sources

- [navanem/gta6-leonida-atlas](https://github.com/navanem/gta6-leonida-atlas): independent community atlas. README/release history describe searchable places, six regions, a Leaflet map and an optional approximate 3D explorer. Community positions are approximate.
- [wpenistone/leonida_gis](https://github.com/wpenistone/leonida_gis): independent GIS reconstruction. Repository tree includes QGIS styles, scripts for georeferencing, contours, derived/publication layers, rail extraction, OSM road/rail generation, QA, plus rasters and source files such as heightmaps and landmark JSON.
- [fbritoferreira/gta6](https://github.com/fbritoferreira/gta6): independent open map data project with map tiles, locations, activities and images hosted as JSON/images.

Do not merge their records or claim official affiliation without direct first-party evidence. Community coordinates remain reconstructions.

## Current GitHub activity sample

- Main head: [de4c37383cad386eaa851047628d7b92c51009c5](https://github.com/ProjectLeonida/Leonida/commit/de4c37383cad386eaa851047628d7b92c51009c5), 2026-11-23 23:30:11 UTC. README Discord link update only.
- Previous commits: [a8b7ddbd50e0775f493d2ece118e2c7c2bf3af79](https://github.com/ProjectLeonida/Leonida/commit/a8b7ddbd50e0775f493d2ece118e2c7c2bf3af79) and [d083a2cc37f793d3178247ce62757b622832321a](https://github.com/ProjectLeonida/Leonida/commit/d083a2cc37f793d3178247ce62757b622832321a), restoring test consistency and fixing docs/test drift.
- [PR #10086](https://github.com/ProjectLeonida/Leonida/pull/10086): automatic float-control fallback selection for MoltenVK/GPUs lacking required properties.
- [PR #10085](https://github.com/ProjectLeonida/Leonida/pull/10085): correct computed EXEC lane-mask handling in RDNA2-to-SPIR-V translation.
- [PR #10083](https://github.com/ProjectLeonida/Leonida/pull/10083): limited sequential-view Vulkan multiview support in the D3D12 layer.
- Current public release listing returned no GitHub releases. Branch listing showed `main`; no exhaustive tag/branch inventory is asserted here.

## Limitations

The complete commit history, all branches/tags/releases, every PR/issue/comment, full tree contents, Wiki pages, and all related repositories have not been exhaustively audited in this research pass. The monitor package was implemented and unit-tested locally before deployment. This initial snapshot is a research sample, not a complete audit. Initial bootstrap can consume significant API quota; use the manual workflow input deliberately.
