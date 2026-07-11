import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/kpi_card.dart';

class MechanicDashboardScreen extends StatefulWidget {
  const MechanicDashboardScreen({super.key});

  @override
  State<MechanicDashboardScreen> createState() =>
      _MechanicDashboardScreenState();
}

class _MechanicDashboardScreenState extends State<MechanicDashboardScreen> {
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
                      label: 'Services Due',
                      value: '${_kpis['upcoming_services'] ?? 0}',
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
              const SizedBox(height: 8),
              KpiCard(
                label: 'Docs Expiring in 30d',
                value: '${_kpis['expiring_documents'] ?? 0}',
              ),
            ],
          );
  }
}
