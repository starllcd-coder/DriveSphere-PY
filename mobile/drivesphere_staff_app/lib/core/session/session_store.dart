import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SessionStore {
  static const _tokenKey = 'staff_access_token';
  static const _branchIdKey = 'staff_active_branch_id';
  static const _rememberMeKey = 'staff_remember_me';
  static const _lastIdentifierKey = 'staff_last_identifier';
  static const _storage = FlutterSecureStorage();
  static String? _volatileToken;

  Future<void> saveToken(String token, {bool persist = true}) async {
    if (token.trim().isEmpty) return;
    _volatileToken = token.trim();
    if (persist) {
      await _storage.write(key: _tokenKey, value: token.trim());
      return;
    }
    await _storage.delete(key: _tokenKey);
  }

  Future<String?> getToken() async {
    final memory = _volatileToken;
    if (memory != null && memory.trim().isNotEmpty) return memory;
    final value = await _storage.read(key: _tokenKey);
    if (value == null || value.trim().isEmpty) return null;
    return value;
  }

  Future<void> saveActiveBranchId(int branchId) async {
    await _storage.write(key: _branchIdKey, value: branchId.toString());
  }

  Future<int?> getActiveBranchId() async {
    final raw = await _storage.read(key: _branchIdKey);
    final parsed = int.tryParse(raw ?? '');
    return parsed;
  }

  Future<void> saveRememberMe(bool enabled) async {
    await _storage.write(key: _rememberMeKey, value: enabled ? '1' : '0');
  }

  Future<bool> getRememberMe() async {
    final raw = await _storage.read(key: _rememberMeKey);
    if (raw == null) return true;
    return raw == '1';
  }

  Future<void> saveLastIdentifier(String identifier) async {
    await _storage.write(key: _lastIdentifierKey, value: identifier.trim());
  }

  Future<String?> getLastIdentifier() async {
    final value = await _storage.read(key: _lastIdentifierKey);
    if (value == null || value.trim().isEmpty) return null;
    return value.trim();
  }

  Future<void> clear() async {
    _volatileToken = null;
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _branchIdKey);
  }
}
