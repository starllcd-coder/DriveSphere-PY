import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/kpi_card.dart';

class AgentDashboardScreen extends StatefulWidget {
  const AgentDashboardScreen({super.key});

  @override
  State<AgentDashboardScreen> createState() => _AgentDashboardScreenState();
}

class _AgentDashboardScreenState extends State<AgentDashboardScreen> {
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
                      label: 'Today Pickups',
                      value: '${_kpis['today_pickups'] ?? 0}',
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: KpiCard(
                      label: 'Active Rentals',
                      value: '${_kpis['active_rentals'] ?? 0}',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: KpiCard(
                      label: 'Today Returns',
                      value: '${_kpis['today_returns'] ?? 0}',
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: KpiCard(
                      label: 'Overdue',
                      value: '${_kpis['overdue_rentals'] ?? 0}',
                    ),
                  ),
                ],
              ),
            ],
          );
  }
}
