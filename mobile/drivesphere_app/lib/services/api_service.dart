import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import '../core/constants/api_constants.dart';
import '../core/config/app_config.dart';
import '../core/constants/app_countries.dart';
import '../models/booking_model.dart';
import '../models/document_model.dart';
import '../models/notification_model.dart';
import '../models/payment_model.dart';
import '../models/profile_model.dart';
import '../models/support_message_model.dart';
import '../models/vehicle_model.dart';
import 'offline/local_db_service.dart';
import 'offline/offline_mode.dart';
import 'offline/offline_mode_controller.dart';

class ApiService {
  static const String _accessTokenKey = 'access_token';
  static const String _selectedCountryKey = 'selected_country';
  static const String _selectedLanguageKey = 'selected_language';
  static const String _selectedCityKey = 'selected_city';
  static const String _favoriteVehicleIdsKey = 'favorite_vehicle_ids';
  static const String _compareVehicleIdsKey = 'compare_vehicle_ids';
  static const String _favoriteCompanyNamesKey = 'favorite_company_names';
  static const String _savedPickupLocationsKey = 'saved_pickup_locations';
  static const String _savedPaymentMethodsKey = 'saved_payment_methods';
  static const String _bookingCartKey = 'booking_cart_vehicle_ids';
  static const String _localNotificationsCacheKey = 'local_notifications';
  static const String _localReviewsCacheKey = 'local_reviews';
  static const String _localDocumentsCacheKey = 'local_documents';
  static const String _localSupportMessagesCacheKey = 'local_support_messages';

  late final Dio _dio;
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  static final OfflineModeController _modeController = OfflineModeController.instance;
  static final LocalDbService _localDb = LocalDbService.instance;
  static final ValueNotifier<int> _queueCount = ValueNotifier<int>(0);
  static final ValueNotifier<bool> _syncing = ValueNotifier<bool>(false);
  static bool _offlineReady = false;
  static bool _syncInProgress = false;

