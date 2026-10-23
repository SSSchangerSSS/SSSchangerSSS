<div align="center">
  <picture>
    <source media="(prefers-reduced-motion: reduce)" srcset="assets/banner-static.svg?v=1" />
    <img src="assets/banner.svg?v=3" width="100%" alt="Matrix-style banner: green code rain falling behind a dark terminal panel that reads Sohrab Iranpak — R&D Software Engineer" />
  </picture>
</div>

# Sohrab Iranpak

**English** · [فارسی](README.fa.md)

```bash
$ whoami
sohrab-iranpak — R&D Software Engineer

$ cat focus.txt
robotics & simulation · MATLAB · .NET (WPF/MVVM) · game development · web & mobile
```

I move between robotics simulation, .NET engineering and game development — and I like finishing things: a MATLAB robot simulator with a working GUI, a complete WPF/MVVM desktop app, and browser games you can actually play.

## Contribution Matrix

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/SSSchangerSSS/SSSchangerSSS/output/github-contribution-grid-snake-dark.svg?v=5" />
    <img src="https://raw.githubusercontent.com/SSSchangerSSS/SSSchangerSSS/output/github-contribution-grid-snake.svg?v=5" alt="A Matrix-green snake moving across the GitHub contribution calendar, consuming the cells that have contributions" />
  </picture>
</div>

A phosphor-green snake on my real contribution calendar. It follows a path over the cells that actually have contributions and eats them as it passes — an eaten cell stays empty until the cycle restarts. The animation is regenerated daily by GitHub Actions (engine: [Platane/snk](https://github.com/Platane/snk), Matrix palette); if the data fetch ever fails, the previous animation is kept rather than publishing a fake calendar.

## Selected projects

### ⚔️ [The Great Rostam](https://github.com/SSSchangerSSS/The-Great-Rostam)

A frame-by-frame 2D action game inspired by Ferdowsi's *Shahnameh* — Rostam against the Lion, built for the browser.

- **Tech:** HTML5 Canvas · vanilla JavaScript (ES modules) · CSS UI layer · procedural WebAudio (no audio files)
- **What works:** hand-painted sprite-sheet animation (~200 frames) locked to a combat state machine, God-of-War-style finisher QTEs, multi-layer parallax desert, mobile-first touch controls at 60 fps
- ▶️ **Playable in the browser:** [ssschangersss.github.io/The-Great-Rostam](https://ssschangersss.github.io/The-Great-Rostam/)

<img src="https://raw.githubusercontent.com/SSSchangerSSS/The-Great-Rostam/main/docs/screenshots/title.png" width="460" alt="The Great Rostam — in-game title screen" />

### 🤖 [RRR Robot Simulation](https://github.com/SSSchangerSSS/3degree_RRR_robot_in_matlab_genetic_algorithm)

A 3-DOF articulated (RRR) robot arm simulated in MATLAB on top of Peter Corke's Robotics Toolbox, with a custom-built GUI.

- **Tech:** MATLAB · Peter Corke Robotics Toolbox · GUI · genetic algorithm
- **What works:** forward and inverse kinematics solved two independent ways — the toolbox and an own transformation-matrix + genetic-algorithm implementation — computed side by side in the GUI and cross-checked against each other, with 3D visualization, a tutorial video and reference PDFs

<img src="https://raw.githubusercontent.com/SSSchangerSSS/3degree_RRR_robot_in_matlab_genetic_algorithm/main/robot.PNG" width="460" alt="RRR robot simulator GUI in MATLAB — toolbox and custom solver results side by side" />

### 🚗 [Car Rental Management — WPF](https://github.com/SSSchangerSSS/MVVM_WPF_Car_Rental_Management_App)

A complete Windows desktop application for car-rental operations, built strictly on the MVVM pattern.

- **Tech:** C# · WPF · MVVM · Entity Framework Core · SQLite · DI via Microsoft.Extensions.Hosting · AutoMapper · Material Design
- **What's inside:** generic CRUD services, a view-model factory, navigation and inter-view-model messaging, async data access, and a store layer that keeps database round-trips low

### 🎮 [2D Game with LÖVE 2D](https://github.com/SSSchangerSSS/2d_lua_game_made_with_love2d_engine_for_android)

A complete 2D game written in Lua with the LÖVE 2D engine, packaged for Android.

- **Tech:** Lua · LÖVE 2D · Android packaging (`FirstGame.apk` in the repo)
- **Note:** the code is free to use and learn from; the bundled art is third-party and not for commercial use — stated up front in the repo

## Focus areas & tools

- **Robotics & simulation** — MATLAB, Peter Corke Robotics Toolbox, genetic algorithms, 3D visualization
- **.NET engineering** — C#, WPF/MVVM, Entity Framework Core, SQLite, dependency injection, AutoMapper
- **Game development** — HTML5 Canvas, JavaScript, Lua / LÖVE 2D, procedural audio & sprite pipelines
- **Web & mobile** — Angular, TypeScript, Flutter/Dart
- **Systems & low-level** — image processing, network packet analysis with Scapy

<div align="center">
  <img src="https://img.shields.io/badge/MATLAB-00FF41?style=flat-square&logo=mathworks&logoColor=00FF41&labelColor=020604" alt="MATLAB" />
  <img src="https://img.shields.io/badge/C%23-00FF41?style=flat-square&logo=csharp&logoColor=00FF41&labelColor=020604" alt="C#" />
  <img src="https://img.shields.io/badge/.NET-00FF41?style=flat-square&logo=.net&logoColor=00FF41&labelColor=020604" alt=".NET" />
  <img src="https://img.shields.io/badge/JavaScript-00FF41?style=flat-square&logo=javascript&logoColor=00FF41&labelColor=020604" alt="JavaScript" />
  <img src="https://img.shields.io/badge/Lua-00FF41?style=flat-square&logo=lua&logoColor=00FF41&labelColor=020604" alt="Lua" />
  <img src="https://img.shields.io/badge/Angular-00FF41?style=flat-square&logo=angular&logoColor=00FF41&labelColor=020604" alt="Angular" />
  <img src="https://img.shields.io/badge/Flutter-00FF41?style=flat-square&logo=flutter&logoColor=00FF41&labelColor=020604" alt="Flutter" />
</div>

## GitHub in numbers

<div align="center">
  <img src="assets/github-stats.svg?v=3" width="480" alt="Matrix-terminal stats card: public repositories, stars on counted repos, commits from the public search index, followers, current streak" />
  <br/>
  <img src="assets/top-langs.svg?v=3" width="480" alt="Matrix-terminal language card: share of code bytes across counted public repositories" />
</div>

Regenerated daily by GitHub Actions from public data. Commit counts come from GitHub's public commit-search index; language shares are code bytes across public non-fork repositories — a size measure, not a skill measure.

---

<div align="center">
  <code>> EOF · code, robots & games — built in the open on GitHub</code>
</div>
