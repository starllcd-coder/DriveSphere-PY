import 'package:dio/dio.dart';

import '../core/constants/api_constants.dart';
import '../core/constants/api_paths.dart';
import '../core/models/branch_model.dart';
import '../core/models/staff_profile.dart';
import '../core/session/session_store.dart';
import 'offline/offline_write_queue.dart';

class StaffBootstrapPayload {
  final StaffProfile profile;
  final BranchModel? activeBranch;
  final List<BranchModel> branches;
  final String companyName;
  final String companyLogoUrl;

  const StaffBootstrapPayload({
    required this.profile,
    required this.activeBranch,
    required this.branches,
    this.companyName = '',
    this.companyLogoUrl = '',
  });
}

class StaffApiService {
  final SessionStore _sessionStore;
  final OfflineWriteQueue _queue = OfflineWriteQueue();
  late final Dio _dio;
  static StaffBootstrapPayload? _bootstrapCache;
  static bool _isFlushingQueue = false;

  StaffApiService({SessionStore? sessionStore})
      : _sessionStore = sessionStore ?? SessionStore() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: const {'Content-Type': 'application/json'},
      ),
    );
  }

  dynamic _unwrap(dynamic payload) {
    if (payload is Map<String, dynamic> && payload.containsKey('data')) {
      return payload['data'];
    }
    return payload;
  }

  Future<String> login({
    required String identifier,
    required String password,
    bool rememberMe = true,
  }) async {
    final response = await _dio.post(
      ApiPaths.login,
      data: {'identifier': identifier, 'password': password},
    );
    final body = response.data as Map<String, dynamic>;
    final token = body['data']?['tokens']?['access']?.toString() ??
        body['tokens']?['access']?.toString() ??
        '';
    if (token.isEmpty) {
      throw Exception('Access token missing in login response.');
    }
    await _sessionStore.saveRememberMe(rememberMe);
    await _sessionStore.saveLastIdentifier(identifier);
    await _sessionStore.saveToken(token, persist: rememberMe);
    await _flushQueuedWrites();
    return token;
  }

  Future<void> logout() async {
    await _sessionStore.clear();
    await _queue.clear();
    _bootstrapCache = null;
  }

  Future<StaffBootstrapPayload> fetchBootstrap({int? branchId}) async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    if (token == null) {
      throw Exception('Not authenticated.');
    }

    final selectedBranchId =
        branchId ?? await _sessionStore.getActiveBranchId();
    final query = <String, dynamic>{};
    if (selectedBranchId != null) {
      query['branch_id'] = selectedBranchId;
    }

    final response = await _dio.get(
      ApiPaths.bootstrap,
      queryParameters: query.isEmpty ? null : query,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data) as Map<String, dynamic>;
    final profile = StaffProfile.fromJson(
      (data['profile'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
    final activeBranchJson =
        (data['active_branch'] as Map?)?.cast<String, dynamic>();
    final branchesJson = (data['branches'] as List?) ?? const [];
    final businessJson =
        (data['business_profile'] as Map?)?.cast<String, dynamic>() ??
            const <String, dynamic>{};
    final branches = branchesJson
        .map((item) =>
            BranchModel.fromJson((item as Map).cast<String, dynamic>()))
        .toList();
    final activeBranch = activeBranchJson == null
        ? null
        : BranchModel.fromJson(activeBranchJson);

    if (activeBranch != null) {
      await _sessionStore.saveActiveBranchId(activeBranch.id);
    }

    final payload = StaffBootstrapPayload(
      profile: profile,
      activeBranch: activeBranch,
      branches: branches,
      companyName: (businessJson['name']?.toString() ?? '').trim(),
      companyLogoUrl: (businessJson['logo_url']?.toString() ?? '').trim(),
    );
    _bootstrapCache = payload;
    return payload;
  }

  Future<StaffBootstrapPayload> getBootstrapCachedOrFetch() async {
    final cached = _bootstrapCache;
    if (cached != null) return cached;
    return fetchBootstrap();
  }

  Future<bool> hasAnyPermission(List<String> permissions) async {
    final payload = await getBootstrapCachedOrFetch();
    final userPerms = payload.profile.permissions.toSet();
    for (final perm in permissions) {
      if (userPerms.contains(perm)) {
        return true;
      }
    }
    return false;
  }

  Future<void> refreshBootstrapCache() async {
    await fetchBootstrap();
  }

  Future<Map<String, dynamic>> fetchReportsOverview({
    required String period,
    String? dateFrom,
    String? dateTo,
  }) async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final branchId = await _sessionStore.getActiveBranchId();
    final response = await _dio.get(
      ApiPaths.reportsOverview,
      queryParameters: {
        'period': period,
        if (dateFrom != null && dateFrom.trim().isNotEmpty)
          'date_from': dateFrom.trim(),
        if (dateTo != null && dateTo.trim().isNotEmpty) 'date_to': dateTo.trim(),
        if (branchId != null) 'branch_id': branchId,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return (_unwrap(response.data) as Map?)?.cast<String, dynamic>() ?? {};
  }

  Future<Map<String, dynamic>> fetchDashboardKpis() async {
    try {
      await _flushQueuedWrites();
      final token = await _sessionStore.getToken();
      final branchId = await _sessionStore.getActiveBranchId();
      final response = await _dio.get(
        ApiPaths.dashboardKpis,
        queryParameters: {
          if (branchId != null) 'branch_id': branchId,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
      return (_unwrap(response.data) as Map?)?.cast<String, dynamic>() ?? {};
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        // Backward-compatible fallback when older backend doesn't expose
        // /internal/dashboard/kpis/ yet.
        final overview = await fetchReportsOverview(period: 'today');
        final financial = await fetchReportsFinancial(period: 'monthly');
        final fleet = await fetchReportsFleet(period: 'monthly');
        final customers = await fetchReportsCustomers(period: 'monthly');
        return {
          'total_bookings': overview['bookings_count'] ?? 0,
          'active_customers': customers['repeat_customers'] ??
              overview['active_customers'] ??
              0,
          'fleet_vehicles': overview['fleet_vehicles'] ?? fleet['fleet_count'] ?? 0,
          'earnings': financial['gross_revenue'] ?? overview['revenue_gross'] ?? 0,
          'trend_total_bookings': 0,
          'trend_active_customers': 0,
          'trend_fleet_vehicles': 0,
          'trend_earnings': 0,
          'active_rentals': overview['active_rentals'] ?? 0,
          'today_pickups': 0,
          'today_returns': 0,
          'overdue_rentals': overview['overdue_rentals'] ?? 0,
          'fleet_utilization':
              overview['fleet_utilization'] ?? fleet['utilization_percent'] ?? 0,
          'upcoming_services': 0,
          'expiring_documents': 0,
          'maintenance_open': overview['maintenance_open'] ?? 0,
        };
      }
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> fetchMaintenance() async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final branchId = await _sessionStore.getActiveBranchId();
    final response = await _dio.get(
      ApiPaths.maintenance,
      queryParameters: {if (branchId != null) 'branch_id': branchId},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<bool> markMaintenanceDone(int taskId) async {
    final branchId = await _sessionStore.getActiveBranchId();
    return _writeAndMaybeQueue(
      method: 'POST',
      path: '${ApiPaths.maintenance}$taskId/done/',
      data: {if (branchId != null) 'branch_id': branchId},
    );
  }

  Future<List<Map<String, dynamic>>> fetchEmployees() async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final response = await _dio.get(
      ApiPaths.employees,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<List<Map<String, dynamic>>> fetchBookings() async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final branchId = await _sessionStore.getActiveBranchId();
    final response = await _dio.get(
      ApiPaths.bookings,
      queryParameters: {
        if (branchId != null) 'branch_id': branchId,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<Map<String, dynamic>> createBooking({
    required int vehicleId,
    required String pickupDate,
    required String returnDate,
    int? customerId,
    String customerName = '',
    String customerPhoneNumber = '',
    String customerIdType = 'ID',
    String customerIdNumber = '',
    String customerEmail = '',
    String customerAddress = '',
    String customerLicenseNumber = '',
    String customerLicenseIssuer = '',
    String customerLicenseIssueDate = '',
    String customerLicenseExpiryDate = '',
    String notes = '',
    String pickupTime = '',
    String returnTime = '',
    String pickupLocation = '',
    String returnLocation = '',
    String dailyRate = '',
    String depositAmount = '',
    String vatRate = '',
    String extrasTotal = '',
    List<Map<String, dynamic>>? extras,
    List<Map<String, dynamic>>? drivers,
  }) async {
    final branchId = await _sessionStore.getActiveBranchId();
    final payload = {
      'vehicle_id': vehicleId,
      'pickup_date': pickupDate,
      'return_date': returnDate,
      if (customerId != null) 'customer_id': customerId,
      if (customerId == null && customerName.trim().isNotEmpty)
        'customer_name': customerName.trim(),
      if (customerId == null && customerPhoneNumber.trim().isNotEmpty)
        'customer_phone_number': customerPhoneNumber.trim(),
      if (customerId == null && customerIdType.trim().isNotEmpty)
        'customer_id_type': customerIdType.trim(),
      if (customerId == null && customerIdNumber.trim().isNotEmpty)
        'customer_id_number': customerIdNumber.trim(),
      if (customerId == null && customerEmail.trim().isNotEmpty)
        'customer_email': customerEmail.trim(),
      if (customerId == null && customerAddress.trim().isNotEmpty)
        'customer_address': customerAddress.trim(),
      if (customerId == null && customerLicenseNumber.trim().isNotEmpty)
        'customer_license_number': customerLicenseNumber.trim(),
      if (customerId == null && customerLicenseIssuer.trim().isNotEmpty)
        'customer_license_issuer': customerLicenseIssuer.trim(),
      if (customerId == null && customerLicenseIssueDate.trim().isNotEmpty)
        'customer_license_issue_date': customerLicenseIssueDate.trim(),
      if (customerId == null && customerLicenseExpiryDate.trim().isNotEmpty)
        'customer_license_expiry_date': customerLicenseExpiryDate.trim(),
      if (pickupTime.trim().isNotEmpty) 'pickup_time': pickupTime.trim(),
      if (returnTime.trim().isNotEmpty) 'return_time': returnTime.trim(),
      if (pickupLocation.trim().isNotEmpty)
        'pickup_location': pickupLocation.trim(),
      if (returnLocation.trim().isNotEmpty)
        'return_location': returnLocation.trim(),
      if (dailyRate.trim().isNotEmpty) 'daily_rate': dailyRate.trim(),
      if (depositAmount.trim().isNotEmpty)
        'deposit_amount': depositAmount.trim(),
      if (vatRate.trim().isNotEmpty) 'vat_rate': vatRate.trim(),
      if (extrasTotal.trim().isNotEmpty) 'extras_total': extrasTotal.trim(),
      if (extras != null && extras.isNotEmpty) 'extras': extras,
      if (drivers != null && drivers.isNotEmpty) 'drivers': drivers,
      'notes': notes,
      if (branchId != null) 'branch_id': branchId,
    };
    final token = await _sessionStore.getToken();
    final headers = {'Authorization': 'Bearer $token'};
    await _flushQueuedWrites();
    try {
      final response = await _dio.request(
        ApiPaths.bookings,
        data: payload,
        options: Options(method: 'POST', headers: headers),
      );
      final body = response.data as Map<String, dynamic>? ?? const {};
      final data = body['data'];
      int? bookingId;
      if (data is Map && data['booking'] is Map) {
        bookingId = (data['booking']['id'] as num?)?.toInt();
      }
      return {'queued': false, 'booking_id': bookingId};
    } on DioException catch (e) {
      if (_shouldQueueError(e)) {
        await _queue.enqueue(method: 'POST', path: ApiPaths.bookings, data: payload);
        return {'queued': true};
      }
      rethrow;
    }
  }

  Future<bool> activateBooking(int bookingId) async {
    return _postBookingAction(ApiPaths.bookingActivate(bookingId));
  }

  Future<bool> extendBooking({
    required int bookingId,
    required String newReturnDate,
  }) async {
    return _postBookingAction(
      ApiPaths.bookingExtend(bookingId),
      data: {'new_return_date': newReturnDate},
    );
  }

  Future<bool> checkoutBooking({
    required int bookingId,
    required int odometerOutKm,
    required int fuelOutPercent,
    Map<String, dynamic>? checklist,
    String signature = '',
  }) async {
    return _postBookingAction(
      ApiPaths.bookingCheckout(bookingId),
      data: {
        'odometer_out_km': odometerOutKm,
        'fuel_out_percent': fuelOutPercent,
        if (checklist != null) 'checklist': checklist,
        if (signature.trim().isNotEmpty) 'signature': signature.trim(),
      },
    );
  }

  Future<Map<String, dynamic>> returnBooking({
    required int bookingId,
    required int odometerInKm,
    required int fuelReturnPercent,
    String actualReturnDate = '',
    String fuelCharge = '0',
    String lateFee = '0',
    String damageFee = '0',
    String otherFee = '0',
    String damageDetails = '',
  }) async {
    final queued = await _postBookingAction(
      ApiPaths.bookingReturn(bookingId),
      data: {
        'odometer_in_km': odometerInKm,
        'fuel_return_percent': fuelReturnPercent,
        if (actualReturnDate.trim().isNotEmpty)
          'actual_return_date': actualReturnDate.trim(),
        'fuel_charge': fuelCharge,
        'late_fee': lateFee,
        'damage_fee': damageFee,
        'other_fee': otherFee,
        'damage_details': damageDetails,
      },
    );
    return {'queued': queued};
  }

  Future<bool> cancelBooking(int bookingId) async {
    return _postBookingAction(ApiPaths.bookingCancel(bookingId));
  }

  Future<Map<String, dynamic>> fetchBookingDetail(int bookingId) async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final branchId = await _sessionStore.getActiveBranchId();
    final response = await _dio.get(
      ApiPaths.bookingDetail(bookingId),
      queryParameters: {if (branchId != null) 'branch_id': branchId},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return (_unwrap(response.data) as Map?)?.cast<String, dynamic>() ?? {};
  }

  Future<Map<String, dynamic>> updateBooking({
    required int bookingId,
    required Map<String, dynamic> payload,
  }) async {
    final branchId = await _sessionStore.getActiveBranchId();
    final queued = await _writeAndMaybeQueue(
      method: 'PUT',
      path: ApiPaths.bookingDetail(bookingId),
      data: {
        ...payload,
        if (branchId != null) 'branch_id': branchId,
      },
    );
    return {'queued': queued};
  }

  Future<List<Map<String, dynamic>>> fetchCustomers({String query = ''}) async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final response = await _dio.get(
      ApiPaths.customers,
      queryParameters: query.trim().isEmpty ? null : {'q': query.trim()},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<Map<String, dynamic>> createCustomer({
    required String name,
    String phoneNumber = '',
    String email = '',
    String idType = 'ID',
    String idNumber = '',
  }) async {
    final queued = await _writeAndMaybeQueue(
      method: 'POST',
      path: ApiPaths.customers,
      data: {
        'name': name,
        'phone_number': phoneNumber,
        'email': email,
        'id_type': idType,
        'id_number': idNumber,
      },
    );
    return {'queued': queued};
  }

  Future<Map<String, dynamic>> updateCustomer({
    required int customerId,
    required Map<String, dynamic> payload,
  }) async {
    final queued = await _writeAndMaybeQueue(
      method: 'PUT',
      path: '${ApiPaths.customers}$customerId/',
      data: payload,
    );
    return {'queued': queued};
  }

  Future<bool> deleteCustomer(int customerId) async {
    return _writeAndMaybeQueue(
      method: 'DELETE',
      path: '${ApiPaths.customers}$customerId/',
    );
  }

  Future<List<Map<String, dynamic>>> fetchPayments({
    int? bookingId,
    String query = '',
  }) async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final branchId = await _sessionStore.getActiveBranchId();
    final queryParams = <String, dynamic>{
      if (branchId != null) 'branch_id': branchId,
      if (bookingId != null) 'booking_id': bookingId,
      if (query.trim().isNotEmpty) 'q': query.trim(),
    };
    final response = await _dio.get(
      ApiPaths.payments,
      queryParameters: queryParams.isEmpty ? null : queryParams,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<List<Map<String, dynamic>>> fetchVehicles({String query = ''}) async {
    await _flushQueuedWrites();
    final response = await _dio.get(
      ApiPaths.vehicles,
      queryParameters: query.trim().isEmpty ? null : {'q': query.trim()},
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<List<Map<String, dynamic>>> fetchAvailableVehicles({
    required String pickupDate,
    required String returnDate,
  }) async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final branchId = await _sessionStore.getActiveBranchId();
    final response = await _dio.get(
      ApiPaths.bookingAvailability,
      queryParameters: {
        'pickup': pickupDate,
        'return': returnDate,
        if (branchId != null) 'branch_id': branchId,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<Map<String, dynamic>> createPayment({
    required int bookingId,
    required String amount,
    String method = 'CASH',
    String notes = '',
  }) async {
    final branchId = await _sessionStore.getActiveBranchId();
    final queued = await _writeAndMaybeQueue(
      method: 'POST',
      path: ApiPaths.payments,
      data: {
        'booking_id': bookingId,
        'amount': amount,
        'method': method,
        'notes': notes,
        if (branchId != null) 'branch_id': branchId,
      },
    );
    return {'queued': queued};
  }

  Future<Map<String, dynamic>> createRefund({
    required int paymentId,
    required String amount,
    String method = 'CASH',
    String notes = '',
  }) async {
    final branchId = await _sessionStore.getActiveBranchId();
    final queued = await _writeAndMaybeQueue(
      method: 'POST',
      path: ApiPaths.createRefund,
      data: {
        'payment_id': paymentId,
        'amount': amount,
        'method': method,
        'notes': notes,
        if (branchId != null) 'branch_id': branchId,
      },
    );
    return {'queued': queued};
  }

  Future<Map<String, dynamic>> fetchReportsFinancial({
    String period = 'monthly',
    String? dateFrom,
    String? dateTo,
  }) async {
    return _fetchReport(
      ApiPaths.reportsFinancial,
      period: period,
      dateFrom: dateFrom,
      dateTo: dateTo,
    );
  }

  Future<Map<String, dynamic>> fetchReportsFleet({
    String period = 'monthly',
    String? dateFrom,
    String? dateTo,
  }) async {
    return _fetchReport(
      ApiPaths.reportsFleet,
      period: period,
      dateFrom: dateFrom,
      dateTo: dateTo,
    );
  }

  Future<Map<String, dynamic>> fetchReportsCustomers({
    String period = 'monthly',
    String? dateFrom,
    String? dateTo,
  }) async {
    return _fetchReport(
      ApiPaths.reportsCustomers,
      period: period,
      dateFrom: dateFrom,
      dateTo: dateTo,
    );
  }

  Future<Map<String, dynamic>> fetchReportsMaintenance({
    String period = 'monthly',
    String? dateFrom,
    String? dateTo,
  }) async {
    return _fetchReport(
      ApiPaths.reportsMaintenance,
      period: period,
      dateFrom: dateFrom,
      dateTo: dateTo,
    );
  }

  Future<Map<String, dynamic>> _fetchReport(String path,
      {required String period, String? dateFrom, String? dateTo}) async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final branchId = await _sessionStore.getActiveBranchId();
    final response = await _dio.get(
      path,
      queryParameters: {
        'period': period,
        if (dateFrom != null && dateFrom.trim().isNotEmpty)
          'date_from': dateFrom.trim(),
        if (dateTo != null && dateTo.trim().isNotEmpty) 'date_to': dateTo.trim(),
        if (branchId != null) 'branch_id': branchId,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return (_unwrap(response.data) as Map?)?.cast<String, dynamic>() ?? {};
  }

  Future<List<Map<String, dynamic>>> fetchNotifications() async {
    await _flushQueuedWrites();
    final token = await _sessionStore.getToken();
    final response = await _dio.get(
      ApiPaths.notifications,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    final data = _unwrap(response.data);
    final list = data is List
        ? data
        : (data is Map<String, dynamic> && data['results'] is List
            ? data['results'] as List
            : <dynamic>[]);
    return list.map((item) => (item as Map).cast<String, dynamic>()).toList();
  }

  Future<bool> markNotificationRead(int id) async {
    return _writeAndMaybeQueue(
      method: 'POST',
      path: ApiPaths.notificationRead(id),
    );
  }

  Future<bool> deleteNotification(int id) async {
    return _writeAndMaybeQueue(
      method: 'DELETE',
      path: ApiPaths.notificationDelete(id),
    );
  }

  Future<int> pendingOfflineActionsCount() => _queue.size();

  Future<List<Map<String, dynamic>>> listPendingOfflineActions() async {
    final rows = await _queue.getAll();
    rows.sort((a, b) {
      final left = a['created_at']?.toString() ?? '';
      final right = b['created_at']?.toString() ?? '';
      return right.compareTo(left);
    });
    return rows;
  }

  String queueGroupForPath(String path) {
    if (path.contains('/internal/bookings/')) return 'Bookings';
    if (path.contains('/internal/customers/')) return 'Customers';
    if (path.contains('/internal/payments/')) return 'Payments';
    if (path.contains('/internal/maintenance/')) return 'Maintenance';
    if (path.contains('/notifications/')) return 'Notifications';
    return 'General';
  }

  Future<Map<String, int>> pendingOfflineActionCountsByGroup() async {
    final rows = await _queue.getAll();
    final out = <String, int>{
      'All': rows.length,
      'Bookings': 0,
      'Customers': 0,
      'Payments': 0,
      'Maintenance': 0,
      'Notifications': 0,
      'General': 0,
    };
    for (final row in rows) {
      final path = row['path']?.toString() ?? '';
      final group = queueGroupForPath(path);
      out[group] = (out[group] ?? 0) + 1;
    }
    return out;
  }

  Future<Map<String, int>> syncOfflineQueue() async {
    final before = await _queue.size();
    await _flushQueuedWrites();
    final after = await _queue.size();
    return {
      'before': before,
      'after': after,
      'synced': before - after,
    };
  }

  Future<Map<String, int>> syncOfflineQueueByGroup(String group) async {
    if (group == 'All') {
      final result = await syncOfflineQueue();
      return {
        'synced': result['synced'] ?? 0,
        'remaining_in_group': result['after'] ?? 0,
        'after_total': result['after'] ?? 0,
      };
    }
    final items = await _queue.getAll();
    var synced = 0;
    for (final item in items) {
      final path = item['path']?.toString() ?? '';
      if (queueGroupForPath(path) != group) continue;
      final status = await _retryQueuedItem(item);
      if (status == 'synced') synced++;
    }
    final counts = await pendingOfflineActionCountsByGroup();
    final afterTotal = await _queue.size();
    return {
      'synced': synced,
      'remaining_in_group': counts[group] ?? 0,
      'after_total': afterTotal,
    };
  }

  Future<int> clearPendingOfflineActions() async {
    final before = await _queue.size();
    await _queue.clear();
    return before;
  }

  Future<int> clearPendingOfflineActionsByGroup(String group) async {
    if (group == 'All') return clearPendingOfflineActions();
    final items = await _queue.getAll();
    var removed = 0;
    for (final item in items) {
      final id = item['id']?.toString() ?? '';
      final path = item['path']?.toString() ?? '';
      if (id.isEmpty || queueGroupForPath(path) != group) continue;
      await _queue.removeById(id);
      removed++;
    }
    return removed;
  }

  Future<bool> discardPendingOfflineAction(String id) async {
    final before = await _queue.size();
    await _queue.removeById(id);
    final after = await _queue.size();
    return after < before;
  }

  Future<String> retryPendingOfflineAction(String id) async {
    final items = await _queue.getAll();
    Map<String, dynamic>? target;
    for (final item in items) {
      if (item['id']?.toString() == id) {
        target = item;
        break;
      }
    }
    if (target == null) return 'not_found';

    return _retryQueuedItem(target);
  }

  Future<int> pendingActionsForPrefix(String prefix) async {
    final rows = await _queue.findByPathPrefix(prefix);
    return rows.length;
  }

  Future<Set<int>> pendingBookingIds() async {
    final rows = await _queue.findByPathContains('/internal/bookings/');
    final out = <int>{};
    for (final row in rows) {
      final path = row['path']?.toString() ?? '';
      final id = _extractIdAfterSegment(path, 'bookings');
      if (id != null) out.add(id);
      final bookingIdFromData =
          int.tryParse('${(row['data'] as Map?)?['booking_id'] ?? ''}');
      if (bookingIdFromData != null && bookingIdFromData > 0) {
        out.add(bookingIdFromData);
      }
    }
    return out;
  }

  Future<Set<int>> pendingCustomerIds() async {
    final rows = await _queue.findByPathContains('/internal/customers/');
    final out = <int>{};
    for (final row in rows) {
      final path = row['path']?.toString() ?? '';
      final id = _extractIdAfterSegment(path, 'customers');
      if (id != null) out.add(id);
    }
    return out;
  }

  Future<Set<int>> pendingPaymentIds() async {
    final rows = await _queue.findByPathContains('/internal/payments/');
    final out = <int>{};
    for (final row in rows) {
      final path = row['path']?.toString() ?? '';
      final id = _extractIdAfterSegment(path, 'payments');
      if (id != null) out.add(id);
      final paymentIdFromData =
          int.tryParse('${(row['data'] as Map?)?['payment_id'] ?? ''}');
      if (paymentIdFromData != null && paymentIdFromData > 0) {
        out.add(paymentIdFromData);
      }
    }
    return out;
  }

  Future<Set<int>> pendingMaintenanceTaskIds() async {
    final rows = await _queue.findByPathContains('/internal/maintenance/');
    final out = <int>{};
    for (final row in rows) {
      final path = row['path']?.toString() ?? '';
      final id = _extractIdAfterSegment(path, 'maintenance');
      if (id != null) out.add(id);
    }
    return out;
  }

  Future<Set<int>> pendingNotificationIds() async {
    final rows = await _queue.findByPathContains('/notifications/');
    final out = <int>{};
    for (final row in rows) {
      final path = row['path']?.toString() ?? '';
      final id = _extractIdAfterSegment(path, 'notifications');
      if (id != null) out.add(id);
    }
    return out;
  }

  Future<bool> _writeAndMaybeQueue({
    required String method,
    required String path,
    Map<String, dynamic>? data,
  }) async {
    final token = await _sessionStore.getToken();
    final headers = {'Authorization': 'Bearer $token'};
    await _flushQueuedWrites();
    try {
      await _dio.request(
        path,
        data: data,
        options: Options(method: method, headers: headers),
      );
      return false;
    } on DioException catch (e) {
      if (_shouldQueueError(e)) {
        await _queue.enqueue(method: method, path: path, data: data);
        return true;
      }
      rethrow;
    }
  }

  bool _shouldQueueError(DioException e) {
    if (e.response != null) return false;
    return e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.unknown;
  }

  Future<void> _flushQueuedWrites() async {
    if (_isFlushingQueue) return;
    _isFlushingQueue = true;
    try {
      final token = await _sessionStore.getToken();
      if (token == null || token.isEmpty) return;
      final headers = {'Authorization': 'Bearer $token'};
      final items = await _queue.getAll();
      for (final item in items) {
        final id = item['id']?.toString() ?? '';
        final method = item['method']?.toString() ?? 'POST';
        final path = item['path']?.toString() ?? '';
        final data = (item['data'] as Map?)?.cast<String, dynamic>();
        if (path.isEmpty || id.isEmpty) continue;
        try {
          await _dio.request(
            path,
            data: data,
            options: Options(method: method, headers: headers),
          );
          await _queue.removeById(id);
        } on DioException catch (e) {
          if (_shouldQueueError(e)) {
            break;
          }
          await _queue.removeById(id);
        }
      }
    } finally {
      _isFlushingQueue = false;
    }
  }

  int? _extractIdAfterSegment(String path, String segment) {
    final parts = path.split('/').where((part) => part.isNotEmpty).toList();
    for (var i = 0; i < parts.length; i++) {
      if (parts[i] == segment && i + 1 < parts.length) {
        final parsed = int.tryParse(parts[i + 1]);
        if (parsed != null && parsed > 0) return parsed;
      }
    }
    return null;
  }

  Future<bool> _postBookingAction(
    String path, {
    Map<String, dynamic>? data,
  }) async {
    final branchId = await _sessionStore.getActiveBranchId();
    final payload = <String, dynamic>{
      ...(data ?? const <String, dynamic>{}),
      if (branchId != null) 'branch_id': branchId,
    };
    return _writeAndMaybeQueue(
      method: 'POST',
      path: path,
      data: payload.isEmpty ? null : payload,
    );
  }

  Future<String> _retryQueuedItem(Map<String, dynamic> item) async {
    final id = item['id']?.toString() ?? '';
    final token = await _sessionStore.getToken();
    final headers = {'Authorization': 'Bearer $token'};
    final method = item['method']?.toString() ?? 'POST';
    final path = item['path']?.toString() ?? '';
    final data = (item['data'] as Map?)?.cast<String, dynamic>();
    if (path.isEmpty || id.isEmpty) {
      if (id.isNotEmpty) await _queue.removeById(id);
      return 'removed_invalid';
    }
    try {
      await _dio.request(
        path,
        data: data,
        options: Options(method: method, headers: headers),
      );
      await _queue.removeById(id);
      return 'synced';
    } on DioException catch (e) {
      if (_shouldQueueError(e)) {
        return 'still_queued';
      }
      await _queue.removeById(id);
      return 'removed_invalid';
    }
  }
}