  ApiService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: const {
          'Content-Type': 'application/json',
        },
      ),
    );
    _ensureOfflineReady();
  }

  ValueListenable<OfflineMode> get modeListenable => _modeController.mode;
  ValueListenable<int> get queueCountListenable => _queueCount;
  ValueListenable<bool> get syncingListenable => _syncing;
  OfflineMode get currentMode => _modeController.mode.value;

  String get modeLabel {
    switch (currentMode) {
      case OfflineMode.online:
        return 'Online';
      case OfflineMode.offline:
        return 'Offline (cached)';
      case OfflineMode.demo:
        return 'Demo mode';
    }
  }

  Future<void> _ensureOfflineReady() async {
    if (_offlineReady) return;
    _offlineReady = true;
    await _modeController.ensureInitialized();
    _queueCount.value = await _localDb.queueSize();
    _modeController.mode.addListener(() {
      if (_modeController.mode.value == OfflineMode.online) {
        _syncQueuedActions();
      }
    });
  }

  Future<Map<String, dynamic>> login({
    required String identifier,
    required String password,
  }) async {
    final response = await _dio.post(
      ApiConstants.login,
      data: {
        'identifier': identifier,
        'password': password,
      },
    );

    final data = response.data as Map<String, dynamic>;
    final accessToken = data['tokens']?['access']?.toString() ?? '';

    await _saveAccessToken(accessToken);

    return data;
  }

  Future<Map<String, dynamic>> register({
    required String fullName,
    required String email,
    required String phone,
    required String password,
    required String nationality,
  }) async {
    try {
      final response = await post(
        ApiConstants.register,
        data: {
          'full_name': fullName,
          'email': email,
          'phone': phone,
          'password': password,
          'nationality': nationality,
        },
      );

      return response.data as Map<String, dynamic>;
    } catch (_) {
      if (!AppConfig.enableDemoMode) rethrow;
      return {
        'success': true,
        'message': 'Registration completed (offline mode).',
      };
    }
  }

  Future<Map<String, dynamic>> requestOtp({required String phone}) async {
    try {
      final response = await post('/auth/otp/request/', data: {'phone': phone});
      return response.data as Map<String, dynamic>;
    } catch (_) {
      if (!AppConfig.enableDemoMode) rethrow;
      return {
        'success': true,
        'otp': '123456',
      };
    }
  }

  Future<Map<String, dynamic>> verifyOtp({
    required String phone,
    required String otp,
  }) async {
    try {
      final response = await post(
        '/auth/otp/verify/',
        data: {
          'phone': phone,
          'otp': otp,
        },
      );
      return response.data as Map<String, dynamic>;
    } catch (_) {
      if (!AppConfig.enableDemoMode) rethrow;
      return {
        'success': otp == '123456',
      };
    }
  }

  Future<bool> loginWithProvider(String provider) async {
    final tokenPayload = await _getSocialToken(provider);

    if (tokenPayload == null) {
      if (AppConfig.enableDemoMode) {
        await _saveAccessToken('${provider.toLowerCase()}_offline_token');
        return true;
      }
      return false;
    }

    try {
      final response = await post(
        ApiConstants.socialAuth,
        data: tokenPayload,
      );
      final data = response.data as Map<String, dynamic>;
      final accessToken = data['tokens']?['access']?.toString() ?? '';
      if (accessToken.isNotEmpty) {
        await _saveAccessToken(accessToken);
        return true;
      }
    } catch (_) {
      if (!AppConfig.enableDemoMode) rethrow;
    }

    if (AppConfig.enableDemoMode) {
      await _saveAccessToken('${provider.toLowerCase()}_offline_token');
      return true;
    }
    return false;
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessTokenKey);
    await _secureStorage.delete(key: _accessTokenKey);
  }

  Future<String?> getToken() async {
    final secureToken = await _secureStorage.read(key: _accessTokenKey);
    if (secureToken != null && secureToken.isNotEmpty) {
      return secureToken;
    }

    final prefs = await SharedPreferences.getInstance();
    final legacyToken = prefs.getString(_accessTokenKey);
    if (legacyToken != null && legacyToken.isNotEmpty) {
      await _saveAccessToken(legacyToken);
      await prefs.remove(_accessTokenKey);
    }
    return legacyToken;
  }

  Future<void> _saveAccessToken(String token) async {
    if (token.isEmpty) return;
    await _secureStorage.write(key: _accessTokenKey, value: token);
  }

  Future<Map<String, dynamic>?> _getSocialToken(String provider) async {
    final normalized = provider.toLowerCase();
    if (normalized == 'google') {
      if (kIsWeb &&
          AppConfig.googleWebClientId.isEmpty &&
          AppConfig.googleServerClientId.isEmpty) {
        throw StateError(
          'GOOGLE_SIGNIN_NOT_CONFIGURED: set GOOGLE_WEB_CLIENT_ID (or GOOGLE_SERVER_CLIENT_ID).',
        );
      }
      final signIn = GoogleSignIn(
        clientId: kIsWeb
            ? (AppConfig.googleWebClientId.isNotEmpty
                ? AppConfig.googleWebClientId
                : AppConfig.googleServerClientId)
            : null,
        serverClientId: AppConfig.googleServerClientId.isEmpty
            ? null
            : AppConfig.googleServerClientId,
      );
      final account = await signIn.signIn();
      if (account == null) return null;
      final auth = await account.authentication;
      return {
        'provider': 'google',
        'id_token': auth.idToken,
        'access_token': auth.accessToken,
      };
    }

    if (normalized == 'apple') {
      if (kIsWeb) {
        throw StateError(
          'APPLE_SIGNIN_NOT_CONFIGURED: Apple web sign-in requires full web service setup.',
        );
      }
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );
      return {
        'provider': 'apple',
        'id_token': credential.identityToken,
        'authorization_code': credential.authorizationCode,
      };
    }

    return null;
  }

  Future<bool> hasToken() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  Future<void> saveSelectedCountry(String country) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_selectedCountryKey, country);

    final config = AppCountries.byName(country);
    await prefs.setString(_selectedCityKey, config.cities.first);
  }

  Future<String?> getSelectedCountry() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_selectedCountryKey);
  }

  Future<bool> hasSelectedCountry() async {
    final country = await getSelectedCountry();
    return country != null && country.isNotEmpty;
  }

  Future<void> saveSelectedLanguage(String languageCode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_selectedLanguageKey, languageCode);
  }

  Future<String?> getSelectedLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_selectedLanguageKey);
  }

  Future<void> saveSelectedCity(String city) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_selectedCityKey, city);
  }

  Future<String?> getSelectedCity() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_selectedCityKey);
  }

  Future<Response> get(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    await _ensureOfflineReady();
    final token = await getToken();
    try {
      final response = await _dio.get(
        path,
        queryParameters: queryParameters,
        options: Options(
          headers: {
            'Authorization': token != null ? 'Bearer $token' : null,
          },
        ),
      );
      _modeController.markOnline();
      return response;
    } catch (e) {
      _modeController.markOffline();
      rethrow;
    }
  }

  Future<Response> post(
    String path, {
    Map<String, dynamic>? data,
  }) async {
    await _ensureOfflineReady();
    final token = await getToken();
    try {
      final response = await _dio.post(
        path,
        data: data,
        options: Options(
          headers: {
            'Authorization': token != null ? 'Bearer $token' : null,
          },
        ),
      );
      _modeController.markOnline();
      await _syncQueuedActions();
      return response;
    } catch (e) {
      _modeController.markOffline();
      rethrow;
    }
  }

  Future<Response> delete(String path) async {
    await _ensureOfflineReady();
    final token = await getToken();
    try {
      final response = await _dio.delete(
        path,
        options: Options(
          headers: {
            'Authorization': token != null ? 'Bearer $token' : null,
          },
        ),
      );
      _modeController.markOnline();
      await _syncQueuedActions();
      return response;
    } catch (e) {
      _modeController.markOffline();
      rethrow;
    }
  }

  dynamic _unwrapData(dynamic payload) {
    if (payload is Map<String, dynamic> && payload.containsKey('data')) {
      return payload['data'];
    }
    return payload;
  }

  Future<List<Map<String, dynamic>>> _getLocalList(String cacheKey) async {
    return _localDb.getCachedList(cacheKey);
  }

  Future<void> _upsertLocalListItem(
    String cacheKey,
    Map<String, dynamic> item, {
    int maxItems = 100,
    bool Function(Map<String, dynamic> existing)? match,
  }) async {
    final current = await _getLocalList(cacheKey);
    final matcher = match ??
        (existing) =>
            existing['id']?.toString() == item['id']?.toString() &&
            existing['id'] != null;
    current.removeWhere(matcher);
    current.insert(0, item);
    await _localDb.saveCache(cacheKey, current.take(maxItems).toList());
  }

  Future<void> _removeLocalListItem(
    String cacheKey,
    bool Function(Map<String, dynamic> item) predicate,
  ) async {
    final current = await _getLocalList(cacheKey);
    current.removeWhere(predicate);
    await _localDb.saveCache(cacheKey, current);
  }

  String _fingerprint(String action, Map<String, dynamic> payload) {
    final keys = payload.keys.toList()..sort();
    final parts = <String>[action];
    for (final key in keys) {
      parts.add('$key=${payload[key]}');
    }
    return parts.join('|');
  }

  Future<void> _enqueueSyncAction(
    String action,
    Map<String, dynamic> payload,
  ) async {
    await _localDb.enqueue(
      action,
      payload,
      fingerprint: _fingerprint(action, payload),
    );
    _queueCount.value = await _localDb.queueSize();
  }

  Future<void> _syncQueuedActions() async {
    if (_syncInProgress || currentMode != OfflineMode.online) return;
    _syncInProgress = true;
    _syncing.value = true;
    try {
      final queue = await _localDb.getQueue();
      for (final item in queue) {
        final id = (item['id'] as num).toInt();
        final action = item['action']?.toString() ?? '';
        final payload = Map<String, dynamic>.from(item['payload'] as Map);
        final attempts = (item['attempts'] as num?)?.toInt() ?? 0;
        try {
          switch (action) {
            case 'create_booking':
              await post(ApiConstants.createBooking, data: payload);
              break;
            case 'create_payment':
              await post(ApiConstants.createPayment, data: payload);
              break;
            case 'send_support_message':
              await post('/support/messages/', data: payload);
              break;
            case 'add_review':
              final vehicleId = payload.remove('vehicle_id');
              await post('/vehicles/$vehicleId/reviews/', data: payload);
              break;
            case 'mark_notification_read':
              final notificationId = payload['id'];
              await post('${ApiConstants.notifications}$notificationId/read/');
              break;
            case 'delete_notification':
              final notificationId = payload['id'];
              await delete('${ApiConstants.notifications}$notificationId/delete/');
              break;
            default:
              break;
          }
          await _localDb.removeQueueItem(id);
          _queueCount.value = await _localDb.queueSize();
        } catch (_) {
          await _localDb.markQueueItemFailed(
            id,
            error: 'sync_failed',
            attempts: attempts + 1,
          );
          break;
        }
      }
    } finally {
      _syncInProgress = false;
      _syncing.value = false;
    }
  }

  Future<List<int>> getFavoriteVehicleIds() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_favoriteVehicleIdsKey) ?? [];
    return raw.map((e) => int.tryParse(e) ?? 0).where((e) => e > 0).toList();
  }

  Future<void> toggleFavoriteVehicle(int vehicleId) async {
    final prefs = await SharedPreferences.getInstance();
    final current = await getFavoriteVehicleIds();

    if (current.contains(vehicleId)) {
      current.remove(vehicleId);
    } else {
      current.add(vehicleId);
    }

    await prefs.setStringList(
      _favoriteVehicleIdsKey,
      current.map((e) => e.toString()).toList(),
    );
  }

  Future<List<int>> getCompareVehicleIds() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_compareVehicleIdsKey) ?? [];
    return raw.map((e) => int.tryParse(e) ?? 0).where((e) => e > 0).toList();
  }

  Future<void> toggleCompareVehicle(int vehicleId) async {
    final prefs = await SharedPreferences.getInstance();
    final current = await getCompareVehicleIds();

    if (current.contains(vehicleId)) {
      current.remove(vehicleId);
    } else {
      if (current.length >= 3) {
        current.removeAt(0);
      }
      current.add(vehicleId);
    }

    await prefs.setStringList(
      _compareVehicleIdsKey,
      current.map((e) => e.toString()).toList(),
    );
  }

  Future<void> clearCompareVehicles() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_compareVehicleIdsKey);
  }

  Future<List<String>> getFavoriteCompanyNames() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_favoriteCompanyNamesKey) ?? [];
  }

  Future<bool> isCompanyFavorite(String companyName) async {
    final favorites = await getFavoriteCompanyNames();
    return favorites.contains(companyName.trim());
  }

  Future<void> toggleFavoriteCompany(String companyName) async {
    final prefs = await SharedPreferences.getInstance();
    final current = await getFavoriteCompanyNames();
    final trimmed = companyName.trim();
    if (trimmed.isEmpty) return;

    if (current.contains(trimmed)) {
      current.remove(trimmed);
    } else {
      current.add(trimmed);
    }

    await prefs.setStringList(_favoriteCompanyNamesKey, current);
  }

  Future<List<int>> getBookingCartVehicleIds() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_bookingCartKey) ?? [];
    return raw.map((e) => int.tryParse(e) ?? 0).where((e) => e > 0).toList();
  }

  Future<void> addBookingCartVehicle(int vehicleId) async {
    final prefs = await SharedPreferences.getInstance();
    final current = await getBookingCartVehicleIds();
    if (!current.contains(vehicleId)) {
      current.add(vehicleId);
    }
    await prefs.setStringList(
      _bookingCartKey,
      current.map((e) => e.toString()).toList(),
    );
  }

  Future<void> removeBookingCartVehicle(int vehicleId) async {
    final prefs = await SharedPreferences.getInstance();
    final current = await getBookingCartVehicleIds();
    current.remove(vehicleId);
    await prefs.setStringList(
      _bookingCartKey,
      current.map((e) => e.toString()).toList(),
    );
  }

  Future<void> clearBookingCart() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_bookingCartKey);
  }

  Future<List<String>> getSavedPickupLocations() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_savedPickupLocationsKey) ?? [];
  }

  Future<void> addSavedPickupLocation(String location) async {
    final prefs = await SharedPreferences.getInstance();
    final current = prefs.getStringList(_savedPickupLocationsKey) ?? [];
    final value = location.trim();
    if (value.isEmpty) return;
    if (!current.contains(value)) {
      current.add(value);
      await prefs.setStringList(_savedPickupLocationsKey, current);
    }
  }

  Future<List<String>> getSavedPaymentMethods() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_savedPaymentMethodsKey) ??
        <String>['CARD', 'APPLE_PAY', 'GOOGLE_PAY', 'CASH_ON_PICKUP'];
  }

  Future<void> savePaymentMethods(List<String> methods) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_savedPaymentMethodsKey, methods);
  }

  Future<void> registerDeviceToken({
    required String token,
    required String platform,
  }) async {
    try {
      await post(
        ApiConstants.registerDevice,
        data: {
          'token': token,
          'platform': platform,
        },
      );
    } catch (_) {}
  }

  Future<void> _addLocalNotification({
    required String title,
    required String message,
    String type = 'BOOKING',
  }) async {
    final id = DateTime.now().millisecondsSinceEpoch;
    await _upsertLocalListItem(
      _localNotificationsCacheKey,
      {
        'id': id,
        'title': title,
        'message': message,
        'notification_type': type,
        'is_read': false,
        'created_at': DateTime.now().toIso8601String(),
      },
      maxItems: 60,
    );
  }

  Future<List<NotificationModel>> _getLocalNotifications() async {
    final current = await _getLocalList(_localNotificationsCacheKey);
    return current.map(NotificationModel.fromJson).toList();
  }

  Future<void> addReview({
    required int vehicleId,
    required int rating,
    required String comment,
  }) async {
    try {
      await post(
        '/vehicles/$vehicleId/reviews/',
        data: {
          'rating': rating,
          'comment': comment,
        },
      );
      await _syncQueuedActions();
    } catch (_) {
      await _enqueueSyncAction('add_review', {
        'vehicle_id': vehicleId,
        'rating': rating,
        'comment': comment,
      });
      await _upsertLocalListItem(
        _localReviewsCacheKey,
        {
          'vehicle_id': vehicleId,
          'rating': rating,
          'comment': comment.replaceAll('|', ' ').trim(),
          'created_at': DateTime.now().toIso8601String(),
        },
        maxItems: 100,
        match: (existing) =>
            existing['vehicle_id']?.toString() == vehicleId.toString() &&
            existing['comment']?.toString() ==
                comment.replaceAll('|', ' ').trim(),
      );
    }
  }

  Future<List<Map<String, dynamic>>> getReviewsForVehicle(int vehicleId) async {
    try {
      final response = await get('/vehicles/$vehicleId/reviews/');
      final data = _unwrapData(response.data);
      final list = data is List
          ? data
          : (data is Map<String, dynamic> && data['results'] is List
              ? data['results'] as List
              : <dynamic>[]);
      if (list.isNotEmpty) {
        return list.map((item) => item as Map<String, dynamic>).toList();
      }
    } catch (_) {}

    final current = await _getLocalList(_localReviewsCacheKey);
    return current
        .where((item) => (item['vehicle_id']?.toString() ?? '') == vehicleId.toString())
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  Future<List<VehicleModel>> fetchVehicles() async {
    try {
      final response = await get(ApiConstants.vehicles);
      final data = _unwrapData(response.data);

      if (data is List) {
        await _localDb.saveCache('vehicles_all', data);
        final ids = await getFavoriteVehicleIds();
        return data
            .map((item) => VehicleModel.fromJson(item as Map<String, dynamic>))
            .map((v) => v.copyWith(isFavorite: ids.contains(v.id)))
            .toList();
      }
    } catch (_) {
      final cached = await _localDb.getCachedList('vehicles_all');
      if (cached.isNotEmpty) {
        final ids = await getFavoriteVehicleIds();
        return cached
            .map((item) => VehicleModel.fromJson(item))
            .map((v) => v.copyWith(isFavorite: ids.contains(v.id)))
            .toList();
      }
    }

    return _mockVehicles();
  }

  Future<List<VehicleModel>> searchVehicles({
    String? brand,
    String? country,
    String? city,
    String? pickupLocation,
    String? returnLocation,
    String? pickupDate,
    String? returnDate,
    String? category,
    String? transmission,
    String? fuelType,
    int? minSeats,
    double? minPrice,
    double? maxPrice,
    double? maxDeposit,
    bool? instantBook,
    bool? deliveryAvailable,
    bool? airportPickup,
    String? company,
    double? minRating,
  }) async {
    final params = <String, dynamic>{};

    if (brand != null && brand.trim().isNotEmpty) {
      params['brand'] = brand.trim();
    }
    if (country != null && country.trim().isNotEmpty) {
      params['country'] = country.trim();
    }
    if (city != null && city.trim().isNotEmpty) {
      params['city'] = city.trim();
    }
    if (pickupLocation != null && pickupLocation.trim().isNotEmpty) {
      params['pickup_location'] = pickupLocation.trim();
    }
    if (returnLocation != null && returnLocation.trim().isNotEmpty) {
      params['return_location'] = returnLocation.trim();
    }
    if (pickupDate != null && pickupDate.trim().isNotEmpty) {
      params['pickup_date'] = pickupDate.trim();
    }
    if (returnDate != null && returnDate.trim().isNotEmpty) {
      params['return_date'] = returnDate.trim();
    }
    if (category != null && category.trim().isNotEmpty) {
      params['category'] = category.trim();
    }
    if (transmission != null && transmission.trim().isNotEmpty) {
      params['transmission'] = transmission.trim();
    }
    if (fuelType != null && fuelType.trim().isNotEmpty) {
      params['fuel_type'] = fuelType.trim();
    }
    if (minSeats != null) {
      params['min_seats'] = minSeats;
    }
    if (minPrice != null) {
      params['min_price'] = minPrice;
    }
    if (maxPrice != null) {
      params['max_price'] = maxPrice;
    }
    if (maxDeposit != null) {
      params['max_deposit'] = maxDeposit;
    }
    if (instantBook != null) {
      params['instant_book'] = instantBook;
    }
    if (deliveryAvailable != null) {
      params['delivery_available'] = deliveryAvailable;
    }
    if (airportPickup != null) {
      params['airport_pickup'] = airportPickup;
    }
    if (company != null && company.trim().isNotEmpty) {
      params['company'] = company.trim();
    }
    if (minRating != null) {
      params['min_rating'] = minRating;
    }

    try {
      final response = await get(
        ApiConstants.vehicleSearch,
        queryParameters: params,
      );

      final data = response.data;
      if (data is List) {
        final ids = await getFavoriteVehicleIds();
        return data
            .map((item) => VehicleModel.fromJson(item as Map<String, dynamic>))
            .map((v) => v.copyWith(isFavorite: ids.contains(v.id)))
            .toList();
      }
    } catch (_) {}

    final all = await fetchVehicles();

    return all.where((vehicle) {
      final brandOk = brand == null || brand.trim().isEmpty
          ? true
          : vehicle.fullName.toLowerCase().contains(brand.trim().toLowerCase());

      final countryOk = country == null || country.trim().isEmpty
          ? true
          : AppCountries.byName(country)
              .cities
              .any((c) => c.toLowerCase() == vehicle.city.toLowerCase());

      final cityOk = city == null || city.trim().isEmpty
          ? true
          : vehicle.city.toLowerCase() == city.trim().toLowerCase();

      final categoryOk = category == null || category.trim().isEmpty
          ? true
          : vehicle.category.toLowerCase() == category.trim().toLowerCase();

      final transmissionOk = transmission == null || transmission.trim().isEmpty
          ? true
          : vehicle.transmission.toLowerCase() ==
              transmission.trim().toLowerCase();

      final fuelOk = fuelType == null || fuelType.trim().isEmpty
          ? true
          : vehicle.fuelType.toLowerCase() == fuelType.trim().toLowerCase();

      final seatsOk = minSeats == null ? true : vehicle.seats >= minSeats;
      final minPriceOk =
          minPrice == null ? true : vehicle.dailyRate >= minPrice;
      final maxPriceOk =
          maxPrice == null ? true : vehicle.dailyRate <= maxPrice;
      final depositOk =
          maxDeposit == null ? true : vehicle.depositAmount <= maxDeposit;
      final instantOk =
          instantBook == null ? true : vehicle.instantBook == instantBook;
      final deliveryOk = deliveryAvailable == null
          ? true
          : vehicle.deliveryAvailable == deliveryAvailable;
      final airportOk =
          airportPickup == null ? true : vehicle.airportPickup == airportPickup;
      final companyOk = company == null || company.trim().isEmpty
          ? true
          : vehicle.companyName
              .toLowerCase()
              .contains(company.trim().toLowerCase());
      final pickupOk = pickupLocation == null || pickupLocation.trim().isEmpty
          ? true
          : vehicle.pickupLocation
              .toLowerCase()
              .contains(pickupLocation.trim().toLowerCase());
      final returnOk = returnLocation == null || returnLocation.trim().isEmpty
          ? true
          : vehicle.pickupLocation
              .toLowerCase()
              .contains(returnLocation.trim().toLowerCase());
      final ratingOk = minRating == null ? true : vehicle.rating >= minRating;

      return brandOk &&
          countryOk &&
          cityOk &&
          categoryOk &&
          transmissionOk &&
          fuelOk &&
          seatsOk &&
          minPriceOk &&
          maxPriceOk &&
          depositOk &&
          instantOk &&
          deliveryOk &&
          airportOk &&
          companyOk &&
          pickupOk &&
          returnOk &&
          ratingOk;
    }).toList();
  }

  Future<bool> validateVehicleAvailability({
    required int vehicleId,
    required String pickupDate,
    required String returnDate,
  }) async {
    try {
      final vehicles = await fetchVehicles();
      final vehicle = vehicles.firstWhere((e) => e.id == vehicleId);
      return vehicle.status.toUpperCase() == 'AVAILABLE';
    } catch (_) {
      return true;
    }
  }

  Future<Map<String, dynamic>> createBooking({
    required int customerId,
    required int vehicleId,
    required String pickupDate,
    required String returnDate,
    required String pickupLocation,
    required String returnLocation,
    required String notes,
  }) async {
    await addSavedPickupLocation(pickupLocation);

    try {
      final response = await post(
        ApiConstants.createBooking,
        data: {
          'customer_id': customerId,
          'vehicle_id': vehicleId,
          'pickup_date': pickupDate,
          'return_date': returnDate,
          'pickup_location': pickupLocation,
          'return_location': returnLocation,
          'notes': notes,
        },
      );

      final data = (_unwrapData(response.data) as Map?)?.cast<String, dynamic>() ?? (response.data as Map<String, dynamic>);
      final bookingId = data['id'] ?? 0;
      final reference = data['reference']?.toString() ??
          'DS-${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}';

      await _addLocalNotification(
        title: 'Booking Confirmed',
        message: 'Your booking $reference is confirmed.',
      );

      return {
        ...data,
        'id': bookingId,
        'reference': reference,
      };
    } catch (_) {
      await _enqueueSyncAction('create_booking', {
        'customer_id': customerId,
        'vehicle_id': vehicleId,
        'pickup_date': pickupDate,
        'return_date': returnDate,
        'pickup_location': pickupLocation,
        'return_location': returnLocation,
        'notes': notes,
      });
      if (!AppConfig.enableDemoMode) rethrow;
      final bookingId = DateTime.now().millisecondsSinceEpoch;
      final reference =
          'DS-${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}';
      await _addLocalNotification(
        title: 'Booking Confirmed',
        message: 'Your booking $reference is confirmed.',
      );
      return {
        'id': bookingId,
        'reference': reference,
        'status': 'CONFIRMED',
      };
    }
  }

  Future<List<BookingModel>> fetchBookings() async {
    try {
      final response = await get(ApiConstants.bookings);
      final data = _unwrapData(response.data);
      final list = data is List
          ? data
          : (data is Map<String, dynamic> && data['results'] is List ? data['results'] as List : <dynamic>[]);
      await _localDb.saveCache('bookings_all', list);
      return list
          .map((item) => BookingModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (_) {
      final cached = await _localDb.getCachedList('bookings_all');
      if (cached.isNotEmpty) {
        return cached.map((item) => BookingModel.fromJson(item)).toList();
      }
      if (!AppConfig.enableDemoMode) rethrow;
      return _mockBookings();
    }
  }

  Future<ProfileModel> fetchProfile() async {
    try {
      final response = await get(ApiConstants.profile);
      final data = _unwrapData(response.data);
      if (data is Map<String, dynamic>) {
        await _localDb.saveCache('profile_me', data);
        return ProfileModel.fromJson(data);
      }
      return ProfileModel.fromJson(response.data as Map<String, dynamic>);
    } catch (_) {
      final cached = await _localDb.getCachedMap('profile_me');
      if (cached != null) {
        return ProfileModel.fromJson(cached);
      }
      if (!AppConfig.enableDemoMode) rethrow;
      return _mockProfile();
    }
  }

  Future<List<NotificationModel>> fetchNotifications() async {
    try {
      final response = await get(ApiConstants.notifications);
      final data = _unwrapData(response.data);
      final list = data is List
          ? data
          : (data is Map<String, dynamic> && data['results'] is List ? data['results'] as List : <dynamic>[]);
      await _localDb.saveCache('notifications_all', list);
      final remote = list
          .map(
            (item) => NotificationModel.fromJson(item as Map<String, dynamic>),
          )
          .toList();
      final local = await _getLocalNotifications();
      return [...local, ...remote];
    } catch (_) {
      final cached = await _localDb.getCachedList('notifications_all');
      if (cached.isNotEmpty) {
        final remote = cached.map((item) => NotificationModel.fromJson(item)).toList();
        final local = await _getLocalNotifications();
        return [...local, ...remote];
      }
      return _getLocalNotifications();
    }
  }

  Future<List<SupportMessageModel>> fetchSupportMessages() async {
    try {
      final response = await get('/support/messages/');
      final data = _unwrapData(response.data);
      final list = data is List
          ? data
          : (data is Map<String, dynamic> && data['results'] is List ? data['results'] as List : <dynamic>[]);
      await _localDb.saveCache('support_messages', list);
      return list.map((item) => SupportMessageModel.fromJson(item)).toList();
    } catch (_) {
      final cached = await _localDb.getCachedList('support_messages');
      if (cached.isNotEmpty) {
        return cached.map((item) => SupportMessageModel.fromJson(item)).toList();
      }
      return _getLocalSupportMessages();
    }
  }

  Future<void> sendSupportMessage(String message) async {
    if (message.trim().isEmpty) return;
    try {
      await post('/support/messages/', data: {'message': message});
      await _syncQueuedActions();
    } catch (_) {
      final id = DateTime.now().millisecondsSinceEpoch;
      final createdAt = DateTime.now().toIso8601String();
      final cleaned = message.replaceAll('|', ' ').trim();
      await _enqueueSyncAction('send_support_message', {'message': cleaned});
      await _upsertLocalListItem(
        _localSupportMessagesCacheKey,
        {
          'id': id,
          'sender': 'customer',
          'created_at': createdAt,
          'message': cleaned,
          '_offline_pending': true,
        },
        maxItems: 120,
      );
    }
  }

  Future<List<SupportMessageModel>> _getLocalSupportMessages() async {
    final current = await _getLocalList(_localSupportMessagesCacheKey);
    return current.map((item) {
      return SupportMessageModel(
        id: int.tryParse(item['id']?.toString() ?? '') ?? 0,
        sender: item['sender']?.toString() ?? 'customer',
        createdAt: item['created_at']?.toString() ?? '',
        message: item['message']?.toString() ?? '',
      );
    }).toList();
  }

  Future<void> markNotificationRead(int id) async {
    try {
      await post('${ApiConstants.notifications}$id/read/');
      await _syncQueuedActions();
    } catch (_) {
      await _enqueueSyncAction('mark_notification_read', {'id': id});
      final current = await _getLocalList(_localNotificationsCacheKey);
      var found = false;
      final updated = current.map((item) {
        final itemId = int.tryParse(item['id']?.toString() ?? '') ?? 0;
        if (itemId == id) {
          found = true;
          return {
            ...item,
            'is_read': true,
            '_offline_pending': true,
          };
        }
        return item;
      }).toList();
      if (found) {
        await _localDb.saveCache(_localNotificationsCacheKey, updated);
      }
    }
  }

  Future<void> deleteNotification(int id) async {
    try {
      await delete('${ApiConstants.notifications}$id/delete/');
      await _syncQueuedActions();
    } catch (_) {
      await _enqueueSyncAction('delete_notification', {'id': id});
      await _removeLocalListItem(
        _localNotificationsCacheKey,
        (item) => (int.tryParse(item['id']?.toString() ?? '') ?? 0) == id,
      );
    }
  }

  Future<List<DocumentModel>> fetchDocuments({
    required int customerId,
  }) async {
    try {
      final response = await get(
        ApiConstants.documents,
        queryParameters: {'customer_id': customerId},
      );

      final data = _unwrapData(response.data);
      final list = data is List
          ? data
          : (data is Map<String, dynamic> && data['results'] is List ? data['results'] as List : <dynamic>[]);
      await _localDb.saveCache('documents_customer_$customerId', list);

      return list
          .map((item) => DocumentModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (_) {
      final cached = await _localDb.getCachedList('documents_customer_$customerId');
      if (cached.isNotEmpty) {
        return cached.map((item) => DocumentModel.fromJson(item)).toList();
      }
      return _getLocalDocuments(customerId: customerId);
    }
  }

  Future<Map<String, dynamic>> uploadDocument({
    required int customerId,
    required String docType,
    required Uint8List fileBytes,
    required String fileName,
    required String expiryDate,
    required String notes,
  }) async {
    try {
      final token = await getToken();

      final formData = FormData.fromMap({
        'customer_id': customerId.toString(),
        'doc_type': docType,
        'expiry_date': expiryDate,
        'notes': notes,
        'file': MultipartFile.fromBytes(fileBytes, filename: fileName),
      });

      final response = await _dio.post(
        ApiConstants.uploadDocument,
        data: formData,
        options: Options(
          headers: {
            'Authorization': token != null ? 'Bearer $token' : null,
            'Content-Type': 'multipart/form-data',
          },
        ),
      );

      return response.data as Map<String, dynamic>;
    } catch (_) {
      final localId = await _saveLocalDocument(
        customerId: customerId,
        docType: docType,
        fileName: fileName,
        expiryDate: expiryDate,
        notes: notes,
      );
      await _addLocalNotification(
        title: 'Document Uploaded',
        message: '$docType uploaded successfully.',
        type: 'DOCUMENT',
      );
      return {
        'id': localId,
        'status': 'UPLOADED',
      };
    }
  }

  Future<List<PaymentModel>> fetchPayments({
    int? bookingId,
  }) async {
    final params = <String, dynamic>{};
    if (bookingId != null) {
      params['booking_id'] = bookingId;
    }

    try {
      final response = await get(
        ApiConstants.payments,
        queryParameters: params.isEmpty ? null : params,
      );

      final data = _unwrapData(response.data);
      final list = data is List
          ? data
          : (data is Map<String, dynamic> && data['results'] is List ? data['results'] as List : <dynamic>[]);
      final cacheKey = bookingId == null ? 'payments_all' : 'payments_booking_$bookingId';
      await _localDb.saveCache(cacheKey, list);

      return list
          .map((item) => PaymentModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (_) {
      final cacheKey = bookingId == null ? 'payments_all' : 'payments_booking_$bookingId';
      final cached = await _localDb.getCachedList(cacheKey);
      if (cached.isNotEmpty) {
        return cached.map((item) => PaymentModel.fromJson(item)).toList();
      }
      if (!AppConfig.enableDemoMode) rethrow;
      return _mockPayments();
    }
  }

  Future<Map<String, dynamic>> createPayment({
    required int bookingId,
    required String amount,
    required String method,
    required String notes,
  }) async {
    final methods = await getSavedPaymentMethods();
    if (!methods.contains(method)) {
      await savePaymentMethods([...methods, method]);
    }

    try {
      final response = await post(
        ApiConstants.createPayment,
        data: {
          'booking_id': bookingId,
          'amount': amount,
          'method': method,
          'notes': notes,
        },
      );
      await _addLocalNotification(
        title: 'Payment Confirmed',
        message: 'Payment for booking #$bookingId was confirmed.',
        type: 'PAYMENT',
      );
      await _syncQueuedActions();
      final data = _unwrapData(response.data);
      return data is Map<String, dynamic> ? data : (response.data as Map<String, dynamic>);
    } catch (_) {
      await _enqueueSyncAction('create_payment', {
        'booking_id': bookingId,
        'amount': amount,
        'method': method,
        'notes': notes,
      });
      if (!AppConfig.enableDemoMode) rethrow;
      final receipt =
          'PAY-${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}';
      await _addLocalNotification(
        title: 'Payment Confirmed',
        message: 'Payment $receipt recorded successfully.',
        type: 'PAYMENT',
      );
      return {
        'receipt_number': receipt,
        'status': 'PAID',
      };
    }
  }

  Future<String> createHyperPayCheckout({
    required int bookingId,
    required String amount,
    required String currency,
    required String paymentBrand,
  }) async {
    try {
      final response = await post(
        ApiConstants.hyperPayCheckout,
        data: {
          'booking_id': bookingId,
          'amount': amount,
          'currency': currency,
          'payment_brand': paymentBrand,
        },
      );

      final data = response.data as Map<String, dynamic>;
      return data['checkout_id']?.toString() ?? '';
    } catch (_) {
      if (!AppConfig.enableDemoMode) rethrow;
      return 'TEST_${DateTime.now().millisecondsSinceEpoch}';
    }
  }

  Future<int> _saveLocalDocument({
    required int customerId,
    required String docType,
    required String fileName,
    required String expiryDate,
    required String notes,
  }) async {
    final id = DateTime.now().millisecondsSinceEpoch;
    final createdAt = DateTime.now().toIso8601String();
    await _upsertLocalListItem(
      _localDocumentsCacheKey,
      {
        'id': id,
        'customer_id': customerId,
        'doc_type': docType,
        'status': 'PENDING',
        'file': fileName,
        'file_url': '',
        'expiry_date': expiryDate,
        'notes': notes.replaceAll('|', ' ').trim(),
        'created_at': createdAt,
        'updated_at': createdAt,
        '_offline_pending': true,
      },
      maxItems: 120,
    );
    return id;
  }

  Future<List<DocumentModel>> _getLocalDocuments({
    required int customerId,
  }) async {
    final current = await _getLocalList(_localDocumentsCacheKey);
    return current
        .where((item) =>
            (int.tryParse(item['customer_id']?.toString() ?? '') ?? 0) ==
            customerId)
        .map((item) {
      final id = int.tryParse(item['id']?.toString() ?? '') ?? 0;
      final customer = int.tryParse(item['customer_id']?.toString() ?? '') ??
          customerId;
      final docType = item['doc_type']?.toString() ?? 'DOCUMENT';
      final status = item['status']?.toString() ?? 'PENDING';
      final fileName = item['file']?.toString() ?? 'document.jpg';
      final fileUrl = item['file_url']?.toString() ?? '';
      final expiryDate = item['expiry_date']?.toString() ?? '';
      final notes = item['notes']?.toString() ?? '';
      final createdAt = item['created_at']?.toString() ?? '';
      final updatedAt = item['updated_at']?.toString() ?? createdAt;
      return DocumentModel(
        id: id,
        customer: customer,
        customerName: 'Customer $customer',
        docType: docType,
        status: status,
        file: fileName,
        fileUrl: fileUrl,
        expiryDate: expiryDate,
        notes: notes,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );
    }).toList();
  }

  Future<List<VehicleModel>> _mockVehicles() async {
    final selectedCountry = await getSelectedCountry();
    final config = AppCountries.byName(selectedCountry);
    final city = await getSelectedCity() ?? config.cities.first;
    final favoriteIds = await getFavoriteVehicleIds();

    final items = <VehicleModel>[
      VehicleModel(
        id: 1,
        brandName: 'Toyota',
        modelName: 'Corolla',
        year: 2024,
        dailyRate: 18,
        status: 'AVAILABLE',
        imageUrl: '',
        companyName: 'DriveSphere Rentals',
        city: city,
        pickupLocation: '$city Airport',
        rating: 4.7,
        depositAmount: 120,
        latitude: config.centerLat + 0.018,
        longitude: config.centerLng + 0.018,
        reviewCount: 122,
        whatsappNumber: '+96890000001',
        deliveryAvailable: true,
        airportPickup: true,
        engineType: '1.8L',
        minimumDriverAge: 21,
        mileageLimitPerDay: 250,
        insuranceCoverage: 'Basic included',
        cancellationPolicy: 'Free cancellation up to 24 hours before pickup',
        category: 'Economy',
        transmission: 'Automatic',
        fuelType: 'Petrol',
        seats: 5,
        luggage: 2,
      ),
      VehicleModel(
        id: 2,
        brandName: 'Nissan',
        modelName: 'X-Trail',
        year: 2023,
        dailyRate: 29,
        status: 'AVAILABLE',
        imageUrl: '',
        companyName: 'Prime Wheels',
        city: city,
        pickupLocation: '$city Downtown',
        rating: 4.8,
        depositAmount: 180,
        latitude: config.centerLat - 0.014,
        longitude: config.centerLng + 0.010,
        reviewCount: 86,
        whatsappNumber: '+96890000002',
        deliveryAvailable: true,
        airportPickup: false,
        engineType: '2.5L',
        minimumDriverAge: 23,
        mileageLimitPerDay: 300,
        insuranceCoverage: 'Comprehensive included',
        cancellationPolicy: 'Free cancellation up to 48 hours before pickup',
        category: 'SUV',
        transmission: 'Automatic',
        fuelType: 'Petrol',
        seats: 7,
        luggage: 4,
      ),
      VehicleModel(
        id: 3,
        brandName: 'Kia',
        modelName: 'Sportage',
        year: 2024,
        dailyRate: 31,
        status: 'AVAILABLE',
        imageUrl: '',
        companyName: 'GCC Mobility',
        city: city,
        pickupLocation: '$city Marina',
        rating: 4.6,
        depositAmount: 160,
        latitude: config.centerLat + 0.012,
        longitude: config.centerLng - 0.016,
        reviewCount: 53,
        whatsappNumber: '+96890000003',
        deliveryAvailable: true,
        airportPickup: false,
        engineType: '2.0L Turbo',
        minimumDriverAge: 23,
        mileageLimitPerDay: 280,
        insuranceCoverage: 'Basic included',
        cancellationPolicy: 'Cancellation fee may apply within 24 hours',
        category: 'SUV',
        transmission: 'Automatic',
        fuelType: 'Petrol',
        seats: 5,
        luggage: 3,
      ),
      VehicleModel(
        id: 4,
        brandName: 'Mercedes',
        modelName: 'C200',
        year: 2024,
        dailyRate: 56,
        status: 'AVAILABLE',
        imageUrl: '',
        companyName: 'Elite Rent',
        city: city,
        pickupLocation: '$city Business Bay',
        rating: 4.9,
        depositAmount: 350,
        latitude: config.centerLat - 0.010,
        longitude: config.centerLng - 0.012,
        reviewCount: 44,
        whatsappNumber: '+96890000004',
        deliveryAvailable: true,
        airportPickup: false,
        engineType: '2.0L Turbo',
        minimumDriverAge: 25,
        mileageLimitPerDay: 220,
        insuranceCoverage: 'Premium included',
        cancellationPolicy: 'Non-refundable within 48 hours of pickup',
        category: 'Luxury',
        transmission: 'Automatic',
        fuelType: 'Petrol',
        seats: 5,
        luggage: 3,
      ),
    ];

    return items
        .map((e) => e.copyWith(isFavorite: favoriteIds.contains(e.id)))
        .toList();
  }

  Future<List<BookingModel>> _mockBookings() async {
    return [
      BookingModel(
        id: 3,
        reference: 'DS-46001',
        customerName: 'Customer',
        vehicleDisplay: 'Mercedes C200 2024',
        branchName: 'Elite Rent',
        pickupDate: '2026-03-19',
        returnDate: '2026-03-21',
        pickupLocation: 'Muscat Business Bay',
        returnLocation: 'Muscat Business Bay',
        status: 'BOOKING_REQUESTED',
        currencyCode: 'OMR',
        dailyRate: 56,
        depositAmount: 350,
        subtotalAmount: 112,
        totalAmount: 117.6,
        createdByUsername: 'customer',
        createdAt: '',
        updatedAt: '',
      ),
      BookingModel(
        id: 1,
        reference: 'DS-45823',
        customerName: 'Customer',
        vehicleDisplay: 'Toyota Corolla 2024',
        branchName: 'DriveSphere Rentals',
        pickupDate: '2026-03-20',
        returnDate: '2026-03-24',
        pickupLocation: 'Muscat Airport',
        returnLocation: 'Muscat Airport',
        status: 'CONFIRMED',
        currencyCode: 'OMR',
        dailyRate: 18,
        depositAmount: 120,
        subtotalAmount: 72,
        totalAmount: 72,
        createdByUsername: 'customer',
        createdAt: '',
        updatedAt: '',
      ),
      BookingModel(
        id: 2,
        reference: 'DS-45880',
        customerName: 'Customer',
        vehicleDisplay: 'Nissan X-Trail 2023',
        branchName: 'Prime Wheels',
        pickupDate: '2026-03-12',
        returnDate: '2026-03-16',
        pickupLocation: 'Muscat Downtown',
        returnLocation: 'Muscat Downtown',
        status: 'ACTIVE',
        currencyCode: 'OMR',
        dailyRate: 29,
        depositAmount: 180,
        subtotalAmount: 116,
        totalAmount: 121.8,
        createdByUsername: 'customer',
        createdAt: '',
        updatedAt: '',
      ),
      BookingModel(
        id: 4,
        reference: 'DS-45710',
        customerName: 'Customer',
        vehicleDisplay: 'Kia Sportage 2024',
        branchName: 'GCC Mobility',
        pickupDate: '2026-03-01',
        returnDate: '2026-03-05',
        pickupLocation: 'Muscat Marina',
        returnLocation: 'Muscat Marina',
        status: 'COMPLETED',
        currencyCode: 'OMR',
        dailyRate: 31,
        depositAmount: 160,
        subtotalAmount: 124,
        totalAmount: 130.2,
        createdByUsername: 'customer',
        createdAt: '',
        updatedAt: '',
      ),
    ];
  }

  ProfileModel _mockProfile() {
    return ProfileModel(
      id: 1,
      username: 'drivesphere_customer',
      email: 'customer@drivesphere.app',
      firstName: 'DriveSphere',
      lastName: 'Customer',
      fullName: 'DriveSphere Customer',
      isActive: true,
      isStaff: false,
    );
  }

  Future<List<PaymentModel>> _mockPayments() async {
    return [
      PaymentModel(
        id: 1,
        receiptNumber: 'PAY-84321',
        bookingId: 1,
        bookingReference: 'DS-45823',
        customerName: 'Customer',
        vehicleDisplay: 'Toyota Corolla 2024',
        branchName: 'DriveSphere Rentals',
        paymentDate: '2026-03-14',
        method: 'CARD',
        amount: 72,
        currencyCode: 'OMR',
        status: 'PAID',
        notes: '',
        createdByEmail: 'customer@drivesphere.app',
        createdAt: '',
        updatedAt: '',
      ),
    ];
  }
}
