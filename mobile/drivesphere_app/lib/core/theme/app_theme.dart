import 'package:flutter/material.dart';

class AppTheme {
  static const primaryColor = Color(0xFF1E3A8A);
  static const accentColor = Color(0xFFD4AF37);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      primaryColor: primaryColor,
      scaffoldBackgroundColor: Colors.white,
      fontFamily: 'Poppins',
      colorScheme: const ColorScheme.light(
        primary: primaryColor,
        secondary: accentColor,
      ),
    );
  }
}
