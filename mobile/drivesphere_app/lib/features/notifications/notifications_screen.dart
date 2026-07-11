import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../models/notification_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_empty_state.dart';
import '../../widgets/app_error_state.dart';
import '../../widgets/app_snackbar.dart';
import '../../widgets/app_skeleton.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final ApiService _apiService = ApiService();

  bool _loading = true;
  bool _retrying = false;
  String? _error;
  List<NotificationModel> _items = <NotificationModel>[];
  final Set<int> _busyIds = <int>{};

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications({
    bool showLoader = true,
    bool showRetrying = false,
  }) async {
    setState(() {
      if (showLoader) _loading = true;
      _retrying = showRetrying;
      _error = null;
    });
    try {
      final items = await _apiService.fetchNotifications();
      if (!mounted) return;
      setState(() => _items = items);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'notifications.failed_load'.tr();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _retrying = false;
        });
      }
    }
  }

  Future<void> _refreshNotifications() async {
    await _loadNotifications(showLoader: false);
  }

  Future<void> _retryNotifications() async {
    await _loadNotifications(showLoader: false, showRetrying: true);
  }

  Color _typeColor(String type) {
    switch (type.toUpperCase()) {
      case 'BOOKING':
        return const Color(0xFF234E8C);
      case 'PAYMENT':
        return const Color(0xFF179D57);
      case 'REMINDER':
        return const Color(0xFFD28A17);
      default:
        return const Color(0xFF6B7280);
    }
  }

  IconData _typeIcon(String type) {
    switch (type.toUpperCase()) {
      case 'BOOKING':
        return Icons.calendar_month_rounded;
      case 'PAYMENT':
        return Icons.payments_rounded;
      case 'REMINDER':
        return Icons.notifications_active_rounded;
      default:
        return Icons.notifications_rounded;
    }
  }

  NotificationModel _copyNotification(
    NotificationModel item, {
    bool? isRead,
  }) {
    return NotificationModel(
      id: item.id,
      title: item.title,
      message: item.message,
      notificationType: item.notificationType,
      isRead: isRead ?? item.isRead,
      createdAt: item.createdAt,
    );
  }

  Future<void> _markRead(NotificationModel item) async {
    if (item.isRead || _busyIds.contains(item.id)) return;
    final idx = _items.indexWhere((n) => n.id == item.id);
    if (idx == -1) return;

    final previous = _items[idx];
    setState(() {
      _busyIds.add(item.id);
      _items[idx] = _copyNotification(item, isRead: true);
    });

    try {
      await _apiService.markNotificationRead(item.id);
    } catch (_) {
      if (!mounted) return;
      setState(() => _items[idx] = previous);
      AppSnackBar.error(context, 'notifications.failed_load'.tr());
    } finally {
      if (mounted) {
        setState(() => _busyIds.remove(item.id));
      }
    }
  }

  Future<void> _delete(NotificationModel item) async {
    if (_busyIds.contains(item.id)) return;
    final idx = _items.indexWhere((n) => n.id == item.id);
    if (idx == -1) return;
    final removed = _items[idx];

    setState(() {
      _busyIds.add(item.id);
      _items.removeAt(idx);
    });

    try {
      await _apiService.deleteNotification(item.id);
    } catch (_) {
      if (!mounted) return;
      setState(() => _items.insert(idx, removed));
      AppSnackBar.error(context, 'notifications.failed_load'.tr());
    } finally {
      if (mounted) {
        setState(() => _busyIds.remove(item.id));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          'notifications.title'.tr(),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _refreshNotifications,
        child: _loading
            ? const AppSkeletonList(itemHeight: 120, count: 6)
            : _error != null
                ? AppErrorState(
                    title: 'notifications.failed_load'.tr(),
                    subtitle: _error!,
                    onRetry: _retryNotifications,
                    isRetrying: _retrying,
                  )
                : _items.isEmpty
                    ? AppEmptyState(
                        icon: Icons.notifications_off_outlined,
                        title: 'notifications.empty_title'.tr(),
                        subtitle: '',
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                        itemCount: _items.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 12),
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          final busy = _busyIds.contains(item.id);

                          return Opacity(
                            opacity: busy ? 0.65 : 1,
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: item.isRead
                                    ? Colors.white
                                    : const Color(0xFFF3F7FF),
                                borderRadius: BorderRadius.circular(20),
                                boxShadow: [
                                  BoxShadow(
                                    color: const Color(0xFFB7C0D1).withAlpha(36),
                                    blurRadius: 12,
                                    offset: const Offset(0, 8),
                                  ),
                                ],
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    width: 42,
                                    height: 42,
                                    decoration: BoxDecoration(
                                      color: _typeColor(item.notificationType)
                                          .withAlpha(31),
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      _typeIcon(item.notificationType),
                                      color: _typeColor(item.notificationType),
                                      size: 22,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Expanded(
                                              child: Text(
                                                item.title,
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                style: TextStyle(
                                                  fontSize: 15,
                                                  fontWeight: item.isRead
                                                      ? FontWeight.w600
                                                      : FontWeight.w700,
                                                  color: const Color(0xFF162E60),
                                                ),
                                              ),
                                            ),
                                            if (busy)
                                              const SizedBox(
                                                width: 14,
                                                height: 14,
                                                child:
                                                    CircularProgressIndicator(
                                                  strokeWidth: 2,
                                                ),
                                              )
                                            else if (!item.isRead)
                                              Container(
                                                width: 9,
                                                height: 9,
                                                decoration: const BoxDecoration(
                                                  color: Color(0xFF234E8C),
                                                  shape: BoxShape.circle,
                                                ),
                                              ),
                                          ],
                                        ),
                                        const SizedBox(height: 6),
                                        Text(
                                          item.message,
                                          style: const TextStyle(
                                            fontSize: 13,
                                            height: 1.5,
                                            color: Color(0xFF687181),
                                          ),
                                        ),
                                        const SizedBox(height: 10),
                                        Row(
                                          children: [
                                            if (!item.isRead)
                                              TextButton(
                                                onPressed: busy
                                                    ? null
                                                    : () => _markRead(item),
                                                style: TextButton.styleFrom(
                                                  padding: EdgeInsets.zero,
                                                  minimumSize: Size.zero,
                                                  tapTargetSize:
                                                      MaterialTapTargetSize
                                                          .shrinkWrap,
                                                ),
                                                child: Text(
                                                  'notifications.mark_read'.tr(),
                                                  style: const TextStyle(
                                                    fontSize: 12,
                                                    fontWeight: FontWeight.w600,
                                                  ),
                                                ),
                                              ),
                                            if (!item.isRead)
                                              const SizedBox(width: 16),
                                            TextButton(
                                              onPressed: busy
                                                  ? null
                                                  : () => _delete(item),
                                              style: TextButton.styleFrom(
                                                padding: EdgeInsets.zero,
                                                minimumSize: Size.zero,
                                                tapTargetSize:
                                                    MaterialTapTargetSize
                                                        .shrinkWrap,
                                              ),
                                              child: Text(
                                                'notifications.delete'.tr(),
                                                style: const TextStyle(
                                                  fontSize: 12,
                                                  fontWeight: FontWeight.w600,
                                                  color: Color(0xFFD14848),
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
