package com.chuatzeyee.tylendar.ui

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.*
import androidx.compose.ui.unit.sp
import com.chuatzeyee.tylendar.R

val Ink = Color(0xFF262D29)
val Paper = Color(0xFFF5F3EC)
val Mat = Color(0xFFFFFEFB)
val Seal = Color(0xFFA63F31)
val Sage = Color(0xFF58664F)
val Garden = Color(0xFFE7EBDF)
val Muted = Color(0xFF656B63)
val Hairline = Color(0xFFD9DCD1)
val Canela = FontFamily(Font(R.font.canela_regular, FontWeight.Normal), Font(R.font.canela_medium, FontWeight.Medium), Font(R.font.canela_bold, FontWeight.Bold))
val Eyebrow = TextStyle(fontSize = 10.sp, lineHeight = 16.sp, letterSpacing = 1.4.sp, fontWeight = FontWeight.Medium)
val PrintTitle = TextStyle(fontFamily = Canela, fontSize = 35.sp, lineHeight = 39.sp, letterSpacing = (-0.7).sp)
@Composable fun TylendarTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = lightColorScheme(primary = Seal, onPrimary = Mat, secondary = Sage, secondaryContainer = Garden,
        onSecondaryContainer = Ink, background = Paper, surface = Mat, onSurface = Ink, onBackground = Ink, outline = Hairline, error = Seal),
        typography = Typography(
            titleLarge = TextStyle(fontFamily = Canela, fontSize = 28.sp, lineHeight = 34.sp),
            bodyLarge = TextStyle(fontSize = 15.sp, lineHeight = 24.sp),
            bodyMedium = TextStyle(fontSize = 13.sp, lineHeight = 21.sp),
            bodySmall = TextStyle(fontSize = 11.sp, lineHeight = 17.sp),
            labelLarge = TextStyle(fontSize = 12.sp, fontWeight = FontWeight.Medium),
            labelSmall = Eyebrow), content = content)
}
