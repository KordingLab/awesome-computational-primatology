# [Awesome Computational Primatology](https://kordinglab.com/awesome-computational-primatology/)

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![Papers](https://img.shields.io/badge/Papers-97-blue)](https://github.com/KordingLab/awesome-computational-primatology#projects)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/KordingLab/awesome-computational-primatology/blob/main/CONTRIBUTING.md)
[![Last Updated](https://img.shields.io/github/last-commit/KordingLab/awesome-computational-primatology?label=last%20updated)](https://github.com/KordingLab/awesome-computational-primatology/commits/main)

This repository contains the corpus of projects at the intersection of deep learning and **non-human** primatology since around the time AlexNet was published (~2012). This repo is intended for papers that provide novel approaches or applications in computational primatology. We occasionally include datasets which contain both primate and non-primate animals. Contributions and edits welcome!

By compiling and highlighting this growing literature, we hope it will inspire future researchers to open-source their own models and data to advance the field.

## Quick Links

- [Browse Interactive Website](https://kordinglab.com/awesome-computational-primatology/)
- [Topic Categories](docs/TOPIC_LEGEND.md)
- [How to Contribute](CONTRIBUTING.md)
- [AI Chat Documentation](docs/HOW_THE_AI_CHAT_WORKS.md)

## Contribute to the List!
We welcome contributions from the community! If you know of a relevant paper or project:

1. **Fork** this repository
2. **Add** your paper to the table in chronological order
3. **Preview** your changes: `python scripts/dev-preview.py`
4. **Submit** a pull request

**Features for contributors:**
- Automatic link checking
- Live preview of your changes
- Auto-generated website updates
- Format validation

Read our [Contributing Guidelines](CONTRIBUTING.md) for detailed instructions!

By sharing your datasets and models, you contribute to advancing primatology and enable reproducible research.


### Topic Legend
| Label | Topic |
|-------|-------|
| PD | Primate Detection |
| BPE | Body Pose Estimation |
| FD | Face Detection |
| FLE | Facial Landmark Estimation |
| FR | Face Recognition and/or Re-Identification |
| FAC | Facial Action Coding / Units |
| HD | Hand Detection |
| HPE | Hand Pose Estimation |
| BR | Behavior Recognition / Understanding / Modeling |
| AM | Avatar / Mesh |
| SI | Species Identification |
| RL | Reinforcement Learning |
| AV | Audio/Vocalization Analysis |
| O | Other|

### Legend for "Model?" Column
- `[Yes](link)`: Code + models available
- `[Code only](link)`: Repository available, but no pre-trained models
- `[No](link)`: Repository with general information, but no functional code or models
- "N/A": No repository or models provided

### Projects
| Year | Paper | Topic | Animal | Model? | Data? | Image/Video Count |
|------|-----|-------|---------|------------|---------------|-------------|
| 2025 | [Huang et al.](https://doi.org/10.1109/ICASSP49660.2025.10887625) | BR | Macaque | N/A | Macaque-Motion-Monitor | N/A |
| 2025 | [Mueller et al.](https://doi.org/10.48550/arXiv.2509.12193) | BR | Ape | [Yes](https://github.com/ecker-lab/dap-behavior) | N/A | N/A |
| 2025 | [SILVI](https://doi.org/10.48550/arXiv.2511.03819) | PD, BR | Any | N/A | N/A | N/A |
| 2025 | [Luo et al.](https://doi.org/10.1080/10888705.2025.2542844) | PD, BR | Gibbon | N/A | N/A | N/A |
| 2025 | [Luetkin et al.](https://doi.org/10.1145/3768539.3768558) | FD, FR | Chimp | TBD | TBD | TBD |
| 2025 | [PrimateFace](https://doi.org/10.1101/2025.08.12.669927) | FD, FLE, FR, FAC | Cross-genus | [Yes](https://github.com/KordingLab/PrimateFace) | [Yes](https://github.com/KordingLab/PrimateFace) | 200K+ images |
| 2025 | [PanAf-FGBG](https://doi.org/10.48550/arXiv.2502.21201) | PD, BR | Chimp | N/A | [Yes](https://obrookes.github.io/panaf-fgbg.github.io/) | TBD |
| 2025 | [PriVi](https://doi.org/10.48550/arXiv.2511.09675) | PD, BR | Apes | N/A | Multiple | N/A |
| 2025 | [Igaue et al.](https://doi.org/10.48550/arXiv.2511.16711) | FD, FAC | Macaque | N/A | N/A | N/A |
| 2025 | [Iashin et al.](https://doi.org/10.48550/arXiv.2507.10552) | FD, FR | Chimp | [Yes](https://github.com/v-iashin/ChimpUFE) | N/A | N/A |
| 2025 | [Fuchs et al.](https://doi.org/10.1007/s11263-025-02484-6) | BR | Chimp | [Yes](https://github.com/MitchFuchs/ChimpBehave) | Yes | 215,000 |
| 2025 | [Clink et al.](https://doi.org/10.1002/ece3.71678) | AV | Gibbon | N/A | N/A | N/A |
| 2024 | [BaboonLand](https://doi.org/10.48550/arXiv.2405.17698) | PD, BR | Baboons | N/A | [Yes](https://baboonland.xyz/) | TBD |
| 2024 | [Scott et al.](https://doi.org/10.48550/arXiv.2412.15966) | BPE | Macaque | N/A | N/A | N/A |
| 2024 | [ChimpVLM](https://doi.org/10.48550/arXiv.2404.08937) | BR | Chimp | N/A | Used PanAf20k | N/A |
| 2024 | [AlphaChimp](https://doi.org/10.48550/arXiv.2410.17136) | PD, BR | Chimp | [Yes](https://github.com/ShirleyMaxx/AlphaChimp?tab=readme-ov-file) | [ChimpAct](https://github.com/ShirleyMaxx/ChimpACT?tab=readme-ov-file#data) | N/A |
| 2024 | [Paulet et al.](https://doi.org/10.1007/s10329-024-01137-5) | FR | Macaque | N/A | N/A | N/A |
| 2024 | [PanAf20K](https://doi.org/10.1007/s11263-024-02003-z) | PD, BR | Apes | [No](https://github.com/obrookes/panaf.github.io) | [Yes](https://data.bris.ac.uk/data/dataset/1h73erszj3ckn2qjwm4sqmr2wt) | 20k |
| 2024 | [Gris et al.](https://doi.org/10.30802/AALAS-JAALAS-23-000056) | FD, O | Macaque | N/A | N/A | N/A |
| 2024 | [MacAction](https://doi.org/10.1101/2024.01.29.577734) | AM | Macaque | N/A | N/A | N/A |
| 2024 | [LabGym](https://doi.org/10.1007/s10329-024-01123-x) | BR | Macaque | [Yes](https://github.com/umyelab/LabGym) | Yes | N/A |
| 2024 | [Cheng et al.](https://doi.org/10.1101/2024.02.27.582429) | BR | Macaque | N/A | N/A | N/A |
| 2024 | [PRIMAT (Vogg et al.)](https://doi.org/10.1101/2024.08.21.607881) | 2D BPE | Cross-species | N/A | N/A | N/A |
| 2024 | [Xing et al.](https://doi.org/10.1101/2024.02.16.580693) | O | Marmoset | N/A | N/A | N/A |
| 2024 | [Menegas et al.](https://doi.org/10.1101/2024.08.30.610159) | BR | Marmoset | N/A | N/A | N/A |
| 2024 | [Wu et al.](https://doi.org/10.48550/arXiv.2410.23279) | AV | Marmoset | N/A | N/A | N/A |
| 2024 | [Batist et al.](https://doi.org/10.1002/ajp.23599) | AV | Lemur | [Yes](https://github.com/emmanueldufourq/PAM_TransferLearning) | N/A | N/A |
| 2023 | [GorillaVision](https://inf-cv.uni-jena.de/wordpress/wp-content/uploads/2023/09/Talk-12-Maximilian-Schall.pdf) | FD, FR | Gorilla | [Yes](https://github.com/Lasklu/gorillavision) | N/A | 832 |
| 2023 | [Abbaspoor, Rahman et al.](https://doi.org/10.1101/2023.12.11.571113) | 3D BPE | Macaque | N/A | N/A | N/A |
| 2023 | [Mimura et al.](https://doi.org/10.1101/2023.03.04.531044) | BR | Macaque, Marmoset | N/A | N/A | N/A |
| 2023 | [Schofield et al.](https://doi.org/10.1111/2041-210X.14181) | FD, FR | Chimp | N/A | N/A | N/A |
| 2023 | [Yang et al.](https://doi.org/10.48550/arXiv.2205.00275) | PD | Great Ape | N/A | N/A | N/A |
| 2023 | [ASBAR](https://doi.org/10.1101/2023.09.24.559236) | BR | Chimp, Gorilla | Yes | [Yes](https://github.com/MitchFuchs/asbar) | 5,440 labels |
| 2023 | [DeepWild](https://doi.org/10.1111/1365-2656.13932) | 2D BPE | Chimp, Bonobo | [Yes](https://github.com/Wild-Minds/DeepWild) | [Upon request](https://doi.org/10.5281/zenodo.5600472) | N/A |
| 2023 | [Kaneko et al.](https://doi.org/10.1101/2023.10.16.561623) | 3D BPE | Marmoset | N/A | N/A | N/A |
| 2023 | [Matsumoto et al.](https://doi.org/10.1101/2023.09.13.556332) | 3D BPE | Macaque | N/A | N/A | N/A |
| 2023 | [ChimpAct](https://doi.org/10.48550/arXiv.2310.16447) | 2D BPE, FR, BR | Chimp | Yes | Yes | 160,500 |
| 2023 | [OpenMonkeyChallenge](https://doi.org/10.1007/s11263-022-01698-2) | 2D BPE | Cross-species | N/A | [Yes](https://competitions.codalab.org/competitions/34342) | 111,529 |
| 2023 | [Pillai et al.](https://doi.org/10.1109/icsses58299.2023.10199762) | PD | Cross-species | N/A | N/A | N/A |
| 2023 | [Reddy et al.](https://doi.org/10.1109/NMITCON58196.2023.10276306) | PD | Cross-species | N/A | N/A | N/A |
| 2023 | [Bala et al.](https://doi.org/10.1007/s11263-023-01804-y) | 3D BPE | Cross-species | N/A | N/A | N/A |
| 2023 | [Brookes et al.](https://doi.org/10.48550/arXiv.2301.02642) | BR | Apes | N/A | N/A | N/A |
| 2023 | [Jiang et al.](https://doi.org/10.48550/arXiv.2301.02214) | AV | Great Apes | [Yes](https://github.com/J22Melody/sed_great_ape) | N/A | N/A |
| 2022 | [Lei et al.](https://doi.org/10.1038/s41598-022-11842-0) | BPE | Loris | N/A | N/A | N/A |
| 2022 | [Ngo et al.](https://doi.org/10.1016/j.cub.2022.06.028) | BR | Marmoset | N/A | N/A | N/A |
| 2022 | [Brachiation](https://doi.org/10.48550/arXiv.2205.03943) | RL | Gibbon | [Yes](https://github.com/brachiation-rl/brachiation) | N/A | N/A |
| 2022 | [SIPEC](https://doi.org/10.1038/s42256-022-00477-5) | 2D BPE, FR, BR | Macaque | [Some](https://www.dropbox.com/sh/y387kik9mwuszl3/AABBVWALEimW-hrbXvdfjHQSa?dl=0) | Upon request | N/A |
| 2022 | [Ueno et al.](https://doi.org/10.1111/eth.13277) | FR | Macaque | N/A | N/A | N/A |
| 2021 | [Brookes & Burghardt](https://doi.org/10.48550/arXiv.2012.04689) | FR | Gorilla | N/A | [Yes](https://data.bris.ac.uk/data/dataset/jf0859kboy8k2ufv60dqeb2t8) | >5,000 |
| 2021 | [Bain et al.](https://doi.org/10.1126/sciadv.abi4883) | BR | Chimp | N/A | N/A | N/A |
| 2021 | [OpenApePose](https://doi.org/10.48550/arXiv.2107.03939) | 2D BPE | Cross-species | N/A | [Yes](https://github.com/desai-nisarg/OpenApePose) | 71,868 |
| 2021 | [MacaquePose](https://doi.org/10.1038/s41598-021-92381-6) | 2D BPE | Macaque | [Yes](https://github.com/primat-ai/MacaquePose) | [Yes](https://www.pri.kyoto-u.ac.jp/datasets/macaquepose/index.html) | 13,000 |
| 2021 | [GreatApe Dictionary](https://zenodo.org/records/5600472#.YX1_ddbMK_J) | BR | Chimp | N/A | Upon request | N/A |
| 2021 | [Negrete et al.](https://doi.org/10.1101/2021.01.28.428726) | 2D BPE | Macaque | N/A | N/A | N/A |
| 2021 | [Müller et al.](https://doi.org/10.1016/j.ecoinf.2021.101423) | AV | Chimp | N/A | N/A | N/A |
| 2021 | [Romero-Mujalli et al.](https://doi.org/10.1038/s41598-021-03941-1) | AV | Lemur | N/A | N/A | N/A |
| 2021 | [Dufourq et al.](https://doi.org/10.1002/rse2.201) | AV | Gibbon | N/A | N/A | N/A |
| 2020 | [Kumar & Shingala](https://doi.org/10.1007/978-981-15-3383-9_34) | PD | Langur | N/A | N/A | N/A |
| 2020 | [Sakib & Burghardt](https://doi.org/10.48550/arXiv.2005.07815) | BR | Chimp | [Yes](https://github.com/fznsakib/great-ape-behaviour-detector) | [Yes](https://data.bris.ac.uk/data/dataset/jh6hrovynjik2ix2h7m6fdea3) | 180,000 |
| 2020 | [OpenMonkeyStudio](https://doi.org/10.1038/s41467-020-18441-5) | 3D BPE | Macaque | Upon request | [Yes](https://github.com/OpenMonkeyStudio/OMS_Data) | 195,228 |
| 2020 | [Tri-A](https://doi.org/10.1016/j.isci.2020.101412) | FD, FR | 41 species | N/A | [Yes](https://data.mendeley.com/datasets/z3x59pv4bz/2) | 102,399 |
| 2020 | [Sanakoyeu et al.](https://doi.org/10.1109/CVPR42600.2020.00528) | AM | Chimp | [Kind of](https://github.com/asanakoy/densepose-evolution) | N/A | N/A |
| 2020 | [EthoLoop](https://doi.org/10.1038/s41592-020-0961-2) | 3D BPE | Lemur | N/A | Upon request | N/A |
| 2019 | [Bain et al.](https://doi.org/10.48550/arXiv.1909.08950) | PD, FD, FR | Chimp | N/A | N/A | N/A |
| 2019 | [Schofield et al.](https://doi.org/10.1126/sciadv.aaw0736) | FD, FR | Chimp | N/A | N/A | N/A |
| 2019 | [Yang et al.](https://doi.org/10.1109/ICCVW.2019.00035) | PD | Chimp | N/A | [Yes](https://data.bris.ac.uk/data/dataset/jh6hrovynjik2ix2h7m6fdea3) | 180,000 |
| 2019 | [Labuguen et al.](https://doi.org/10.3389/fnbeh.2020.581154) | 2D BPE | Macaque | N/A | N/A | N/A |
| 2019 | [Oikarinen et al.](https://doi.org/10.1121/1.5091005) | AV | Marmoset | [Yes](https://marmosetbehavior.mit.edu) | N/A | N/A |
| 2018 | [Sinha, Agarwal et al.](https://doi.org/10.1007/978-3-030-11009-3_33) | PD | Cross-species | N/A | N/A | N/A |
| 2018 | [Deb et al.](https://doi.org/10.1109/BTAS.2018.8698538) | FR | Cross-species | N/A | N/A | N/A |
| 2018 | [Witham](https://doi.org/10.1016/j.jneumeth.2017.07.020) | FLE | Macaque | N/A | [Yes](https://figshare.com/articles/dataset/Macaque_Faces/9862586/1?file=17682749) | 4,000 |
| 2018 | [Labuguen et al.](https://doi.org/10.1101/377895) | PD | Macaque | N/A | N/A | N/A |
| 2018 | [Zhang et al.](https://doi.org/10.1121/1.5047743) | AV | Marmoset | N/A | N/A | N/A |
| 2017 | [LemurFaceID](https://doi.org/10.1186/s40850-016-0011-9) | FD, FR | Lemur | N/A | [Yes](https://biometrics.cse.msu.edu/Publications/Databases/MSU_LemurFaceID/) | 462 |
| 2017 | [Brust et al.](https://doi.org/10.1109/ICCVW.2017.333) | FD, FR | Gorilla | N/A | N/A | N/A |
| 2016 | [Crunchant et al.](https://doi.org/10.1002/ajp.22627) | FD | Chimp | N/A | N/A | N/A |
| 2016 | [Nakamura et al.](https://doi.org/10.1371/journal.pone.0166154) | AM | Macaque | N/A | N/A | N/A |
| 2016 | [Freytag et al.](https://doi.org/10.1007/978-3-319-45886-1_5) | FR | Chimp | N/A | [Yes](https://github.com/cvjena/chimpanzee_faces) | 6,486 |
| 2014 | [Ballesta et al.](https://doi.org/10.1016/j.jneumeth.2014.05.022) | 3D, O | Macaque | N/A | N/A | N/A |
| 2013 | [Loos & Ernst](https://doi.org/10.1186/1687-5281-2013-49) | FD, FR | Chimp | N/A | N/A | 6,522 |
| 2012 | [Loos & Pfitzer](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6208167) | FR | Chimp | N/A | N/A | N/A |
| 2012 | [Loos & Ernst](https://doi.org/10.1109/ISM.2012.30) | FD, FR | Chimp | N/A | N/A | N/A |
| 2011 | [Loos et al.](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7074032) | FR | Chimp | N/A | N/A | N/A |
| 2011 | [Ernst & Küblbeck](https://doi.org/10.1109/AVSS.2011.6027337) | FD, SI | Chimp, Gorilla | N/A | N/A | N/A |

#### Dataset with both primate and non-primate data
| Year | Paper | Topic | Animal | Model? | Data? | Image/Video Count |
|------|-----|-------|---------|------------|---------------|-------------|
| 2023 | [MammalNet](https://doi.org/10.48550/arXiv.2306.00576) | BR | Cross-species | [Yes](https://github.com/Vision-CAIR/MammalNet) | [Yes](https://mammal-net.github.io/) | 18k videos |
| 2022 | [Animal Kingdom](https://doi.org/10.48550/arXiv.2204.08129) | 2D BPE, BR | Cross-species | N/A | [Yes](https://github.com/sutdcv/Animal-Kingdom) | N/A |
| 2022 | [APT-36K](https://doi.org/10.48550/arXiv.2206.05683) | 2D BPE | Cross-species | N/A | [Yes](https://github.com/pandorgan/APT-36K) | < 36K |
| 2021 | [AP10k](https://doi.org/10.48550/arXiv.2108.12617) | 2D BPE | Cross-species | [Yes](https://github.com/open-mmlab/mmpose/tree/main/configs/animal_2d_keypoint/topdown_heatmap/ap10k) | [Yes](https://github.com/AlexTheBad/AP-10K) | 10,015 (675 primates) |
| 2021 | [LiftPose3D](https://doi.org/10.1038/s41592-021-01226-z) | 3D BPE | Cross-species | [Yes](https://github.com/NeLy-EPFL/LiftPose3D) | N/A | N/A |
| 2020 | [AnimalWeb](https://doi.org/10.1007/s11263-020-01393-0) | FD, FLE | Cross-species | N/A | [Yes](https://fdmaoz.github.io/AnimalWeb/) | 21,921 |

#### Reviews & Related
| Year | Tag | Topic | Animal |
|------|-----|-------|--------|
| 2025 | [Parodi et al.](https://doi.org/10.1016/j.tics.2025.09.002) | Primate neuroethology review | All |
| 2024 | [Vogg et al.](https://doi.org/10.48550/arXiv.2401.16424) | CV for primates Review | All |
| 2024 | [Cauzinille et al.](https://doi.org/10.1002/ajp.23666) | ML for primate bioacoustics review | All |
| 2024 | [Tlaie et al.](https://doi.org/10.1101/2024.01.24.577055) | Neuro | Macaque, mice |
| 2021 | [Hayden et al.](https://doi.org/10.1002/ajp.23348) | Review | All |
| 2020 | [Siebert et al.](https://doi.org/10.1523/ENEURO.0524-19.2020) | Face avatar | Macaque |
| 2019 | [Murphy & Leopold](https://doi.org/10.1016/j.jneumeth.2019.06.001) | Face avatar | Macaque |
