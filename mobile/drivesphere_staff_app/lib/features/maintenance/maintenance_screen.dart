import 'package:flutter/material.dart';

import '../../core/formatters/currency_formatter.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class MaintenanceScreen extends StatefulWidget {
  const MaintenanceScreen({super.key});

  @override
  State<MaintenanceScreen> createState() => _MaintenanceScreenState();
}

class _MaintenanceScreenState extends State<MaintenanceScreen> {
  final _api = StaffApiService();
  List<Map<String, dynamic>> _rows = const [];
  Set<String> _permissions = const <String>{};
  Set<int> _pendingIds = const <int>{};
  int _pendingCount = 0;
  bool _loading = true;
  String _error = '';
  String _statusFilter = 'ALL';

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
        _api.getBootstrapCachedOrFetch(),
        _api.fetchMaintenance(),
        _api.pendingMaintenanceTaskIds(),
        _api.pendingActionsForPrefix('/internal/maintenance/'),
      ]);
      final bootstrap = results[0] as StaffBootstrapPayload;
      final rows = results[1] as List<Map<String, dynamic>>;
      final pendingIds = results[2] as Set<int>;
      final pendingCount = results[3] as int;
      if (!mounted) return;
      setState(() {
        _rows = rows;
        _permissions = bootstrap.profile.permissions.toSet();
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

  bool _canMarkDone() {
    for (final perm in const [
      'maintenance.manage',
      'maintenance.complete',
      'maintenance.update',
    ]) {
      if (_permissions.contains(perm)) return true;
    }
    return false;
  }

  String _statusValue(Map<String, dynamic> item) {
    return (item['status']?.toString() ?? 'OPEN').toUpperCase();
  }

  List<Map<String, dynamic>> _filteredRows() {
    if (_statusFilter == 'ALL') return _rows;
    return _rows.where((item) => _statusValue(item) == _statusFilter).toList();
  }

  Future<void> _markDone(Map<String, dynamic> item) async {
    final id = (item['id'] as num?)?.toInt() ?? 0;
    if (id <= 0) return;
    try {
      final queued = await _api.markMaintenanceDone(id);
      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            queued
                ? 'No network. Action queued and will sync automatically.'
                : 'Maintenance task marked done.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  String _taskTitle(Map<String, dynamic> item) {
    final vehicle = item['vehicle_display']?.toString().trim();
    final category = item['category']?.toString().trim();
    final service = item['service_type']?.toString().trim();
    if (vehicle != null && vehicle.isNotEmpty) return vehicle;
    if (service != null && service.isNotEmpty) return service;
    if (category != null && category.isNotEmpty) return category;
    return 'Maintenance Task';
  }

  String _taskSubtitle(Map<String, dynamic> item) {
    final out = <String>[];
    final type = item['service_type']?.toString().trim();
    final dueDate = item['due_date']?.toString().trim();
    final branch = item['branch_name']?.toString().trim();
    if (type != null && type.isNotEmpty) out.add(type);
    if (dueDate != null && dueDate.isNotEmpty) out.add('Due $dueDate');
    if (branch != null && branch.isNotEmpty) out.add(branch);
    if (out.isEmpty) return 'Task details';
    return out.join('  |  ');
  }

  @override
  Widget build(BuildContext context) {
    final visibleRows = _filteredRows();
    return StaffScaffold(
      title: 'Maintenance',
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    children: [
                      SectionHeader(
                        title: 'Service Queue',
                        subtitle: '${visibleRows.length} task(s)',
                        trailing: IconButton(
                          onPressed: _load,
                          icon: const Icon(Icons.refresh_rounded),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 6,
                        children: [
                          for (final status in const ['ALL', 'OPEN', 'IN_PROGRESS', 'DONE'])
                            ChoiceChip(
                              label: Text(status),
                              selected: _statusFilter == status,
                              onSelected: (_) => setState(() => _statusFilter = status),
                            ),
                        ],
                      ),
                      const SizedBox(height: 10),
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
                          child: Text('Pending maintenance actions to sync: $_pendingCount'),
                        ),
                      if (visibleRows.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.build_circle_outlined,
                          title: 'No Maintenance Tasks',
                          message: 'Open tasks will appear here when available.',
                        )
                      else
                        ...visibleRows.map((item) {
                          final id = (item['id'] as num?)?.toInt() ?? 0;
                          final pending = _pendingIds.contains(id);
                          final status = _statusValue(item);
                          final canDone = _canMarkDone() && status != 'DONE';
                          final estimatedCost = item['estimated_cost'] ?? item['cost_estimate'];
                          final odometer = item['odometer_km'] ?? item['odometer'];

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.fromLTRB(12, 10, 10, 10),
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
                                  child: const Icon(
                                    Icons.build_outlined,
                                    color: Color(0xFF234E87),
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
                                              _taskTitle(item),
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w700,
                                                color: Color(0xFF1E3355),
                                              ),
                                            ),
                                          ),
                                          _statusChip(status),
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        _taskSubtitle(item),
                                        style: const TextStyle(
                                          color: Color(0xFF6A7390),
                                          fontSize: 13,
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      Wrap(
                                        spacing: 6,
                                        runSpacing: 6,
                                        children: [
                                          if (estimatedCost != null) _chip('Est. ${formatCurrency(estimatedCost)}'),
                                          if (odometer != null) _chip('Odo $odometer km'),
                                          if (pending) _chip('Pending Sync', tint: const Color(0xFFFFF3D9)),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                                if (canDone)
                                  IconButton(
                                    tooltip: 'Mark Done',
                                    onPressed: () => _markDone(item),
                                    icon: const Icon(Icons.check_circle_outline_rounded),
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

  Widget _statusChip(String status) {
    final isDone = status == 'DONE';
    final isProgress = status == 'IN_PROGRESS';
    final bg = isDone
        ? const Color(0xFFE8F6ED)
        : isProgress
            ? const Color(0xFFEAF1FD)
            : const Color(0xFFFFF3D9);
    final fg = isDone
        ? const Color(0xFF1E7A45)
        : isProgress
            ? const Color(0xFF234E87)
            : const Color(0xFF77540A);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: fg.withValues(alpha: 0.22)),
      ),
      child: Text(
        status,
        style: TextStyle(
          color: fg,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _chip(String text, {Color tint = const Color(0xFFF1F5FC)}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: tint,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFDFE7F5)),
      ),
      child: Text(
        text,
        style: const TextStyle(fontSize: 12, color: Color(0xFF465271)),
      ),
    );
  }
}
