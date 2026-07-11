import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class OfflineWriteQueue {
  static const _key = 'staff_offline_write_queue_v1';

  Future<List<Map<String, dynamic>>> getAll() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null || raw.trim().isEmpty) return const [];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return const [];
      return decoded
          .whereType<Map>()
          .map((item) => item.cast<String, dynamic>())
          .toList();
    } catch (_) {
      return const [];
    }
  }

  Future<void> enqueue({
    required String method,
    required String path,
    Map<String, dynamic>? data,
  }) async {
    final items = await getAll();
    items.add({
      'id': DateTime.now().microsecondsSinceEpoch.toString(),
      'method': method.toUpperCase(),
      'path': path,
      'data': data ?? const <String, dynamic>{},
      'created_at': DateTime.now().toIso8601String(),
    });
    await _save(items);
  }

  Future<void> removeById(String id) async {
    final items = await getAll();
    items.removeWhere((item) => item['id']?.toString() == id);
    await _save(items);
  }

  Future<int> size() async => (await getAll()).length;

  Future<List<Map<String, dynamic>>> findByPathContains(String fragment) async {
    final items = await getAll();
    return items
        .where((item) => (item['path']?.toString() ?? '').contains(fragment))
        .toList();
  }

  Future<List<Map<String, dynamic>>> findByPathPrefix(String prefix) async {
    final items = await getAll();
    return items
        .where((item) => (item['path']?.toString() ?? '').startsWith(prefix))
        .toList();
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }

  Future<void> _save(List<Map<String, dynamic>> items) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(items));
  }
}
