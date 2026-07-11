import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../services/api_service.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    await Future.delayed(const Duration(milliseconds: 1200));

    bool hasCountry = false;
    bool hasToken = false;
    try {
      hasCountry = await _apiService
          .hasSelectedCountry()
          .timeout(const Duration(seconds: 2), onTimeout: () => false);
      hasToken = await _apiService
          .hasToken()
          .timeout(const Duration(seconds: 2), onTimeout: () => false);
    } catch (_) {}

    if (!mounted) return;

    if (!hasCountry) {
      Navigator.pushReplacementNamed(context, AppRoutes.countrySelection);
      return;
    }

    if (hasToken) {
      try {
        await _apiService.fetchProfile().timeout(const Duration(seconds: 5));
      } catch (_) {}
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, AppRoutes.appShell);
      return;
    }

    if (!mounted) return;
    Navigator.pushReplacementNamed(context, AppRoutes.login);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF234E8C),
              Color(0xFF1D467E),
              Color(0xFFD3AE52),
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset(
                'assets/images/logo.png',
                width: 120,
                fit: BoxFit.contain,
              ),
              const SizedBox(height: 18),
              Text(
                'app_name'.tr(),
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'tagline'.tr(),
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 36),
              const SizedBox(
                width: 28,
                height: 28,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 14),
              Text(
                'splash.loading'.tr(),
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.white,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
