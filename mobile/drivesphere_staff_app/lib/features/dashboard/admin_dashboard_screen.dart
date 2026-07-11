import 'package:flutter/material.dart';

import '../../core/formatters/currency_formatter.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/kpi_card.dart';
import '../../widgets/section_header.dart';

class AdminDashboardScreen extends StatefulWidget {
  const AdminDashboardScreen({super.key});

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> {
  final _api = StaffApiService();
  Map<String, dynamic> _kpis = const {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _api.fetchDashboardKpis();
      if (!mounted) return;
      setState(() {
        _kpis = data;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _loading
        ? const Center(child: CircularProgressIndicator())
        : RefreshIndicator(
            onRefresh: _load,
            child: ListView(
              children: [
                const SectionHeader(
                  title: 'Performance Snapshot',
                  subtitle: 'Live operational view for your active branch',
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                        child: KpiCard(
                            label: 'Total Bookings',
                            value: '${_kpis['total_bookings'] ?? 0}')),
                    const SizedBox(width: 8),
                    Expanded(
                        child: KpiCard(
                            label: 'Active Customers',
                            value: '${_kpis['active_customers'] ?? 0}')),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                        child: KpiCard(
                            label: 'Fleet Vehicles',
                            value: '${_kpis['fleet_vehicles'] ?? 0}')),
                    const SizedBox(width: 8),
                    Expanded(
                        child: KpiCard(
                            label: 'Earnings',
                            value: formatCurrency(_kpis['earnings']))),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                        child: KpiCard(
                            label: 'Active Rentals',
                            value: '${_kpis['active_rentals'] ?? 0}')),
                    const SizedBox(width: 8),
                    Expanded(
                        child: KpiCard(
                            label: 'Fleet Utilization',
                            value: '${_kpis['fleet_utilization'] ?? 0}%')),
                  ],
                ),
              ],
            ),
          );
  }
}
