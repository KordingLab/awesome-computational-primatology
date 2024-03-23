# [Awesome Computational Primatology](http://kordinglab.com/awesome-computational-primatology/)
This repository contains the corpus of projects at the intersection of deep learning and **non-human** primatology since around the time AlexNet was published (~2012). This repo is intended for papers that provide novel approaches or applications in computational primatology. We occasionally include datasets which contain both primate and non-primate animals. Contributions and edits welcome!

By compiling and highlighting this growing literature, we hope it will inspire future researchers to open-source their own models and data to advance the field.

Consider contributing to this community by curating a dataset or training OSS models on any of these datasets!

**Topic Legend**
- PD = Primate detection
- BPE = Body pose estimation
- FD = Face detection
- FLE = Facial landmark estimation
- FR = Face recognition and/or Re-Identification
- HD = Hand detection
- HPE = Hand pose estimation
- BR = Behavior recognition / understanding / modeling 
- AM = Avatar/Mesh
- SI = Species Identification
- RL = Reinforcement learning
- O = Other

## By year
| Year | Paper | Topic | Animal | Model? | Data? | Image/Video Count | 
|------|-----|-------|---------|------------|---------------|-------------|
| 2024 | [PanAf20K](https://link.springer.com/article/10.1007/s11263-024-02003-z) | PD, BR | Apes | [No](https://github.com/obrookes/panaf.github.io) | [Yes](https://data.bris.ac.uk/data/dataset/1h73erszj3ckn2qjwm4sqmr2wt) | 20k |
| 2024 | [Gris et al.](https://docserver.ingentaconnect.com/deliver/fasttrack/aalas/15596109/jaalas_23000056.pdf?expires=1710859610&id=pennsylvaniapa&checksum=13D04EE26CE4C36535F9651507F83EDC) | FD, O | Macaque | No | No | N/A |
| 2024 | [MacAction](https://www.biorxiv.org/content/10.1101/2024.01.29.577734v1.full.pdf) | AM | Macaque | No | No | N/A |
| 2023 | [GorillaVision](https://inf-cv.uni-jena.de/wordpress/wp-content/uploads/2023/09/Talk-12-Maximilian-Schall.pdf) | FD, FR | Gorilla | [Yes](https://github.com/Lasklu/gorillavision) | No | 832 |
| 2023 | [Abbaspoor, Rahman et al.](https://www.biorxiv.org/content/10.1101/2023.12.11.571113v1.abstract) | 3D BPE | Macaque | No | No | N/A |
| 2023 | [Mimura et al.](https://www.biorxiv.org/content/10.1101/2023.03.04.531044v3.abstract) | BR | Macaque, Marmoset | No | No | N/A |
| 2023 | [Schofield et al.](https://besjournals.onlinelibrary.wiley.com/doi/epdf/10.1111/2041-210X.14181) | FD, FR | Chimp | No | No | N/A
| 2023 | [Yang et al.](https://arxiv.org/pdf/2205.00275.pdf) | PD | Great Ape | No | No | N/A |
| 2023 | [ASBAR](https://www.biorxiv.org/content/10.1101/2023.09.24.559236v1.full.pdf) | BR | Chimp, Gorilla | Yes | [Yes](https://github.com/MitchFuchs/asbar) | 5,440 labels |
| 2023 | [DeepWild](https://besjournals-onlinelibrary-wiley-com.proxy.library.upenn.edu/doi/full/10.1111/1365-2656.13932) | 2D BPE | Chimp, Bonobo | [Yes](https://github.com/Wild-Minds/DeepWild) | [Upon request](https://doi-org.proxy.library.upenn.edu/10.5281/zenodo.5600472) | N/A |
| 2023 | [Kaneko et al.](https://www.biorxiv.org/content/10.1101/2023.10.16.561623v1.full.pdf) | 3D BM | Marmoset | No | No | N/A |
| 2023 | [Matsumoto et al.](https://www.biorxiv.org/content/10.1101/2023.09.13.556332v1.full.pdf) | 3D BM | Macaque | No | No | N/A |
| 2023 | [ChimpAct](https://proceedings.neurips.cc/paper_files/paper/2023/file/57a95cd3898bf4912269848a01f53620-Paper-Datasets_and_Benchmarks.pdf) | 2D BPE, FR, BR | Chimp | Yes | Yes | 160,500 |
| 2023 | OpenMonkeyChallenge | 2D BPE | Cross-species | No | [Yes](http://openmonkeychallenge.com/) | 111,529 |
| 2023 | [Pillai et al.](https://ieeexplore-ieee-org.proxy.library.upenn.edu/stamp/stamp.jsp?tp=&arnumber=10199762&tag=1) | PD | Cross-Species | No | No | N/A |
| 2023 | [Reddy et al.](https://ieeexplore-ieee-org.proxy.library.upenn.edu/stamp/stamp.jsp?tp=&arnumber=10276306) | PD | Cross-species | No | No | N/A | 
| 2023 | [Bala et al.](https://link-springer-com.proxy.library.upenn.edu/article/10.1007/s11263-023-01804-y) | 3D BPE | Cross-species | No | No | N/A |
| 2023 | [Brookes et al.](https://arxiv.org/pdf/2301.02642.pdf) | Apes | No | No | N/A |
| 2022 | [Ngo et al.](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10203885/) | BR | Marmoset | No | No | N/A |
| 2022 | [Brachiation](https://arxiv.org/pdf/2205.03943.pdf) | RL | Gibbon | [Yes](https://github.com/brachiation-rl/brachiation) | No | N/A |
| 2022 | [SIPEC](https://www-nature-com.proxy.library.upenn.edu/articles/s42256-022-00477-5) | 2D BPE, FR, BR | Macaque | [Some](https://www.dropbox.com/sh/y387kik9mwuszl3/AABBVWALEimW-hrbXvdfjHQSa?dl=0) | Upon request | N/A |
| 2021 | [Brookes & Burghardt](https://arxiv.org/pdf/2012.04689.pdf) | FR | Gorilla | No | [Yes](https://data.bris.ac.uk/data/dataset/jf0859kboy8k2ufv60dqeb2t8) | >5,000 |
| 2021 | [Bain et al.](https://www-science-org.proxy.library.upenn.edu/doi/full/10.1126/sciadv.abi4883) | BR | Chimp | No | [Some](https://datadryad.org/stash/share/UUfSTzsL9eTbAo-78pdaXPdaIUJmdJzSuqhXcb48vHM) | N/A |
| 2021 | OpenApePose | 2D BPE | Cross-species | No | Yes | 71,868 |
| 2021 | MacaquePose | 2D BPE | Macaque | Yes | Yes | 13,000 |
| 2021 | [GreatApe Dictionary](https://zenodo.org/records/5600472#.YX1_ddbMK_J) | Data | Chimp | No | Upon request | N/A |
| 2021 | [Negrete et al.](https://www.biorxiv.org/content/10.1101/2021.01.28.428726v1.full.pdf) | 2D BPE | Macaque | No | No | N/A |
| 2020 | [Kumar & Shingala](https://link-springer-com.proxy.library.upenn.edu/chapter/10.1007/978-981-15-3383-9_34) | PD | Langur | No | No | N/A | 
| 2020 | Sakib & Burghardt | BR | Chimp | [Yes](https://github.com/fznsakib/great-ape-behaviour-detector) | [Yes: Labeled Pan African](https://data.bris.ac.uk/data/dataset/jh6hrovynjik2ix2h7m6fdea3) | 180,000 |
| 2020 | OpenMonkeyStudio | 3D BPE | Macaque | Upon request | [Yes](https://github.com/OpenMonkeyStudio/OMS_Data) | 195,228 |
| 2020 | [Tri-A](https://www.sciencedirect.com/science/article/pii/S2589004220306027#mmc1) | FD, FR | 41 species | No | [Yes](https://data.mendeley.com/datasets/z3x59pv4bz/2) | 102,399 |
| 2020 | [Sanakoyeu et al.](https://openaccess.thecvf.com/content_CVPR_2020/papers/Sanakoyeu_Transferring_Dense_Pose_to_Proximal_Animal_Classes_CVPR_2020_paper.pdf) | AM | Chimp | [Kind of](https://github.com/asanakoy/densepose-evolution) | No | N/A
| 2020 | [EthoLoop](https://www.nature.com/articles/s41592-020-0961-2) | 3D BPE | Lemur | No | Upon request | N/A |
| 2019 | [Bain et al.](https://arxiv.org/pdf/1909.08950.pdf) | PD, FD, FR | Chimp | No | No | N/A |
| 2019 | [Schofield et al.](https://www-science-org.proxy.library.upenn.edu/doi/full/10.1126/sciadv.aaw0736) | FD, FR | Chimp | No | No | N/A |
| 2019 | Yang et al. | PD | Chimp | No | [Yes: Labeled Pan African](https://data.bris.ac.uk/data/dataset/jh6hrovynjik2ix2h7m6fdea3) | 180,000 |
| 2019 | Labuguen et al. | 2D BPE | Macaque | No | No | N/A |
| 2018 | [Sinha, Agarwal et al.](https://openaccess.thecvf.com/content_ECCVW_2018/papers/11129/Sinha_Exploring_Bias_in_Primate_Face_Detection_and_Recognition_ECCVW_2018_paper.pdf) | PD | Cross-species | No | No | N/A |
| 2018 | [Deb et al.](https://ieeexplore-ieee-org.proxy.library.upenn.edu/abstract/document/8698538/authors) | FR | Cross-species | No | No | N/A |
| 2018 | [Witham](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5909037/) | FLE | Macaque | [Yes](http://www.mackenziemathislab.org/dlc-modelzoo) | [Yes](https://figshare.com/articles/dataset/Macaque_Faces/9862586/1?file=17682749) | 4,000 |
| 2018 | [Labuguen et al.](https://www.biorxiv.org/content/10.1101/377895v1.full.pdf) | PD | Macaque | No | No | N/A |
| 2017 | [LemurFaceID](https://link-springer-com.proxy.library.upenn.edu/article/10.1186/s40850-016-0011-9) | FD, FR | Lemur | No | [Yes](http://biometrics.cse.msu.edu/Publications/Databases/MSU_LemurFaceID/) | 462
| 2017 | [Brust et al.](https://openaccess.thecvf.com/content_ICCV_2017_workshops/papers/w41/Brust_Towards_Automated_Visual_ICCV_2017_paper.pdf) | FD, FR | Gorilla | No | No | N/A |
| 2016 | [Crunchant et al.](https://onlinelibrary.wiley.com/doi/epdf/10.1002/ajp.22627) | FD | Chimp | No | No | N/A |
| 2016 | [Nakamura et al.](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0166154) | 3D BM | Macaque | No | No | N/A |
| 2016 | [Freytag et al.](https://link-springer-com.proxy.library.upenn.edu/chapter/10.1007/978-3-319-45886-1_5) | FR | Chimp | No | [Yes](https://github.com/cvjena/chimpanzee_faces) | 6,486 |
| 2014 | [Ballesta et al.](https://www-sciencedirect-com.proxy.library.upenn.edu/science/article/pii/S0165027014001848?via%3Dihub) | 3D, O | Macaque | No | No | N/A |
| 2013 | [Loos & Ernst](https://link-springer-com.proxy.library.upenn.edu/article/10.1186/1687-5281-2013-49) | FD, FR | Chimp | No | [For purchase](http://www.saisbeco.com/) | 6,522 |
| 2012 | [Loos & Pfitzer](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6208167) | FR | Chimp | No | No | N/A |
| 2012 | [Loos & Ernst](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6424643) | FD, Fr | Chimp | No | No | N/A |
| 2011 | [Loos et al.](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7074032) | FR | Chimp | No | No | N/A | 
| 2011 | [Ernst & Küblbeck](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6027337) | FD, SI | Chimp, Gorilla | No | No | N/A |

## Datasets that contain non-human primate data with other animal data
| Year | Paper | Topic | Animal | Model? | Data? | Image/Video Count | 
|------|-----|-------|---------|------------|---------------|-------------|
| 2023 | [MammalNet](https://arxiv.org/pdf/2306.00576.pdf) | BR | Cross-species | [Yes](https://github.com/Vision-CAIR/MammalNet) | [Yes](https://mammal-net.github.io/) | 18k videos |
| 2022 | [Animal Kingdom](https://arxiv.org/pdf/2204.08129.pdf) | 2D BPE, BR | Cross-species | No | [Yes](https://github.com/sutdcv/Animal-Kingdom) | N/A |
| 2022 | [APT-36K](https://arxiv.org/pdf/2206.05683.pdf) | 2D BPE | Cross-species | No | [Yes](https://github.com/pandorgan/APT-36K) | < 36K |
| 2021 | AP10k | 2D BPE | Cross-species | [Yes](https://github.com/open-mmlab/mmpose/tree/main/configs/animal_2d_keypoint/topdown_heatmap/ap10k) | Yes | 10,015 (675 primates) |
| 2021 | [LiftPose3D](https://www-nature-com.proxy.library.upenn.edu/articles/s41592-021-01226-z) | 3D BPE | Cross-species | Yes | No | N/A |
| 2020 | AnimalWeb | FD, FLE | Cross-species | No | Yes | 21,921 (not all prims) |

## Reviews
| Year | Tag | Topic | Animal |
|------|-----|-------|--------|
| 2024 | [Vogg et al.](https://arxiv.org/pdf/2401.16424.pdf) | Review | All |
| 2021 | [Hayden et al.](https://onlinelibrary-wiley-com.proxy.library.upenn.edu/doi/full/10.1002/ajp.23348) | Review | All |

## Related projects
- Macaque Face Avatars
  - [Siebert et al., 2020](https://www.eneuro.org/content/eneuro/7/4/ENEURO.0524-19.2020.full.pdf)
  - [Murphy & Leopold 2019](https://www.sciencedirect.com/science/article/pii/S0165027019301591#sec0160)
