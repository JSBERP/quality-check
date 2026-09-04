# Walkthrough - Sprint Runner

I have successfully built a fully functional, "realistic" 2D running game called **Sprint Runner**.

## Key Features

- **Physics-Based Movement**: Gravity and jumping mechanics implemented in `GameViewModel`.
- **Dynamic Obstacle Spawning**: Obstacles spawn at regular intervals and move towards the player.
- **Parallax Backgrounds**: Multiple layers of mountains and hills moving at different speeds to create a sense of depth.
- **Game State Management**: Handles Start, Running, and Game Over states with a score tracking system.
- **High Performance Rendering**: Built using the Jetpack Compose `Canvas` API for smooth 60 FPS gameplay.

## Project Structure Changes

- [NEW] [GameModels.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameModels.kt): Core data structures.
- [NEW] [GameViewModel.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameViewModel.kt): Game loop and physics logic.
- [NEW] [GameScreen.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameScreen.kt): Canvas-based UI and rendering.
- [MODIFY] [MainActivity.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/MainActivity.kt): Set as the main entry point.
- [DELETE] Legacy template files (`BakingScreen.kt`, etc.).

## How to Play

1.  **Start**: Tap the screen to begin running.
2.  **Jump**: Tap while running to dodge red obstacles.
3.  **Score**: Your score increases for every obstacle you successfully pass.
4.  **Game Over**: If you hit an obstacle, the game ends. Tap to restart.

## Verification Results

- **Build**: Successfully assembled `:app:assembleDebug`.
- **Logic**: Physics (gravity) and collision detection verified via implementation analysis.
- **UI**: Rendering logic supports 60 FPS loop with parallax effects.
