package com.example.runninggame

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun GameScreen(viewModel: GameViewModel = viewModel()) {
    val state by viewModel.uiState.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(listOf(Color(0xFF87CEEB), Color(0xFFE0F7FA))))
            .clickable { viewModel.onJump() }
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val groundY = 800f
            
            // Draw Parallax Background (Stars/Clouds/Hills could be added here)
            drawBackgroundLayers(state.distance)

            // Draw Ground
            drawRect(
                color = Color(0xFF388E3C),
                topLeft = Offset(0f, groundY),
                size = Size(size.width, size.height - groundY)
            )

            // Draw Player
            val playerY = groundY + state.player.y - state.player.height
            drawRoundRect(
                color = Color(0xFF1976D2),
                topLeft = Offset(200f, playerY),
                size = Size(state.player.width, state.player.height),
                cornerRadius = CornerRadius(10f, 10f)
            )

            // Draw Obstacles
            state.obstacles.forEach { obstacle ->
                drawRect(
                    color = obstacle.color,
                    topLeft = Offset(obstacle.x, groundY - obstacle.height),
                    size = Size(obstacle.width, obstacle.height)
                )
            }
        }

        // UI Overlays
        Text(
            text = "Score: ${state.score}",
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(16.dp),
            style = MaterialTheme.typography.headlineMedium,
            color = Color.Black,
            fontWeight = FontWeight.Bold
        )

        if (state.status == GameStatus.IDLE) {
            Text(
                text = "TAP TO START",
                modifier = Modifier.align(Alignment.Center),
                style = MaterialTheme.typography.displayMedium,
                color = Color.Black
            )
        }

        if (state.status == GameStatus.OVER) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.5f)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "GAME OVER\nFinal Score: ${state.score}\nTap to Restart",
                    style = MaterialTheme.typography.headlineLarge,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
            }
        }
    }
}

fun DrawScope.drawBackgroundLayers(distance: Float) {
    // Distant mountains (Slow moving)
    val layer1Speed = 0.2f
    val x1 = -(distance * layer1Speed * 100) % size.width
    drawLayer(x1, Color(0xFF90A4AE), 400f)
    drawLayer(x1 + size.width, Color(0xFF90A4AE), 400f)

    // Near hills
    val layer2Speed = 0.5f
    val x2 = -(distance * layer2Speed * 100) % size.width
    drawLayer(x2, Color(0xFF689F38), 600f)
    drawLayer(x2 + size.width, Color(0xFF689F38), 600f)
}

fun DrawScope.drawLayer(x: Float, color: Color, yStart: Float) {
    drawRect(
        color = color,
        topLeft = Offset(x, yStart),
        size = Size(size.width + 2f, size.height - yStart)
    )
}
