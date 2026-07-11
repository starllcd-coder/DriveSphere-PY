import 'package:flutter/foundation.dart';

import '../config/app_config.dart';

class ApiConstants {
  static String get baseUrl {
    const configured = AppConfig.apiBaseUrl;
    if (!kIsWeb) return configured;

    try {
      final uri = Uri.parse(configured);
      final host = uri.host.toLowerCase();
      final isLocal = host == '127.0.0.1' || host == 'localhost';
      if (!isLocal) return configured;

      final browserHost = Uri.base.host;
      final browserHostLower = browserHost.toLowerCase();
      final browserIsLocal =
          browserHostLower == '127.0.0.1' || browserHostLower == 'localhost';
      if (browserHost.isEmpty || browserIsLocal) return configured;

      return uri.replace(host: browserHost).toString();
    } catch (_) {
      return configured;
    }
  }
}
