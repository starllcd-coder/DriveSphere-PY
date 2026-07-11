import 'package:flutter/material.dart';

import '../../core/formatters/currency_formatter.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class VehiclesScreen extends StatefulWidget {
  const VehiclesScreen({super.key});

  @override
  State<VehiclesScreen> createState() => _VehiclesScreenState();
}

class _VehiclesScreenState extends State<VehiclesScreen> {
  final _api = StaffApiService();
  final _searchController = TextEditingController();
  bool _loading = true;
  String _error = '';
  List<Map<String, dynamic>> _rows = const [];
  String _statusFilter = 'ALL';

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

  Future<void> _load({String query = ''}) async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final rows = await _api.fetchVehicles(query: query);
      if (!mounted) return;
      setState(() => _rows = rows);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<Map<String, dynamic>> _filteredRows() {
    if (_statusFilter == 'ALL') return _rows;
    return _rows
        .where((item) => (item['status']?.toString() ?? '') == _statusFilter)
        .toList();
  }

  String _vehicleTitle(Map<String, dynamic> item) {
    final brand = item['brand_name']?.toString() ?? '';
    final model = item['model_name']?.toString() ?? '';
    final year = item['year']?.toString() ?? '';
    final label = '$brand $model'.trim();
    if (year.isEmpty) return label.isEmpty ? 'Vehicle' : label;
    return label.isEmpty ? 'Vehicle $year' : '$label ($year)';
  }

  @override
  Widget build(BuildContext context) {
    final visibleRows = _filteredRows();
    return StaffScaffold(
      title: 'Vehicles',
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : RefreshIndicator(
                  onRefresh: () => _load(query: _searchController.text.trim()),
                  child: ListView(
                    children: [
                      SectionHeader(
                        title: 'Fleet Explorer',
                        subtitle: '${visibleRows.length} vehicle(s)',
                        trailing: IconButton(
                          onPressed: () => _load(query: _searchController.text.trim()),
                          icon: const Icon(Icons.refresh_rounded),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _searchController,
                              decoration: const InputDecoration(
                                hintText: 'Search by brand, model, city, status...',
                              ),
                              onSubmitted: (value) => _load(query: value),
                            ),
                          ),
                          const SizedBox(width: 8),
                          FilledButton.tonal(
                            onPressed: () => _load(query: _searchController.text.trim()),
                            child: const Text('Search'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 6,
                        children: [
                          for (final status in const [
                            'ALL',
                            'AVAILABLE',
                            'RESERVED',
                            'RENTED',
                            'MAINTENANCE',
                          ])
                            ChoiceChip(
                              label: Text(status),
                              selected: _statusFilter == status,
                              onSelected: (_) => setState(() => _statusFilter = status),
                            ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      if (visibleRows.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.directions_car_outlined,
                          title: 'No Vehicles Found',
                          message: 'Try another search/filter to find vehicles quickly.',
                        )
                      else
                        ...visibleRows.map((item) {
                          final status = item['status']?.toString() ?? 'UNKNOWN';
                          final dailyRate = formatCurrency(item['daily_rate']);
                          final deposit = formatCurrency(item['deposit_amount']);
                          final rating = (item['rating'] as num?)?.toStringAsFixed(1) ?? '0.0';
                          final city = item['city']?.toString() ?? '';

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xF8FFFFFF),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFFD8E2F0)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _vehicleTitle(item),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF1E3355),
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  city.isEmpty ? 'Status: $status' : '$city | $status',
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
                                    _chip('Rate: $dailyRate'),
                                    _chip('Deposit: $deposit'),
                                    _chip('Rating: $rating'),
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

  Widget _chip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F5FC),
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


