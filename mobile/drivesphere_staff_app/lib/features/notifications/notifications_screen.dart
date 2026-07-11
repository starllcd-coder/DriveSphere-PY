import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class NotificationsScreen extends StatefulWidget {
  final bool showBackButton;

  const NotificationsScreen({super.key, this.showBackButton = true});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final _api = StaffApiService();
  bool _loading = true;
  String _error = '';
  List<Map<String, dynamic>> _rows = const [];
  Set<int> _pendingIds = const <int>{};
  int _pendingCount = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final results = await Future.wait([
        _api.fetchNotifications(),
        _api.pendingNotificationIds(),
        _api.pendingActionsForPrefix('/notifications/'),
      ]);
      final data = results[0] as List<Map<String, dynamic>>;
      final pendingIds = results[1] as Set<int>;
      final pendingCount = results[2] as int;
      if (!mounted) return;
      setState(() {
        _rows = data;
        _pendingIds = pendingIds;
        _pendingCount = pendingCount;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _markRead(int id) async {
    final queued = await _api.markNotificationRead(id);
    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          queued
              ? 'No network. Mark-read action queued.'
              : 'Notification marked as read.',
        ),
      ),
    );
  }

  Future<void> _delete(int id) async {
    final queued = await _api.deleteNotification(id);
    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          queued
              ? 'No network. Delete action queued.'
              : 'Notification deleted.',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'Notifications',
      showBackButton: widget.showBackButton,
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    children: [
                      SectionHeader(
                        title: 'Inbox',
                        subtitle: '${_rows.length} notification(s)',
                        trailing: IconButton(
                          onPressed: _load,
                          icon: const Icon(Icons.refresh_rounded),
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (_pendingCount > 0)
                        Container(
                          width: double.infinity,
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: const Color(0xFFE8F0FE),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: const Color(0xFFB7CCF7)),
                          ),
                          child: Text('Pending notification actions to sync: $_pendingCount'),
                        ),
                      if (_rows.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.notifications_none_rounded,
                          title: 'No Notifications',
                          message: 'You are all caught up.',
                        )
                      else
                        ..._rows.map((item) {
                          final id = (item['id'] as num?)?.toInt() ?? 0;
                          final isRead = item['is_read'] == true;
                          final pending = _pendingIds.contains(id);
                          final title = item['title']?.toString().trim().isNotEmpty == true
                              ? item['title'].toString().trim()
                              : 'Notification';
                          final message = item['message']?.toString() ?? '';
                          final created = item['created_at']?.toString() ?? '';
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.fromLTRB(12, 10, 8, 10),
                            decoration: BoxDecoration(
                              color: const Color(0xF8FFFFFF),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: isRead ? const Color(0xFFD8E2F0) : const Color(0xFF9DB7DC),
                              ),
                            ),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 40,
                                  height: 40,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: isRead ? const Color(0xFFEAF1FD) : const Color(0xFFE1ECFC),
                                  ),
                                  child: Icon(
                                    isRead ? Icons.notifications_none_rounded : Icons.notifications_active_outlined,
                                    color: const Color(0xFF234E87),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              title,
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w700,
                                                color: Color(0xFF1E3355),
                                              ),
                                            ),
                                          ),
                                          if (!isRead) _pill('NEW', const Color(0xFFEAF1FD)),
                                          if (pending) ...[
                                            const SizedBox(width: 6),
                                            _pill('PENDING', const Color(0xFFFFF3D9)),
                                          ],
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        message,
                                        style: const TextStyle(
                                          color: Color(0xFF6A7390),
                                          fontSize: 13,
                                        ),
                                      ),
                                      if (created.trim().isNotEmpty) ...[
                                        const SizedBox(height: 4),
                                        Text(
                                          created,
                                          style: const TextStyle(
                                            color: Color(0xFF8A93AD),
                                            fontSize: 11,
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                                Wrap(
                                  spacing: 4,
                                  children: [
                                    if (!isRead)
                                      IconButton(
                                        tooltip: 'Mark read',
                                        onPressed: () => _markRead(id),
                                        icon: const Icon(Icons.mark_email_read_outlined, size: 18),
                                      ),
                                    IconButton(
                                      tooltip: 'Delete',
                                      onPressed: () => _delete(id),
                                      icon: const Icon(Icons.delete_outline_rounded, size: 18),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
    );
  }

  Widget _pill(String text, Color bg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFDFE7F5)),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: Color(0xFF465271),
        ),
      ),
    );
  }
}
