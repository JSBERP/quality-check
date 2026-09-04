package com.example.runninggame

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color

data class Player(
    val y: Float,
    val velocityY: Float = 0f,
    val isJumping: Boolean = false,
    val width: Float = 100f,
    val height: Float = 150f
)

data class Obstacle(
    val x: Float,
    val width: Float = 80f,
    val height: Float = 120f,
    val color: Color = Color.Red
)

data class BackgroundLayer(
    val x: Float,
    val speedFactor: Float,
    val color: Color,
    val heightRange: ClosedFloatingPointRange<Float>
)

enum class GameStatus {
    IDLE, RUNNING, OVER
}

data class GameState(
    val player: Player = Player(y = 0f),
    val obstacles: List<Obstacle> = emptyList(),
    val score: Int = 0,
    val status: GameStatus = GameStatus.IDLE,
    val distance: Float = 0f
)
