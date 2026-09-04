package com.example.runninggame

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlin.random.Random

class GameViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(GameState())
    val uiState = _uiState.asStateFlow()

    private val gravity = 0.8f
    private val jumpStrength = -20f
    private val groundY = 800f
    private val obstacleSpeed = 10f
    private val spawnInterval = 1500L // ms

    init {
        startGameLoop()
    }

    private fun startGameLoop() {
        viewModelScope.launch {
            var lastSpawnTime = 0L
            while (true) {
                if (_uiState.value.status == GameStatus.RUNNING) {
                    val currentTime = System.currentTimeMillis()
                    
                    // Update physics
                    updatePhysics()

                    // Spawn obstacles
                    if (currentTime - lastSpawnTime > spawnInterval) {
                        spawnObstacle()
                        lastSpawnTime = currentTime
                    }

                    // Check collisions
                    checkCollisions()
                }
                delay(16) // ~60 FPS
            }
        }
    }

    private fun updatePhysics() {
        _uiState.update { state ->
            val player = state.player
            var newY = player.y + player.velocityY
            var newVelocityY = player.velocityY + gravity
            var isJumping = true

            if (newY >= 0f) { // Simple ground level at 0 relative to offset
                newY = 0f
                newVelocityY = 0f
                isJumping = false
            }

            val updatedObstacles = state.obstacles.map { it.copy(x = it.x - obstacleSpeed) }
                .filter { it.x > -200f } // Remove off-screen obstacles

            state.copy(
                player = player.copy(y = newY, velocityY = newVelocityY, isJumping = isJumping),
                obstacles = updatedObstacles,
                distance = state.distance + (obstacleSpeed / 100f),
                score = state.score + if (updatedObstacles.size < state.obstacles.size) 1 else 0
            )
        }
    }

    private fun spawnObstacle() {
        _uiState.update { state ->
            val newObstacle = Obstacle(x = 1200f) // Start off-screen right
            state.copy(obstacles = state.obstacles + newObstacle)
        }
    }

    private fun checkCollisions() {
        val state = _uiState.value
        val player = state.player
        val playerRectRight = 200f + player.width // Player is fixed at x=200
        val playerRectLeft = 200f
        val playerRectBottom = groundY + player.y
        val playerRectTop = playerRectBottom - player.height

        for (obstacle in state.obstacles) {
            val obsLeft = obstacle.x
            val obsRight = obstacle.x + obstacle.width
            val obsBottom = groundY
            val obsTop = groundY - obstacle.height

            if (playerRectRight > obsLeft && playerRectLeft < obsRight &&
                playerRectBottom > obsTop && playerRectTop < obsBottom
            ) {
                _uiState.update { it.copy(status = GameStatus.OVER) }
                break
            }
        }
    }

    fun onJump() {
        if (_uiState.value.status == GameStatus.RUNNING && !_uiState.value.player.isJumping) {
            _uiState.update { it.copy(player = it.player.copy(velocityY = jumpStrength, isJumping = true)) }
        } else if (_uiState.value.status != GameStatus.RUNNING) {
            resetGame()
        }
    }

    private fun resetGame() {
        _uiState.value = GameState(status = GameStatus.RUNNING)
    }
}
