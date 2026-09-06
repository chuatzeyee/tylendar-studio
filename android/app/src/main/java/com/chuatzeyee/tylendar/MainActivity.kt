package com.chuatzeyee.tylendar

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.chuatzeyee.tylendar.ui.App
import com.chuatzeyee.tylendar.ui.TylendarTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            TylendarTheme {
                App(viewModel())
            }
        }
    }
}
