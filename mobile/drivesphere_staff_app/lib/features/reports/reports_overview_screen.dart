import 'package:flutter/material.dart';

import '../../core/formatters/currency_formatter.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/kpi_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class ReportsOverviewScreen extends StatefulWidget {
  const ReportsOverviewScreen({super.key});

  @override
  State<ReportsOverviewScreen> createState() => _ReportsOverviewScreenState();
}

class _ReportsOverviewScreenState extends State<ReportsOverviewScreen> {
  final _api = StaffApiService();
  bool _loading = true;
  String _error = '';
  _ReportPeriod _period = _ReportPeriod.monthly;
  DateTimeRange? _customRange;
  Map<String, dynamic> _overview = const {};
  Map<String, dynamic> _financial = const {};
  Map<String, dynamic> _fleet = const {};
  Map<String, dynamic> _customers = const {};
  Map<String, dynamic> _maintenance = const {};

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
      final useCustom = _period == _ReportPeriod.custom && _customRange != null;
      final periodValue = _apiPeriodValue(_period);
      final dateFrom = useCustom ? _dateOnly(_customRange!.start) : null;
      final dateTo = useCustom ? _dateOnly(_customRange!.end) : null;
      final results = await Future.wait([
        _api.fetchReportsOverview(
          period: periodValue,
          dateFrom: dateFrom,
          dateTo: dateTo,
        ),
        _api.fetchReportsFinancial(
          period: periodValue,
          dateFrom: dateFrom,
          dateTo: dateTo,
        ),
        _api.fetchReportsFleet(
          period: periodValue,
          dateFrom: dateFrom,
          dateTo: dateTo,
        ),
        _api.fetchReportsCustomers(
          period: periodValue,
          dateFrom: dateFrom,
          dateTo: dateTo,
        ),
        _api.fetchReportsMaintenance(
          period: periodValue,
          dateFrom: dateFrom,
          dateTo: dateTo,
        ),
      ]);
      if (!mounted) return;
      setState(() {
        _overview = results[0];
        _financial = results[1];
        _fleet = results[2];
        _customers = results[3];
        _maintenance = results[4];
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Unable to load reports. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _apiPeriodValue(_ReportPeriod period) {
    switch (period) {
      case _ReportPeriod.today:
        return 'today';
      case _ReportPeriod.weekly:
        return 'weekly';
      case _ReportPeriod.monthly:
      case _ReportPeriod.custom:
        return 'monthly';
    }
  }

  String _periodLabel(_ReportPeriod period) {
    switch (period) {
      case _ReportPeriod.today:
        return 'Today';
      case _ReportPeriod.weekly:
        return 'Weekly';
      case _ReportPeriod.monthly:
        return 'Monthly';
      case _ReportPeriod.custom:
        return 'Custom';
    }
  }

  String _dateOnly(DateTime value) {
    final y = value.year.toString().padLeft(4, '0');
    final m = value.month.toString().padLeft(2, '0');
    final d = value.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }

  String _activeFilterText() {
    if (_period == _ReportPeriod.custom && _customRange != null) {
      return '${_dateOnly(_customRange!.start)} to ${_dateOnly(_customRange!.end)}';
    }
    return _periodLabel(_period);
  }

  Future<void> _openFilters() async {
    var selectedPeriod = _period;
    var selectedRange = _customRange;

    final result = await showDialog<_ReportFilterSelection>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            Future<void> pickDateRange() async {
              final now = DateTime.now();
              final firstDate = DateTime(now.year - 2);
              final lastDate = DateTime(now.year + 2, 12, 31);
              final picked = await showDateRangePicker(
                context: context,
                firstDate: firstDate,
                lastDate: lastDate,
                initialDateRange: selectedRange,
              );
              if (picked == null) return;
              setDialogState(() => selectedRange = picked);
            }

            return AlertDialog(
              title: const Text('Filter Reports'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButtonFormField<_ReportPeriod>(
                    initialValue: selectedPeriod,
                    decoration: const InputDecoration(labelText: 'Period'),
                    items: _ReportPeriod.values
                        .map(
                          (item) => DropdownMenuItem(
                            value: item,
                            child: Text(_periodLabel(item)),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      if (value == null) return;
                      setDialogState(() => selectedPeriod = value);
                    },
                  ),
                  if (selectedPeriod == _ReportPeriod.custom) ...[
                    const SizedBox(height: 12),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: OutlinedButton.icon(
                        onPressed: pickDateRange,
                        icon: const Icon(Icons.date_range_rounded),
                        label: Text(
                          selectedRange == null
                              ? 'Select date range'
                              : '${_dateOnly(selectedRange!.start)} to ${_dateOnly(selectedRange!.end)}',
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: selectedPeriod == _ReportPeriod.custom &&
                          selectedRange == null
                      ? null
                      : () {
                          Navigator.of(context).pop(
                            _ReportFilterSelection(
                              period: selectedPeriod,
                              range: selectedRange,
                            ),
                          );
                        },
                  child: const Text('Apply'),
                ),
              ],
            );
          },
        );
      },
    );

    if (result == null) return;
    setState(() {
      _period = result.period;
      _customRange = result.period == _ReportPeriod.custom ? result.range : null;
    });
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'Reports Overview',
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                children: [
                  SectionHeader(
                    title: 'Performance Snapshot',
                    subtitle: 'Filter: ${_activeFilterText()}',
                    trailing: Wrap(
                      spacing: 8,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        FilledButton.tonalIcon(
                          onPressed: _openFilters,
                          icon: const Icon(Icons.filter_alt_outlined, size: 18),
                          label: const Text('Filter'),
                        ),
                        IconButton(
                          onPressed: _load,
                          icon: const Icon(Icons.refresh_rounded),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 6),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        for (final period in const [
                          _ReportPeriod.today,
                          _ReportPeriod.weekly,
                          _ReportPeriod.monthly,
                        ])
                          Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: ChoiceChip(
                              label: Text(_periodLabel(period)),
                              selected: _period == period,
                              onSelected: (_) async {
                                setState(() {
                                  _period = period;
                                  _customRange = null;
                                });
                                await _load();
                              },
                            ),
                          ),
                        ChoiceChip(
                          label: Text(
                            _period == _ReportPeriod.custom && _customRange != null
                                ? 'Custom*'
                                : 'Custom',
                          ),
                          selected: _period == _ReportPeriod.custom,
                          onSelected: (_) => _openFilters(),
                        ),
                      ],
                    ),
                  ),
                  if (_error.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFF0F0),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFF1C8C8)),
                      ),
                      child: Text(
                        _error,
                        style: const TextStyle(
                          color: Color(0xFF9E2A2A),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 12),
                  const Text('Overview', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  GridView.count(
                    crossAxisCount: 2,
                    crossAxisSpacing: 10,
                    mainAxisSpacing: 10,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    children: [
                      KpiCard(
                        label: 'Bookings',
                        value: '${_overview['bookings_count'] ?? 0}',
                      ),
                      KpiCard(
                        label: 'Active Rentals',
                        value: '${_overview['active_rentals'] ?? 0}',
                      ),
                      KpiCard(
                        label: 'Revenue Net',
                        value: formatCurrency(_overview['revenue_net']),
                      ),
                      KpiCard(
                        label: 'Fleet Utilization',
                        value: '${_overview['fleet_utilization'] ?? 0}%',
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('Financial', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  KpiCard(
                    label: 'Gross Revenue',
                    value: formatCurrency(_financial['gross_revenue']),
                  ),
                  const SizedBox(height: 8),
                  KpiCard(
                    label: 'Net Revenue',
                    value: formatCurrency(_financial['net_revenue']),
                  ),
                  const SizedBox(height: 12),
                  const Text('Fleet & Customers', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  KpiCard(
                    label: 'Fleet Count',
                    value: '${_fleet['fleet_count'] ?? 0}',
                  ),
                  const SizedBox(height: 8),
                  KpiCard(
                    label: 'New Customers',
                    value: '${_customers['new_customers'] ?? 0}',
                  ),
                  const SizedBox(height: 8),
                  KpiCard(
                    label: 'Maintenance Open',
                    value: '${_maintenance['overdue_open'] ?? 0}',
                  ),
                ],
              ),
            ),
    );
  }
}

enum _ReportPeriod { today, weekly, monthly, custom }

class _ReportFilterSelection {
  final _ReportPeriod period;
  final DateTimeRange? range;

  const _ReportFilterSelection({required this.period, this.range});
}
