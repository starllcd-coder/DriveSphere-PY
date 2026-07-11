import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

class LocalDbService {
  LocalDbService._();

  static final LocalDbService instance = LocalDbService._();
  Database? _db;

  static final Map<String, String> _webCache = <String, String>{};
  static final List<Map<String, dynamic>> _webQueue = <Map<String, dynamic>>[];
  static int _webQueueId = 1;

  bool get _useWebStore => kIsWeb;

  Future<Database> _database() async {
    if (_db != null) return _db!;
    final basePath = await getDatabasesPath();
    final dbPath = p.join(basePath, 'drivesphere_offline.db');
    _db = await openDatabase(
      dbPath,
      version: 2,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE cache_entries(
            key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at INTEGER NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE sync_queue(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            payload TEXT NOT NULL,
            fingerprint TEXT NOT NULL UNIQUE,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_error TEXT NOT NULL DEFAULT '',
            next_retry_at INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
          )
        ''');
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute("ALTER TABLE sync_queue ADD COLUMN fingerprint TEXT");
          await db.execute(
              "ALTER TABLE sync_queue ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0");
          await db.execute(
              "ALTER TABLE sync_queue ADD COLUMN last_error TEXT NOT NULL DEFAULT ''");
          await db.execute(
              "ALTER TABLE sync_queue ADD COLUMN next_retry_at INTEGER NOT NULL DEFAULT 0");
          await db.execute(
              "ALTER TABLE sync_queue ADD COLUMN updated_at INTEGER NOT NULL DEFAULT 0");
          await db.execute(
              "UPDATE sync_queue SET fingerprint = action || ':' || id WHERE fingerprint IS NULL OR fingerprint = ''");
          await db.execute(
              "UPDATE sync_queue SET updated_at = created_at WHERE updated_at = 0");
          await db.execute(
              "CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_queue_fingerprint ON sync_queue(fingerprint)");
        }
      },
    );
    return _db!;
  }

  Future<void> saveCache(String key, dynamic payload) async {
    if (_useWebStore) {
      _webCache[key] = jsonEncode(payload);
      return;
    }
    final db = await _database();
    await db.insert(
      'cache_entries',
      {
        'key': key,
        'payload': jsonEncode(payload),
        'updated_at': DateTime.now().millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getCachedList(String key) async {
    if (_useWebStore) {
      final raw = _webCache[key];
      if (raw == null) return <Map<String, dynamic>>[];
      final decoded = jsonDecode(raw);
      if (decoded is! List) return <Map<String, dynamic>>[];
      return decoded
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }
    final db = await _database();
    final rows =
        await db.query('cache_entries', where: 'key = ?', whereArgs: [key], limit: 1);
    if (rows.isEmpty) return <Map<String, dynamic>>[];
    final raw = jsonDecode(rows.first['payload'] as String);
    if (raw is! List) return <Map<String, dynamic>>[];
    return raw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<Map<String, dynamic>?> getCachedMap(String key) async {
    if (_useWebStore) {
      final raw = _webCache[key];
      if (raw == null) return null;
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return null;
      return Map<String, dynamic>.from(decoded);
    }
    final db = await _database();
    final rows =
        await db.query('cache_entries', where: 'key = ?', whereArgs: [key], limit: 1);
    if (rows.isEmpty) return null;
    final raw = jsonDecode(rows.first['payload'] as String);
    if (raw is! Map) return null;
    return Map<String, dynamic>.from(raw);
  }

  Future<void> enqueue(
    String action,
    Map<String, dynamic> payload, {
    required String fingerprint,
  }) async {
    if (_useWebStore) {
      final now = DateTime.now().millisecondsSinceEpoch;
      final index = _webQueue.indexWhere((e) => e['fingerprint'] == fingerprint);
      if (index == -1) {
        _webQueue.add({
          'id': _webQueueId++,
          'action': action,
          'payload': Map<String, dynamic>.from(payload),
          'fingerprint': fingerprint,
          'attempts': 0,
          'last_error': '',
          'next_retry_at': 0,
          'created_at': now,
          'updated_at': now,
        });
      } else {
        _webQueue[index]['payload'] = Map<String, dynamic>.from(payload);
        _webQueue[index]['updated_at'] = now;
      }
      return;
    }
    final db = await _database();
    final now = DateTime.now().millisecondsSinceEpoch;
    final existing = await db.query(
      'sync_queue',
      where: 'fingerprint = ?',
      whereArgs: [fingerprint],
      limit: 1,
    );
    if (existing.isEmpty) {
      await db.insert(
        'sync_queue',
        {
          'action': action,
          'payload': jsonEncode(payload),
          'fingerprint': fingerprint,
          'attempts': 0,
          'last_error': '',
          'next_retry_at': 0,
          'created_at': now,
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.abort,
      );
      return;
    }

    final id = existing.first['id'];
    await db.update(
      'sync_queue',
      {
        'payload': jsonEncode(payload),
        'updated_at': now,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<List<Map<String, dynamic>>> getQueue() async {
    if (_useWebStore) {
      final now = DateTime.now().millisecondsSinceEpoch;
      return _webQueue
          .where((row) => (row['next_retry_at'] as int? ?? 0) <= now)
          .map(
            (row) => {
              'id': row['id'],
              'action': row['action'],
              'payload': Map<String, dynamic>.from(row['payload'] as Map),
              'attempts': row['attempts'] ?? 0,
            },
          )
          .toList();
    }
    final db = await _database();
    final now = DateTime.now().millisecondsSinceEpoch;
    final rows = await db.query(
      'sync_queue',
      where: 'next_retry_at <= ?',
      whereArgs: [now],
      orderBy: 'id ASC',
    );
    return rows
        .map(
          (row) => {
            'id': row['id'],
            'action': row['action'],
            'payload': jsonDecode(row['payload'] as String),
            'attempts': row['attempts'] ?? 0,
          },
        )
        .toList();
  }

  Future<void> removeQueueItem(int id) async {
    if (_useWebStore) {
      _webQueue.removeWhere((row) => (row['id'] as int?) == id);
      return;
    }
    final db = await _database();
    await db.delete('sync_queue', where: 'id = ?', whereArgs: [id]);
  }

  Future<int> queueSize() async {
    if (_useWebStore) {
      return _webQueue.length;
    }
    final db = await _database();
    final rows = await db.rawQuery('SELECT COUNT(*) AS c FROM sync_queue');
    return int.tryParse(rows.first['c'].toString()) ?? 0;
  }

  Future<void> markQueueItemFailed(
    int id, {
    required String error,
    required int attempts,
  }) async {
    if (_useWebStore) {
      final now = DateTime.now().millisecondsSinceEpoch;
      final backoffSeconds = attempts <= 1 ? 15 : (attempts <= 3 ? 60 : 300);
      final index = _webQueue.indexWhere((row) => (row['id'] as int?) == id);
      if (index == -1) return;
      _webQueue[index]['attempts'] = attempts;
      _webQueue[index]['last_error'] = error;
      _webQueue[index]['next_retry_at'] = now + (backoffSeconds * 1000);
      _webQueue[index]['updated_at'] = now;
      return;
    }
    final db = await _database();
    final now = DateTime.now().millisecondsSinceEpoch;
    final backoffSeconds = attempts <= 1 ? 15 : (attempts <= 3 ? 60 : 300);
    await db.update(
      'sync_queue',
      {
        'attempts': attempts,
        'last_error': error,
        'next_retry_at': now + (backoffSeconds * 1000),
        'updated_at': now,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
