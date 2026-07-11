import 'package:flutter/material.dart';

class AppColors {
  static const primary = Color(0xFF1F4E8C);
  static const primaryDark = Color(0xFF17375F);
  static const accent = Color(0xFFD1A646);
  static const scaffold = Color(0xFFF3F5F9);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceSoft = Color(0xFFF9FAFC);
  static const border = Color(0xFFDDE4EF);
  static const text = Color(0xFF1F2A44);
  static const textMuted = Color(0xFF6A7893);
}

class AppTheme {
  static ThemeData get light {
    const baseText = TextTheme(
      bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: AppColors.text),
      bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: AppColors.text),
      bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: AppColors.textMuted),
      titleLarge: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.primaryDark),
      titleMedium: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.primaryDark),
      titleSmall: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.primaryDark),
      labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.primaryDark),
      labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.text),
    );

    return ThemeData(
      useMaterial3: true,
      fontFamily: 'Poppins',
      textTheme: baseText,
      scaffoldBackgroundColor: AppColors.scaffold,
      colorScheme: const ColorScheme.light(
        primary: AppColors.primary,
        secondary: AppColors.accent,
        surface: AppColors.surface,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 0,
        foregroundColor: AppColors.primaryDark,
        iconTheme: IconThemeData(
          color: AppColors.primaryDark,
          size: 22,
        ),
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontFamily: 'Poppins',
          color: AppColors.primaryDark,
          fontWeight: FontWeight.w600,
          fontSize: 22,
        ),
      ),
      cardTheme: const CardThemeData(
        color: AppColors.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        hintStyle: const TextStyle(color: AppColors.textMuted),
        labelStyle: const TextStyle(color: AppColors.textMuted),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.primary, width: 1.2),
        ),
      ),
      chipTheme: const ChipThemeData(
        backgroundColor: AppColors.surfaceSoft,
        selectedColor: AppColors.primary,
        labelStyle: TextStyle(color: AppColors.text),
        secondaryLabelStyle: TextStyle(color: AppColors.surface, fontWeight: FontWeight.w600),
        side: BorderSide(color: AppColors.border),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          foregroundColor: AppColors.surface,
          backgroundColor: AppColors.primary,
          textStyle: const TextStyle(fontWeight: FontWeight.w700, letterSpacing: 0.2),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primaryDark,
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
          side: const BorderSide(color: AppColors.border),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primaryDark,
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      navigationBarTheme: const NavigationBarThemeData(
        backgroundColor: AppColors.surface,
        indicatorColor: Color(0x1FD1A646),
        labelTextStyle: WidgetStatePropertyAll(
          TextStyle(
            fontWeight: FontWeight.w600,
            color: AppColors.text,
          ),
        ),
      ),
    );
  }
}
