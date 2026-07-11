import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

import 'core/routes/app_routes.dart';
import 'core/theme/app_theme.dart';
import 'services/push_notification_service.dart';

class _FocusCleanupObserver extends NavigatorObserver {
  void _clearFocus() {
    FocusManager.instance.primaryFocus?.unfocus();
  }

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    _clearFocus();
    super.didPush(route, previousRoute);
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    _clearFocus();
    super.didPop(route, previousRoute);
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    _clearFocus();
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
  }
}

final _focusCleanupObserver = _FocusCleanupObserver();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await EasyLocalization.ensureInitialized();
  try {
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
  } catch (_) {}

  runApp(
    EasyLocalization(
      supportedLocales: const [
        Locale('en'),
        Locale('ar'),
      ],
      path: 'assets/translations',
      fallbackLocale: const Locale('en'),
      startLocale: const Locale('en'),
      saveLocale: true,
      child: const DriveSphereApp(),
    ),
  );
}

class DriveSphereApp extends StatelessWidget {
  const DriveSphereApp({super.key});

  @override
  Widget build(BuildContext context) {
    final isArabic = context.locale.languageCode == 'ar';
    final fontFamily = isArabic ? 'Cairo' : 'Poppins';
    final baseTheme = AppTheme.lightTheme;

    return MaterialApp(
      title: 'DriveSphere',
      debugShowCheckedModeBanner: false,
      theme: baseTheme.copyWith(
        textTheme: baseTheme.textTheme.apply(fontFamily: fontFamily),
        primaryTextTheme:
            baseTheme.primaryTextTheme.apply(fontFamily: fontFamily),
      ),
      locale: context.locale,
      supportedLocales: context.supportedLocales,
      localizationsDelegates: context.localizationDelegates,
      initialRoute: AppRoutes.splash,
      onGenerateRoute: AppRoutes.onGenerateRoute,
      navigatorObservers: [_focusCleanupObserver],
      builder: (context, widget) {
        return GestureDetector(
          behavior: HitTestBehavior.translucent,
          onTap: () => FocusManager.instance.primaryFocus?.unfocus(),
          child: Directionality(
            textDirection:
                isArabic ? ui.TextDirection.rtl : ui.TextDirection.ltr,
            child: Container(
              color: const Color(0xFFEFEFEF),
              child: Center(
                child: SizedBox(
                  width: 430,
                  child: widget,
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
