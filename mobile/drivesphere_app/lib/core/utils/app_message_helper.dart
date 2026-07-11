import 'package:dio/dio.dart';

import '../constants/api_constants.dart';

class AppMessageHelper {
  static String extractErrorMessage(dynamic error) {
    final text = (error?.toString() ?? '').trim();

    if (_looksLikeConnectionError(error, text)) {
      return 'Unable to connect to server. Make sure backend is running at ${ApiConstants.baseUrl}.';
    }

    if (_looksLikeGoogleClientConfigError(text)) {
      return 'Google sign-in is not configured for web. Set GOOGLE_WEB_CLIENT_ID and restart app.';
    }

    if (_looksLikeAppleConfigError(text)) {
      return 'Apple sign-in is not configured for this build. Use username/password or OTP.';
    }

    if (error is DioException) {
      final data = error.response?.data;

      if (error.response?.statusCode == 401) {
        return 'Invalid username/email or password.';
      }

      final extracted = _extractFromData(data);
      if (extracted != null) return extracted;
    }

    if (text.contains("NoSuchMethodError") &&
        text.contains("response") &&
        text.contains("AssertionError")) {
      return 'Provider sign-in is not configured correctly for this build. Use username/password or OTP.';
    }

    if (text.isNotEmpty) return text;
    return 'Something went wrong. Please try again.';
  }

  static bool _looksLikeConnectionError(dynamic error, String text) {
    if (error is DioException) {
      return error.type == DioExceptionType.connectionError ||
          error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout ||
          error.type == DioExceptionType.sendTimeout;
    }

    final lower = text.toLowerCase();
    return lower.contains('dioexception [connection error]') ||
        lower.contains('xmlhttprequest onerror callback') ||
        lower.contains('socketexception') ||
        lower.contains('connection refused');
  }

  static String? _extractFromData(dynamic data) {
    if (data == null) return null;
    if (data is String && data.trim().isNotEmpty) return data;
    if (data is! Map) return null;
    final map = Map<String, dynamic>.from(data);

    final direct = [
      map['message'],
      map['detail'],
      map['error'],
    ];
    for (final value in direct) {
      final text = value?.toString().trim();
      if (text != null && text.isNotEmpty) return text;
    }

    final nonField = map['non_field_errors'];
    if (nonField is List && nonField.isNotEmpty) {
      return nonField.first.toString();
    }

    for (final entry in map.entries) {
      final value = entry.value;
      if (value is List && value.isNotEmpty) {
        return value.first.toString();
      }
      if (value is String && value.trim().isNotEmpty) {
        return value;
      }
    }
    return null;
  }

  static bool _looksLikeGoogleClientConfigError(String text) {
    final lower = text.toLowerCase();
    return lower.contains("google_sign_in_web") &&
        (lower.contains("clientid != null") ||
            lower.contains("clientid not set") ||
            lower.contains("google-signin-client_id"));
  }

  static bool _looksLikeAppleConfigError(String text) {
    final lower = text.toLowerCase();
    return lower.contains('apple_signin_not_configured') ||
        lower.contains("typeerrorimpl") ||
        lower.contains("is not a subtype of type 'jsobject'");
  }
}
