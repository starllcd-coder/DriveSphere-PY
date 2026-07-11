import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'api_service.dart';

class PushNotificationService {
  PushNotificationService({required ApiService apiService})
      : _apiService = apiService;

  final ApiService _apiService;
  Future<void> initialize() async {
    if (Firebase.apps.isEmpty) {
      return;
    }
    final FirebaseMessaging messaging = FirebaseMessaging.instance;

    final settings = await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      return;
    }

    final token = await messaging.getToken();
    if (token != null && token.isNotEmpty) {
      await _apiService.registerDeviceToken(
        token: token,
        platform: Platform.isIOS ? 'ios' : 'android',
      );
    }

    messaging.onTokenRefresh.listen((newToken) async {
      await _apiService.registerDeviceToken(
        token: newToken,
        platform: Platform.isIOS ? 'ios' : 'android',
      );
    });
  }
}

Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  return;
}
