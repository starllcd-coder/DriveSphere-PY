import 'package:flutter/material.dart';

import '../../core/formatters/currency_formatter.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/kpi_card.dart';

class AccountantDashboardScreen extends StatefulWidget {
  const AccountantDashboardScreen({super.key});

  @override
  State<AccountantDashboardScreen> createState() =>
      _AccountantDashboardScreenState();
}

class _AccountantDashboardScreenState extends State<AccountantDashboardScreen> {
  final _api = StaffApiService();
  bool _loading = true;
  Map<String, dynamic> _kpis = const {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _api.fetchDashboardKpis();
      if (!mounted) return;
      setState(() => _kpis = data);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _loading
        ? const Center(child: CircularProgressIndicator())
        : ListView(
            children: [
              Row(
                children: [
                  Expanded(
                    child: KpiCard(
                      label: 'Earnings',
                      value: formatCurrency(_kpis['earnings']),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: KpiCard(
                      label: 'Trend Earnings',
                      value: '${_kpis['trend_earnings'] ?? 0}%',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: KpiCard(
                      label: 'Overdue Rentals',
                      value: '${_kpis['overdue_rentals'] ?? 0}',
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: KpiCard(
                      label: 'Open Maintenance',
                      value: '${_kpis['maintenance_open'] ?? 0}',
                    ),
                  ),
                ],
              ),
            ],
          );
  }
}
