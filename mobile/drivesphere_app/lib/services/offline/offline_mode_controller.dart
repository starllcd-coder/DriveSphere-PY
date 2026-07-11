import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

import '../../core/config/app_config.dart';
import 'offline_mode.dart';

class OfflineModeController {
  OfflineModeController._();
  static final OfflineModeController instance = OfflineModeController._();

  final ValueNotifier<OfflineMode> mode = ValueNotifier<OfflineMode>(
    AppConfig.enableDemoMode ? OfflineMode.demo : OfflineMode.online,
  );

  bool _initialized = false;

  Future<void> ensureInitialized() async {
    if (_initialized) return;
    _initialized = true;
    if (AppConfig.enableDemoMode) {
      mode.value = OfflineMode.demo;
      return;
    }

    Connectivity().onConnectivityChanged.listen((result) {
      final hasNetwork = _hasNetwork(result);
      mode.value = hasNetwork ? OfflineMode.online : OfflineMode.offline;
    });

    final first = await Connectivity().checkConnectivity();
    mode.value = _hasNetwork(first) ? OfflineMode.online : OfflineMode.offline;
  }

  void markOnline() {
    if (!AppConfig.enableDemoMode) {
      mode.value = OfflineMode.online;
    }
  }

  void markOffline() {
    if (!AppConfig.enableDemoMode) {
      mode.value = OfflineMode.offline;
    }
  }

  bool _hasNetwork(dynamic connectivity) {
    if (connectivity is List<ConnectivityResult>) {
      return connectivity.any((item) => item != ConnectivityResult.none);
    }
    if (connectivity is ConnectivityResult) {
      return connectivity != ConnectivityResult.none;
    }
    return true;
  }
}
