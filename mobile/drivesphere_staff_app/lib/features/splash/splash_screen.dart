import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../core/session/session_store.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/brand_background.dart';
import '../../widgets/glass_panel.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final _session = SessionStore();
  final _api = StaffApiService();

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    await Future.delayed(const Duration(milliseconds: 900));
    final token = await _session.getToken();
    if (!mounted) return;

    if (token == null) {
      Navigator.pushReplacementNamed(context, AppRoutes.login);
      return;
    }

    try {
      final payload = await _api.fetchBootstrap();
      if (!mounted) return;
      Navigator.pushReplacementNamed(
        context,
        AppRoutes.shell,
        arguments: payload,
      );
    } catch (_) {
      await _session.clear();
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, AppRoutes.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BrandBackground(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 360),
            child: GlassPanel(
              borderRadius: BorderRadius.circular(26),
              child: const Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(height: 4),
                  Image(
                    image: AssetImage('assets/images/logo.png'),
                    width: 170,
                  ),
                  SizedBox(height: 6),
                  Text(
                    'DriveSphere Staff',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF274772),
                    ),
                  ),
                  SizedBox(height: 14),
                  CircularProgressIndicator(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
