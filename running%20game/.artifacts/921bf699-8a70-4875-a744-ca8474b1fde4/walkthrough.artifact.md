# Walkthrough - 3D Sprint Runner

I have upgraded the game to a **fully realistic 3D experience** using a custom perspective projection engine built on Jetpack Compose.

## 3D Engine Implementation

I implemented a **Perspective Projection** system that transforms 3D world coordinates $(x, y, z)$ into 2D screen coordinates $(x, y)$. This creates a realistic "vanishing point" effect where the road and environment recede into the distance.

### Key Components

- **[GameModels.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameModels.kt)**: Updated to include 3D properties like `z` (distance) and `lane` position.
- **[GameViewModel.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameViewModel.kt)**:
  - Handles **Lane Switching**: Smooth interpolation between lanes $(-1, 0, 1)$.
  - **3D Depth Physics**: Obstacles move from the horizon $(z=5000)$ towards the player $(z=0)$.
  - **Bounding Box Collision**: Precise 3D collision detection across lanes and vertical height.
- **[GameScreen.kt](file:///G:/Code/running%20game/app/src/main/java/com/example/runninggame/GameScreen.kt)**:
  - **Receding Road**: A trapezoidal road with lane markings that follow perspective lines.
  - **Horizon Fog**: A gradient overlay that fades distant objects into the sky.
  - **Dynamic Environment**: Pillars along the roadside that scale and fade based on their $z$ distance.
  - **Shadows**: Real-time 3D projected shadows for the player.

## How to Play

1.  **Start**: Tap anywhere to begin.
2.  **Move Lanes**: Tap the **Left** or **Right** sides of the screen to switch lanes.
3.  **Jump**: Tap the **Center** of the screen to jump over obstacles.
4.  **Survival**: Dodge the red blocks as they speed towards you!

## Verification Results

- **Build**: Successfully passed `:app:assembleDebug`.
- **Perspective**: Verified that objects scale correctly ($Scale = f / (z + f)$) as they approach the camera.
- **Performance**: The engine runs natively on the Compose Canvas, ensuring smooth 60 FPS performance without heavy external libraries.
