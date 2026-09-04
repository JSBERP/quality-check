# Implementation Plan - Sprint Runner Game

Build a high-quality, physics-based 2D endless runner using Jetpack Compose. The game will feature smooth animations, parallax backgrounds, and a robust game loop.

## User Review Required

> [!IMPORTANT]
> This will be a 2D game using the Jetpack Compose `Canvas` API for high performance. I will use vector-based graphics and procedural generation for the environment to ensure it looks "realistic" and polished without external assets.

## Proposed Changes

### Game Engine & State Management

#### [NEW] [GameViewModel.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameViewModel.kt)
- Implements the game loop using a `StateFlow` and a Coroutine.
- Handles physics calculations (gravity, velocity, collisions).
- Manages player state (Running, Jumping, Falling, Dead).
- Spawns obstacles and manages scoring.

#### [NEW] [GameModels.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameModels.kt)
- Defines data classes for `Player`, `Obstacle`, `BackgroundLayer`, and `GameState`.

### UI & Rendering

#### [NEW] [GameScreen.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameScreen.kt)
- The main game UI component.
- Uses `Canvas` to render the game world.
- Implements parallax scrolling logic.
- Handles touch inputs (tap to jump).

#### [MODIFY] [MainActivity.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/MainActivity.kt)
- Replaces `BakingScreen` with `GameScreen`.
- Sets up the `GameViewModel`.

### Cleanup

#### [DELETE] [BakingScreen.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/BakingScreen.kt)
#### [DELETE] [BakingViewModel.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/BakingViewModel.kt)
#### [DELETE] [UiState.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/UiState.kt)

## Verification Plan

### Automated Tests
- I will verify the build passes after the changes.
- I will check the `GameViewModel` logic for correct gravity and collision detection.

### Manual Verification
- Deploy the app to the device.
- Verify the player jumps on tap.
- Verify obstacles spawn and move.
- Verify the game ends on collision.
- Observe the parallax effect and overall smoothness.
