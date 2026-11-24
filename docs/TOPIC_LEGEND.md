# Topic Categories

This document defines the topic categories used to classify papers in the Awesome Computational Primatology collection.

## Topic Legend

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **PD** | Primate Detection | Detecting and localizing primates in images/video |
| **BPE** | Body Pose Estimation | Estimating body keypoints (2D or 3D) |
| **2D BPE** / **3D BPE** | 2D / 3D Body Pose Estimation | BPE, when the paper is specifically 2D or 3D |
| **FD** | Face Detection | Detecting and localizing primate faces |
| **FLE** | Facial Landmark Estimation | Detecting facial keypoints (eyes, nose, mouth, etc.) |
| **FR** | Face Recognition / Re-Identification | Identifying individual primates from facial features |
| **FAC** | Facial Action Coding | Analyzing facial expressions and action units |
| **HD** | Hand Detection | Detecting and localizing primate hands |
| **HPE** | Hand Pose Estimation | Estimating hand/finger keypoints |
| **BR** | Behavior Recognition | Classifying or understanding primate behaviors |
| **AM** | Avatar / Mesh | 3D modeling, avatars, or mesh reconstruction |
| **SI** | Species Identification | Classifying primate species |
| **RL** | Reinforcement Learning | RL-based approaches for primate-related tasks |
| **AV** | Audio / Vocalization | Analysis of primate vocalizations and sounds |
| **O** | Other | Topics not covered by the above categories |

## Model Availability Legend

The "Model?" column in paper tables uses these values:

| Value | Meaning |
|-------|---------|
| `[Yes](link)` | Code and pre-trained models available |
| `[Code only](link)` | Repository available, but no pre-trained models |
| `[No](link)` | Repository with information, but no functional code |
| `N/A` | No repository or models provided |
| `Upon request` | Available by contacting authors |

## Data Availability Legend

The "Data?" column uses similar conventions:

| Value | Meaning |
|-------|---------|
| `[Yes](link)` | Dataset publicly available |
| `[Name](link)` | Data is (part of) a named dataset released elsewhere |
| `Upon request` | Available by contacting authors |
| `N/A` | No dataset provided |

Use `N/A` rather than `TBD` when availability is unknown; CI rejects other values (`python scripts/lint_readme.py --strict`).
