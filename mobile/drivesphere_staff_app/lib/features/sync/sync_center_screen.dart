import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class SyncCenterScreen extends StatefulWidget {
  const SyncCenterScreen({super.key});

  @override
  State<SyncCenterScreen> createState() => _SyncCenterScreenState();
}

class _SyncCenterScreenState extends State<SyncCenterScreen> {
  final _api = StaffApiService();
  final TextEditingController _searchController = TextEditingController();
  static const List<String> _groups = <String>[
    'All',
    'Bookings',
    'Customers',
    'Payments',
    'Maintenance',
    'Notifications',
    'General',
  ];

  bool _loading = true;
  bool _syncing = false;
  String _selectedGroup = 'All';
  String _query = '';
  List<Map<String, dynamic>> _items = const [];
  Map<String, int> _groupCounts = const <String, int>{};

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final results = await Future.wait<dynamic>([
        _api.listPendingOfflineActions(),
        _api.pendingOfflineActionCountsByGroup(),
      ]);
      final rows = results[0] as List<Map<String, dynamic>>;
      final counts = results[1] as Map<String, int>;
      if (!mounted) return;
      setState(() {
        _items = rows;
        _groupCounts = counts;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<Map<String, dynamic>> _filteredItems() {
    final query = _query.trim().toLowerCase();
    return _items.where((item) {
      final path = item['path']?.toString() ?? '';
      final method = (item['method']?.toString() ?? '').toLowerCase();
      final group = _api.queueGroupForPath(path);
      if (_selectedGroup != 'All' && group != _selectedGroup) return false;
      if (query.isEmpty) return true;
      return path.toLowerCase().contains(query) || method.contains(query);
    }).toList();
  }

  String _formatTime(String value) {
    final dt = DateTime.tryParse(value);
    if (dt == null) return '-';
    final local = dt.toLocal();
    final date =
        '${local.year}-${local.month.toString().padLeft(2, '0')}-${local.day.toString().padLeft(2, '0')}';
    final time =
        '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
    return '$date $time';
  }

  Future<void> _syncSelectedGroup() async {
    setState(() => _syncing = true);
    try {
      final result = await _api.syncOfflineQueueByGroup(_selectedGroup);
      await _load();
      if (!mounted) return;
      final synced = result['synced'] ?? 0;
      final remainingInGroup = result['remaining_in_group'] ?? 0;
      final afterTotal = result['after_total'] ?? 0;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Synced $synced action(s) in $_selectedGroup. '
            'Remaining in group: $remainingInGroup. Total queued: $afterTotal',
          ),
        ),
      );
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  Future<void> _clearSelectedGroup() async {
    final target = _selectedGroup;
    final ok = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Clear Pending Queue'),
            content: Text(
              target == 'All'
                  ? 'Remove all queued actions? This cannot be undone.'
                  : 'Remove queued actions in $target only? This cannot be undone.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Clear'),
              ),
            ],
          ),
        ) ??
        false;
    if (!ok) return;
    final removed = await _api.clearPendingOfflineActionsByGroup(target);
    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Cleared $removed queued action(s) in $target.')),
    );
  }

  Future<void> _retryOne(String id) async {
    final status = await _api.retryPendingOfflineAction(id);
    await _load();
    if (!mounted) return;
    String message;
    if (status == 'synced') {
      message = 'Action synced.';
    } else if (status == 'still_queued') {
      message = 'Still offline. Action remains queued.';
    } else if (status == 'removed_invalid') {
      message = 'Action invalid and removed from queue.';
    } else {
      message = 'Action no longer exists in queue.';
    }
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _discardOne(String id) async {
    final removed = await _api.discardPendingOfflineAction(id);
    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(removed ? 'Action removed.' : 'Action not found.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _filteredItems();
    return StaffScaffold(
      title: 'Sync Center',
      body: RefreshIndicator(
        onRefresh: _load,
        child: _loading
            ? ListView(
                children: const [
                  SizedBox(height: 220),
                  Center(child: CircularProgressIndicator()),
                ],
              )
            : ListView(
                children: [
                  SectionHeader(
                    title: 'Offline Queue',
                    subtitle: '${filtered.length} queued action(s)',
                    trailing: Wrap(
                      spacing: 6,
                      children: [
                        IconButton(
                          onPressed: _syncing ? null : _syncSelectedGroup,
                          tooltip: 'Sync $_selectedGroup',
                          icon: _syncing
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.cloud_sync_outlined),
                        ),
                        IconButton(
                          onPressed: filtered.isEmpty ? null : _clearSelectedGroup,
                          tooltip: 'Clear $_selectedGroup',
                          icon: const Icon(Icons.delete_sweep_outlined),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: 'Search path or method',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: _query.isEmpty
                          ? null
                          : IconButton(
                              onPressed: () {
                                _searchController.clear();
                                setState(() => _query = '');
                              },
                              icon: const Icon(Icons.clear),
                            ),
                    ),
                    onChanged: (value) => setState(() => _query = value),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    height: 36,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _groups.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 6),
                      itemBuilder: (context, index) {
                        final group = _groups[index];
                        final count = _groupCounts[group] ?? 0;
                        return ChoiceChip(
                          label: Text('$group ($count)'),
                          selected: _selectedGroup == group,
                          onSelected: (_) => setState(() => _selectedGroup = group),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 10),
                  if (_items.isEmpty)
                    const EmptyStateCard(
                      icon: Icons.cloud_done_outlined,
                      title: 'Queue Is Empty',
                      message: 'No queued offline actions.',
                    )
                  else if (filtered.isEmpty)
                    const EmptyStateCard(
                      icon: Icons.filter_alt_off_outlined,
                      title: 'No Matching Actions',
                      message: 'Try another search or group filter.',
                    )
                  else
                    ...filtered.map((item) {
                      final id = item['id']?.toString() ?? '';
                      final method = (item['method']?.toString() ?? 'POST').toUpperCase();
                      final path = item['path']?.toString() ?? '';
                      final created = _formatTime(item['created_at']?.toString() ?? '');
                      final group = _api.queueGroupForPath(path);
                      return Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.fromLTRB(12, 10, 8, 10),
                        decoration: BoxDecoration(
                          color: const Color(0xF8FFFFFF),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFFD8E2F0)),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: const Color(0xFFEAF1FD),
                                border: Border.all(color: const Color(0xFFD8E2F0)),
                              ),
                              child: const Icon(Icons.cloud_upload_outlined, color: Color(0xFF234E87)),
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
                                          '$group | $method',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w700,
                                            color: Color(0xFF1E3355),
                                          ),
                                        ),
                                      ),
                                      _pill(method),
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    path,
                                    style: const TextStyle(
                                      color: Color(0xFF6A7390),
                                      fontSize: 13,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Queued: $created',
                                    style: const TextStyle(
                                      color: Color(0xFF8A93AD),
                                      fontSize: 11,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Wrap(
                              spacing: 4,
                              children: [
                                IconButton(
                                  tooltip: 'Retry',
                                  onPressed: id.isEmpty ? null : () => _retryOne(id),
                                  icon: const Icon(Icons.refresh_rounded),
                                ),
                                IconButton(
                                  tooltip: 'Discard',
                                  onPressed: id.isEmpty ? null : () => _discardOne(id),
                                  icon: const Icon(Icons.delete_outline_rounded),
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

  Widget _pill(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F5FC),
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
